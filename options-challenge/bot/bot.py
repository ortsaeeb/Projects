"""Webull options bot: signal watcher, entry, and automatic exit management.

Paper mode is the default. Live orders require BOTH "mode": "live" in config.json AND the --live flag.

Commands (run `python bot.py -h` for all flags):
  check                        connectivity test: account balance, SPY quote, one option quote
  chain SPY --type C           today's option chain near the money with live bid/ask
  buy SPY --type C             buy the nearest-money contract with ask <= max price, then manage exits
  manage SPY260924C00769000 --entry 0.58
                               attach take-profit + stop (+ breakeven trail) to a position you already hold
  watch QQQ --call-above 742.7 --put-below 740.2 [--auto]
                               watch 5-min closes; alert (or with --auto, buy + manage) on a trigger
  rsi2                         daily RSI(2) pullback scan on SPY/QQQ/IWM (the strategy that backtested well)

Safety: max cost per trade, max trades per day, max daily loss, no new entries after 14:30 CT,
forced exit at flatten_time_ct, and a kill switch: create a file named KILL in this folder to stop all entries.
"""
import argparse
import csv
import json
import math
import os
import sys
import time
import logging
import uuid
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
# The Webull SDK logs full request headers (incl. access tokens) on errors; keep that out of the console.
logging.getLogger("webull").setLevel(logging.CRITICAL)
logging.getLogger().setLevel(logging.WARNING)
CT = ZoneInfo("America/Chicago")
LOG_DIR = os.path.join(HERE, "logs")
os.makedirs(LOG_DIR, exist_ok=True)


# ----------------------------------------------------------------- helpers
def now_ct():
    return datetime.now(CT)


def log(msg):
    line = f"{now_ct():%Y-%m-%d %H:%M:%S} CT  {msg}"
    print(line, flush=True)
    with open(os.path.join(LOG_DIR, f"bot-{now_ct():%Y-%m-%d}.log"), "a") as f:
        f.write(line + "\n")


def occ_symbol(underlying, expiry, cp, strike):
    """SPY, date(2026,9,24), 'C', 769 -> SPY260924C00769000"""
    return f"{underlying.upper()}{expiry:%y%m%d}{cp.upper()}{int(round(strike * 1000)):08d}"


def parse_occ(sym):
    i = len(sym) - 15
    return sym[:i], datetime.strptime(sym[i:i + 6], "%y%m%d").date(), sym[i + 6], int(sym[i + 7:]) / 1000


def short_err(e):
    """One-line error text without request headers/tokens."""
    txt = str(e)
    for marker in ("Code:", "Msg:"):
        if marker in txt:
            return txt[txt.index("HTTP Status") if "HTTP Status" in txt else 0:].split(", RequestID")[0]
    return txt[:200]


def r2(x):
    return round(x + 1e-9, 2)


def find(obj, *keys):
    """Depth-first search for the first matching key (case-insensitive) in nested dict/list JSON."""
    want = {k.lower() for k in keys}
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() in want and v not in (None, ""):
                return v
        for v in obj.values():
            got = find(v, *keys)
            if got is not None:
                return got
    elif isinstance(obj, list):
        for v in obj:
            got = find(v, *keys)
            if got is not None:
                return got
    return None


def dict_rows(obj, key):
    """All dicts anywhere in a JSON response that directly contain `key` (e.g. quote rows or bar rows)."""
    out = []
    if isinstance(obj, dict):
        if key in obj:
            out.append(obj)
        for v in obj.values():
            if isinstance(v, (dict, list)):
                out += dict_rows(v, key)
    elif isinstance(obj, list):
        for v in obj:
            out += dict_rows(v, key)
    return out


# ----------------------------------------------------------------- state / risk
class RiskState:
    def __init__(self, cfg):
        self.cfg = cfg["risk"]
        self.path = os.path.join(LOG_DIR, f"state-{now_ct():%Y-%m-%d}.json")
        self.s = {"trades": 0, "realized": 0.0}
        if os.path.exists(self.path):
            self.s = json.load(open(self.path))

    def save(self):
        json.dump(self.s, open(self.path, "w"))

    def can_enter(self, cost):
        if os.path.exists(os.path.join(HERE, "KILL")):
            return False, "KILL file present"
        t = now_ct().time()
        if not (datetime.strptime("08:35", "%H:%M").time() <= t <= datetime.strptime("14:30", "%H:%M").time()):
            return False, "outside entry hours (08:35-14:30 CT)"
        if self.s["trades"] >= self.cfg["max_trades_per_day"]:
            return False, "max trades per day reached"
        if -self.s["realized"] >= self.cfg["max_daily_loss"]:
            return False, "max daily loss reached"
        if cost > self.cfg["max_cost_per_trade"]:
            return False, f"cost ${cost:.2f} > max ${self.cfg['max_cost_per_trade']}"
        return True, ""

    def record(self, pnl):
        self.s["trades"] += 1
        self.s["realized"] = round(self.s["realized"] + pnl, 2)
        self.save()
        with open(os.path.join(LOG_DIR, "trades.csv"), "a", newline="") as f:
            csv.writer(f).writerow([now_ct().isoformat(timespec="seconds"), round(pnl, 2), self.s["realized"]])


# ----------------------------------------------------------------- broker
class Broker:
    """Thin wrapper over the official Webull OpenAPI SDK (pip install webull-openapi-python-sdk)."""

    def __init__(self, cfg, live):
        from webull.core.client import ApiClient
        from webull.data.data_client import DataClient
        from webull.trade.trade_client import TradeClient

        for name in list(logging.root.manager.loggerDict):
            if name.startswith("webull"):
                logging.getLogger(name).setLevel(logging.CRITICAL)
        api = ApiClient(cfg["app_key"], cfg["app_secret"], cfg["region_id"])
        if cfg.get("api_endpoint"):
            api.add_endpoint(cfg["region_id"], cfg["api_endpoint"])
        api.set_token_dir(os.path.join(HERE, "conf"))
        self.data = DataClient(api)
        self.trade = TradeClient(api)
        self.account = cfg["account_id"]
        self.live = live

    @staticmethod
    def _ok(res, what):
        if isinstance(res, Exception):
            raise RuntimeError(f"{what} failed: {res}")
        if res.status_code != 200:
            raise RuntimeError(f"{what} failed: HTTP {res.status_code} {res.text[:300]}")
        return res.json()

    # ---- market data
    def stock_quote(self, symbol):
        from webull.data.common.category import Category
        j = self._ok(self.data.market_data.get_snapshot(symbol, Category.US_STOCK.name), "stock snapshot")
        row = (dict_rows(j, "symbol") or [j])[0]
        return {k: float(find(row, *names) or 0) for k, names in
                (("price", ("price", "close", "last")), ("bid", ("bid", "bid_price")), ("ask", ("ask", "ask_price")))}

    def bars_5m(self, symbol, count=80):
        from webull.data.common.category import Category
        from webull.data.common.timespan import Timespan
        j = self._ok(self.data.market_data.get_batch_history_bar([symbol], Category.US_STOCK.name,
                                                                 Timespan.M5.name, count), "bars")
        rows = dict_rows(j, "close")
        bars = [{"time": find(r, "time"), "o": float(find(r, "open")), "h": float(find(r, "high")),
                 "l": float(find(r, "low")), "c": float(find(r, "close")), "v": float(find(r, "volume") or 0)} for r in rows]
        return sorted(bars, key=lambda b: str(b["time"]))

    def option_quotes(self, occ_list):
        from webull.data.common.category import Category
        out = {}
        for i in range(0, len(occ_list), 20):
            chunk = occ_list[i:i + 20]
            j = self._ok(self.data.option_market_data.get_option_snapshot(",".join(chunk), Category.US_OPTION.name),
                         "option snapshot")
            for row in dict_rows(j, "symbol"):
                sym = find(row, "symbol")
                out[sym] = {"bid": float(find(row, "bid", "bid_price") or 0),
                            "ask": float(find(row, "ask", "ask_price") or 0),
                            "last": float(find(row, "price", "last", "close") or 0),
                            "volume": float(find(row, "volume") or 0),
                            "oi": float(find(row, "open_interest") or 0),
                            "iv": float(find(row, "implied_volatility", "iv") or 0),
                            "delta": float(find(row, "delta") or 0)}
        return out

    def chain(self, underlying, expiry, cp, spot, width=12):
        """Build OCC symbols for $1 strikes around spot (SPY/QQQ/IWM list $1 strikes) and quote them."""
        base = round(spot)
        strikes = [base + d for d in range(-width, width + 1)]
        syms = [occ_symbol(underlying, expiry, cp, k) for k in strikes]
        q = self.option_quotes(syms)
        return [(s, q[s]) for s in syms if s in q]

    # ---- account / orders
    def positions(self):
        return self._ok(self.trade.account_v2.get_account_position(self.account), "positions")

    def accounts(self):
        return self._ok(self.trade.account_v2.get_account_list(), "account list")

    def balance(self):
        return self._ok(self.trade.account_v2.get_account_balance(self.account), "balance")

    def place_option(self, occ, side, qty, limit):
        und, exp, cp, strike = parse_occ(occ)
        coid = uuid.uuid4().hex
        order = [{
            "client_order_id": coid, "combo_type": "NORMAL", "order_type": "LIMIT",
            "quantity": str(qty), "limit_price": f"{limit:.2f}", "option_strategy": "SINGLE",
            "side": side, "time_in_force": "DAY", "entrust_type": "QTY",
            "legs": [{"side": side, "quantity": str(qty), "symbol": und, "strike_price": f"{strike:g}",
                      "option_expire_date": f"{exp:%Y-%m-%d}", "instrument_type": "OPTION",
                      "option_type": "CALL" if cp == "C" else "PUT", "market": "US"}],
        }]
        if not self.live:
            raise RuntimeError("Broker.place_option called in paper mode")
        self._ok(self.trade.order_v2.place_option(self.account, order), "place option")
        log(f"LIVE ORDER {side} {qty} {occ} @ {limit:.2f}  id={coid}")
        return coid

    def cancel(self, coid):
        self._ok(self.trade.order_v2.cancel_option(self.account, coid), "cancel")

    def order_status(self, coid):
        j = self._ok(self.trade.order_v2.get_order_detail(self.account, coid), "order detail")
        status = str(find(j, "status", "order_status") or "").upper()
        filled = float(find(j, "filled_quantity", "filled_qty") or 0)
        px = float(find(j, "filled_price", "avg_filled_price", "average_price") or 0)
        return status, filled, px


class PaperBroker(Broker):
    """Real quotes, simulated fills (buy fills when ask <= limit, sell when bid >= limit)."""

    def __init__(self, cfg):
        super().__init__(cfg, live=False)
        self.orders = {}

    def place_option(self, occ, side, qty, limit):
        coid = uuid.uuid4().hex
        self.orders[coid] = {"occ": occ, "side": side, "qty": qty, "limit": limit, "status": "SUBMITTED", "px": 0}
        log(f"PAPER ORDER {side} {qty} {occ} @ {limit:.2f}  id={coid[:8]}")
        return coid

    def cancel(self, coid):
        if self.orders[coid]["status"] != "FILLED":
            self.orders[coid]["status"] = "CANCELLED"

    def order_status(self, coid):
        o = self.orders[coid]
        if o["status"] == "SUBMITTED":
            q = self.option_quotes([o["occ"]]).get(o["occ"])
            if q:
                if o["side"] == "BUY" and 0 < q["ask"] <= o["limit"]:
                    o.update(status="FILLED", px=q["ask"])
                elif o["side"] == "SELL" and q["bid"] >= o["limit"]:
                    o.update(status="FILLED", px=q["bid"])
        return o["status"], (o["qty"] if o["status"] == "FILLED" else 0), o["px"]


# ----------------------------------------------------------------- trading logic
def wait_fill(broker, coid, seconds, poll):
    for _ in range(max(1, int(seconds / max(poll, 1)))):
        status, filled, px = broker.order_status(coid)
        if "FILLED" in status and "PARTIAL" not in status:
            return px
        if status in ("CANCELLED", "REJECTED", "FAILED", "EXPIRED"):
            return None
        time.sleep(poll)
    return None


def sell_now(broker, occ, qty, poll):
    """Aggressive exit: sell at bid, re-price down up to 4 times."""
    for step in (0.00, 0.02, 0.05, 0.10, 0.20):
        q = broker.option_quotes([occ]).get(occ, {"bid": 0})
        px = max(0.01, r2(q["bid"] - step))
        coid = broker.place_option(occ, "SELL", qty, px)
        got = wait_fill(broker, coid, 15, poll)
        if got is not None:
            return got
        broker.cancel(coid)
    log("!! could not exit automatically — SELL MANUALLY IN WEBULL")
    return None


def manage(broker, risk, occ, qty, entry, cfg):
    """Take-profit limit + stop + breakeven trail + forced exit at flatten time."""
    rk = cfg["risk"]
    tp = r2(entry * (1 + rk["take_profit_pct"]))
    stop = r2(entry * (1 - rk["stop_loss_pct"]))
    trail_at = r2(entry * 1.4)  # after +40%, the stop moves to breakeven
    flatten = datetime.strptime(rk["flatten_time_ct"], "%H:%M").time()
    log(f"MANAGE {occ} x{qty} entry {entry:.2f} | take-profit {tp:.2f} | stop {stop:.2f} | breakeven after {trail_at:.2f}")
    tp_id = broker.place_option(occ, "SELL", qty, tp)
    while True:
        status, filled, px = broker.order_status(tp_id)
        if "FILLED" in status and "PARTIAL" not in status:
            pnl = (px - entry) * 100 * qty
            log(f"TAKE-PROFIT FILLED @ {px:.2f}  P/L ${pnl:+.2f}")
            risk.record(pnl)
            return
        q = broker.option_quotes([occ]).get(occ)
        if q and q["bid"] > 0:
            if q["bid"] >= trail_at and stop < entry:
                stop = entry
                log(f"bid {q['bid']:.2f} >= {trail_at:.2f}: stop raised to breakeven {stop:.2f}")
            reason = None
            if q["bid"] <= stop:
                reason = f"stop hit (bid {q['bid']:.2f} <= {stop:.2f})"
            elif now_ct().time() >= flatten:
                reason = f"flatten time {rk['flatten_time_ct']} CT"
            elif os.path.exists(os.path.join(HERE, "KILL")):
                reason = "KILL file"
            if reason:
                log(f"EXIT: {reason}")
                broker.cancel(tp_id)
                px = sell_now(broker, occ, qty, cfg["poll_seconds"])
                if px is not None:
                    pnl = (px - entry) * 100 * qty
                    log(f"EXITED @ {px:.2f}  P/L ${pnl:+.2f}")
                    risk.record(pnl)
                return
        time.sleep(cfg["poll_seconds"])


def pick_contract(broker, underlying, cp, max_price, expiry):
    spot = broker.stock_quote(underlying)["price"]
    rows = broker.chain(underlying, expiry, cp, spot)
    # nearest-to-money contract whose ask fits the budget, with a tight spread
    rows = [(s, q) for s, q in rows if 0.05 <= q["ask"] <= max_price and (q["ask"] - q["bid"]) <= max(0.05, 0.15 * q["ask"])]
    if not rows:
        return (None, None), spot
    return max(rows, key=lambda r: r[1]["ask"]), spot  # most expensive that fits = nearest the money


def buy_and_manage(broker, risk, cfg, underlying, cp, max_price, expiry):
    (occ, q), spot = pick_contract(broker, underlying, cp, max_price, expiry)
    if not occ:
        log(f"no {underlying} {cp} contract with ask <= {max_price:.2f}")
        return
    ok, why = risk.can_enter(q["ask"] * 100)
    if not ok:
        log(f"ENTRY BLOCKED: {why}")
        return
    log(f"ENTRY {underlying} spot {spot:.2f} -> {occ} bid {q['bid']:.2f} ask {q['ask']:.2f} delta {q['delta']:.2f}")
    coid = broker.place_option(occ, "BUY", 1, q["ask"])
    px = wait_fill(broker, coid, 30, cfg["poll_seconds"])
    if px is None:
        broker.cancel(coid)
        log("entry not filled in 30s — cancelled (no chase)")
        return
    log(f"FILLED {occ} @ {px:.2f}")
    manage(broker, risk, occ, 1, px, cfg)


def watch(broker, risk, cfg, symbol, call_above, put_below, auto, max_price, vol_mult):
    log(f"WATCH {symbol}: CALL on 5-min close > {call_above} | PUT on close < {put_below} | auto={auto}")
    seen = None
    while True:
        bars = broker.bars_5m(symbol, 30)
        if len(bars) >= 3:
            last = bars[-2]  # last COMPLETED bar
            if last["time"] != seen:
                seen = last["time"]
                avg_v = sum(b["v"] for b in bars[-14:-2]) / max(1, len(bars[-14:-2]))
                vol_ok = last["v"] >= vol_mult * avg_v
                side = "C" if last["c"] > call_above else "P" if last["c"] < put_below else None
                log(f"{symbol} 5m close {last['c']:.2f} vol {last['v']:,.0f} (avg {avg_v:,.0f}) -> "
                    f"{'CALL' if side == 'C' else 'PUT' if side == 'P' else 'no trigger'}{'' if vol_ok or not side else ' (volume too low)'}")
                if side and vol_ok:
                    log(f"*** TRIGGER {'CALL' if side == 'C' else 'PUT'} ***")
                    if auto:
                        buy_and_manage(broker, risk, cfg, symbol, side, max_price, now_ct().date())
                        return
        if now_ct().time() >= datetime.strptime("14:30", "%H:%M").time():
            log("watch window over (14:30 CT)")
            return
        time.sleep(20)


def rsi2_scan(broker):
    from webull.data.common.category import Category
    from webull.data.common.timespan import Timespan
    for sym in ("SPY", "QQQ", "IWM"):
        j = broker._ok(broker.data.market_data.get_batch_history_bar([sym], Category.US_STOCK.name, Timespan.D.name, 220),
                       "daily bars")
        rows = sorted(dict_rows(j, "close"), key=lambda r: str(r.get("time")))
        closes = [float(find(r, "close")) for r in rows]
        live = broker.stock_quote(sym)["price"]
        if live:
            closes[-1] = live
        up = dn = 0.0
        for a, b in zip(closes, closes[1:]):
            d = b - a
            up = 0.5 * up + 0.5 * max(d, 0)
            dn = 0.5 * dn + 0.5 * max(-d, 0)
        rsi = 100 - 100 / (1 + up / dn) if dn else 100
        sma200 = sum(closes[-200:]) / 200
        sma5 = sum(closes[-5:]) / 5
        sig = rsi < 10 and closes[-1] > sma200
        log(f"RSI2 {sym}: price {closes[-1]:.2f} RSI2 {rsi:.1f} SMA200 {sma200:.2f} SMA5 {sma5:.2f} -> "
            f"{'ENTRY SIGNAL (bull put spread, ~5 DTE)' if sig else 'exit zone' if closes[-1] > sma5 else 'no signal'}")


# ----------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--live", action="store_true", help="place REAL orders (also needs mode=live in config.json)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    sub.add_parser("accounts")
    p = sub.add_parser("chain"); p.add_argument("symbol"); p.add_argument("--type", default="C", choices=["C", "P"])
    p = sub.add_parser("buy"); p.add_argument("symbol"); p.add_argument("--type", required=True, choices=["C", "P"])
    p.add_argument("--max-price", type=float, default=0.50)
    p = sub.add_parser("manage"); p.add_argument("occ"); p.add_argument("--entry", type=float, required=True)
    p.add_argument("--qty", type=int, default=1)
    p = sub.add_parser("watch"); p.add_argument("symbol"); p.add_argument("--call-above", type=float, required=True)
    p.add_argument("--put-below", type=float, required=True); p.add_argument("--auto", action="store_true")
    p.add_argument("--max-price", type=float, default=0.50); p.add_argument("--vol-mult", type=float, default=1.5)
    sub.add_parser("rsi2")
    a = ap.parse_args()

    cfg_path = os.path.join(HERE, "config.json")
    if not os.path.exists(cfg_path):
        sys.exit("Missing bot/config.json — copy config.example.json to config.json and fill in your keys.")
    cfg = json.load(open(cfg_path))
    live = a.live and cfg.get("mode") == "live"
    if a.live and not live:
        sys.exit('--live given but config.json has "mode": "paper". Refusing to trade live.')
    broker = Broker(cfg, live=True) if live else PaperBroker(cfg)
    risk = RiskState(cfg)
    log(f"=== {'LIVE' if live else 'PAPER'} mode | cmd={a.cmd} ===")

    if a.cmd == "accounts":
        for acc in dict_rows(broker.accounts(), "account_id"):
            print(f"account_id: {acc.get('account_id')}   number: {acc.get('account_number')}   "
                  f"type: {acc.get('account_type') or acc.get('account_class')}   label: {acc.get('account_label', '')}")
        print("\nPut the account_id of your MARGIN / options account into config.json")
    elif a.cmd == "check":
        try:
            bal = broker.balance()
            print("Balance OK:", json.dumps(bal)[:600])
        except Exception as e:
            print(f"Balance failed ({short_err(e)}).\nRun:  python bot.py accounts   and copy the right account_id into config.json")
        spy = {"price": 0}
        try:
            spy = broker.stock_quote("SPY")
        except Exception:
            pass
        occ = occ_symbol("SPY", now_ct().date(), "C", round(spy["price"] or 767))
        try:
            print("SPY:", broker.stock_quote("SPY"))
        except Exception as e:
            print("Stock quote failed:", short_err(e))
        try:
            print(occ, broker.option_quotes([occ]))
        except Exception as e:
            print("Option quote failed:", short_err(e))
    elif a.cmd == "chain":
        spot = broker.stock_quote(a.symbol)["price"]
        for s, q in broker.chain(a.symbol, now_ct().date(), a.type, spot):
            print(f"{s}  bid {q['bid']:.2f}  ask {q['ask']:.2f}  vol {q['volume']:,.0f}  OI {q['oi']:,.0f}  "
                  f"IV {q['iv']:.2f}  delta {q['delta']:.2f}")
    elif a.cmd == "buy":
        buy_and_manage(broker, risk, cfg, a.symbol, a.type, a.max_price, now_ct().date())
    elif a.cmd == "manage":
        manage(broker, risk, a.occ, a.qty, a.entry, cfg)
    elif a.cmd == "watch":
        watch(broker, risk, cfg, a.symbol, a.call_above, a.put_below, a.auto, a.max_price, a.vol_mult)
    elif a.cmd == "rsi2":
        rsi2_scan(broker)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("stopped by user (Ctrl+C)")
    except Exception as e:
        log(f"ERROR: {short_err(e)}")
        sys.exit(1)

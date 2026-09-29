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
  testorder                    places and cancels $0.01 orders that cannot fill, to prove Webull accepts the bot's orders
  guard                        trade guardian: every option you buy in Webull gets a stop order at once, the stop
                               ratchets up (breakeven at +40%, locks +30% at +80%, +90% at +150%, then trails 25%),
                               same-day options are closed at flatten time
  auto                         hands-off day: 15-min opening-range levels on SPY+QQQ, confirmed breakouts,
                               automatic exits (backtest: loses money — paper mode only)
  rsi2                         daily RSI(2) pullback scan on SPY/QQQ/IWM (the strategy that backtested well)

Safety: max cost per trade, max trades per day, max daily loss, no new entries after 14:30 CT,
forced exit at flatten_time_ct, and a kill switch: create a file named KILL (or KILL.txt; KILL.bat does it) in this folder to stop all entries.
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
from datetime import datetime, timedelta
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
    with open(os.path.join(LOG_DIR, f"bot-{now_ct():%Y-%m-%d}.log"), "a", encoding="utf-8") as f:
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


# NYSE calendar exceptions (update each year). Early close = 12:00 CT, same-day options expire then.
HOLIDAYS = {"2026-11-26", "2026-12-25", "2027-01-01", "2027-01-18", "2027-02-15", "2027-03-26", "2027-05-31",
            "2027-06-18", "2027-07-05", "2027-09-06", "2027-11-25", "2027-12-24"}
EARLY_CLOSE = {"2026-11-27", "2026-12-24", "2027-11-26"}


def market_day(d):
    return d.weekday() < 5 and f"{d:%Y-%m-%d}" not in HOLIDAYS


def console_no_quickedit():
    """Windows cmd: turn QuickEdit off, so clicking or selecting text in the window can't pause the program."""
    if os.name != "nt":
        return False
    try:
        import ctypes
        k32 = ctypes.windll.kernel32
        handle = k32.GetStdHandle(-10)  # the console's input
        mode = ctypes.c_uint32()
        if not k32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        return bool(k32.SetConsoleMode(handle, (mode.value & ~0x0040) | 0x0080))  # QuickEdit off, keep other flags
    except Exception:
        return False


KILL_FILES = ("KILL", "KILL.txt")  # KILL.txt too: Notepad and right-click > New add ".txt" and Windows hides it


def kill_paths():
    """The KILL switch files that exist in the bot folder (KILL.bat creates one, UNKILL.bat removes them)."""
    return [p for p in (os.path.join(HERE, n) for n in KILL_FILES) if os.path.exists(p)]


PENNY = {"SPY", "QQQ", "IWM"}  # $0.01 ticks at every price; most other options use $0.05 at $3 and up


def tick_down(occ, px):
    """Round a price down to a valid option tick."""
    if px >= 3 and parse_occ(occ)[0] not in PENNY:
        return math.floor(px * 20 + 1e-9) / 20
    return math.floor(px * 100 + 1e-9) / 100


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
            try:
                with open(self.path) as f:
                    self.s = json.load(f)
            except (OSError, ValueError):  # half-written (window closed mid-save): start the day's totals over
                log(f"!! {os.path.basename(self.path)} was damaged — today's trade count and P/L restart at 0")

    def save(self):
        tmp = self.path + ".tmp"
        try:
            with open(tmp, "w") as f:
                json.dump(self.s, f)
            os.replace(tmp, self.path)  # swap in the finished file, so a closed window never leaves half a file
        except OSError as e:  # e.g. antivirus holding the file: the totals are only bookkeeping, keep guarding
            log(f"!! could not save today's totals ({e})")

    def can_enter(self, cost):
        if kill_paths():
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

    def option_positions(self):
        """{occ: {"qty": int, "cost": per-share cost}} for every open option position."""
        out, j = {}, self.positions()
        for row in dict_rows(j, "legs") or dict_rows(j, "option_type"):
            leg = (row.get("legs") or [row])[0]
            if str(find(leg, "instrument_type") or find(row, "instrument_type") or "OPTION").upper() != "OPTION":
                continue
            und = find(leg, "symbol", "underlying_symbol")
            exp = find(leg, "option_expire_date", "expire_date", "expiration_date")
            cp = str(find(leg, "option_type") or "").upper()[:1]
            strike = find(leg, "option_exercise_price", "strike_price")
            qty = int(float(find(row, "quantity", "qty") or 0))
            if not (und and exp and cp in ("C", "P") and strike and qty > 0):
                continue  # short or empty: the guard only protects long options
            occ = occ_symbol(und, datetime.strptime(str(exp)[:10], "%Y-%m-%d").date(), cp, float(strike))
            out[occ] = {"qty": qty, "cost": float(find(row, "cost_price", "avg_price") or find(leg, "cost") or 0)}
        return out

    def place_option(self, occ, side, qty, limit, stop=None):
        und, exp, cp, strike = parse_occ(occ)
        coid = uuid.uuid4().hex
        order = [{
            "client_order_id": coid, "combo_type": "NORMAL", "order_type": "STOP_LOSS_LIMIT" if stop else "LIMIT",
            "quantity": str(qty), "limit_price": f"{limit:.2f}", "option_strategy": "SINGLE",
            "side": side, "time_in_force": "DAY", "entrust_type": "QTY",
            "legs": [{"side": side, "quantity": str(qty), "symbol": und, "strike_price": f"{strike:g}",
                      "option_expire_date": f"{exp:%Y-%m-%d}", "instrument_type": "OPTION",
                      "option_type": "CALL" if cp == "C" else "PUT", "market": "US"}],
        }]
        if stop:
            order[0]["stop_price"] = f"{stop:.2f}"
        if not self.live:
            raise RuntimeError("Broker.place_option called in paper mode")
        self._ok(self.trade.order_v2.place_option(self.account, order), "place option")
        log(f"LIVE ORDER {side} {qty} {occ} " + (f"STOP {stop:.2f} / LIMIT {limit:.2f}" if stop else f"@ {limit:.2f}") + f"  id={coid[:8]}")
        return coid

    def cancel(self, coid):
        self._ok(self.trade.order_v2.cancel_option(self.account, coid), "cancel")

    def order_status(self, coid):
        j = self._ok(self.trade.order_v2.get_order_detail(self.account, coid), "order detail")
        status = str(find(j, "status", "order_status") or "").upper()
        filled = float(find(j, "filled_quantity", "filled_qty") or 0)
        px = float(find(j, "filled_price", "avg_filled_price", "filled_avg_price", "avg_fill_price",
                        "average_price", "avg_price") or 0)
        return status, filled, px


class PaperBroker(Broker):
    """Real quotes, simulated fills (buy fills when ask <= limit, sell when bid >= limit)."""

    def __init__(self, cfg):
        super().__init__(cfg, live=False)
        self.orders = {}

    def place_option(self, occ, side, qty, limit, stop=None):
        coid = uuid.uuid4().hex
        self.orders[coid] = {"occ": occ, "side": side, "qty": qty, "limit": limit, "stop": stop,
                             "status": "SUBMITTED", "px": 0}
        log(f"PAPER ORDER {side} {qty} {occ} " + (f"STOP {stop:.2f} / LIMIT {limit:.2f}" if stop else f"@ {limit:.2f}")
            + f"  id={coid[:8]}")
        return coid

    def cancel(self, coid):
        if self.orders[coid]["status"] != "FILLED":
            self.orders[coid]["status"] = "CANCELLED"

    def order_status(self, coid):
        o = self.orders[coid]
        if o["status"] == "SUBMITTED":
            q = self.option_quotes([o["occ"]]).get(o["occ"])
            if q:
                if o.get("stop") and q["bid"] > o["stop"]:
                    pass  # stop not triggered yet
                elif o["side"] == "BUY" and 0 < q["ask"] <= o["limit"]:
                    o.update(status="FILLED", px=q["ask"])
                elif o["side"] == "SELL" and q["bid"] >= o["limit"]:
                    o.update(status="FILLED", px=q["bid"])
        return o["status"], (o["qty"] if o["status"] == "FILLED" else 0), o["px"]


# ----------------------------------------------------------------- trading logic
def wait_fill(broker, coid, seconds, poll):
    for _ in range(max(1, int(seconds / max(poll, 1)))):
        try:
            status, _, px = broker.order_status(coid)
        except Exception:  # status unreachable for a moment: keep waiting, don't abandon the order
            status, px = "", 0
        if "FILLED" in status and "PARTIAL" not in status:
            return px
        if status in ("CANCELLED", "REJECTED", "FAILED", "EXPIRED"):
            return None
        time.sleep(poll)
    return None


def sell_now(broker, occ, qty, poll, last_bid=0):
    """Aggressive exit: sell at bid, re-price down up to 4 times. No quote? Price off last_bid."""
    for step in (0.00, 0.02, 0.05, 0.10, 0.20):
        try:
            bid = broker.option_quotes([occ]).get(occ, {"bid": 0})["bid"]
        except Exception:  # quotes down: the last bid we saw is the best guess
            bid = last_bid
        px = max(0.01, tick_down(occ, bid - step))
        coid = broker.place_option(occ, "SELL", qty, px)
        got = wait_fill(broker, coid, 15, poll)
        if got is not None:
            return got
        try:
            broker.cancel(coid)
        except Exception as e:
            log(f"cancel sell: {short_err(e)}")
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
    st = {"tp_id": broker.place_option(occ, "SELL", qty, tp), "stop": stop}
    errors = 0
    while True:
        try:
            if manage_step(broker, risk, occ, qty, entry, cfg, st, trail_at, flatten):
                return
            errors = 0
        except Exception as e:  # a network/API hiccup must not leave the position unmanaged
            errors += 1
            log(f"manage: error #{errors} ({short_err(e)}) — retrying")
            if errors >= 12:
                log("!! too many errors — SELL MANUALLY IN WEBULL")
                return
        time.sleep(cfg["poll_seconds"])


def manage_step(broker, risk, occ, qty, entry, cfg, st, trail_at, flatten):
    """One pass of the exit logic. Returns True when the position is closed (or handed to the user)."""
    status, filled, px = broker.order_status(st["tp_id"])
    tp = r2(entry * (1 + cfg["risk"]["take_profit_pct"]))
    if "FILLED" in status and "PARTIAL" not in status:
        px = px if px > 0 else tp
        pnl = (px - entry) * 100 * qty
        log(f"TAKE-PROFIT FILLED @ {px:.2f}  P/L ${pnl:+.2f}")
        risk.record(pnl)
        return True
    q = broker.option_quotes([occ]).get(occ)
    if not q or q["bid"] <= 0:
        return False
    if q["bid"] >= trail_at and st["stop"] < entry:
        st["stop"] = entry
        log(f"bid {q['bid']:.2f} >= {trail_at:.2f}: stop raised to breakeven {entry:.2f}")
    reason = None
    if q["bid"] <= st["stop"]:
        reason = f"stop hit (bid {q['bid']:.2f} <= {st['stop']:.2f})"
    elif now_ct().time() >= flatten:
        reason = f"flatten time {flatten:%H:%M} CT"
    elif kill_paths():
        reason = "KILL file"
    if not reason:
        return False
    log(f"EXIT: {reason}")
    try:
        broker.cancel(st["tp_id"])
    except Exception as e:
        log(f"cancel take-profit: {short_err(e)}")
    status, filled, px = broker.order_status(st["tp_id"])
    if "FILLED" in status and "PARTIAL" not in status:  # filled while we were cancelling
        px = px if px > 0 else tp
        pnl = (px - entry) * 100 * qty
        log(f"TAKE-PROFIT FILLED @ {px:.2f}  P/L ${pnl:+.2f}")
        risk.record(pnl)
        return True
    px = sell_now(broker, occ, qty, cfg["poll_seconds"])
    if px is not None:
        px = px if px > 0 else q["bid"]
        pnl = (px - entry) * 100 * qty
        log(f"EXITED @ {px:.2f}  P/L ${pnl:+.2f}")
        risk.record(pnl)
    return True


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


AUTO_DEFAULTS = {
    "symbols": ["SPY", "QQQ"],  # watched together; the other one must be on the same side of its VWAP
    "max_price": 0.50,          # max option ask ($50 per contract)
    "vol_mult": 1.5,            # breakout bar volume vs average of the previous 12 bars
    "buffer": 0.05,             # $ beyond the opening-range high/low
    "close_strength": 0.6,      # breakout bar must close in the top (calls) / bottom (puts) 40% of its range
    "confirm": True,
}


def hm(s):
    return datetime.strptime(s, "%H:%M").time()


def bar_dt(t):
    """Bar timestamp (epoch s/ms or ISO string) -> datetime in CT."""
    utc = ZoneInfo("UTC")
    if isinstance(t, (int, float)) or (isinstance(t, str) and t.isdigit()):
        v = int(t)
        return datetime.fromtimestamp(v / 1000 if v > 1e11 else v, tz=utc).astimezone(CT)
    s = str(t).replace("Z", "+00:00")
    if len(s) > 5 and s[-5] in "+-" and s[-3] != ":":
        s = s[:-2] + ":" + s[-2:]
    d = datetime.fromisoformat(s)
    return (d if d.tzinfo else d.replace(tzinfo=utc)).astimezone(CT)


def today_bars(broker, symbol):
    """Today's COMPLETED regular-hours 5-min bars (08:30-15:00 CT), oldest first."""
    now = now_ct()
    out = []
    for b in broker.bars_5m(symbol, 150):
        d = bar_dt(b["time"])
        if d.date() == now.date() and hm("08:30") <= d.time() < hm("15:00") and d + timedelta(minutes=5) <= now:
            out.append({**b, "dt": d})
    return out


def vwap(bars):
    v = sum(b["v"] for b in bars)
    return sum((b["h"] + b["l"] + b["c"]) / 3 * b["v"] for b in bars) / v if v else bars[-1]["c"]


def auto(broker, risk, cfg):
    """Fully automatic day: levels = 15-min opening range, then trade confirmed breakouts until 14:30 CT."""
    a = {**AUTO_DEFAULTS, **cfg.get("auto", {})}
    syms = [s.upper() for s in a["symbols"]]
    log(f"AUTO {syms}: waiting for the 15-min opening range (08:30-08:45 CT)")
    while now_ct().time() < hm("08:46"):
        if kill_paths():
            log("KILL file present — not trading today")
            return
        time.sleep(20)

    levels = {}
    for _ in range(20):  # ~10 min of retries (slow data / late start); none at all = market closed
        for s in syms:
            if s not in levels:
                try:
                    orb = [b for b in today_bars(broker, s) if b["dt"].time() < hm("08:45")]
                except Exception as e:
                    log(f"{s} bars: {short_err(e)}")
                    continue
                if len(orb) >= 3:
                    levels[s] = (r2(max(b["h"] for b in orb) + a["buffer"]), r2(min(b["l"] for b in orb) - a["buffer"]))
                    log(f"LEVELS {s}: CALL on 5-min close > {levels[s][0]} | PUT on close < {levels[s][1]}")
        if len(levels) == len(syms):
            break
        time.sleep(30)
    if not levels:
        log("no bars for today — market closed? Nothing to do.")
        return

    seen = {}
    while True:
        ok, why = risk.can_enter(0)
        if not ok:
            log(f"AUTO done: {why}")
            break
        state = {}
        try:
            for s in levels:
                bars = today_bars(broker, s)
                if bars:
                    state[s] = (bars, vwap(bars))
        except Exception as e:
            log(f"data error ({short_err(e)}) — retrying")
            time.sleep(20)
            continue
        if len(state) < len(levels):  # need every symbol for the confirmation check
            time.sleep(20)
            continue
        for s, (bars, vw) in state.items():
            last = bars[-1]
            if seen.get(s) == last["dt"]:
                continue
            seen[s] = last["dt"]
            hi, lo = levels[s]
            side = "C" if last["c"] > hi else "P" if last["c"] < lo else None
            if not side:
                log(f"{s} {last['dt']:%H:%M} close {last['c']:.2f} (range {lo}-{hi}, VWAP {vw:.2f}) -> no trigger")
                continue
            prev = bars[-13:-1]
            avg_v = sum(b["v"] for b in prev) / len(prev) if prev else last["v"]
            rng = last["h"] - last["l"]
            strength = (last["c"] - last["l"]) / rng if rng else 0.5
            if side == "P":
                strength = 1 - strength
            fails = []
            if last["v"] < a["vol_mult"] * avg_v:
                fails.append(f"volume {last['v']:,.0f} < {a['vol_mult']}x avg {avg_v:,.0f}")
            if (side == "C") != (last["c"] > vw):
                fails.append("wrong side of VWAP")
            if strength < a["close_strength"]:
                fails.append("weak close")
            if a["confirm"]:
                for o, (ob, ovw) in state.items():
                    if o != s and (side == "C") != (ob[-1]["c"] > ovw):
                        fails.append(f"{o} not confirming")
            name = "CALL" if side == "C" else "PUT"
            if fails:
                log(f"{s} {last['dt']:%H:%M} close {last['c']:.2f} -> {name} breakout SKIPPED: {', '.join(fails)}")
                continue
            log(f"*** {s} {name} TRIGGER: close {last['c']:.2f}, vol {last['v']:,.0f}, VWAP {vw:.2f} ***")
            try:
                buy_and_manage(broker, risk, cfg, s, side, a["max_price"], now_ct().date())
            except Exception as e:
                log(f"!! entry error ({short_err(e)}) — CHECK WEBULL for an open position/order")
                return
            break  # fresh data after a trade
        time.sleep(20)
    log(f"AUTO summary: {risk.s['trades']} trade(s), realized P/L ${risk.s['realized']:+.2f}")


GUARD_DEFAULTS = {
    "risk_pct": 0.30,                 # first stop: aim 30% under the entry...
    "risk_min": 10,                   # ...but risk at least $10 per trade (all contracts together)
    "risk_max": 20,                   # ...and never more than $20
    "stop_pct": 0.35,                 # used only when risk_pct is set to 0
    "ladder": [[0.40, 0.00], [0.80, 0.30], [1.50, 0.90]],  # [peak gain reached, gain locked by the stop]
    "trail_after": 1.50,              # above +150%, also trail...
    "trail_pct": 0.25,                # ...25% below the highest bid
    "limit_offset_pct": 0.10,         # stop-limit: limit this far under the stop so it fills in a fast drop
    "warn_time_ct": "14:30",
    "end_time_ct": "15:00",
    "size_alert_pct": 0.30,           # warn when one position costs more than 30% of the account
    "reprotect": True,                # put the stop back if it gets cancelled
    "lockout": False,                 # after the daily limit, sell any new position immediately
    "lockout_losses": 2,
    "lockout_loss": 25,
    "warn_loss": 20,                  # just a heads-up in the log when the day's realized loss reaches this
    "manual_grace_s": 60,             # after you cancel the guard's stop in the app, wait this long before re-placing
    "startup_test": True,             # live: place+cancel a $0.01 test order when the market is open
    "warnings": True,                 # trade warnings from the journal's patterns (never block anything)
    "midday_ct": ["10:30", "13:30"],  # warn on new trades in this window
    "reentry_min": 10,                # warn on a new trade this soon after a loss
    "trade_count_warn": 4,            # warn from this many new trades in a day
    "otm_warn_pct": 0.0035,           # warn when a same-day strike is this far out of the money (0.35% ~ $2.60 on QQQ)
}


def trade_warnings(broker, occ, now, day, g):
    """Heads-ups for a new position, based on the patterns in JOURNAL.md (9/25). Never blocks."""
    out = []
    t = now.time()
    lo, hi = (hm(x) for x in g["midday_ct"])
    if lo <= t < hi:
        out.append(f"MIDDAY TRADE ({g['midday_ct'][0]}-{g['midday_ct'][1]} CT): most midday trades in the journal "
                   f"lost to chop")
    if day.get("last_loss_at") and (now - day["last_loss_at"]).total_seconds() < g["reentry_min"] * 60:
        mins = (now - day["last_loss_at"]).total_seconds() / 60
        out.append(f"RE-ENTRY {'<1' if mins < 1 else f'{mins:.0f}'} min after a loss: quick re-buys after a loss lost on 9/25; "
                   f"is this a new setup?")
    if day["opened"] >= g["trade_count_warn"]:
        out.append(f"TRADE #{day['opened']} TODAY: on 9/25 the P/L peaked after the first trades and chop gave it back")
    try:
        und, exp, cp, strike = parse_occ(occ)
        spot = broker.stock_quote(und)["price"]
        if spot:
            away = (strike - spot) / spot if cp == "C" else (spot - strike) / spot
            limit = g["otm_warn_pct"] if exp == now.date() else g["otm_warn_pct"] * 3
            if away > limit:
                out.append(f"FAR FROM THE MONEY: {und} {strike:g}{cp} is ${abs(strike - spot):.2f} ({away:.2%}) away "
                           f"from {spot:.2f}; it needs a big move fast before time decay wins")
    except Exception:
        pass
    return out


def guard_stop(t, g):
    """Stop price for a tracked position from its entry and highest bid (never lower than before)."""
    gain = t["peak"] / t["entry"] - 1
    if g.get("risk_pct"):
        cost = t["entry"] * 100 * t["qty"]
        risk = min(g["risk_max"], max(g["risk_min"], g["risk_pct"] * cost))
        stop = max(0.05, t["entry"] - risk / (100 * t["qty"]))
    else:
        stop = t["entry"] * (1 - g["stop_pct"])
    for reached, lock in g["ladder"]:
        if gain >= reached:
            stop = max(stop, t["entry"] * (1 + lock))
    if gain >= g["trail_after"]:
        stop = max(stop, t["peak"] * (1 - g["trail_pct"]))
    return max(t["stop"], r2(stop))


def guard(broker, risk, cfg):
    """Protect every long option position in the account: stop order right away, ratchet it up, flatten
    same-day options at flatten time. Entries stay manual."""
    g = {**GUARD_DEFAULTS, **cfg.get("guard", {})}
    flatten = hm(cfg["risk"]["flatten_time_ct"])
    done_states = ("CANCELLED", "CANCELED", "REJECTED", "FAILED", "EXPIRED")
    tracked, day = {}, {"realized": 0.0, "losses": 0, "closed": 0, "opened": 0}
    flat_txt = cfg["risk"]["flatten_time_ct"]
    today = now_ct().date()
    if f"{today:%Y-%m-%d}" in EARLY_CLOSE:
        flatten, g["end_time_ct"], g["warn_time_ct"] = hm("11:50"), "12:00", "11:30"
        flat_txt = "11:50"
        log("EARLY CLOSE today (12:00 CT): same-day options will be closed at 11:50 CT")
    if not market_day(today):
        log("market is closed today (weekend/holiday) — the guard will just watch")
    for kill in kill_paths():
        if datetime.fromtimestamp(os.path.getmtime(kill), CT).date() < today:
            os.remove(kill)
            log(f"removed an old {os.path.basename(kill)} file from a previous day")
        else:
            log(f"!! {os.path.basename(kill)} is present: every option position will be SOLD. "
                f"Double-click UNKILL.bat to trade normally.")
    lock = os.path.join(LOG_DIR, "guard.lock")

    def lock_age():
        try:
            with open(lock) as f:
                return now_ct().timestamp() - float(f.read() or 0)
        except (OSError, ValueError):
            return None  # no lock file: no other Guardian

    age = lock_age()
    if age is not None and age < 30:  # another window, or one you closed a moment ago: wait and see
        log("another Guardian was running a moment ago — checking it's gone (up to 30s)...")
        time.sleep(31 - age)
        age = lock_age()
        if age is not None and age < 30:  # it updated the lock again: it's really running
            log("!! another Guardian window is already running — close this one (two would fight over the stops)")
            return
    if console_no_quickedit():
        log("QuickEdit is off for this window: clicking or selecting text can no longer pause the Guardian")
    state_path = os.path.join(LOG_DIR, f"guard-state-{today:%Y-%m-%d}.json")
    try:  # what the last Guardian window left today: its stop orders, so a restart picks them up
        with open(state_path) as f:
            saved = json.load(f)
    except (OSError, ValueError):
        saved = {}
    saved_pos, last_saved = saved.get("pos", {}), None

    def save_state():
        nonlocal last_saved
        data = json.dumps({"pos": {o: {"oid": t["oid"], "stop": t["stop"], "peak": t["peak"], "entry": t["entry"],
                                       "qty": t["qty"], "per_contract": t.get("per_contract", False)}
                                   for o, t in tracked.items() if not t.get("closed") and t.get("oid")}})
        if data == last_saved:
            return
        try:
            with open(state_path + ".tmp", "w") as f:
                f.write(data)
            os.replace(state_path + ".tmp", state_path)
            last_saved = data
        except OSError:
            pass

    warned, first_pass, last_beat, last_top = False, True, 0.0, 0.0
    test_pending = bool(g["startup_test"] and getattr(broker, "live", False))
    if test_pending:
        log("order test: runs once the market is open (8:30 CT) — a $0.01 buy that cannot fill, then cancelled")
    first = (f"first stop {g['risk_pct']:.0%} under entry, risk ${g['risk_min']}-${g['risk_max']} per trade"
             if g.get("risk_pct") else f"stop -{g['stop_pct']:.0%}")
    log(f"GUARD on: {first}, ladder {g['ladder']}, trail {g['trail_pct']:.0%} after "
        f"+{g['trail_after']:.0%}, same-day options closed at {flat_txt} CT, "
        f"lockout {'ON' if g['lockout'] else 'off'}")

    def filled(st):
        return "FILLED" in st and "PARTIAL" not in st

    def fill_px(px, t):
        return px if px and px > 0 else (t.get("last_bid") or t["stop"])  # some responses omit the fill price

    def place_stop(occ, t):
        stop = tick_down(occ, t["stop"])
        limit = tick_down(occ, max(0.01, stop - max(0.03, g["limit_offset_pct"] * stop)))
        try:
            t["oid"] = broker.place_option(occ, "SELL", t["qty"], limit, stop=stop)
            t.update(soft=False, cancelling=False, placed=True, fails=0)
            log(f"PROTECTED {occ} x{t['qty']}: stop {stop:.2f} (limit {limit:.2f})")
        except Exception as e:
            t["oid"], t["soft"] = None, True
            t["fails"] = t.get("fails", 0) + 1
            t["retry_at"] = now_ct().timestamp() + 15
            if t["fails"] == 1:
                log(f"!! stop order rejected ({short_err(e)}) — GUARD watches {stop:.2f} itself and keeps "
                    f"retrying the order every 15s. If you placed your own sell order in Webull, cancel it: "
                    f"the guard needs the contracts free for its stop.")

    def cancel_stop(t):
        """Cancel our resting stop. Returns the fill price if it filled before the cancel went through."""
        oid = t.get("oid")
        if not oid:
            return None
        t["cancelling"], t["oid"] = True, None
        try:
            broker.cancel(oid)
        except Exception as e:
            log(f"cancel stop: {short_err(e)}")
        for _ in range(4):  # wait for Webull to confirm, so a new stop isn't rejected for "position in use"
            try:
                st, _, px = broker.order_status(oid)
            except Exception:
                st, px = "", 0
            if filled(st):
                return fill_px(px, t)
            if st in done_states:
                return None
            time.sleep(1)
        log("!! old stop not confirmed cancelled yet")
        return None

    def stop_status(t):
        """Status of our stop order; ("", 0, 0) = unknown when Webull can't be reached (never aborts the pass)."""
        try:
            st = broker.order_status(t["oid"])
            t["status_err"] = False
            return st
        except Exception as e:
            if not t.get("status_err"):
                t["status_err"] = True
                log(f"!! can't read the stop order's status ({short_err(e)}) — the stop stays at Webull; "
                    f"GUARD keeps watching the price, the 14:50 exit and the safety net")
            return "", 0, 0

    def close(occ, t, px, why, est=False):
        pnl = (px - t["entry"]) * 100 * t["qty"] if px is not None else None
        if pnl is not None:
            risk.record(pnl)
            day["realized"] += pnl
            day["losses"] += pnl < 0
            if pnl < 0:
                day["last_loss_at"] = now_ct()
        day["closed"] += 1
        if g.get("warn_loss") and -day["realized"] >= g["warn_loss"] and not day.get("warned_loss"):
            day["warned_loss"] = True
            log(f"!! heads-up: down ${-day['realized']:.2f} today (warning level ${g['warn_loss']}) — "
                f"trading continues, no lockout")
        peak_pnl = (t["peak"] - t["entry"]) * 100 * t["qty"]
        tilde = "~" if est else ""
        log(f"CLOSED {occ} x{t['qty']} ({why}) entry {t['entry']:.2f} exit "
            f"{'?' if px is None else f'{tilde}{px:.2f}'} P/L {'?' if pnl is None else f'{tilde}${pnl:+.2f}'} "
            f"(best was ${peak_pnl:+.2f})")
        t["closed"] = True

    def exit_now(occ, t, why):
        px = cancel_stop(t)
        if px is None:
            t0 = now_ct().timestamp()
            try:
                px = sell_now(broker, occ, t["qty"], cfg["poll_seconds"], t.get("last_bid") or 0)
            except Exception as e:
                log(f"sell failed: {short_err(e)}")
                px = None
            day["busy"] = day.get("busy", 0.0) + now_ct().timestamp() - t0
            px = None if px is None else fill_px(px, t)
        if px is None:
            t["exit"] = why  # keep the position tracked and try again next pass
            t["exit_fails"] = t.get("exit_fails", 0) + 1
            if t["exit_fails"] % 6 == 1:
                log(f"!! {occ}: exit ({why}) not filled — retrying every few seconds; "
                    f"SELL MANUALLY IN WEBULL if this keeps showing")
            place_stop(occ, t)  # stay protected while retrying
            return
        close(occ, t, px, why)

    errs = {"n": 0, "last": 0.0}
    while True:
        now = now_ct()
        if now.time() >= hm(g["end_time_ct"]):
            break
        gap = now.timestamp() - last_top - day.get("busy", 0.0) - cfg["poll_seconds"] if last_top else 0.0
        if gap > 40:  # a check takes seconds; minutes means Windows paused the program
            log(f"!! GUARD was paused for {gap / 60:.1f} min (text selected in this window, or the PC slept) "
                f"— catching up now. Stop orders already at Webull kept working.")
        last_top, day["busy"] = now.timestamp(), 0.0
        try:
            with open(lock, "w") as f:
                f.write(str(now.timestamp()))
        except OSError:
            pass
        try:
            if test_pending and market_day(now.date()) and hm("08:30") <= now.time() < hm("11:30" if flatten < hm("12:00") else "14:45"):
                test_pending = False
                ok = order_test(broker, with_stop=False)
                if ok:
                    log("ORDER TEST PASSED — Webull accepts the bot's orders")
                elif ok is False:
                    log("!! ORDER TEST FAILED — send me this window. The guard keeps running and will watch "
                        "your stops itself if Webull rejects them.")
            try:
                pos, pos_ok = broker.option_positions(), True
                # positions where Webull reported cost per contract: convert to per share
                pos = {o: dict(p, cost=p["cost"] / 100) if tracked.get(o, {}).get("per_contract") else p
                       for o, p in pos.items()}
                if day.get("pos_err"):
                    day["pos_err"] = False
                    log("positions readable again")
            except Exception as e:  # can't read positions: keep managing the ones already tracked
                pos, pos_ok = {o: {"qty": t["qty"], "cost": t["entry"]} for o, t in tracked.items()
                               if not t.get("closed")}, False
                if not day.get("pos_err"):
                    day["pos_err"] = True
                    log(f"!! can't read positions ({short_err(e)}) — GUARD keeps managing the "
                        f"{len(pos)} it already knows (new trades show up once Webull answers again)")
            # positions gone: our stop filled, or sold by hand in the app
            for occ, t in list(tracked.items()):
                if occ in pos:
                    t["missing"] = 0
                    continue
                if t.get("closed"):
                    del tracked[occ]
                    continue
                if t.get("oid"):
                    st, _, fpx = stop_status(t)
                    if filled(st):
                        close(occ, t, fill_px(fpx, t), "stop filled")
                        del tracked[occ]
                        continue
                # one empty positions reply can be a glitch: wait for a second one before letting go
                t["missing"] = t.get("missing", 0) + 1
                if t["missing"] >= 2:
                    cancel_stop(t)  # never leave a sell order behind for a position that's gone
                    close(occ, t, t.get("last_bid"), "sold in the app", est=True)
                    del tracked[occ]
            # new positions, or contracts added / partly sold
            for occ, p in pos.items():
                t = tracked.get(occ)
                if t and t.get("closed"):
                    # we closed it but it's still listed: Webull lagging, or you bought it again
                    t["lingers"] = t.get("lingers", 0) + 1
                    if p["cost"] == t["entry"] and t["lingers"] < 3:
                        continue  # probably lag: give Webull a few seconds
                    del tracked[occ]  # bought again: guard it as a new trade
                    pos_pc = t.get("per_contract")
                    t = None
                else:
                    pos_pc = False
                if t:
                    if t["qty"] != p["qty"]:
                        log(f"{occ}: quantity changed {t['qty']} -> {p['qty']}, resetting the stop")
                        cancel_stop(t)
                        t.update(qty=p["qty"], entry=p["cost"] or t["entry"], stop=0.0)
                        t["stop"] = guard_stop(t, g)
                    continue
                if p["cost"] <= 0:
                    continue
                entry = p["cost"]
                t = tracked[occ] = {"qty": p["qty"], "entry": entry, "peak": entry, "stop": 0.0, "oid": None,
                                    "soft": False, "below": 0, "startup": first_pass, "per_contract": pos_pc}
                t["stop"] = guard_stop(t, g)
                s_ = saved_pos.get(occ) if first_pass else None
                if s_ and s_.get("qty") == p["qty"]:
                    try:
                        st_, _, _ = broker.order_status(s_["oid"])
                    except Exception:
                        st_ = ""
                    if st_ and not filled(st_) and st_ not in done_states:  # its stop is still working: keep it
                        t.update(oid=s_["oid"], stop=s_["stop"], entry=s_["entry"], peak=max(s_["entry"], s_["peak"]),
                                 per_contract=s_.get("per_contract", False), placed=True, seen=True)
                        entry = t["entry"]
                        log(f"{occ}: picked up the stop the last Guardian window left at Webull — stop "
                            f"{t['stop']:.2f}, best price {t['peak']:.2f}; trailing continues")
                log(f"{'FOUND' if first_pass else 'NEW'} POSITION {occ} x{p['qty']} @ {entry:.2f} — max loss at "
                    f"the stop ${(entry - t['stop']) * 100 * p['qty']:.2f} ({1 - t['stop'] / entry:.0%})")
                if not first_pass:
                    day["opened"] += 1
                    if g["warnings"]:
                        for w in trade_warnings(broker, occ, now, day, g):
                            log(f"!! {w}")
                if t["stop"] > entry * 0.8:
                    log(f"!! stop is only {1 - t['stop'] / entry:.0%} under the entry — normal wiggles may hit it; "
                        f"a cheaper contract or fewer contracts gives it more room")
                if not first_pass and g["lockout"] and (day["losses"] >= g["lockout_losses"]
                                                        or -day["realized"] >= g["lockout_loss"]):
                    log("LOCKOUT: daily limit reached — selling the new position")
                    t["exit"] = "lockout"
                try:
                    acct = float(find(broker.balance(), "net_liquidation_value", "total_net_liquidation_value") or 0)
                    if acct and entry * 100 * p["qty"] > g["size_alert_pct"] * acct:
                        log(f"!! SIZE: this trade is ${entry * 100 * p['qty']:.0f} = "
                            f"{entry * 100 * p['qty'] / acct:.0%} of the account (limit {g['size_alert_pct']:.0%})")
                except Exception:
                    pass
            if pos_ok:
                first_pass = False

            live = [o for o, t in tracked.items() if not t.get("closed")]
            try:
                quotes = broker.option_quotes(live) if live else {}
            except Exception as e:
                quotes = {}
                log(f"guard: quotes failed ({short_err(e)}) — stop orders stay in place")
            for occ in live:
                t = tracked[occ]
                q = quotes.get(occ)
                bid = q["bid"] if q and q.get("bid", 0) > 0 else None
                if bid is not None:
                    t["last_bid"] = bid
                if t.get("exit"):
                    exit_now(occ, t, t["exit"])
                    continue
                # our stop order: filled? cancelled or rejected?
                if t.get("oid"):
                    st, _, fpx = stop_status(t)
                    if filled(st):
                        close(occ, t, fill_px(fpx, t), "stop filled")
                        continue
                    if st in done_states:
                        if not t.get("cancelling"):
                            if st.startswith("CANCEL"):
                                t["retry_at"] = now.timestamp() + g["manual_grace_s"]
                                log(f"!! the stop on {occ} was cancelled in the app — selling by hand? Go ahead. "
                                    f"If you still hold it in {g['manual_grace_s']}s the stop goes back on.")
                            else:
                                log(f"!! the stop on {occ} was {st.lower()} by Webull")
                        t["oid"] = None
                    elif st and not st.startswith("PENDING") and not day.get("stop_ok"):
                        day["stop_ok"] = True
                        log(f"STOP ORDER CONFIRMED — Webull shows the stop on {occ} as {st}. Stops work.")
                # Webull's cost should be per share (0.56); 20x the bid means it came per contract (56)
                if bid is not None and not t.get("seen") and t["entry"] > 20 * bid:
                    cancel_stop(t)
                    t["per_contract"] = True  # later reads of this position get converted too
                    t.update(entry=t["entry"] / 100, peak=t["peak"] / 100, stop=0.0)
                    t["stop"] = guard_stop(t, g)
                    log(f"!! {occ}: cost looked like a per-contract price — using entry {t['entry']:.2f}, "
                        f"stop {t['stop']:.2f}. Check this matches your fill in Webull.")
                # a position that was already under its stop when GUARD started: don't dump it on sight
                if bid is not None and t.get("startup") and not t.get("seen") and bid <= t["stop"]:
                    old, t["stop"] = t["stop"], r2(max(0.01, bid * 0.85))
                    log(f"!! {occ} was already under its stop when GUARD started (bid {bid:.2f} <= {old:.2f}); "
                        f"stop set 15% under the bid at {t['stop']:.2f}")
                if bid is not None:
                    t["seen"] = True
                if not t.get("oid") and (g["reprotect"] or not t.get("placed")) \
                        and now_ct().timestamp() >= t.get("retry_at", 0):
                    place_stop(occ, t)
                # same-day options: out before the close
                if parse_occ(occ)[1] == now.date() and now.time() >= flatten:
                    exit_now(occ, t, f"flatten {flat_txt} CT")
                    continue
                if kill_paths():
                    exit_now(occ, t, "KILL file")
                    continue
                if bid is None:
                    continue
                # ratchet the stop up (never down); the peak only counts a bid seen on two checks in a row
                confirmed = min(bid, t.get("prev_bid", bid))
                t["prev_bid"] = bid
                if confirmed > t["peak"]:
                    t["peak"] = confirmed
                new = min(guard_stop(t, g), r2(confirmed - 0.02))
                if new >= t["stop"] + max(0.02, 0.03 * t["stop"]):
                    old = t["stop"]
                    got = cancel_stop(t)
                    if got is not None:
                        close(occ, t, got, "stop filled")
                        continue
                    t["stop"] = new
                    log(f"TRAIL {occ}: bid {bid:.2f}, best {t['peak']:.2f} -> stop {old:.2f} -> {new:.2f} "
                        f"(locks ${(new - t['entry']) * 100 * t['qty']:+.2f})")
                    place_stop(occ, t)
                # safety net: bid under the stop but no fill (no resting order, or a stuck stop-limit)
                t["below"] = t["below"] + 1 if bid <= t["stop"] else 0
                if (t["soft"] and bid <= t["stop"]) or t["below"] >= 3:
                    exit_now(occ, t, f"bid {bid:.2f} under stop {t['stop']:.2f}")
            live = [o for o, t in tracked.items() if not t.get("closed")]
            if not warned and now.time() >= hm(g["warn_time_ct"]) and any(
                    parse_occ(o)[1] == now.date() for o in live):
                warned = True
                log(f"!! same-day options will be closed at {flat_txt} CT")
            save_state()
            if now.timestamp() - last_beat >= 300:
                last_beat = now.timestamp()
                what = ", ".join(f"{o} stop {tracked[o]['stop']:.2f}{'' if tracked[o].get('oid') else ' (watching)'}"
                                 for o in live) or "no open option positions"
                log(f"GUARD alive — {what}")
            if errs["n"]:
                log(f"connection back after {errs['n']} failed checks")
                errs["n"] = 0
        except Exception as e:
            errs["n"] += 1
            if errs["n"] == 1 or now.timestamp() - errs["last"] >= 300:
                errs["last"] = now.timestamp()
                log(f"!! guard error ({short_err(e)}) — stop orders already placed stay active at Webull. "
                    f"Retrying every {cfg['poll_seconds']}s. If this keeps showing, restart the guard "
                    f"(approve the 2FA prompt on your phone if asked).")
        time.sleep(cfg["poll_seconds"])
    try:
        os.remove(lock)
    except OSError:
        pass
    log(f"GUARD summary: {day['closed']} closed, realized ${day['realized']:+.2f}, losses {day['losses']}. "
        f"Stop orders are DAY orders: run guard again tomorrow for anything held overnight.")


ORDER_DONE = ("CANCELLED", "CANCELED", "REJECTED", "FAILED", "EXPIRED")


def order_test(broker, with_stop=True):
    """Prove Webull accepts the bot's orders without risking money: a $0.01 buy on an at-the-money SPY call
    (cannot fill) is placed and cancelled; with_stop and an option held: a $0.01 stop-limit sell on it too.
    Returns True/False for the limit-order test (None if it could not run)."""
    done_states = ORDER_DONE

    def detail(oid):
        try:
            raw = json.dumps(broker._ok(broker.trade.order_v2.get_order_detail(broker.account, oid), "order detail"))
            return raw.replace(str(broker.account), "***")[:700]
        except Exception as e:
            return f"(detail failed: {short_err(e)})"

    def place_cancel(label, occ, side, qty, limit, stop=None):
        log(f"{label}: placing {side} {qty} {occ} " + (f"STOP {stop:.2f} / " if stop else "") + f"LIMIT {limit:.2f}")
        try:
            oid = broker.place_option(occ, side, qty, limit, stop=stop)
        except Exception as e:
            log(f"{label} FAILED — Webull rejected the order: {short_err(e)}")
            return False
        try:
            time.sleep(2)
            st, _, _ = broker.order_status(oid)
            log(f"{label}: accepted, status {st or '?'}")
            log(f"{label}: order detail {detail(oid)}")
        except Exception as e:
            log(f"{label}: status error {short_err(e)}")
        finally:
            try:
                broker.cancel(oid)
            except Exception as e:
                log(f"{label}: cancel error {short_err(e)}")
        st = ""
        for _ in range(5):
            time.sleep(1)
            try:
                st, _, _ = broker.order_status(oid)
            except Exception:
                continue
            if st in done_states:
                log(f"{label} PASSED — placed and cancelled (status {st})")
                return True
            if "FILLED" in st:
                log(f"!! {label}: the test order FILLED — check Webull and close it")
                return False
        log(f"!! {label}: cancel not confirmed (status {st}) — CANCEL THE $0.01 ORDER IN WEBULL BY HAND")
        return False

    now = now_ct()
    exp = now.date() + timedelta(days=7)  # a week out: an at-the-money call is worth dollars, never $0.01
    while not market_day(exp):
        exp += timedelta(days=1)
    spot = broker.stock_quote("SPY")["price"]
    if not spot:
        log("order test: no SPY price — try again during market hours")
        return None
    occ = occ_symbol("SPY", exp, "C", round(spot))
    q = broker.option_quotes([occ]).get(occ)
    if q and 0 < q["ask"] < 0.10:
        log(f"order test: {occ} ask is only {q['ask']:.2f}; a $0.01 order is not safely unfillable — skipping")
        return None
    ok1 = place_cancel("TEST 1 (limit order)", occ, "BUY", 1, 0.01)
    if not with_stop:
        return ok1

    ok2 = None
    held = broker.option_positions()
    if not held:
        log("TEST 2 (stop-limit order) skipped: no option position. It gets checked on your first trade — "
            "look for 'PROTECTED' in the guard window and a Stop Limit order in Webull.")
    else:
        pocc, p = next(iter(held.items()))
        pq = broker.option_quotes([pocc]).get(pocc)
        if not pq or pq["bid"] <= 0.05:
            log(f"TEST 2 skipped: {pocc} has no bid above $0.05")
        else:
            ok2 = place_cancel("TEST 2 (stop-limit order)", pocc, "SELL", p["qty"], 0.01, stop=0.01)
            if not ok2:
                log("   (if the guard is running it already holds a sell order on this position — "
                    "that also blocks this test)")
    log("RESULT: " + ("orders work" if ok1 else "limit orders FAILED — send me this window") +
        ("" if ok2 is None else ("; stop-limit orders work" if ok2 else "; stop-limit FAILED — send me this window")))
    return ok1


def testorder(broker):
    if not broker.live:
        log('PAPER mode: run  python bot.py --live testorder  (nothing can fill: every test order is at $0.01)')
        return
    order_test(broker, with_stop=True)


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
    sub.add_parser("testorder", help="prove Webull accepts the bot's orders with $0.01 orders that cannot fill")
    sub.add_parser("guard", help="protect every option position you open: stop, trailing stop, same-day flatten")
    sub.add_parser("auto", help="hands-off day: opening-range levels, confirmed breakouts, automatic exits")
    a = ap.parse_args()

    cfg_path = os.path.join(HERE, "config.json")
    if not os.path.exists(cfg_path):
        sys.exit("Missing bot/config.json — copy config.example.json to config.json and fill in your keys.")
    try:
        cfg = json.load(open(cfg_path, encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        sys.exit(f"config.json has a typo at line {e.lineno}, column {e.colno}: {e.msg}. "
                 f"Check for a missing comma or quote.")
    cfg.setdefault("poll_seconds", 5)
    cfg.setdefault("risk", {})
    for k, v in {"max_cost_per_trade": 50, "max_trades_per_day": 2, "max_daily_loss": 40, "take_profit_pct": 0.8,
                 "stop_loss_pct": 0.35, "flatten_time_ct": "14:50"}.items():
        cfg["risk"].setdefault(k, v)
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
        try:  # the 'guard' command depends on reading positions correctly
            print("Option positions (as the guard reads them):", broker.option_positions() or "none")
        except Exception as e:
            print("Positions failed:", short_err(e))
        try:  # the 'auto' command depends on these 5-min candles and their timestamps
            bars = broker.bars_5m("SPY", 150)
            b = bars[-1]
            print(f"5-min bars OK: {len(bars)} bars, last {bar_dt(b['time']):%Y-%m-%d %H:%M} CT close {b['c']:.2f}")
        except Exception as e:
            print("5-min bars failed:", short_err(e))
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
    elif a.cmd == "auto":
        auto(broker, risk, cfg)
    elif a.cmd == "guard":
        guard(broker, risk, cfg)
    elif a.cmd == "testorder":
        testorder(broker)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("stopped by user (Ctrl+C)")
    except Exception as e:
        log(f"ERROR: {short_err(e)}")
        sys.exit(1)

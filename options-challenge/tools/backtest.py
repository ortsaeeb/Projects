"""Backtest the playbook's two same-day setups on Webull 5-minute bars.

Usage:
    python backtest.py [--start 101.30] [--iv-mult 1.15] [--spread 0.02] [--verbose]

Reads data/{SPY,QQQ,IWM}_M5.csv (UTC timestamps, regular hours only).

There is no historical option data, so each 0DTE option is priced with Black-Scholes:
  - IV = realized volatility of the prior 5 sessions (5-min returns) x --iv-mult, floor 12%
  - time to expiry = trading minutes left until 16:00 ET / (390 x 252)
  - $1 strikes; pick the strike nearest the money whose price fits the premium cap
  - pay mid + spread on entry, receive mid - spread on exit
IV is held constant through the trade, so real IV crush after the open is NOT captured.
"""
import argparse
import csv
import math
import os
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
SYMBOLS = ["SPY", "QQQ", "IWM"]
CLOSE_MIN = 20 * 60  # 16:00 ET = 20:00 UTC (EDT)


# ---------- option pricing ----------
def ncdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def bs(spot, strike, minutes_left, iv, kind):
    t = max(minutes_left, 0.5) / (390 * 252)
    sd = iv * math.sqrt(t)
    d1 = (math.log(spot / strike) + 0.5 * sd * sd) / sd
    d2 = d1 - sd
    if kind == "C":
        return spot * ncdf(d1) - strike * ncdf(d2), ncdf(d1)
    return strike * ncdf(-d2) - spot * ncdf(-d1), ncdf(d1) - 1


def pick_strike(spot, minutes_left, iv, kind, cap):
    """Nearest-to-money $1 strike whose mid price is <= cap."""
    k = math.ceil(spot) if kind == "C" else math.floor(spot)
    for _ in range(200):
        price, delta = bs(spot, k, minutes_left, iv, kind)
        if price <= cap:
            return k, price, delta
        k += 1 if kind == "C" else -1
    return None


# ---------- data ----------
def load(symbol):
    days = defaultdict(list)
    with open(os.path.join(DATA, f"{symbol}_M5.csv")) as f:
        for r in csv.DictReader(f):
            if "time_et" in r:  # data files store Eastern time; this script works in UTC
                t = datetime.fromisoformat(r["time_et"]).replace(tzinfo=ZoneInfo("America/New_York"))
                t = t.astimezone(timezone.utc).replace(tzinfo=None)
            else:
                t = datetime.fromisoformat(r["time_utc"])
            days[t.date()].append({
                "t": t, "min": t.hour * 60 + t.minute,
                "o": float(r["open"]), "h": float(r["high"]), "l": float(r["low"]),
                "c": float(r["close"]), "v": float(r["volume"]),
            })
    # keep only complete sessions that start at 9:30 ET
    return {d: sorted(b, key=lambda x: x["t"]) for d, b in days.items()
            if b and min(x["min"] for x in b) == 13 * 60 + 30 and len(b) >= 77}


def realized_iv(prev_days, mult):
    rets = []
    for bars in prev_days[-5:]:
        rets += [math.log(b["c"] / a["c"]) for a, b in zip(bars, bars[1:])]
    if len(rets) < 50:
        return None
    var = sum(r * r for r in rets) / len(rets)
    return max(math.sqrt(var * 78 * 252) * mult, 0.12)


def vwap_series(bars):
    pv = vol = 0.0
    out = []
    for b in bars:
        pv += (b["h"] + b["l"] + b["c"]) / 3 * b["v"]
        vol += b["v"]
        out.append(pv / vol)
    return out


# ---------- trade simulation ----------
def run_trade(bars, i, kind, strike, iv, entry_mid, spread, level_back_inside,
              stop_pct, target_pct, exit_min):
    """Walk bars after index i. Returns (exit_price, reason, exit_time)."""
    entry = entry_mid + spread
    stop = entry * (1 - stop_pct)
    target = entry * (1 + target_pct)
    for b in bars[i + 1:]:
        left = CLOSE_MIN - (b["min"] + 5)
        adverse = b["l"] if kind == "C" else b["h"]
        favour = b["h"] if kind == "C" else b["l"]
        worst, _ = bs(adverse, strike, left, iv, kind)
        best, _ = bs(favour, strike, left, iv, kind)
        if worst - spread <= stop:  # stops checked first (conservative)
            return stop, f"stop -{stop_pct:.0%}", b["t"]
        if best - spread >= target:
            return target, f"target +{target_pct:.0%}", b["t"]
        # once up 30%, stop moves to breakeven
        if best - spread >= entry * 1.30:
            stop = max(stop, entry)
        close_val = bs(b["c"], strike, left, iv, kind)[0] - spread
        if level_back_inside(b["c"]):
            return close_val, "back inside level", b["t"]
        if b["min"] + 5 >= exit_min:
            return close_val, "time stop", b["t"]
    last = bars[-1]
    return bs(last["c"], strike, 1, iv, kind)[0] - spread, "session end", last["t"]


def setup_a(bars, iv, prev_avg_vol, spread, cap, filters=True, stop=0.25, target=0.50):
    """Opening range breakout: OR = first 5-min bar, trigger bars close 9:40-9:50 ET."""
    orh, orl = bars[0]["h"], bars[0]["l"]
    vw = vwap_series(bars)
    for i, b in enumerate(bars[1:4], start=1):  # bars ending 9:40, 9:45, 9:50
        kind = "C" if b["c"] > orh else "P" if b["c"] < orl else None
        if not kind:
            continue
        if filters:
            if b["v"] < 1.5 * prev_avg_vol:
                continue
            if (kind == "C" and b["c"] < vw[i]) or (kind == "P" and b["c"] > vw[i]):
                continue
        left = CLOSE_MIN - (b["min"] + 5)
        pick = pick_strike(b["c"], left, iv, kind, cap)
        if not pick:
            return None
        strike, mid, delta = pick
        back_inside = (lambda c: c < orh) if kind == "C" else (lambda c: c > orl)
        px, reason, t = run_trade(bars, i, kind, strike, iv, mid, spread, back_inside,
                                  stop, target, 14 * 60 + 15)
        return dict(setup="A", kind=kind, strike=strike, delta=delta, entry=mid + spread,
                    exit=px, reason=reason, t_in=b["t"], t_out=t)
    return None


def setup_b(bars, iv, spread, cap, filters=True):
    """Power hour push on trend days, trigger bars close 15:35-15:50 ET."""
    vw = vwap_series(bars)
    idx = {b["min"]: i for i, b in enumerate(bars)}
    if 19 * 60 + 25 not in idx or 18 * 60 + 30 not in idx:
        return None
    afternoon = [i for i in range(idx[17 * 60 + 30], idx[19 * 60 + 25] + 1)]
    above = sum(bars[i]["c"] > vw[i] for i in afternoon) / len(afternoon)
    trend = "C" if above >= 0.8 else "P" if above <= 0.2 else None
    if not trend:
        return None
    cons = bars[idx[18 * 60 + 30]: idx[19 * 60 + 25] + 1]
    hi, lo = max(b["h"] for b in cons), min(b["l"] for b in cons)
    avg_v = sum(b["v"] for b in cons) / len(cons)
    for m in (19 * 60 + 30, 19 * 60 + 35, 19 * 60 + 40, 19 * 60 + 45):
        if m not in idx:
            continue
        i = idx[m]
        b = bars[i]
        broke = b["c"] > hi if trend == "C" else b["c"] < lo
        if not broke or (filters and b["v"] < 1.5 * avg_v):
            continue
        left = CLOSE_MIN - (b["min"] + 5)
        pick = pick_strike(b["c"], left, iv, trend, cap)
        if not pick:
            return None
        strike, mid, delta = pick
        back_inside = (lambda c: c < hi) if trend == "C" else (lambda c: c > lo)
        px, reason, t = run_trade(bars, i, trend, strike, iv, mid, spread, back_inside,
                                  0.30, 0.75, 19 * 60 + 55)
        return dict(setup="B", kind=trend, strike=strike, delta=delta, entry=mid + spread,
                    exit=px, reason=reason, t_in=b["t"], t_out=t)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=float, default=101.30)
    ap.add_argument("--iv-mult", type=float, default=1.15)
    ap.add_argument("--spread", type=float, default=0.02)
    ap.add_argument("--cap-a", type=float, default=0.80)
    ap.add_argument("--cap-b", type=float, default=0.30)
    ap.add_argument("--no-filters", action="store_true")
    ap.add_argument("--no-halt", action="store_true", help="ignore daily/circuit-breaker limits")
    ap.add_argument("--only", choices=["A", "B"], help="trade one setup only")
    ap.add_argument("--flat", action="store_true", help="take every signal (no balance/overlap limits) to measure raw edge")
    ap.add_argument("--stop-a", type=float, default=0.25)
    ap.add_argument("--target-a", type=float, default=0.50)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    trades = []
    for sym in SYMBOLS:
        days = load(sym)
        dates = sorted(days)
        for n, d in enumerate(dates):
            if n < 5:
                continue  # need history for IV and volume
            prev = [days[x] for x in dates[n - 5:n]]
            iv = realized_iv(prev, a.iv_mult)
            prev_avg_vol = sum(b["v"] for b in prev[-1]) / len(prev[-1])
            for t in (setup_a(days[d], iv, prev_avg_vol, a.spread, a.cap_a, not a.no_filters,
                              a.stop_a, a.target_a),
                      setup_b(days[d], iv, a.spread, a.cap_b, not a.no_filters)):
                if t:
                    t.update(sym=sym, date=d, iv=iv)
                    trades.append(t)

    if a.only:
        trades = [t for t in trades if t["setup"] == a.only]
    trades.sort(key=lambda t: t["t_in"])
    # ---- account simulation: 1 contract, one position at a time, playbook risk rules ----
    bal = peak = a.start
    halted = False
    taken, day_loss, day_losers, cur_day, busy_until = [], 0.0, 0, None, None
    for t in trades:
        if t["date"] != cur_day:
            cur_day, day_start, day_loss, day_losers = t["date"], bal, 0.0, 0
        if not a.no_halt and (halted or day_losers >= 2 or day_loss >= 0.30 * day_start):
            continue
        if not a.flat:
            if busy_until and t["t_in"] < busy_until:
                continue
            if t["entry"] * 100 > bal * 0.8:
                continue
        pnl = (t["exit"] - t["entry"]) * 100 - 0.0  # Webull charges no option commission
        bal += pnl
        peak = max(peak, bal)
        busy_until = t["t_out"]
        if pnl < 0:
            day_loss -= pnl
            day_losers += 1
        t["pnl"], t["bal"] = pnl, bal
        taken.append(t)
        if bal < 0.6 * peak and not a.no_halt:
            halted = True

    def stats(ts, label):
        if not ts:
            print(f"{label}: no trades")
            return
        wins = [t for t in ts if t["pnl"] > 0]
        losses = [t for t in ts if t["pnl"] <= 0]
        aw = sum(t["pnl"] for t in wins) / len(wins) if wins else 0
        al = sum(t["pnl"] for t in losses) / len(losses) if losses else 0
        print(f"{label}: {len(ts)} trades  win rate {len(wins) / len(ts):.0%}  "
              f"avg win ${aw:.2f}  avg loss ${al:.2f}  net ${sum(t['pnl'] for t in ts):+.2f}")

    all_dates = sorted({t["date"] for t in trades})
    print(f"Signals found: {len(trades)} over {len(all_dates)} days  "
          f"(filters {'OFF' if a.no_filters else 'ON'}, IV x{a.iv_mult}, spread ${a.spread})")
    stats(taken, "ALL")
    stats([t for t in taken if t["setup"] == "A"], "  Setup A (open)")
    stats([t for t in taken if t["setup"] == "B"], "  Setup B (close)")
    for s in SYMBOLS:
        stats([t for t in taken if t["sym"] == s], f"  {s}")
    lows = min([a.start] + [t["bal"] for t in taken])
    print(f"Account ${a.start:.2f} -> ${bal:.2f}  (low ${lows:.2f}, peak ${peak:.2f})"
          + ("  ** circuit breaker hit **" if halted else ""))
    avg_delta = sum(abs(t["delta"]) for t in taken) / len(taken) if taken else 0
    print(f"Average |delta| of affordable contracts: {avg_delta:.2f}")
    if a.verbose:
        for t in taken:
            print(f"  {t['date']} {t['sym']} {t['setup']} {t['strike']}{t['kind']} d{t['delta']:+.2f} "
                  f"IV {t['iv']:.0%}  in {t['entry']:.2f} out {t['exit']:.2f}  {t['pnl']:+7.2f}  "
                  f"{t['reason']:<18} bal {t['bal']:.2f}")


if __name__ == "__main__":
    main()

"""Study 9: backtest the live bot's `auto` rules exactly, then test one change at a time.

Bot rules (bot/bot.py auto + manage):
  levels  = 15-min opening range (first 3 bars) high + $0.05 / low - $0.05, on SPY and QQQ
  trigger = completed 5-min bar closes beyond a level, 08:50-14:30 CT (bar close time)
  checks  = volume >= 1.5x avg of up to 12 prior bars today; right side of VWAP; close in top/bottom 40%
            of bar range; other ETF on the same side of its VWAP
  entry   = same-day option, most expensive with ask <= $0.50, bought at the ask at the bar close
  exits   = take-profit +80%, stop -35% (on the bid), stop -> breakeven once bid >= +40%, flatten 14:50 CT
  limits  = one position at a time, max 2 trades/day, $40 daily loss

Option prices are modelled (lab.py Black-Scholes, intraday realised vol x iv_mult, bid/ask on every fill).
Run:  python study9_bot_auto.py          (IV_MULTS env var to change the IV grid)
"""
import os
import sys

import numpy as np

import lab

BASE = dict(buffer=0.05, vol_mult=1.5, vwap=True, strength=0.6, confirm=True, max_price=0.50,
            tp=0.80, sl=0.35, be=0.40, last_entry_bar=71, flatten_bar=75, max_trades=2, max_loss=40.0,
            time_stop=None, min_or=None, max_or=None, retest=False)
# bar i covers ET 9:30+5i .. 9:35+5i; close time CT = 8:35 + 5i. i=71 closes 14:30 CT, i=75 closes 14:50 CT.


def pair_days():
    spy = {d.date: d for d in lab.universe(["SPY"])}
    qqq = {d.date: d for d in lab.universe(["QQQ"])}
    return [(spy[k], qqq[k]) for k in sorted(set(spy) & set(qqq))]


def vol_ok(d, i, mult):
    prev = d.v[max(0, i - 12):i]
    return d.v[i] >= mult * (prev.mean() if len(prev) else d.v[i])


def run_trade(d, i, kind, p):
    """Buy at bar i close; manage like bot.manage. Returns (pnl $, reason, exit bar) or None."""
    pick = lab.choose_contract(d, i, kind, p["max_price"])
    if not pick:
        return None
    k, mid, _ = pick
    entry = mid + lab.half_spread(mid, d.sym)
    tp, stop, be_at = entry * (1 + p["tp"]), entry * (1 - p["sl"]), entry * (1 + p["be"])
    for j in range(i + 1, p["flatten_bar"] + 1):
        t, iv = lab.t_years(d, j), lab.iv_at(d, j)
        adverse = d.l[j] if kind == "C" else d.h[j]
        favour = d.h[j] if kind == "C" else d.l[j]
        worst = lab.bs(adverse, k, t, iv, kind)[0]
        worst -= lab.half_spread(worst, d.sym)
        best = lab.bs(favour, k, t, iv, kind)[0]
        best -= lab.half_spread(best, d.sym)
        if worst <= stop:  # conservative: adverse extreme assumed first
            return (stop - entry) * 100, "stop" if stop < entry else "breakeven", j
        if best >= tp:
            return (tp - entry) * 100, "target", j
        if best >= be_at:
            stop = max(stop, entry)
        if p["time_stop"] and j - i >= p["time_stop"]:
            cv = lab.bs(d.c[j], k, t, iv, kind)[0]
            cv -= lab.half_spread(cv, d.sym)
            if cv <= entry:
                return (max(cv, 0) - entry) * 100, "time-stop", j
    j = p["flatten_bar"]
    t, iv = lab.t_years(d, j), lab.iv_at(d, j)
    v = lab.bs(d.c[j], k, t, iv, kind)[0]
    v = max(v - lab.half_spread(v, d.sym), 0.0)
    return (v - entry) * 100, "flatten", j


def run_day(pair, p):
    days = {d.sym: d for d in pair}
    lv, vw = {}, {}
    for s, d in days.items():
        hi, lo = d.h[:3].max() + p["buffer"], d.l[:3].min() - p["buffer"]
        rng = (hi - lo) / d.c[2]
        if (p["min_or"] and rng < p["min_or"]) or (p["max_or"] and rng > p["max_or"]):
            return []
        lv[s] = (hi, lo)
        vw[s] = d.vwap
    out, realized, i = [], 0.0, 3
    armed = {}  # for retest mode: sym -> side after a valid breakout
    while i <= p["last_entry_bar"] and len(out) < p["max_trades"] and -realized < p["max_loss"]:
        took = None
        for s, d in days.items():
            o = [x for x in days if x != s][0]
            hi, lo = lv[s]
            c = d.c[i]
            side = "C" if c > hi else "P" if c < lo else None
            if p["retest"] and s in armed:  # wait for a pullback to the level that holds
                sd = armed[s]
                touched = d.l[i] <= hi + 0.10 if sd == "C" else d.h[i] >= lo - 0.10
                held = c > hi if sd == "C" else c < lo
                if touched and held:
                    took = (s, sd)
                    del armed[s]
                    break
                if (sd == "C" and c < lo) or (sd == "P" and c > hi):
                    del armed[s]
                continue
            if not side:
                continue
            if p["vol_mult"] and not vol_ok(d, i, p["vol_mult"]):
                continue
            if p["vwap"] and (side == "C") != (c > vw[s][i]):
                continue
            rng = d.h[i] - d.l[i]
            st = (c - d.l[i]) / rng if rng else 0.5
            if side == "P":
                st = 1 - st
            if p["strength"] and st < p["strength"]:
                continue
            od = days[o]
            if p["confirm"] and (side == "C") != (od.c[i] > vw[o][i]):
                continue
            if p["retest"]:
                armed[s] = side
                continue
            took = (s, side)
            break
        if not took:
            i += 1
            continue
        s, side = took
        r = run_trade(days[s], i, side, p)
        if r is None:
            i += 1
            continue
        pnl, why, j = r
        realized += pnl
        out.append(dict(date=days[s].date, sym=s, side=side, bar=i, pnl=pnl, why=why))
        i = j + 1
    return out


def stats(trades):
    def f(ts):
        if not ts:
            return "n=  0"
        a = np.array([t["pnl"] for t in ts])
        tstat = a.mean() / (a.std(ddof=1) / np.sqrt(len(a))) if len(a) > 1 and a.std() > 0 else 0
        return f"n={len(a):3d} win {np.mean(a > 0):4.0%} avg ${a.mean():+6.2f} total ${a.sum():+8.0f} t {tstat:+5.2f}"
    tr = [t for t in trades if t["date"] < lab.SPLIT]
    te = [t for t in trades if t["date"] >= lab.SPLIT]
    return f"TRAIN {f(tr)} | TEST {f(te)}"


def backtest(pairs, **over):
    p = {**BASE, **over}
    out = []
    for pr in pairs:
        out += run_day(pr, p)
    return out


VARIANTS = [
    ("BOT AS-IS", {}),
    ("- no volume check", dict(vol_mult=None)),
    ("- no VWAP check", dict(vwap=False)),
    ("- no close-strength check", dict(strength=None)),
    ("- no other-ETF confirm", dict(confirm=False)),
    ("- no checks at all (plain ORB)", dict(vol_mult=None, vwap=False, strength=None, confirm=False)),
    ("+ entries only until 10:30 CT", dict(last_entry_bar=23)),
    ("+ entries only until 12:00 CT", dict(last_entry_bar=41)),
    ("+ time stop 30 min if not green", dict(time_stop=6)),
    ("+ time stop 60 min if not green", dict(time_stop=12)),
    ("+ skip tiny opening range (<0.25%)", dict(min_or=0.0025)),
    ("+ skip wide opening range (>0.8%)", dict(max_or=0.008)),
    ("+ retest entry", dict(retest=True)),
    ("+ max price $1.00 (nearer the money)", dict(max_price=1.00)),
    ("+ take-profit 50%", dict(tp=0.5)),
    ("+ take-profit 150%", dict(tp=1.5)),
    ("+ stop 25%", dict(sl=0.25)),
    ("+ stop 50%", dict(sl=0.50)),
    ("+ 1 trade per day", dict(max_trades=1)),
]

if __name__ == "__main__":
    pairs = pair_days()
    print(f"{len(pairs)} days of SPY+QQQ, {pairs[0][0].date:%Y-%m-%d} .. {pairs[-1][0].date:%Y-%m-%d}; "
          f"train < {lab.SPLIT:%Y-%m-%d} <= test\n")
    for ivm in [float(x) for x in os.environ.get("IV_MULTS", "1.0,1.15,1.3").split(",")]:
        lab.MODEL["iv_mult"] = ivm
        print(f"=== IV = {ivm:.2f} x intraday realised vol ===")
        for name, over in VARIANTS:
            print(f"{name:<38} {stats(backtest(pairs, **over))}")
        print()
    lab.MODEL["iv_mult"] = 1.15
    ts = backtest(pairs)
    print("BOT AS-IS @1.15 exit reasons:", {k: sum(t['why'] == k for t in ts) for k in set(t['why'] for t in ts)})
    print("by symbol:", {s: round(sum(t['pnl'] for t in ts if t['sym'] == s)) for s in ("SPY", "QQQ")},
          " by side:", {s: round(sum(t['pnl'] for t in ts if t['side'] == s)) for s in ("C", "P")})
    if "-v" in sys.argv:
        for t in ts:
            print(f"{t['date']:%Y-%m-%d} {t['sym']} {t['side']} bar {t['bar']:2d} {t['why']:<9} ${t['pnl']:+.2f}")

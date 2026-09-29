"""Study 11: what worked in September 2026? Regime stats + 11 intraday strategies, SPY/QQQ/IWM, 5-min bars.

Every strategy is tested on September 2026 AND on the 11 months before it (Oct 2025 - Aug 2026): a rule that
only worked in one month of ~20 trading days is most likely luck.

Trades: same-day option bought at the ask at a completed 5-min close (bar i), priced with lab.py's model.
Exits (default) = the live Trade Guardian's rules: first stop 30% of cost clamped to $10-$20, ladder
(+40% -> breakeven, +80% -> +30%, +150% -> +90%), trail 25% under the best price after +150%, forced exit 14:50 CT.
Conservative fills: the adverse bar extreme is checked first, the best price only counts at bar closes,
stop fills 3% under the stop. Also reported: the underlying's move in the trade direction (signal quality,
no option pricing), and the same trade with a fixed +80% / -35% exit and with hold-to-14:50.

Run:  python study11_september.py        (env vars for sensitivity: IV=1.0, BUDGET=3.00, DTE=1)
"""
import math
import os
from collections import defaultdict

import numpy as np
import pandas as pd

import lab
from study10_volume_profile import profile

SYMS = ["SPY", "QQQ", "IWM"]
SEPT = pd.Timestamp("2026-09-01")
AUG = pd.Timestamp("2026-08-01")
FLAT = 75            # bar closing 14:50 CT
BUDGET = float(os.environ.get("BUDGET", "0.50"))
lab.MODEL["iv_mult"] = float(os.environ.get("IV", "1.15"))
DTE = int(os.environ.get("DTE", "0"))  # 0 = same-day expiry; N = option expiring N trading days later
if DTE:
    lab.days_to_expiry = lambda day: DTE


# ---------------------------------------------------------------- exits
def guard_stop(entry, peak, qty=1):
    cost = entry * 100 * qty
    risk = min(20, max(10, 0.30 * cost))
    stop = max(0.05, entry - risk / (100 * qty))
    gain = peak / entry - 1
    for reached, lock in ((0.40, 0.0), (0.80, 0.30), (1.50, 0.90)):
        if gain >= reached:
            stop = max(stop, entry * (1 + lock))
    if gain >= 1.50:
        stop = max(stop, peak * 0.75)
    return stop


def opt_px(d, j, spot, k, kind):
    v = lab.bs(spot, k, lab.t_years(d, j), lab.iv_at(d, j), kind)[0]
    return max(v - lab.half_spread(v, d.sym), 0.0)


def trade(d, i, kind, exit_mode="guardian", budget=BUDGET):
    pick = lab.choose_contract(d, i, kind, budget)
    if not pick:
        return None
    k, mid, _ = pick
    entry = mid + lab.half_spread(mid, d.sym)
    peak = entry
    stop = guard_stop(entry, peak)
    for j in range(i + 1, FLAT + 1):
        adverse = d.l[j] if kind == "C" else d.h[j]
        worst = opt_px(d, j, adverse, k, kind)
        close = opt_px(d, j, d.c[j], k, kind)
        if exit_mode == "fixed":
            best = opt_px(d, j, d.h[j] if kind == "C" else d.l[j], k, kind)
            if worst <= entry * 0.65:
                return (entry * 0.65 - entry) * 100
            if best >= entry * 1.80:
                return (entry * 0.80) * 100
            continue
        if exit_mode == "guardian":
            if worst <= stop:
                fill = min(stop * 0.97, opt_px(d, j, d.o[j], k, kind)) if j > i + 1 else stop * 0.97
                return (max(fill, 0) - entry) * 100
            peak = max(peak, close)
            stop = max(stop, min(guard_stop(entry, peak), close - 0.02))
    return (opt_px(d, FLAT, d.c[FLAT], k, kind) - entry) * 100


def und_move(d, i, kind):
    """Underlying move from entry close to the 14:50 close, in the trade direction, in bps."""
    r = d.c[FLAT] / d.c[i] - 1
    return (r if kind == "C" else -r) * 1e4


# ---------------------------------------------------------------- helpers
def rsi(c, n=14):
    diff = np.diff(c, prepend=c[0])
    up, dn = np.clip(diff, 0, None), np.clip(-diff, 0, None)
    out = np.full(len(c), 50.0)
    au, ad = up[1:n + 1].mean(), dn[1:n + 1].mean()
    for t in range(n + 1, len(c)):
        au = (au * (n - 1) + up[t]) / n
        ad = (ad * (n - 1) + dn[t]) / n
        out[t] = 100 - 100 / (1 + au / ad) if ad > 0 else 100
    return out


def ema(x, n):
    a, out = 2 / (n + 1), np.empty(len(x))
    out[0] = x[0]
    for t in range(1, len(x)):
        out[t] = a * x[t] + (1 - a) * out[t - 1]
    return out


# ---------------------------------------------------------------- strategies: return first (bar, kind) or None
def s_orb(d, prof):
    hi, lo = d.h[:3].max(), d.l[:3].min()
    for i in range(3, 24):
        if d.c[i] > hi:
            return i, "C"
        if d.c[i] < lo:
            return i, "P"


def s_orb_fail(d, prof):
    hi, lo = d.h[:3].max(), d.l[:3].min()
    brk = None
    for i in range(3, 30):
        if brk is None:
            brk = ("up", i) if d.c[i] > hi else ("dn", i) if d.c[i] < lo else None
        elif i - brk[1] <= 3:
            if brk[0] == "up" and d.c[i] < hi:
                return i, "P"
            if brk[0] == "dn" and d.c[i] > lo:
                return i, "C"
        else:
            return None


def s_vwap_pullback(d, prof):
    vw = d.vwap
    for i in range(7, 60):
        above = np.all(d.c[i - 6:i] > vw[i - 6:i])
        below = np.all(d.c[i - 6:i] < vw[i - 6:i])
        if above and d.l[i] <= vw[i] and d.c[i] > vw[i]:
            return i, "C"
        if below and d.h[i] >= vw[i] and d.c[i] < vw[i]:
            return i, "P"


def s_ema_cross(d, prof):
    e9, e21, vw = ema(d.c, 9), ema(d.c, 21), d.vwap
    for i in range(6, 42):
        if e9[i - 1] <= e21[i - 1] and e9[i] > e21[i] and d.c[i] > vw[i]:
            return i, "C"
        if e9[i - 1] >= e21[i - 1] and e9[i] < e21[i] and d.c[i] < vw[i]:
            return i, "P"


def s_rsi_revert(d, prof):
    r = rsi(d.c)
    for i in range(6, 66):
        if r[i] < 25:
            return i, "C"
        if r[i] > 75:
            return i, "P"


def s_gap_fade(d, prof):
    g = d.o[0] / d.prev_close - 1
    if abs(g) < 0.003:
        return None
    return (2, "P") if g > 0 else (2, "C")


def s_gap_go(d, prof):
    g = d.o[0] / d.prev_close - 1
    if abs(g) < 0.003:
        return None
    if g > 0 and d.c[2] > d.o[0]:
        return 2, "C"
    if g < 0 and d.c[2] < d.o[0]:
        return 2, "P"


def s_value_plan(d, prof):
    """The plan traded live on 09-29: open vs prior-day value; acceptance or failure."""
    poc, vah, val = prof
    o = d.o[0]
    if val <= o <= vah:  # A: open inside -> first close outside value
        for i in range(3, 24):
            if d.c[i] > vah:
                return i, "C"
            if d.c[i] < val:
                return i, "P"
        return None
    if o > vah:  # B: gap up above value
        if d.c[1] > vah and d.c[2] > vah:
            return 2, "C"
        for i in range(1, 24):
            if d.c[i] < vah:
                return i, "P"
        return None
    if d.c[1] < val and d.c[2] < val:  # C: gap down below value
        return 2, "P"
    for i in range(1, 24):
        if d.c[i] > val:
            return i, "C"


def s_trend_1030(d, prof):
    i = 23  # bar closing 10:30 CT
    move = d.c[i] / d.o[0] - 1
    vw = d.vwap
    if move > 0.004 and d.c[i] > vw[i]:
        return i, "C"
    if move < -0.004 and d.c[i] < vw[i]:
        return i, "P"


def s_power_hour(d, prof):
    hi, lo = d.h[24:66].max(), d.l[24:66].min()  # 10:30-14:00 CT range
    for i in range(66, 71):
        if d.c[i] > hi:
            return i, "C"
        if d.c[i] < lo:
            return i, "P"


def s_poc_magnet(d, prof):
    """Open outside prior value, back inside for 2 closes -> trade toward the POC."""
    poc, vah, val = prof
    o = d.o[0]
    if val <= o <= vah:
        return None
    run = 0
    for i in range(1, 24):
        inside = val <= d.c[i] <= vah
        run = run + 1 if inside else 0
        if run == 2:
            if o > vah and d.c[i] > poc:
                return i, "P"
            if o < val and d.c[i] < poc:
                return i, "C"
            return None


STRATS = {
    "ORB 15-min breakout": s_orb,
    "ORB failed breakout (fade)": s_orb_fail,
    "VWAP pullback in trend": s_vwap_pullback,
    "EMA 9/21 cross + VWAP": s_ema_cross,
    "RSI(14) 5-min extreme reversal": s_rsi_revert,
    "Gap fade (>0.3%)": s_gap_fade,
    "Gap and go (>0.3%)": s_gap_go,
    "Prior-day value plan (09-29 plan)": s_value_plan,
    "Trend day at 10:30 CT (>0.4% + VWAP)": s_trend_1030,
    "Power hour break (14:00 CT)": s_power_hour,
    "Back into value -> POC": s_poc_magnet,
}


def period(date):
    return "SEP" if date >= SEPT else "PRIOR"


# ---------------------------------------------------------------- regime
def regime(days):
    rows = []
    for d in days:
        rng = d.h.max() - d.l.min()
        vw = d.vwap
        side = np.sign(d.c - vw)
        rows.append(dict(
            sym=d.sym, month=d.date.strftime("%Y-%m"),
            range_pct=rng / d.o[0] * 100,
            trend=abs(d.c[-1] - d.o[0]) / rng if rng else 0,
            gap_pct=abs(d.o[0] / d.prev_close - 1) * 100,
            orb_held=float(np.sign(d.c[-1] - d.o[0]) == np.sign(d.c[5] - d.o[0])),
            extreme_first30=float(d.h[:6].max() == d.h.max() or d.l[:6].min() == d.l.min()),
            vwap_flips=int(np.sum(side[1:] != side[:-1])),
            mid_share=(d.h[24:66].max() - d.l[24:66].min()) / rng if rng else 0,
            up=float(d.c[-1] > d.o[0]),
        ))
    return pd.DataFrame(rows)


def main():
    days = lab.universe(SYMS)
    byday = defaultdict(list)
    for d in days:
        byday[d.sym].append(d)
    profs = {}
    for s, ds in byday.items():
        ds.sort(key=lambda x: x.date)
        for a, b in zip(ds[:-1], ds[1:]):
            profs[(s, b.date)] = profile(a)
    days = [d for d in days if (d.sym, d.date) in profs]

    reg = regime(days)
    recent = reg[reg.month >= "2026-04"]
    print(f"IV x{lab.MODEL['iv_mult']}, budget ${BUDGET:.2f}, DTE {DTE}, symbols {SYMS}")
    print("\n== REGIME by month (all 3 ETFs) ==")
    g = recent.groupby("month").agg(days=("sym", "size"), range_pct=("range_pct", "mean"), trend=("trend", "mean"),
                                     gap_pct=("gap_pct", "mean"), orb_held=("orb_held", "mean"),
                                     ext30=("extreme_first30", "mean"), vwap_flips=("vwap_flips", "mean"),
                                     mid_share=("mid_share", "mean"), up_days=("up", "mean"))
    print(g.round(2).to_string())

    print("\n== STRATEGIES (1 signal per symbol-day; Guardian exits) ==")
    hdr = f"{'strategy':<38} {'period':<6} {'n':>4} {'win':>5} {'$/trade':>8} {'total':>8} {'und bps':>8} {'fixed$':>7} {'hold$':>7}"
    print(hdr)
    summary = []
    for name, fn in STRATS.items():
        res = defaultdict(list)
        for d in days:
            sig = fn(d, profs[(d.sym, d.date)])
            if not sig:
                continue
            i, kind = sig
            pnl = trade(d, i, kind)
            if pnl is None:
                continue
            res[period(d.date)].append((pnl, und_move(d, i, kind), trade(d, i, kind, "fixed"), trade(d, i, kind, "hold"),
                                        d.sym, d.date))
        for per in ("SEP", "PRIOR"):
            r = res[per]
            if not r:
                print(f"{name:<38} {per:<6}    0")
                continue
            a = np.array([x[0] for x in r])
            u = np.array([x[1] for x in r])
            fx = np.array([x[2] for x in r])
            hd = np.array([x[3] for x in r])
            print(f"{name:<38} {per:<6} {len(a):>4} {np.mean(a > 0):>5.0%} {a.mean():>+8.2f} {a.sum():>+8.0f} "
                  f"{u.mean():>+8.1f} {fx.mean():>+7.2f} {hd.mean():>+7.2f}")
            summary.append((name, per, len(a), a.mean(), u.mean()))
    return summary


if __name__ == "__main__":
    main()

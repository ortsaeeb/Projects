"""Study 10: prior-day volume profile (VAH / POC / VAL) setups for same-day options.

Profile: previous regular session, 5-min bars, each bar's volume spread evenly over its high-low range,
~$0.05 rows (scaled to price), value area = 70% of volume grown out from the POC.

Setups (entries on a completed 5-min close, from 8:45 CT until the entry cut-off):
  A  open > VAH, a bar touches VAH and closes above it          -> call, stop = close back below VAH
  B  open < VAL, a bar touches VAL and closes below it          -> put,  stop = close back above VAL
  C  open outside value, 6 straight closes back inside (80% rule) -> trade toward the other edge,
     stop = close back outside on the open side, target = the other edge
  D  open inside value, first close outside value (acceptance)   -> trade the break, stop = close back inside
Exits: level stop (bar close), optional target level, optional option take-profit, forced exit at 14:50 CT.
Limits: one position at a time, max 2 trades/day, stop after 2 losses.

Run:  python study10_volume_profile.py            (IV_MULTS / SYMS env vars to change the grid)
"""
import itertools
import math
import os

import numpy as np

import lab

SYMS = os.environ.get("SYMS", "SPY,QQQ,IWM").split(",")
FLAT = 75            # bar closing 14:50 CT
BASE = dict(setups="ABCD", cut=23, budget=0.50, tp=None, max_trades=2, target=True, hold_bars=None)


def profile(d):
    """Return (poc, vah, val) for day d's regular session."""
    step = max(0.01, round(d.c[-1] * 7e-5, 2))
    lo_all, hi_all = d.l.min(), d.h.max()
    n = int(math.ceil((hi_all - lo_all) / step)) + 1
    vol = np.zeros(n)
    for h, l, v in zip(d.h, d.l, d.v):
        a, b = int((l - lo_all) / step), int((h - lo_all) / step)
        vol[a:b + 1] += v / (b - a + 1)
    p = int(vol.argmax())
    lo = hi = p
    acc, tot = vol[p], vol.sum()
    while acc < 0.7 * tot:
        up = vol[hi + 1] if hi + 1 < n else -1
        dn = vol[lo - 1] if lo > 0 else -1
        if up >= dn:
            hi += 1
            acc += up
        else:
            lo -= 1
            acc += dn
    px = lambda k: lo_all + (k + 0.5) * step
    return px(p), px(hi) + step / 2, px(lo) - step / 2


def signals(d, poc, vah, val, p):
    """Yield (bar, side, stop_level, stop_dir, target) candidates in time order.
    stop_dir=+1: exit when close > stop_level; -1: exit when close < stop_level."""
    o = d.o[0]
    inside_run = 0
    opened = "above" if o > vah else "below" if o < val else "inside"
    for i in range(3, p["cut"] + 1):
        c, h, l = d.c[i], d.h[i], d.l[i]
        if "A" in p["setups"] and opened == "above" and l <= vah < c:
            yield i, "C", vah, -1, (d.h[:i + 1].max() if p["target"] else None), "A"
        if "B" in p["setups"] and opened == "below" and h >= val > c:
            yield i, "P", val, +1, (d.l[:i + 1].min() if p["target"] else None), "B"
        if "C" in p["setups"] and opened != "inside":
            inside_run = inside_run + 1 if val <= c <= vah else 0
            if inside_run == 6:
                if opened == "above":
                    yield i, "P", vah, +1, (val if p["target"] else None), "C"
                else:
                    yield i, "C", val, -1, (vah if p["target"] else None), "C"
        if "D" in p["setups"] and opened == "inside":
            if c > vah and d.c[i - 1] <= vah:
                yield i, "C", vah, -1, None, "D"
            if c < val and d.c[i - 1] >= val:
                yield i, "P", val, +1, None, "D"


def run_trade(d, i, side, stop_lvl, stop_dir, target, p):
    pick = lab.choose_contract(d, i, side, p["budget"])
    if not pick:
        return None
    k, mid, _ = pick
    entry = mid + lab.half_spread(mid, d.sym)
    s = 1 if side == "C" else -1
    last = FLAT if p["hold_bars"] is None else min(FLAT, i + p["hold_bars"])
    for j in range(i + 1, last + 1):
        t, iv = lab.t_years(d, j), lab.iv_at(d, j)
        if p["tp"]:
            fav = d.h[j] if side == "C" else d.l[j]
            best = lab.bs(fav, k, t, iv, side)[0]
            best -= lab.half_spread(best, d.sym)
            if best >= entry * (1 + p["tp"]):
                return entry * p["tp"], "tp", j, s * (fav / d.c[i] - 1)
        hit_target = target is not None and ((side == "C" and d.h[j] >= target) or (side == "P" and d.l[j] <= target))
        stopped = (stop_dir < 0 and d.c[j] < stop_lvl) or (stop_dir > 0 and d.c[j] > stop_lvl)
        if hit_target or stopped or j == last:
            px = target if hit_target and not stopped else d.c[j]
            v = lab.bs(px, k, t, iv, side)[0]
            v = max(v - lab.half_spread(v, d.sym), 0.0)
            why = "stop" if stopped else "target" if hit_target else "time"
            return v - entry, why, j, s * (px / d.c[i] - 1)
    return None


def run_day(d, prev, p):
    poc, vah, val = profile(prev)
    out, busy_until, losses = [], -1, 0
    for i, side, sl, sd, tgt, name in signals(d, poc, vah, val, p):
        if i <= busy_until or len(out) >= p["max_trades"] or losses >= 2:
            continue
        r = run_trade(d, i, side, sl, sd, tgt, p)
        if r is None:
            continue
        pnl, why, j, und = r
        out.append(dict(date=d.date, sym=d.sym, setup=name, side=side, bar=i, pnl=pnl * 100,
                        ret=pnl / (lab.choose_contract(d, i, side, p["budget"])[1] + 1e-9), und=und * 1e4, why=why))
        losses += pnl < 0
        busy_until = j
    return out


def all_days():
    out = []
    for s in SYMS:
        days = lab.universe([s])
        out += [(days[k], days[k - 1]) for k in range(1, len(days)) if (days[k].date - days[k - 1].date).days <= 4]
    return out


def backtest(pairs, **over):
    p = {**BASE, **over}
    res = []
    for d, prev in pairs:
        res += run_day(d, prev, p)
    return res


def fmt(ts):
    if not ts:
        return "n=  0" + " " * 52
    a = np.array([t["pnl"] for t in ts])
    u = np.array([t["und"] for t in ts])
    tt = a.mean() / (a.std(ddof=1) / math.sqrt(len(a))) if len(a) > 1 and a.std() > 0 else 0
    return f"n={len(a):3d} win {np.mean(a > 0):4.0%} ${a.mean():+6.2f}/tr tot ${a.sum():+7.0f} t{tt:+5.2f} und {u.mean():+5.1f}bp"


def report(label, ts):
    tr = [t for t in ts if t["date"] < lab.SPLIT]
    te = [t for t in ts if t["date"] >= lab.SPLIT]
    print(f"{label:<34} TRAIN {fmt(tr)} | TEST {fmt(te)}")


if __name__ == "__main__":
    pairs = all_days()
    print(f"{len(pairs)} symbol-days ({','.join(SYMS)}), train < {lab.SPLIT:%Y-%m-%d} <= test\n")
    for ivm in [float(x) for x in os.environ.get("IV_MULTS", "1.0,1.15,1.3").split(",")]:
        lab.MODEL["iv_mult"] = ivm
        print(f"=== IV {ivm:.2f}x ===")
        base = backtest(pairs)
        report("ALL setups (base)", base)
        for s in "ABCD":
            report(f"  setup {s} only", backtest(pairs, setups=s))
        for label, over in [("  no targets", dict(target=False)), ("  entries until 9:30 CT", dict(cut=11)),
                            ("  entries until 12:00 CT", dict(cut=41)), ("  option TP +50%", dict(tp=0.5)),
                            ("  option TP +100%", dict(tp=1.0)), ("  hold max 30 min", dict(hold_bars=6)),
                            ("  hold max 60 min", dict(hold_bars=12)), ("  budget $1.50", dict(budget=1.5)),
                            ("  budget $3.00 (near ATM)", dict(budget=3.0)), ("  1 trade/day", dict(max_trades=1))]:
            report(label, backtest(pairs, **over))
        print()
    lab.MODEL["iv_mult"] = 1.15
    base = backtest(pairs)
    print("exit reasons @1.15:", {w: sum(t["why"] == w for t in base) for w in ("stop", "target", "tp", "time")})
    for s in SYMS:
        report(f"symbol {s}", [t for t in base if t["sym"] == s])

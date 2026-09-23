"""Step 1: does each signal predict direction of the underlying at all?

For every signal we record the signed forward return (positive = signal was right),
in basis points, and in units of the day's expected move (ATR). Train/test split
at lab.SPLIT so we can see if an effect survives out of sample.
"""
import math
import sys
from collections import defaultdict

import numpy as np

import lab

days = lab.universe()
print(f"{len(days)} ticker-days loaded")

sig = defaultdict(list)  # name -> list of (date, sym, signed_ret_bps, signed_ret_atr)


def add(name, d, direction, entry_px, exit_px):
    r = direction * (exit_px / entry_px - 1)
    sig[name].append((d.date, d.sym, r * 1e4, direction * (exit_px - entry_px) / d.atr14))


for d in days:
    c, o, h, l, v = d.c, d.o, d.h, d.l, d.v
    vw = d.vwap
    gap = o[0] / d.prev_close - 1
    open_ = o[0]
    grp = "ETF" if d.sym in lab.ETFS else "STK"

    # ---- 1. Intraday momentum (Gao et al.): first 30 min (prev close -> 10:00) predicts last 30 min
    r30 = c[5] / d.prev_close - 1
    if abs(r30) > 0:
        add(f"{grp} mom: first30 -> 15:30-16:00", d, np.sign(r30), c[71], c[77])
    # open -> 15:00 predicts last hour
    r_day = c[65] / open_ - 1
    add(f"{grp} mom: open-15:00 -> 15:00-16:00", d, np.sign(r_day), c[65], c[77])
    # strong-trend days only
    if abs(r_day) > 0.5 * d.atr14 / open_:
        add(f"{grp} mom: strong open-15:00 -> last hour", d, np.sign(r_day), c[65], c[77])
        add(f"{grp} mom: strong open-15:30 -> last 30", d, np.sign(c[71] / open_ - 1), c[71], c[77])

    # ---- 2. Opening range breakout, OR = first N bars, first close outside OR up to 11:00
    for n in (1, 3, 6):
        orh, orl = h[:n].max(), l[:n].min()
        for i in range(n, 18):
            if c[i] > orh or c[i] < orl:
                direction = 1 if c[i] > orh else -1
                rvol = v[:i + 1].sum() / d.avgvol20[:i + 1].sum()
                for hold, lbl in ((6, "30m"), (12, "60m"), (77 - i, "close")):
                    j = min(i + hold, 77)
                    add(f"{grp} ORB{n * 5} -> {lbl}", d, direction, c[i], c[j])
                    if rvol > 1.5:
                        add(f"{grp} ORB{n * 5} rvol>1.5 -> {lbl}", d, direction, c[i], c[j])
                    if np.sign(gap) == direction and abs(gap) > 0.003:
                        add(f"{grp} ORB{n * 5} with-gap -> {lbl}", d, direction, c[i], c[j])
                    if (direction == 1 and c[i] > vw[i]) or (direction == -1 and c[i] < vw[i]):
                        add(f"{grp} ORB{n * 5} vwap-ok -> {lbl}", d, direction, c[i], c[j])
                break

    # ---- 3. Gaps: fade vs go (open -> 10:00, open -> close)
    gap_atr = (open_ - d.prev_close) / d.atr14
    if abs(gap_atr) > 0.3:
        add(f"{grp} gap>0.3ATR FADE open->10:00", d, -np.sign(gap_atr), open_, c[5])
        add(f"{grp} gap>0.3ATR FADE open->close", d, -np.sign(gap_atr), open_, c[77])
        # gap & go: first 15 min continues gap direction
        if np.sign(c[2] - open_) == np.sign(gap_atr):
            add(f"{grp} gap&go (15m confirms) -> 11:00", d, np.sign(gap_atr), c[2], c[17])
            add(f"{grp} gap&go (15m confirms) -> close", d, np.sign(gap_atr), c[2], c[77])
        else:
            add(f"{grp} gap-fail (15m reverses) fade -> 11:00", d, -np.sign(gap_atr), c[2], c[17])
            add(f"{grp} gap-fail (15m reverses) fade -> close", d, -np.sign(gap_atr), c[2], c[77])

    # ---- 4. Previous-day high/low break (first break before noon)
    for i in range(1, 30):
        if c[i] > d.prev_high or c[i] < d.prev_low:
            direction = 1 if c[i] > d.prev_high else -1
            add(f"{grp} PDH/PDL break -> 60m", d, direction, c[i], c[min(i + 12, 77)])
            add(f"{grp} PDH/PDL break -> close", d, direction, c[i], c[77])
            break

    # ---- 5. VWAP trend pullback: at 10:30-12:00, trend (above VWAP 80% of bars), pullback touches VWAP and closes back in trend
    above = c[:12] > vw[:12]
    frac = above.mean()
    if frac >= 0.8 or frac <= 0.2:
        direction = 1 if frac >= 0.8 else -1
        for i in range(12, 30):
            touched = l[i] <= vw[i] if direction == 1 else h[i] >= vw[i]
            closed_ok = c[i] > vw[i] if direction == 1 else c[i] < vw[i]
            if touched and closed_ok:
                add(f"{grp} VWAP pullback -> 60m", d, direction, c[i], c[min(i + 12, 77)])
                add(f"{grp} VWAP pullback -> close", d, direction, c[i], c[77])
                break

    # ---- 6. Mean reversion: 5-min move stretched > 2.5 sd bands from VWAP, fade 30m
    dev = c - vw
    for i in range(6, 70):
        sd = np.std(c[max(0, i - 20):i + 1] - vw[max(0, i - 20):i + 1]) + 1e-9
        if abs(dev[i]) > 2.5 * sd and abs(dev[i]) > 0.25 * d.atr14:
            add(f"{grp} VWAP stretch fade -> 30m", d, -np.sign(dev[i]), c[i], c[min(i + 6, 77)])
            break

    # ---- 7. Late-day: 15:00 break of 14:00-15:00 range in day-trend direction
    rng_h, rng_l = h[54:66].max(), l[54:66].min()
    trend = np.sign(c[65] - open_)
    for i in range(66, 74):
        if (trend > 0 and c[i] > rng_h) or (trend < 0 and c[i] < rng_l):
            add(f"{grp} power-hour break w/ trend -> close", d, trend, c[i], c[77])
            break


def stats(rows):
    a = np.array([r[2] for r in rows])
    atr = np.array([r[3] for r in rows])
    t = a.mean() / (a.std(ddof=1) / math.sqrt(len(a))) if len(a) > 2 else 0
    return len(a), np.mean(a > 0), a.mean(), atr.mean(), t


print(f"{'signal':<44} {'n':>5} {'hit':>5} {'bps':>6} {'ATR':>6} {'t':>6} || "
      f"{'TRAIN n':>7} {'bps':>6} {'t':>5} | {'TEST n':>6} {'bps':>6} {'t':>5}")
for name in sorted(sig):
    rows = sig[name]
    n, hit, bps, atr, t = stats(rows)
    tr = [r for r in rows if r[0] < lab.SPLIT]
    te = [r for r in rows if r[0] >= lab.SPLIT]
    if len(tr) < 5 or len(te) < 5:
        continue
    _, _, btr, _, ttr = stats(tr)
    _, _, bte, _, tte = stats(te)
    flag = " <==" if ttr > 2 and tte > 1.5 else ""
    print(f"{name:<44} {n:5d} {hit:5.0%} {bps:+6.1f} {atr:+6.3f} {t:+6.2f} || "
          f"{len(tr):7d} {btr:+6.1f} {ttr:+5.2f} | {len(te):6d} {bte:+6.1f} {tte:+5.2f}{flag}")

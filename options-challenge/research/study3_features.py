"""Step 3: build a table of every candidate entry with its context features and outcomes.

Candidates (all tickers):
  orb15   first close outside the 15-min opening range (9:45-11:00)
  orb30   first close outside the 30-min opening range (10:00-11:30)
  pdhl    first close beyond prior-day high/low before noon
  vwpb    trend-day VWAP pullback 10:30-12:00
Outcomes: underlying forward return (ATR units) and option returns for a nearest-money
single option under the lab model, for several exits. Saved to research/out/candidates.csv
"""
import os

import numpy as np
import pandas as pd

import lab
import opt

IVM = float(os.environ.get("IVM", lab.MODEL["iv_mult"]))
lab.MODEL["iv_mult"] = IVM
OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)

days = lab.universe()
by_date = {}
for d in days:
    by_date.setdefault(d.date, {})[d.sym] = d


def market_align(date, i, direction):
    """+1 if SPY at bar i is on the trade's side of both its VWAP and its open, -1 if opposite, 0 mixed."""
    spy = by_date.get(date, {}).get("SPY")
    if spy is None:
        return 0
    vw = spy.vwap[i]
    a = np.sign(spy.c[i] - vw) * direction
    b = np.sign(spy.c[i] - spy.o[0]) * direction
    return int(a) if a == b else 0


rows = []


def record(d, i, direction, cand, und_stop):
    kind = "C" if direction > 0 else "P"
    c = d.c
    gap = (d.o[0] - d.prev_close) / d.atr14
    feat = dict(
        sym=d.sym, date=d.date, cand=cand, bar=i, dir=direction, etf=int(d.sym in lab.ETFS), dow=d.dow,
        gap_al=gap * direction,                                    # gap aligned with trade (ATR units)
        move_al=(c[i] - d.o[0]) / d.atr14 * direction,             # move since open aligned
        or_rng=(d.h[:3].max() - d.l[:3].min()) / d.atr14,          # 15-min range vs ATR
        rvol=d.v[:i + 1].sum() / d.avgvol20[:i + 1].sum(),
        prev_al=np.sign(d.prev_ret) * direction,
        vw_dist=(c[i] - d.vwap[i]) / d.atr14 * direction,
        mkt=market_align(d.date, i, direction),
        rv20=d.rv20,
        fwd12=(c[min(i + 12, 77)] - c[i]) / d.atr14 * direction,
        fwd_close=(c[77] - c[i]) / d.atr14 * direction,
    )
    for name, kw in (
        ("o_60m", dict(exit_bar=min(i + 12, 77), und_stop=und_stop)),
        ("o_2h", dict(exit_bar=min(i + 24, 77), und_stop=und_stop)),
        ("o_close_trail", dict(exit_bar=76, und_stop=und_stop, trail_pct=0.3)),
    ):
        t = opt.run(d, i, kind, "atm", 0, **kw)
        feat[name] = t.ret if t else np.nan
    t = opt.run(d, i, kind, "single", 100, exit_bar=min(i + 12, 77), und_stop=und_stop)
    feat["o100_60m"] = t.ret if t else np.nan
    feat["o100_delta"] = abs(t.delta) if t else np.nan
    rows.append(feat)


for d in days:
    c, h, l = d.c, d.h, d.l
    # orb15 / orb30
    for cand, n, last in (("orb15", 3, 17), ("orb30", 6, 23)):
        orh, orl = h[:n].max(), l[:n].min()
        for i in range(n, last + 1):
            if c[i] > orh or c[i] < orl:
                direction = 1 if c[i] > orh else -1
                record(d, i, direction, cand, orl if direction > 0 else orh)
                break
    # prior-day high/low
    for i in range(1, 30):
        if c[i] > d.prev_high or c[i] < d.prev_low:
            direction = 1 if c[i] > d.prev_high else -1
            record(d, i, direction, "pdhl", d.prev_high if direction > 0 else d.prev_low)
            break
    # vwap pullback on trend mornings
    vw = d.vwap
    frac = (c[:12] > vw[:12]).mean()
    if frac >= 0.8 or frac <= 0.2:
        direction = 1 if frac >= 0.8 else -1
        for i in range(12, 30):
            touched = l[i] <= vw[i] if direction > 0 else h[i] >= vw[i]
            ok = c[i] > vw[i] if direction > 0 else c[i] < vw[i]
            if touched and ok:
                record(d, i, direction, "vwpb", vw[i] - direction * 0.1 * d.atr14)
                break

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, f"candidates_iv{IVM}.csv"), index=False)
print(len(df), "candidates")
print(df.groupby(["cand", "etf"])[["fwd12", "fwd_close", "o_60m", "o_2h", "o_close_trail", "o100_60m"]].mean().round(3))

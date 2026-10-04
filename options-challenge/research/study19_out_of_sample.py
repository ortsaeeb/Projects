"""Study 19: out-of-sample test on years the strategies never saw (May 2023 - Aug 2025).

Data: data/ext/{SPY,QQQ}_M5.csv, built by tools/build_ext_m5.py from Dukascopy's 1-minute S&P 500 / Nasdaq-100
index CFDs, scaled to SPY / QQQ prices. Options priced at market IV (market_iv.py: VIX1D, VXN/VIX for QQQ, variance
clock from the ORIGINAL data's train days), at 1.0x and 1.25x.

Pre-registered before looking at this data (2026-10-04):
  primary    the sweep model exactly as in study14b (CFG unchanged), $0.60 and $0.30 contracts
  secondary  gap fade > 0.3% with a 1-hour exit; gap and go > 0.3% held to 14:50 CT; failed-ORB fade held to 14:50 CT
  controls   ORB 15-min with a 1-hour exit, RSI(14) 5-min extremes with a 1-hour exit, power hour (none passed before)
  explore    the sweep model with sweep="any" (study14's looser first version, about twice as many trades): reported,
             not a candidate
  "works"    average $/contract > 0 at BOTH 1.0x and 1.25x market IV over the new period, t > 1.5 at 1.0x.
Volume/VWAP rules are not tested: the CFD's volume is tick volume, not exchange volume.

Also: a check of the CFD bars against the real SPY/QQQ bars on the overlap window (Sep-Oct 2025).
Run:  python study19_out_of_sample.py
"""
import math
import os
import sys

import numpy as np
import pandas as pd

import lab
import market_iv

EXT = os.path.join(os.path.dirname(__file__), "..", "data", "ext")
SYMS = ["SPY", "QQQ"]
NEW_END = pd.Timestamp("2025-08-29")


def load_ext():
    """Real-data clock profile first, then swap lab's cache so every study sees the CFD-built days."""
    for s in SYMS:
        market_iv.clock_factor(s, 0)
    real = {s: lab.universe([s]) for s in SYMS}
    keep, lab.DATA = lab.DATA, EXT
    try:
        ext = {s: lab.load(s) for s in SYMS}
    finally:
        lab.DATA = keep
    trading = set(pd.read_csv(os.path.join(os.path.dirname(__file__), "..", "data", "SPY_D.csv"),
                              parse_dates=["date"]).date)
    alld = sorted(trading)
    prev_of = {alld[i]: alld[i - 1] for i in range(1, len(alld))}
    for s in SYMS:  # drop days whose previous trading day is missing from the CFD set (wrong prior-day levels)
        have = {d.date for d in ext[s]}
        ext[s] = [d for d in ext[s] if prev_of.get(d.date) in have]
    return real, ext


def check_overlap(real, ext):
    print("CFD bars vs real ETF bars on the overlap days:")
    for s in SYMS:
        r = {d.date: d for d in real[s]}
        rows = []
        for d in ext[s]:
            if d.date not in r:
                continue
            a, b = r[d.date], d
            ra, rb = np.diff(np.log(a.c)), np.diff(np.log(b.c))
            rows.append(dict(corr=np.corrcoef(ra, rb)[0, 1],
                             orh=abs(a.h[:3].max() / b.h[:3].max() - 1) * 1e4, orl=abs(a.l[:3].min() / b.l[:3].min() - 1) * 1e4,
                             day=abs((a.c[-1] / a.o[0]) - (b.c[-1] / b.o[0])) * 1e4,
                             gap=abs((a.o[0] / a.prev_close) - (b.o[0] / b.prev_close)) * 1e4,
                             rng=(b.h.max() - b.l.min()) / (a.h.max() - a.l.min())))
        x = pd.DataFrame(rows)
        if len(x):
            print(f"  {s}: {len(x)} days, 5-min return corr {x.corr.median():.3f} (median), opening-range high/low off by "
                  f"{x.orh.median():.1f}/{x.orl.median():.1f} bps, open-to-close off by {x.day.median():.1f} bps, "
                  f"gap off by {x.gap.median():.1f} bps, CFD/real day range {x.rng.median():.2f}")


def one_hour(d, i, kind, budget=0.50):
    import study11_september as S11
    pick = lab.choose_contract(d, i, kind, budget)
    if not pick:
        return None
    k, mid, _ = pick
    entry = mid + lab.half_spread(mid, d.sym)
    j = min(i + 12, S11.FLAT)
    return (S11.opt_px(d, j, d.c[j], k, kind) - entry) * 100


def run_rules(days):
    import study11_september as S11
    rules = [("gap fade >0.3%, 1 hour", S11.s_gap_fade, "1h"), ("gap and go >0.3%, hold 14:50", S11.s_gap_go, "hold"),
             ("failed ORB fade, hold 14:50", S11.s_orb_fail, "hold"), ("control: ORB 15-min, 1 hour", S11.s_orb, "1h"),
             ("control: RSI(14) extremes, 1 hour", S11.s_rsi_revert, "1h"),
             ("control: power hour, hold", S11.s_power_hour, "hold")]
    out = []
    for name, fn, ex in rules:
        for d in days:
            sig = fn(d, None)
            if not sig:
                continue
            i, kind = sig
            pnl = one_hour(d, i, kind) if ex == "1h" else S11.trade(d, i, kind, "hold")
            if pnl is None:
                continue
            j = min(i + 12, S11.FLAT) if ex == "1h" else S11.FLAT
            und = (d.c[j] / d.c[i] - 1) * (1 if kind == "C" else -1) * 1e4
            out.append(dict(rule=name, sym=d.sym, date=d.date, pnl=pnl, und=und))
    return out


def run_sweep():
    import study14b_sweep_model as B
    out = []
    for label, cfg, budgets in (("SWEEP MODEL", B.CFG, (0.60, 0.30)), ("explore: sweep 'any'", dict(B.CFG, sweep="any"), (0.30,))):
        for budget in budgets:
            B.BUDGET = budget
            e, _ = B.run(SYMS, cfg)
            for r in e.itertuples():
                if r.usd == r.usd:
                    out.append(dict(rule=f"{label} ${budget:.2f}", sym=r.sym, date=r.date, pnl=r.usd, und=r.R))
    return out


def tstat(a):
    a = np.asarray(a, float)
    return a.mean() / (a.std(ddof=1) / math.sqrt(len(a))) if len(a) > 2 and a.std() > 0 else 0.0


def main():
    real, ext = load_ext()
    check_overlap(real, ext)
    new = {s: [d for d in ext[s] if d.date <= NEW_END] for s in SYMS}
    print(f"\nnew period: {min(d.date for s in SYMS for d in new[s]):%Y-%m-%d} .. "
          f"{max(d.date for s in SYMS for d in new[s]):%Y-%m-%d}, days SPY {len(new['SPY'])} QQQ {len(new['QQQ'])}")
    for s in SYMS:
        lab._cache[s] = new[s]
    rows = []
    for m in (1.0, 1.25):
        market_iv.install(m)
        for r in run_sweep() + run_rules(new["SPY"] + new["QQQ"]):
            r["iv"] = m
            rows.append(r)
    market_iv.uninstall()
    df = pd.DataFrame(rows)
    df["year"] = df.date.dt.year
    print(f"\n{'rule':<36}{'IV':>5}{'n':>5}{'win':>6}{'$/contract':>12}{'t':>6}   by year ($/contract, n)      und")
    for (rule, m), g in df.groupby(["rule", "iv"], sort=False):
        yrs = "  ".join(f"{y}: {x.pnl.mean():+6.1f} ({len(x)})" for y, x in g.groupby("year"))
        und = f"{g.und.mean():+.2f}R" if "SWEEP" in rule or "sweep" in rule else f"{g.und.mean():+.1f}bp"
        print(f"{rule:<36}{m:>5.2f}{len(g):>5}{np.mean(g.pnl > 0):>6.0%}{g.pnl.mean():>+12.2f}{tstat(g.pnl):>+6.1f}   {yrs}   {und}")
    df.to_csv(os.path.join(os.path.dirname(__file__), "out", "study19_rows.csv"), index=False)
    return df


if __name__ == "__main__":
    main()

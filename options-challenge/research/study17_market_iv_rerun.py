"""Study 17: re-run the earlier same-day SPY/QQQ strategies with market option prices.

Why: study14c/market_iv.py showed lab.py's model priced same-day options with ~1.5x (SPY) to ~1.7x (QQQ) the
implied vol the market itself showed (Cboe VIX1D, scaled by VXN/VIX for QQQ). Parts 1 and 4-7 of RESEARCH.md all
used that model, so every same-day option-buying result was tilted against the buyer. Here the same signals and
exits are priced with market IV (market_iv.py), at 1.0x and 1.25x of it.

Families (signals unchanged from their studies; SPY + QQQ; train < 2026-05-01 <= test):
  study11  the 11 intraday rules (ORB, fades, VWAP pullback, EMA cross, RSI(14) extremes, gap fade / go,
           value plan, trend day, power hour, POC magnet), each with 3 exits: Guardian / 1 hour / hold to 14:50 CT
  study9   the live bot's auto rules, as-is and entries until 10:30 CT
  study10  prior-day volume profile setups A-D
  study12  Clint's opening-range break: no filter / volume+RSI / all his rules, his exit
  study14b the sweep model
Run:  python study17_market_iv_rerun.py
"""
import math
import sys
from collections import defaultdict

import numpy as np
import pandas as pd

import lab
import market_iv
import study11_september as S11
from study10_volume_profile import profile

SYMS = ["SPY", "QQQ"]


def one_hour(d, i, kind, budget=0.50):
    pick = lab.choose_contract(d, i, kind, budget)
    if not pick:
        return None
    k, mid, _ = pick
    entry = mid + lab.half_spread(mid, d.sym)
    j = min(i + 12, S11.FLAT)
    return (S11.opt_px(d, j, d.c[j], k, kind) - entry) * 100


def tstat(a):
    a = np.asarray(a, float)
    return a.mean() / (a.std(ddof=1) / math.sqrt(len(a))) if len(a) > 2 and a.std() > 0 else 0.0


def cell(x):
    if not len(x):
        return f"{'n=0':>28}"
    x = np.asarray(x, float)
    return f"n={len(x):3d} {np.mean(x > 0):4.0%} ${x.mean():+6.2f} t{tstat(x):+5.1f}"


def rows_study11(days, profs):
    out = []
    for name, fn in S11.STRATS.items():
        for d in days:
            sig = fn(d, profs[(d.sym, d.date)])
            if not sig:
                continue
            i, kind = sig
            g = S11.trade(d, i, kind)
            if g is None:
                continue
            out.append(dict(fam="study11", name=name, exit="guardian", date=d.date, sym=d.sym, pnl=g))
            out.append(dict(fam="study11", name=name, exit="1 hour", date=d.date, sym=d.sym, pnl=one_hour(d, i, kind)))
            out.append(dict(fam="study11", name=name, exit="hold 14:50", date=d.date, sym=d.sym,
                            pnl=S11.trade(d, i, kind, "hold")))
    return out


def rows_study9():
    import study9_bot_auto as B9
    out = []
    pairs = B9.pair_days()
    for label, over in (("bot auto rules as-is", {}), ("bot auto, entries until 10:30 CT", dict(last_entry_bar=23))):
        for t in B9.backtest(pairs, **over):
            out.append(dict(fam="study9", name=label, exit="bot", date=t["date"], sym=t["sym"], pnl=t["pnl"]))
    return out


def rows_study10():
    import study10_volume_profile as B10
    out = []
    pairs = [(d, p) for d, p in B10.all_days() if d.sym in SYMS]
    for s in "ABCD":
        for t in B10.backtest(pairs, setups=s):
            out.append(dict(fam="study10", name=f"volume profile setup {s}", exit="level", date=t["date"],
                            sym=t["sym"], pnl=t["pnl"]))
    return out


def rows_study12():
    import study12_clint_orb as C
    days = lab.universe(SYMS)
    by = defaultdict(dict)
    for d in days:
        by[d.sym][d.date] = d
    out = []
    for sym in SYMS:
        other = "QQQ" if sym == "SPY" else "SPY"
        dates = sorted(by[sym])
        for n, date in enumerate(dates):
            if n < 11 or date not in by[other]:
                continue
            d, prev = by[sym][date], by[sym][dates[n - 1]]
            widths = [(by[sym][x].h[:3].max() - by[sym][x].l[:3].min()) / by[sym][x].o[0] for x in dates[n - 10:n]]
            sig = C.signal(d, prev.c, by[other][date], np.median(widths))
            if not sig:
                continue
            i, kind, f = sig
            h = C.his_exit(d, i, kind)
            if h is None:
                continue
            for label, ok in (("Clint ORB, no filter", True), ("Clint ORB, volume + RSI", f["vol"] and f["rsi"]),
                              ("Clint ORB, all his rules", all(f.values()))):
                if ok:
                    out.append(dict(fam="study12", name=label, exit="his", date=date, sym=sym, pnl=h[0]))
    return out


def rows_sweep():
    import study14b_sweep_model as B
    e, _ = B.run(SYMS)
    return [dict(fam="study14b", name="sweep model ($0.60)", exit="2R / 1 hour", date=r.date, sym=r.sym, pnl=r.usd)
            for r in e.itertuples() if r.usd == r.usd]


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
    mults = [float(x) for x in (sys.argv[1:] or ["1.0", "1.25"])]
    allrows = []
    for m in mults:
        market_iv.install(m)
        rows = rows_study11(days, profs) + rows_study9() + rows_study10() + rows_study12() + rows_sweep()
        for r in rows:
            r["iv"] = m
        allrows += rows
    market_iv.uninstall()
    df = pd.DataFrame(allrows).dropna(subset=["pnl"])
    df["per"] = np.where(df.date < lab.SPLIT, "train", "test")
    print(f"SPY + QQQ, same-day options priced at market IV (VIX1D, VXN/VIX for QQQ). $ per contract.\n")
    for m in mults:
        x = df[df.iv == m]
        print(f"=== market IV x{m} ===")
        print(f"{'family':<9}{'rule':<38}{'exit':<12}{'TRAIN':>29}  {'TEST':>29}  both+")
        for (fam, name, ex), g in x.groupby(["fam", "name", "exit"], sort=False):
            a, b = g[g.per == "train"].pnl, g[g.per == "test"].pnl
            both = "  YES" if len(a) >= 15 and len(b) >= 10 and a.mean() > 0 and b.mean() > 0 else ""
            print(f"{fam:<9}{name[:37]:<38}{ex:<12}{cell(a):>29}  {cell(b):>29}{both}")
        print()
    df.to_csv("out/study17_rows.csv", index=False)
    return df


if __name__ == "__main__":
    main()

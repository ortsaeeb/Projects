"""Step 2: turn the one robust direction signal (stock gap + 15-min ORB in gap direction) into option trades.

Parameters are compared on TRAIN only; TEST is shown alongside to check they hold up.
"""
import itertools
import math
import sys

import numpy as np

import lab
import opt

days = lab.universe(lab.STOCKS)


def signals(min_gap_atr=0.3, or_bars=3, last_entry_bar=17):
    """Yield (day, entry_bar, kind, or_high, or_low)."""
    for d in days:
        gap_atr = (d.o[0] - d.prev_close) / d.atr14
        if abs(gap_atr) < min_gap_atr:
            continue
        orh, orl = d.h[:or_bars].max(), d.l[:or_bars].min()
        for i in range(or_bars, last_entry_bar + 1):
            up, dn = d.c[i] > orh, d.c[i] < orl
            if up or dn:
                if (up and gap_atr > 0) or (dn and gap_atr < 0):
                    yield d, i, ("C" if up else "P"), orh, orl
                break  # only the first break counts


def evaluate(trades):
    def part(ts):
        if not ts:
            return dict(n=0, win=0, avg=0, t=0, pnl=0)
        r = np.array([x.ret for x in ts])
        t = r.mean() / (r.std(ddof=1) / math.sqrt(len(r))) if len(r) > 2 and r.std() > 0 else 0
        return dict(n=len(r), win=np.mean(r > 0), avg=r.mean(), t=t, pnl=sum(x.pnl for x in ts))
    tr = [x for x in trades if x.date < lab.SPLIT]
    te = [x for x in trades if x.date >= lab.SPLIT]
    return part(tr), part(te)


def fmt(p):
    return f"n={p['n']:3d} win {p['win']:4.0%} avg {p['avg']:+6.1%} t {p['t']:+5.2f} ${p['pnl']:+8.0f}"


if __name__ == "__main__":
    grid = dict(
        structure=["single", "vertical", "atm"],
        budget=[100, 250],
        min_gap=[0.3, 0.6],
        hold=[6, 12, 24],              # bars after entry (30m, 60m, 2h)
        stop=["or_mid", "or_far", None],
        target=[None, 0.5, 1.0],
    )
    rows = []
    for structure, budget, min_gap, hold, stop, target in itertools.product(*grid.values()):
        if structure == "atm" and budget != 100:
            continue
        trades = []
        for d, i, kind, orh, orl in signals(min_gap):
            und = None
            if stop == "or_mid":
                und = (orh + orl) / 2
            elif stop == "or_far":
                und = orl if kind == "C" else orh
            t = opt.run(d, i, kind, structure, budget, width_steps=2 if budget >= 250 else 1,
                        exit_bar=min(i + hold, 77), und_stop=und, stop_pct=None, target_pct=target)
            if t:
                trades.append(t)
        tr, te = evaluate(trades)
        rows.append((structure, budget, min_gap, hold, stop, target, tr, te))

    rows.sort(key=lambda r: -r[6]["avg"])
    print(f"{'structure':<9} {'bud':>4} {'gap':>4} {'hold':>4} {'stop':<7} {'tgt':>4} | TRAIN{'':<40} | TEST")
    show = [r for r in rows if len(sys.argv) < 2 or r[0] == sys.argv[1]]
    for s, b, g, h, st, tg, tr, te in show[:25]:
        print(f"{s:<9} {b:>4} {g:>4} {h:>4} {str(st):<7} {str(tg):>4} | {fmt(tr)} | {fmt(te)}")
    print("...")
    print("Median TEST avg across all configs:", f"{np.median([r[7]['avg'] for r in rows]):+.1%}")
    print("Share of configs with TEST avg > 0:", f"{np.mean([r[7]['avg'] > 0 for r in rows]):.0%}")

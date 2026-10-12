"""Study 25: do older pivot points matter, or only today's?

Floor-trader pivots (P = (H+L+C)/3, R1 = 2P-L, S1 = 2P-H, R2 = P+(H-L), S2 = P-(H-L)) built from:
  today's       yesterday's high/low/close (what charts show by default)
  2 days ago    the day before yesterday's (yesterday's pivots, carried into today)
  3 days ago
  weekly        last week's high/low/close
  fake          today's levels moved up or down by 0.15% (lines nobody watches; the "is it real?" control)
A touch: the previous 3 five-minute closes on one side of the level, then a candle wicks to it (9:45-15:00 ET).
Hold = the candle closes back on its side. Bounce = move away from the level over the next 30 min, in bp
(1 bp = 0.01%), positive = in the bounce direction. If a set of levels matters, its touches should hold and bounce
more than the fake lines. SPY+QQQ 5-min, Sep 2025 - Sep 2026.

Run:  python study25_pivot_ages.py
"""
import numpy as np
import pandas as pd

import study23_ema200 as S


def pivots(h, l, c):
    p = (h + l + c) / 3
    return {"P": p, "R1": 2 * p - l, "S1": 2 * p - h, "R2": p + (h - l), "S2": p - (h - l)}


def touches(day, levels):
    """Touches of each level in one day's 5-min bars."""
    o, h, l, c, m = (day[k].values for k in ("o", "h", "l", "c", "mod"))
    out = []
    for name, lv in levels.items():
        for t in range(3, len(c) - 6):
            if not 15 <= m[t] <= 325:
                continue
            if all(c[t - k] > lv for k in (1, 2, 3)) and l[t] <= lv:
                side = 1
            elif all(c[t - k] < lv for k in (1, 2, 3)) and h[t] >= lv:
                side = -1
            else:
                continue
            hold = c[t] > lv if side > 0 else c[t] < lv
            out.append(dict(level=name, hold=hold, bounce=(c[t + 6] / lv - 1) * side * 1e4))
    return out


def main():
    rows = []
    for sym in S.SYMS:
        base = S.base_m5(sym)
        days = [g for _, g in base.groupby("date")]
        dly = pd.DataFrame([(g.date.iloc[0], g.h.max(), g.l.min(), g.c.iloc[-1]) for g in days],
                           columns=["date", "h", "l", "c"])
        wk = dly.assign(w=dly.date.dt.to_period("W")).groupby("w").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
        for i in range(3, len(days)):
            sets = {}
            for age, j in (("today's", i - 1), ("2 days ago", i - 2), ("3 days ago", i - 3)):
                for k, v in pivots(dly.h[j], dly.l[j], dly.c[j]).items():
                    sets[f"{age}|{k}"] = v
            pw = dly.date[i].to_period("W") - 1
            if pw in wk.index:
                for k, v in pivots(wk.h[pw], wk.l[pw], wk.c[pw]).items():
                    sets[f"weekly|{k}"] = v
            for k, v in pivots(dly.h[i - 1], dly.l[i - 1], dly.c[i - 1]).items():
                sets[f"fake +0.15%|{k}"] = v * 1.0015
                sets[f"fake -0.15%|{k}"] = v * 0.9985
            for r in touches(days[i], sets):
                r["set"], r["level"] = r["level"].split("|")
                r["date"] = dly.date[i]
                rows.append(r)
    x = pd.DataFrame(rows)
    x["half"] = np.where(x.date < pd.Timestamp("2026-04-01"), "first half", "second half")
    print(f"{'levels':<14}{'touches':>8}{'hold':>7}{'bounce 30m':>12}{'t':>6}   hold by half")
    for name in ("today's", "2 days ago", "3 days ago", "weekly", "fake +0.15%", "fake -0.15%"):
        g = x[x.set == name]
        t = g.bounce.mean() / (g.bounce.std() / np.sqrt(len(g)))
        hh = " / ".join(f"{g[g.half == h].hold.mean():.0%}" for h in ("first half", "second half"))
        print(f"{name:<14}{len(g):>8}{g.hold.mean():>7.0%}{g.bounce.mean():>+10.1f}bp{t:>+6.1f}   {hh}")
    print("\ntoday's pivots by level:")
    for lv in ("R2", "R1", "P", "S1", "S2"):
        g = x[(x.set == "today's") & (x.level == lv)]
        print(f"  {lv:<4} touches {len(g):4d}  hold {g.hold.mean():.0%}  bounce {g.bounce.mean():+.1f}bp")


if __name__ == "__main__":
    main()

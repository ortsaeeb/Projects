"""Study 22: does the size of an FVG's middle candle matter?

Every wick-to-wick FVG on SPY/QQQ 5-min bars (Sep 2025 - Sep 2026, regular hours, gaps formed 9:45-15:00 ET),
grouped by the middle candle's body vs the 20-bar average candle range (what the Webull indicator's "Big candle"
setting filters on). Two outcomes, in the gap's direction, in basis points (1 bp = 0.01%):
  follow   the move from the 3rd candle's close over the next hour (does the gap lead to continuation?)
  retest   if price comes back to the gap's near edge within 12 bars, the move from that edge over the next hour
           (does the gap act as support/resistance when retested? this is how traders use FVGs)
Train < 2026-05-01 <= test.
"""
import numpy as np
import pandas as pd

import lab

BINS = [(0, 0.75, "small (< 0.75x)"), (0.75, 1.25, "normal (0.75-1.25x)"), (1.25, 2.0, "big (1.25-2x)"),
        (2.0, 99, "huge (> 2x)")]


def events(days):
    out = []
    for d in days:
        rng = d.h - d.l
        for k in range(22, 66):
            avg = rng[k - 21:k - 1].mean()
            body = abs(d.c[k - 1] - d.o[k - 1]) / avg if avg > 0 else 0
            for side in (1, -1):
                if side > 0 and d.l[k] > d.h[k - 2]:
                    near, far = d.l[k], d.h[k - 2]
                elif side < 0 and d.h[k] < d.l[k - 2]:
                    near, far = d.h[k], d.l[k - 2]
                else:
                    continue
                j = min(k + 12, 77)
                follow = (d.c[j] / d.c[k] - 1) * side * 1e4
                retest = np.nan
                for t in range(k + 1, min(k + 13, 77)):
                    if (side > 0 and d.l[t] <= near) or (side < 0 and d.h[t] >= near):
                        e = min(t + 12, 77)
                        retest = (d.c[e] / near - 1) * side * 1e4
                        break
                out.append(dict(sym=d.sym, date=d.date, side=side, body=body, follow=follow, retest=retest,
                                size=abs(near - far) / d.c[k] * 1e4))
    return pd.DataFrame(out)


def main():
    x = events(lab.universe(["SPY", "QQQ"]))
    x["per"] = np.where(x.date < lab.SPLIT, "train", "test")
    print(f"{len(x)} FVGs; middle candle vs average: median {x.body.median():.2f}x\n")
    print(f"{'middle candle':<22}{'n':>6}{'follow train':>14}{'follow test':>13}{'retest n':>10}{'retest train':>14}{'retest test':>13}")
    for lo, hi, name in BINS:
        g = x[(x.body >= lo) & (x.body < hi)]
        f = [g[g.per == p].follow.mean() for p in ("train", "test")]
        r = g.dropna(subset=["retest"])
        rr = [r[r.per == p].retest.mean() for p in ("train", "test")]
        print(f"{name:<22}{len(g):>6}{f[0]:>+13.1f}b{f[1]:>+12.1f}b{len(r):>10}{rr[0]:>+13.1f}b{rr[1]:>+12.1f}b")
    a = x.dropna(subset=["retest"])
    print(f"\nall gaps: follow {x.follow.mean():+.1f}b (t {x.follow.mean()/(x.follow.std()/np.sqrt(len(x))):+.1f}), "
          f"retest {a.retest.mean():+.1f}b (t {a.retest.mean()/(a.retest.std()/np.sqrt(len(a))):+.1f}); "
          f"share retested within an hour {len(a)/len(x):.0%}")


if __name__ == "__main__":
    main()

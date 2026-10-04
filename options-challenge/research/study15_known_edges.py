"""Study 15: edges with published evidence, checked on our data.

  A. Intraday momentum into the close (Gao, Han, Li & Zhou 2018 "Market intraday momentum";
     Baltussen, Da, Lammers & Martens 2021 "Hedging demand and market intraday momentum").
     The return from yesterday's close to 15:30 ET predicts the 15:30-16:00 return, most strongly on big-move days
     (dealer and leveraged-ETF hedging all lands in the last half hour).
     5-min bars, SPY/QQQ/IWM, Sep 2025 - Sep 2026.
  B. Turn of the month: equities earn most of their return from the last trading day of a month to the 3rd day
     of the next (Lakonishok & Smidt 1988; Etula et al. 2020 "Patterns in short-term returns").
  C. Overnight vs daytime: index returns accrue mostly overnight (Cliff, Cooper & Gulen 2008; Lou, Polk & Skouras 2019).
  D. Short-term reversal in an uptrend (study5's RSI(2)); summarised for comparison.
  B-D use daily bars, Dec 2021 - Sep 2026.

Run:  python study15_known_edges.py
"""
import math
import os

import numpy as np
import pandas as pd

import lab

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
I1530 = 71   # bar closing 15:30 ET
I1000 = 5    # bar closing 10:00 ET


def t(a):
    a = np.asarray(a, float)
    return a.mean() / (a.std(ddof=1) / math.sqrt(len(a))) if len(a) > 2 else np.nan


def line(name, r, unit=1e4, suffix="bps"):
    r = np.asarray(r, float)
    return f"  {name:<46} n={len(r):4d}  avg {r.mean()*unit:+6.1f} {suffix}  win {np.mean(r > 0):4.0%}  t {t(r):+5.2f}"


def opt_last_half_hour(d, kind, budget=0.40):
    """Buy a same-day option at 15:30 ET, sell at 15:55 (last bar before the close auction)."""
    pick = lab.choose_contract(d, I1530, kind, budget)
    if not pick:
        return np.nan
    k, mid, _ = pick
    paid = mid + lab.half_spread(mid, d.sym)
    j = 76
    v = lab.bs(d.c[j], k, lab.t_years(d, j), lab.iv_at(d, j), kind)[0]
    v = max(0.0, v - lab.half_spread(v, d.sym))
    return (v - paid) * 100


def part_a():
    print("A. Intraday momentum: trade 15:30 -> 16:00 ET (14:30 -> 15:00 CT) in the direction of the day so far")
    rows = []
    for d in lab.universe(lab.ETFS):
        day = d.c[I1530] / d.prev_close - 1
        first = d.c[I1000] / d.prev_close - 1
        last = d.c[77] / d.c[I1530] - 1
        sd = d.rv20 / math.sqrt(252)  # typical daily move
        rows.append(dict(sym=d.sym, date=d.date, day=day, first=first, last=last, z=abs(day) / sd, d=d))
    df = pd.DataFrame(rows)
    df["follow"] = np.sign(df.day) * df["last"]
    df["follow_first"] = np.sign(df["first"]) * df["last"]
    print(line("all days, follow prev close->15:30", df.follow))
    print(line("all days, follow prev close->10:00 (Gao)", df.follow_first))
    for lo, hi in ((0, 0.5), (0.5, 1), (1, 1.5), (1.5, 99)):
        x = df[(df.z >= lo) & (df.z < hi)]
        print(line(f"day move {lo}-{hi} x normal daily move", x.follow))
    for s in lab.ETFS:
        print(line(f"{s}, day move >= 1x normal", df[(df.sym == s) & (df.z >= 1)].follow))
    for per, m in (("before May 2026", df.date < lab.SPLIT), ("May 2026 on", df.date >= lab.SPLIT)):
        print(line(f"day move >= 1x normal, {per}", df[m & (df.z >= 1)].follow))
    big = df[df.z >= 1].copy()
    big["usd"] = [opt_last_half_hour(r.d, "C" if r.day > 0 else "P") for r in big.itertuples()]
    y = big.dropna(subset=["usd"])
    print(f"  same-day $0.40 option, 14:30 -> 14:55 CT, day move >= 1x: n={len(y)}  avg ${y.usd.mean():+.2f}  "
          f"win {np.mean(y.usd > 0):.0%}  (model prices; 0DTE spreads at 14:30 CT are wide in real life)")
    return df


def daily(sym):
    df = pd.read_csv(os.path.join(DATA, f"{sym}_D.csv"), parse_dates=["date"]).set_index("date")
    df["ret"] = df.close.pct_change()
    df["on"] = df.open / df.close.shift() - 1
    df["day"] = df.close / df.open - 1
    m = df.index.to_period("M")
    df["dom"] = df.groupby(m).cumcount() + 1                     # trading day of month, 1 = first
    df["dom_rev"] = df.groupby(m).cumcount(ascending=False) + 1  # 1 = last trading day
    return df.dropna()


def part_bc():
    print("\nB. Turn of the month (daily close-to-close, Dec 2021 - Sep 2026)")
    for s in ("SPY", "QQQ", "IWM"):
        df = daily(s)
        tom = (df.dom_rev == 1) | (df.dom <= 3)
        print(line(f"{s} turn-of-month days (last + first 3)", df.ret[tom]))
        print(line(f"{s} all other days", df.ret[~tom]))
        # the trade: buy at the close 2 days before month-end, sell at the close of day 3
        df2 = df.copy()
        ent = df2.index[df2.dom_rev == 2]
        tr = []
        for e in ent:
            i = df2.index.get_loc(e)
            if i + 4 < len(df2):
                tr.append(df2.close.iloc[i + 4] / df2.close.iloc[i] - 1)
        print(line(f"{s} hold 4 days (close of 2nd-last day -> day 3)", tr))
    print("\nC. Overnight (close -> open) vs daytime (open -> close)")
    for s in ("SPY", "QQQ", "IWM"):
        df = daily(s)
        print(line(f"{s} overnight", df.on))
        print(line(f"{s} daytime", df.day))
        print(f"  {s} growth of $1: overnight only {np.prod(1 + df.on):.2f}, daytime only {np.prod(1 + df.day):.2f}, "
              f"buy and hold {np.prod(1 + df.ret):.2f}")


def main():
    part_a()
    part_bc()


if __name__ == "__main__":
    main()

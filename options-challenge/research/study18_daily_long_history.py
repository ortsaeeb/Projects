"""Study 18: SPY/QQQ swing signals on 50 years of S&P 500 closes, and the RSI(2) dip as LONG CALLS priced with
real implied vol (a Level-2 trade: no spreads needed).

A. data/SPX_cboe.csv: S&P 500 daily closes 1975-2026 (Cboe). Close-only signals, next-close entry is not needed
   because every rule enters at the signal day's close and exits at a later close.
     rsi2     RSI(2) < 10 and close > 200-day SMA; exit first close > 5-day SMA, max 5 days   (Connors)
     rsi2_5   same with RSI(2) < 5
     down3    3 lower closes in a row above the 200-day SMA; same exit
     vixspike VIX close > 1.3x its 20-day average and S&P > 200-day SMA; hold 5 days            (1990-)
   Reported by decade, vs the average 1-5 day return of all days (the drift you get anyway).
B. SPY/QQQ 2022-2026: on the RSI(2) signal, buy the nearest call whose ask fits a budget, ~10 calendar days out,
   sell at the signal's exit. IV = VIX9D x 0.85-1.05 (x VXN/VIX for QQQ), calls 0.5 vol point cheaper per 1% OTM
   (equity skew), 1% half-spread (min $0.01) each way.
Run:  python study18_daily_long_history.py
"""
import math
import os

import numpy as np
import pandas as pd

import study5_daily as s5
from study6_rsi2_options import bs

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def cboe(name, col="CLOSE"):
    df = pd.read_csv(os.path.join(DATA, f"{name}_cboe.csv"), parse_dates=["DATE"]).set_index("DATE")
    return df[col]


def rsi2(c):
    d = c.diff()
    up, dn = d.clip(lower=0), -d.clip(upper=0)
    return 100 - 100 / (1 + up.ewm(alpha=0.5, adjust=False).mean() / dn.ewm(alpha=0.5, adjust=False).mean())


def tstat(a):
    a = np.asarray(a, float)
    return a.mean() / (a.std(ddof=1) / math.sqrt(len(a))) if len(a) > 2 else float("nan")


def signals_spx():
    c = cboe("SPX", "SPX")
    df = pd.DataFrame(dict(c=c))
    df["r2"] = rsi2(c)
    df["sma200"] = c.rolling(200).mean()
    df["sma5"] = c.rolling(5).mean()
    vix = cboe("VIX")
    df["vix"] = vix
    df["vixavg"] = vix.rolling(20).mean()
    df = df.dropna(subset=["sma200"])
    cv, s5v = df.c.values, df.sma5.values
    out = []
    for name in ("rsi2", "rsi2_5", "down3", "vixspike"):
        i = 3
        while i < len(df) - 6:
            r = df.iloc[i]
            up = r.c > r.sma200
            hit = (name == "rsi2" and up and r.r2 < 10) or (name == "rsi2_5" and up and r.r2 < 5) or \
                  (name == "down3" and up and cv[i] < cv[i - 1] < cv[i - 2] < cv[i - 3]) or \
                  (name == "vixspike" and up and r.vix == r.vix and r.vix > 1.3 * r.vixavg)
            if not hit:
                i += 1
                continue
            j = i + 1
            if name != "vixspike":
                while j < i + 5 and cv[j] <= s5v[j]:
                    j += 1
            else:
                j = i + 5
            out.append(dict(sig=name, date=df.index[i], ret=cv[j] / cv[i] - 1, held=j - i))
            i = j
    base = pd.Series(cv[3:] / cv[:-3] - 1, index=df.index[:-3])  # any 3-day hold, for comparison
    return pd.DataFrame(out), base


def part_a():
    t, base = signals_spx()
    t["decade"] = (t.date.dt.year // 10 * 10).astype(str) + "s"
    print("A. S&P 500, 1975-2026, return per trade (index points, no costs)")
    print(f"   any 3-day hold, all days: avg {base.mean():+.2%}, up {np.mean(base > 0):.0%}")
    for name, g in t.groupby("sig", sort=False):
        print(f"   {name:<9} n={len(g):4d} win {np.mean(g.ret > 0):4.0%} avg {g.ret.mean():+.2%} t {tstat(g.ret):+5.2f}  "
              f"held {g.held.mean():.1f}d | by decade: " +
              "  ".join(f"{dec} {x.ret.mean():+.2%}({len(x)})" for dec, x in g.groupby("decade")))


def call_trades(sym, budget, atm_mult, dte_cal=10):
    df = s5.load(sym).join(cboe("VIX9D").rename("v9"), how="inner")
    if sym == "QQQ":
        df = df.join((cboe("VXN") / cboe("VIX")).rename("ratio"), how="left")
        df["v9"] *= df.ratio.fillna(1.3)
    c, v9 = df.close.values, df.v9.values / 100
    out = []
    for d0, direction, held, ret, i, j in s5.trades(df, "rsi2"):
        s0 = c[i]
        atm = v9[i] * atm_mult
        t0 = dte_cal / 365
        iv = lambda s, k, a: max(0.05, a - 0.5 / 100 * max(0.0, math.log(k / s) * 100))
        k = math.ceil(s0)
        while True:
            mid = bs(s0, k, t0, iv(s0, k, atm), "C")
            ask = mid + max(0.01, 0.01 * mid)
            if ask <= budget or mid < 0.05:
                break
            k += 1
        if mid < 0.05:
            continue
        cal = (df.index[j] - df.index[i]).days
        t1 = max(dte_cal - cal, 0) / 365
        a1 = v9[j] * atm_mult
        val = bs(c[j], k, t1, iv(c[j], k, a1), "C") if t1 > 0 else max(0.0, c[j] - k)
        val = max(0.0, val - max(0.01, 0.01 * val))
        out.append(dict(sym=sym, date=d0, pnl=(val - ask) * 100, cost=ask * 100, otm=k / s0 - 1, und=ret))
    return pd.DataFrame(out)


def part_b():
    print("\nB. RSI(2) dip as a long call (Level 2), SPY+QQQ, priced with VIX9D; train < 2025 <= test")
    for budget in (1.00, 1.50, 3.00):
        for m in (0.85, 1.05):
            x = pd.concat([call_trades(s, budget, m) for s in ("SPY", "QQQ")])
            a, b = x[x.date < s5.SPLIT], x[x.date >= s5.SPLIT]
            f = lambda y: (f"n={len(y):2d} win {np.mean(y.pnl > 0):4.0%} ${y.pnl.mean():+6.1f}/trade "
                           f"({(y.pnl / y.cost).mean():+5.0%}) t {tstat(y.pnl):+4.1f}")
            print(f"   ask <= ${budget:.2f} ({x.otm.mean():.1%} OTM avg), IV = VIX9D x{m:.2f}:  TRAIN {f(a)} | TEST {f(b)}")


if __name__ == "__main__":
    part_a()
    part_b()

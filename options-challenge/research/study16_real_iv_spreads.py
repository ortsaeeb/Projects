"""Study 16: re-test option SELLING with real implied volatility instead of the model's assumption.

Banks and market makers mostly earn by selling options: implied volatility is usually above the volatility that
follows (the variance risk premium). Studies 2/6 assumed it (IV = realised x 1.1-1.5). Here the IV comes from the
market: Cboe's VIX9D (9-day implied vol on the S&P 500, data/VIX9D_cboe.csv, downloaded from cdn.cboe.com).

  Underlying  SPY (VIX9D is the S&P's own 9-day IV); QQQ/IWM with VIX9D scaled by their 20-day vol vs SPY's
  ATM IV      VIX9D x ATM (0.85 / 0.95 / 1.05). VIX-style indexes include the put skew, so ATM IV sits below them.
  Skew        each further-out put pays +1.5 vol points per 1% below spot (steep, short-dated skew; conservative)
  Costs       half-spread 1% of each leg's price, min $0.01, on entry and exit
  Structure   bull put credit spread: short the first strike below spot, long w dollars lower, 5 trading days out

  rsi2        study5's signal (RSI(2) < 10 above the 200-day SMA), exit at close > 5-day SMA or expiry
  weekly      no signal: sell one every Monday close, hold to expiry (pure premium selling)

Run:  python study16_real_iv_spreads.py
"""
import math
import os

import numpy as np
import pandas as pd

import study5_daily as s5
from study6_rsi2_options import bs

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
DTE = 5
SKEW = 1.5  # vol points per 1% OTM


def vix9d():
    v = pd.read_csv(os.path.join(DATA, "VIX9D_cboe.csv"), parse_dates=["DATE"]).set_index("DATE")
    return v.CLOSE / 100


def leg_iv(atm, s, k):
    return atm + SKEW / 100 * max(0.0, math.log(s / k) * 100)


def spread_value(s, k, w, t, atm, side):
    """Value of short k / long k-w put spread; side=+1 to buy it back (pay ask), -1 to sell it (receive bid)."""
    p1 = bs(s, k, t, leg_iv(atm, s, k), "P")
    p2 = bs(s, k - w, t, leg_iv(atm, s, k - w), "P")
    cost = max(0.01, 0.01 * p1) + max(0.01, 0.01 * p2)
    return p1 - p2 + side * cost


def load(sym, v9, atm_mult):
    df = s5.load(sym).join(v9.rename("v9"), how="inner")
    spy = s5.load("SPY")
    ratio = (df.rv20 / spy.rv20.reindex(df.index)).clip(0.6, 2.5) if sym != "SPY" else 1.0
    df["atm"] = df.v9 * atm_mult * ratio
    return df


def trade(df, i, j, w):
    c, atm = df.close.values, df.atm.values
    s0 = c[i]
    k = math.floor(s0)
    held = j - i
    credit = spread_value(s0, k, w, DTE * 7 / 5 / 365, atm[i], -1)
    left = (DTE - held) * 7 / 5 / 365
    if held >= DTE:  # expiry: intrinsic
        close = max(0, k - c[j]) - max(0, k - w - c[j])
    else:
        close = spread_value(c[j], k, w, left, atm[j], +1)
    pnl = credit - close
    return dict(date=df.index[i], held=held, credit=credit * 100, pnl=pnl * 100, risk=(w - credit) * 100,
                ret=pnl / (w - credit))


def run(sym, mode, w, atm_mult, v9):
    df = load(sym, v9, atm_mult)
    out = []
    if mode == "rsi2":
        for d0, direction, held, ret, i, j in s5.trades(df, "rsi2"):
            out.append(trade(df, i, min(j, i + DTE), w))
    else:
        for i in range(len(df) - DTE):
            if df.index[i].dayofweek == 0:
                out.append(trade(df, i, i + DTE, w))
    x = pd.DataFrame(out)
    x["sym"] = sym
    return x


def fmt(x):
    if len(x) < 3:
        return "n/a"
    t = x.ret.mean() / x.ret.std(ddof=1) * math.sqrt(len(x))
    return (f"n={len(x):3d} win {np.mean(x.pnl > 0):4.0%} avg ${x.pnl.mean():+6.1f} ({x.ret.mean():+6.1%} of risk) "
            f"t {t:+5.2f} worst ${x.pnl.min():+5.0f}")


def main():
    v9 = vix9d()
    print(f"VIX9D {v9.index.min():%Y-%m-%d} .. {v9.index.max():%Y-%m-%d}; train < {s5.SPLIT:%Y-%m-%d} <= test\n")
    for mode in ("rsi2", "weekly"):
        for w in (2, 5):
            for m in (0.85, 0.95, 1.05):
                parts = []
                for syms, lab_ in ((["SPY"], "SPY"), (["SPY", "QQQ", "IWM"], "ETFs")):
                    x = pd.concat([run(s, mode, w, m, v9) for s in syms])
                    parts.append((lab_, x))
                for lab_, x in parts:
                    tr, te = x[x.date < s5.SPLIT], x[x.date >= s5.SPLIT]
                    print(f"{mode:<6} ${w} wide  ATM=VIX9Dx{m:.2f}  {lab_:<4} TRAIN {fmt(tr)} | TEST {fmt(te)}")
        print()


if __name__ == "__main__":
    main()

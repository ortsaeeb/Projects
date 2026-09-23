"""Step 5: multi-day (1-5 day) signals on daily bars, 2022-2026.

Well-documented short-term effects, each with few parameters (little room to overfit):
  rsi2      RSI(2) < 10 while above 200-day SMA -> long; exit close > 5-day SMA or 5 days
  down3     3 lower closes in a row while above 200-day SMA -> long; exit first up close or 5 days
  ibs       close in bottom 20% of the day's range (IBS < 0.2) above 200-day SMA -> long next close
  rsi2s     mirror short: RSI(2) > 90 while below 200-day SMA -> short
  brk20     close at a 20-day high -> long 5 days (trend following)
TRAIN = 2022-2024, TEST = 2025-2026.
"""
import math
import os
import sys

import numpy as np
import pandas as pd

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
SYMS = ["SPY", "QQQ", "IWM", "TSLA", "NVDA", "AMD", "PLTR", "META", "AAPL", "AMZN"]
SPLIT = pd.Timestamp("2025-01-01")


def load(sym):
    df = pd.read_csv(os.path.join(DATA, f"{sym}_D.csv"), parse_dates=["date"]).set_index("date")
    c = df.close
    d = c.diff()
    up, dn = d.clip(lower=0), -d.clip(upper=0)
    df["rsi2"] = 100 - 100 / (1 + up.ewm(alpha=1 / 2, adjust=False).mean() / dn.ewm(alpha=1 / 2, adjust=False).mean())
    df["sma200"] = c.rolling(200).mean()
    df["sma5"] = c.rolling(5).mean()
    df["ibs"] = (c - df.low) / (df.high - df.low)
    df["hi20"] = c.rolling(20).max()
    df["rv20"] = np.log(c).diff().rolling(20).std() * math.sqrt(252)
    return df.dropna()


def trades(df, sig):
    """Returns list of (entry_date, direction, days_held, return)."""
    out, i, c = [], 0, df.close.values
    idx = df.index
    while i < len(df) - 1:
        r = df.iloc[i]
        direction = 0
        if sig == "rsi2" and r.rsi2 < 10 and r.close > r.sma200:
            direction = 1
        elif sig == "down3" and i >= 3 and c[i] < c[i - 1] < c[i - 2] < c[i - 3] and r.close > r.sma200:
            direction = 1
        elif sig == "ibs" and r.ibs < 0.2 and r.close > r.sma200:
            direction = 1
        elif sig == "rsi2s" and r.rsi2 > 90 and r.close < r.sma200:
            direction = -1
        elif sig == "brk20" and r.close >= r.hi20:
            direction = 1
        if not direction:
            i += 1
            continue
        j = i + 1
        while j < len(df) - 1 and j - i < 5:
            if sig in ("rsi2", "rsi2s") and (c[j] - df.sma5.values[j]) * direction > 0:
                break
            if sig == "down3" and c[j] > c[j - 1]:
                break
            if sig == "ibs":
                break
            j += 1
        out.append((idx[i], direction, j - i, direction * (c[j] / c[i] - 1), i, j))
        i = j
    return out


if __name__ == "__main__":
    print(f"{'sig':<6} {'sym':<5} {'TRAIN n':>7} {'win':>4} {'avg':>7} {'t':>5} | {'TEST n':>6} {'win':>4} {'avg':>7} {'t':>5}")
    for sig in ["rsi2", "down3", "ibs", "rsi2s", "brk20"]:
        agg_tr, agg_te = [], []
        for s in SYMS:
            ts = trades(load(s), sig)
            tr = np.array([t[3] for t in ts if t[0] < SPLIT])
            te = np.array([t[3] for t in ts if t[0] >= SPLIT])
            agg_tr += list(tr)
            agg_te += list(te)

            def f(a):
                if len(a) < 3:
                    return f"{len(a):7d}"
                return f"{len(a):7d} {np.mean(a > 0):4.0%} {a.mean():+7.2%} {a.mean() / a.std(ddof=1) * math.sqrt(len(a)):+5.2f}"
            print(f"{sig:<6} {s:<5} {f(tr)} | {f(te)}")
        a, b = np.array(agg_tr), np.array(agg_te)
        print(f"{sig:<6} {'ALL':<5} {len(a):7d} {np.mean(a > 0):4.0%} {a.mean():+7.2%} {a.mean() / a.std(ddof=1) * math.sqrt(len(a)):+5.2f} | "
              f"{len(b):6d} {np.mean(b > 0):4.0%} {b.mean():+7.2%} {b.mean() / b.std(ddof=1) * math.sqrt(len(b)):+5.2f}")
        print()

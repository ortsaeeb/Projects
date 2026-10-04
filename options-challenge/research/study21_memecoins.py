"""Study 21: can a simple, repeatable rule make money in memecoins after Webull's costs?

Data: Binance daily candles (tools/fetch_crypto.py), 18 memecoins listed there (DOGE, SHIB, PEOPLE, PEPE, FLOKI, MEME,
1000SATS, BONK, BOME, WIF, DOGS, NEIRO, TURBO, PNUT, ACT, PENGU, TRUMP) + BTC as the market filter.
Survivorship: only coins that grew big enough to be listed; real memecoin buyers also hold the ones that died first.
Costs: Webull's crypto spread, 1% each way (every entry and exit costs 1% of the amount traded).
Long only (Webull spot: no shorting). Signal at a day's close, position from the next day.
TRAIN = up to 2024-12-31, TEST = 2025-01-01 on. A coin joins the universe 30 days after its listing.

Rules (each coin is its own sleeve, equal weight across the coins available that day; a sleeve in cash earns 0):
  hold         buy and hold every coin (rebalanced to equal weight monthly)
  sma N        hold the coin while its close > its N-day average            N = 20, 50, 100
  mom N        hold while its N-day return > 0                              N = 7, 14, 30
  btc N        hold every coin only while BTC > its N-day average          N = 50, 100
  sma50+btc    both conditions
  donchian     buy a close above the 20-day high, sell a close below the 10-day low
  top3 mom14   each Monday hold the 3 coins with the best positive 14-day return (cash if none)
  dip -20%     buy after a day down 20%+, sell 5 days later
Run:  python study21_memecoins.py
"""
import glob
import math
import os

import numpy as np
import pandas as pd

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "crypto")
MEMES = ["DOGE", "SHIB", "PEOPLE", "PEPE", "FLOKI", "MEME", "1000SATS", "BONK", "BOME", "WIF", "DOGS", "NEIRO", "TURBO",
         "PNUT", "ACT", "PENGU", "TRUMP"]
SPLIT = pd.Timestamp("2025-01-01")
COST = float(os.environ.get("COST", "0.01"))
WARMUP = 30


def load():
    px = {}
    for c in MEMES + ["BTC"]:
        d = pd.read_csv(os.path.join(DATA, f"{c}_1d.csv"), parse_dates=["date"]).set_index("date").close
        px[c] = d
    p = pd.DataFrame(px)
    return p[p.index >= "2021-01-01"]


def sleeves(p, rule):
    """Position (0/1) per coin per day, decided at that day's close."""
    m = p[MEMES]
    avail = m.notna() & (m.notna().cumsum() > WARMUP)
    btc = p["BTC"]
    if rule == "hold":
        pos = avail.astype(float)
    elif rule.startswith("sma") and "+" not in rule:
        n = int(rule.split()[1])
        pos = (m > m.rolling(n, min_periods=n).mean()).astype(float)
    elif rule.startswith("mom"):
        n = int(rule.split()[1])
        pos = (m / m.shift(n) - 1 > 0).astype(float)
    elif rule.startswith("btc"):
        n = int(rule.split()[1])
        pos = pd.DataFrame(np.repeat((btc > btc.rolling(n).mean()).values[:, None], len(MEMES), 1), index=m.index,
                           columns=MEMES).astype(float)
    elif rule == "sma50+btc":
        pos = ((m > m.rolling(50, min_periods=50).mean()) &
               pd.DataFrame(np.repeat((btc > btc.rolling(50).mean()).values[:, None], len(MEMES), 1), index=m.index,
                            columns=MEMES)).astype(float)
    elif rule == "donchian":
        hi, lo = m.rolling(20).max().shift(1).values, m.rolling(10).min().shift(1).values
        x, out = m.values, np.zeros(m.shape)
        for j in range(m.shape[1]):
            state = 0.0
            for t in range(m.shape[0]):
                if x[t, j] != x[t, j]:
                    continue
                if state == 0 and hi[t, j] == hi[t, j] and x[t, j] > hi[t, j]:
                    state = 1.0
                elif state == 1 and lo[t, j] == lo[t, j] and x[t, j] < lo[t, j]:
                    state = 0.0
                out[t, j] = state
        pos = pd.DataFrame(out, index=m.index, columns=MEMES)
    elif rule == "dip -20%":
        r, out = m.pct_change().values, np.zeros(m.shape)
        for j in range(m.shape[1]):
            left = 0
            for t in range(m.shape[0]):
                if left > 0:
                    out[t, j] = 1.0
                    left -= 1
                if r[t, j] < -0.20:
                    left, out[t, j] = 5, 1.0
        pos = pd.DataFrame(out, index=m.index, columns=MEMES)
    elif rule == "top3 mom14":
        mom = m / m.shift(14) - 1
        pos = pd.DataFrame(0.0, index=m.index, columns=MEMES)
        cur = []
        for t, day in enumerate(m.index):
            if day.dayofweek == 0:
                s = mom.loc[day][avail.loc[day]].dropna()
                s = s[s > 0].sort_values(ascending=False)
                cur = list(s.index[:3])
            for c in cur:
                pos.at[day, c] = 1.0
        return pos.where(avail, 0.0), "top"
    else:
        raise ValueError(rule)
    return pos.where(avail, 0.0), "sleeve"


def backtest(p, rule):
    pos, kind = sleeves(p, rule)
    r = p[MEMES].pct_change().fillna(0.0)
    held = pos.shift(1).fillna(0.0)          # decided at yesterday's close
    trade = (pos - pos.shift(1).fillna(0.0)).abs()
    avail = (p[MEMES].notna() & (p[MEMES].notna().cumsum() > WARMUP))
    if kind == "top":
        w = held.div(held.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
        tw = (w - w.shift(1).fillna(0.0)).abs().sum(axis=1)
        daily = (w * r).sum(axis=1) - COST * tw.shift(-1).fillna(0.0).shift(1).fillna(0.0)
        return daily, held.sum(axis=1).gt(0).mean(), tw.sum() / 2
    n = avail.sum(axis=1).replace(0, np.nan)
    sleeve = held * r - COST * trade.shift(1).fillna(0.0)   # pay the spread on the day the position changes
    daily = (sleeve.where(avail.shift(1, fill_value=False), 0.0).sum(axis=1) / n).fillna(0.0)
    return daily, (held.where(avail, np.nan).stack().mean()), trade.where(avail, 0).sum().sum() / 2


def stats(d):
    if len(d) < 30:
        return "n/a"
    eq = (1 + d).cumprod()
    yrs = len(d) / 365
    cagr = eq.iloc[-1] ** (1 / yrs) - 1
    sharpe = d.mean() / d.std() * math.sqrt(365) if d.std() > 0 else 0
    mdd = (eq / eq.cummax() - 1).min()
    return f"{eq.iloc[-1] - 1:+8.0%} total {cagr:+6.0%}/yr  Sharpe {sharpe:+5.2f}  worst drop {mdd:5.0%}"


def main():
    p = load()
    print(f"cost {COST:.1%} per side; memecoins equal-weighted; train 2021-2024, test 2025-Oct 2026\n")
    for rule in ("hold", "sma 20", "sma 50", "sma 100", "mom 7", "mom 14", "mom 30", "btc 50", "btc 100", "sma50+btc",
                 "donchian", "top3 mom14", "dip -20%"):
        d, inmkt, trades = backtest(p, rule)
        tr, te = d[d.index < SPLIT], d[d.index >= SPLIT]
        print(f"{rule:<11} in market {inmkt:4.0%} | TRAIN {stats(tr)} | TEST {stats(te)}")


if __name__ == "__main__":
    main()

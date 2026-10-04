"""Market implied volatility from Cboe's index history (data/*_cboe.csv), as a drop-in for lab.iv_at.

Same-day options: VIX1D (the S&P 500's 1-day implied vol) at that morning's open, held for the whole day.
  - VIX1D's 1-day variance (VIX1D^2 / 365) matched SPY's realised 10:00-16:00 variance on average (ratio 1.00,
    246 days, study14c), so it is used as the session's IV, converted to lab.py's trading-time clock
    (x sqrt(252/365)). MULT scales it for sensitivity (1.25 = treat VIX1D as already on a trading-day clock).
  - QQQ and IWM normally carry more IV than the S&P: scaled by the prior day's VXN/VIX and RVX/VIX ratios.

  - Variance clock (clock=True): the open and the close are the busiest parts of the day, so the IV that prices the
    rest of the session falls through the morning. IV at bar i = session IV x sqrt(share of the day's variance still
    to come / share of the day's time still to come), from the average 5-min squared returns of each symbol's
    TRAIN days (e.g. SPY 0.97 at 9:45 ET, 0.86 at noon, 0.94 at 15:30).

Usage:  import market_iv; market_iv.install(mult=1.0)   # every lab.iv_at call now uses market IV
"""
import math
import os

import pandas as pd

import lab

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def _load(name):
    return pd.read_csv(os.path.join(DATA, f"{name}_cboe.csv"), parse_dates=["DATE"]).set_index("DATE")


V1D = _load("VIX1D")
RATIO = {
    "QQQ": (_load("VXN").CLOSE / _load("VIX").CLOSE).shift(1),
    "IWM": (_load("RVX").CLOSE / _load("VIX").CLOSE).shift(1),
}
_orig = lab.iv_at
MULT = 1.0
CLOCK = True
_profile = {}


def clock_factor(sym, i):
    if sym not in _profile:
        import numpy as np
        ds = [d for d in lab.universe([sym]) if d.date < lab.SPLIT]
        r2 = np.array([np.diff(np.log(np.concatenate([[d.o[0]], d.c]))) ** 2 for d in ds]).mean(axis=0)
        rem = 1 - np.cumsum(r2 / r2.sum())
        tim = (lab.BARS - 1 - np.arange(lab.BARS)) / lab.BARS
        _profile[sym] = np.sqrt(np.where(tim > 0, np.clip(rem, 0, None) / np.where(tim > 0, tim, 1), 1.0))
    return float(_profile[sym][i])


def iv_market(day, bar_end_idx):
    if day.sym not in lab.ETFS or day.date not in V1D.index or lab.days_to_expiry(day) != 0:
        return _orig(day, bar_end_idx)
    iv = V1D.OPEN.loc[day.date] / 100 * math.sqrt(252 / 365) * MULT
    if day.sym in RATIO:
        r = RATIO[day.sym].get(day.date)
        iv *= r if r == r and r is not None else 1.3
    if CLOCK:
        iv *= clock_factor(day.sym, bar_end_idx)
    return iv


def install(mult=1.0, clock=True):
    global MULT, CLOCK
    MULT, CLOCK = mult, clock
    lab.iv_at = iv_market


def uninstall():
    lab.iv_at = _orig

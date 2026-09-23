"""Shared research utilities: data loading, day features, option pricing, trade simulation."""
import math
import os
from dataclasses import dataclass

import numpy as np
import pandas as pd

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
ETFS = ["SPY", "QQQ", "IWM"]
STOCKS = ["TSLA", "NVDA", "AMD", "PLTR", "META", "AAPL", "AMZN"]
ALL = ETFS + STOCKS
SPLIT = pd.Timestamp("2026-05-01")  # train < SPLIT <= test
BARS = 78


@dataclass
class Day:
    sym: str
    date: pd.Timestamp
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    v: np.ndarray
    prev_close: float
    prev_high: float
    prev_low: float
    rv20: float      # annualised close-to-close vol, 20 days
    irv20: float     # annualised intraday (9:30-16:00) realised vol from 5-min returns, 20 days
    atr14: float     # daily ATR in $
    avgvol20: np.ndarray  # average volume per bar slot over 20 prior days
    prev_ret: float  # prior day open->close return
    dow: int

    @property
    def vwap(self):
        tp = (self.h + self.l + self.c) / 3
        return np.cumsum(tp * self.v) / np.cumsum(self.v)


def load(sym):
    df = pd.read_csv(os.path.join(DATA, f"{sym}_M5.csv"), parse_dates=["time_et"])
    df["date"] = df.time_et.dt.normalize()
    days = []
    groups = [g for _, g in df.groupby("date") if len(g) == BARS]
    closes = [g.close.iloc[-1] for g in groups]
    ivar = []
    for g in groups:
        px = np.concatenate([[g.open.iloc[0]], g.close.values])
        ivar.append(np.sum(np.diff(np.log(px)) ** 2))
    for i, g in enumerate(groups):
        if i < 21:
            continue
        prev = groups[i - 1]
        rets = np.diff(np.log(closes[i - 21:i]))
        trs = []
        for j in range(i - 14, i):
            gj, pc = groups[j], closes[j - 1]
            trs.append(max(gj.high.max(), pc) - min(gj.low.min(), pc))
        days.append(Day(
            sym=sym, date=g.date.iloc[0],
            o=g.open.values, h=g.high.values, l=g.low.values, c=g.close.values, v=g.volume.values.astype(float),
            prev_close=closes[i - 1], prev_high=prev.high.max(), prev_low=prev.low.min(),
            rv20=float(np.std(rets) * math.sqrt(252)),
            irv20=float(math.sqrt(np.mean(ivar[i - 20:i]) * 252)), atr14=float(np.mean(trs)),
            avgvol20=np.mean([groups[j].volume.values for j in range(i - 20, i)], axis=0),
            prev_ret=prev.close.iloc[-1] / prev.open.iloc[0] - 1,
            dow=g.date.iloc[0].dayofweek,
        ))
    return days


_cache = {}


def universe(syms=ALL):
    out = []
    for s in syms:
        if s not in _cache:
            _cache[s] = load(s)
        out += _cache[s]
    return out


# ---------------- option model ----------------
SQRT2 = math.sqrt(2)


def ncdf(x):
    return 0.5 * (1 + math.erf(x / SQRT2))


def bs(spot, strike, t_years, iv, kind):
    t = max(t_years, 1e-6)
    sd = iv * math.sqrt(t)
    d1 = (math.log(spot / strike) + 0.5 * sd * sd) / sd
    d2 = d1 - sd
    if kind == "C":
        return spot * ncdf(d1) - strike * ncdf(d2), ncdf(d1)
    return strike * ncdf(-d2) - spot * ncdf(-d1), ncdf(d1) - 1


def strike_step(price, sym):
    if sym in ETFS:
        return 1.0
    if price < 50:
        return 0.5
    if price < 200:
        return 1.0
    if price < 500:
        return 2.5
    return 5.0


def days_to_expiry(day):
    """ETFs: same-day expiry. Stocks: Friday weekly (0 on Friday)."""
    if day.sym in ETFS:
        return 0
    return max(0, 4 - day.dow)


def t_years(day, bar_end_idx):
    """Time to 16:00 expiry measured from the end of bar `bar_end_idx` (0..77)."""
    minutes_left = (BARS - 1 - bar_end_idx) * 5
    return (minutes_left + days_to_expiry(day) * 390) / (390 * 252)


# Model assumptions (tunable for sensitivity tests)
MODEL = dict(iv_mult=1.15, open_premium=0.10, open_decay_min=45, hs_etf=0.01, hs_stk=0.015, hs_min=0.01,
             gap_iv=0.25)  # IV rises on gap days: x(1 + gap_iv * |gap| / daily sd), capped at 2x


def iv_at(day, bar_end_idx):
    """IV = 20d realised vol x iv_mult, plus an opening premium that decays linearly after 9:30."""
    # same-day expiry only lives through market hours -> price off intraday vol;
    # multi-day expiry spans overnights -> close-to-close vol. iv_mult = premium over realised.
    realised = day.irv20 if days_to_expiry(day) == 0 else day.rv20
    base = max(realised * MODEL["iv_mult"], 0.08)
    daily_sd = day.rv20 / math.sqrt(252)
    gap = abs(day.o[0] / day.prev_close - 1)
    base *= min(2.0, 1 + MODEL["gap_iv"] * gap / max(daily_sd, 1e-4))
    minutes = (bar_end_idx + 1) * 5
    boost = MODEL["open_premium"] * max(0.0, 1 - minutes / MODEL["open_decay_min"])
    return base * (1 + boost)


def half_spread(premium, sym):
    pct = MODEL["hs_etf"] if sym in ETFS else MODEL["hs_stk"]
    return max(MODEL["hs_min"], pct * premium)


def choose_contract(day, i, kind, budget, min_delta=0.0):
    """Strike nearest the money whose ask fits the budget (per share). Returns (strike, mid, delta) or None."""
    spot = day.c[i]
    step = strike_step(spot, day.sym)
    t, iv = t_years(day, i), iv_at(day, i)
    k = math.ceil(spot / step) * step if kind == "C" else math.floor(spot / step) * step
    for _ in range(60):
        mid, delta = bs(spot, k, t, iv, kind)
        if mid + half_spread(mid, day.sym) <= budget:
            if abs(delta) < min_delta or mid < 0.05:
                return None
            return k, mid, delta
        k += step if kind == "C" else -step
    return None


# ---------------- trade simulation ----------------
@dataclass
class Result:
    sym: str
    date: pd.Timestamp
    kind: str
    entry: float
    exit: float
    ret: float
    reason: str
    delta: float
    entry_bar: int
    exit_bar: int


def simulate(day, i, kind, budget, stop_pct=None, target_pct=None, exit_bar=77,
             und_stop=None, trail_pct=None, min_delta=0.0):
    """Buy at close of bar i. Walk bars i+1..exit_bar with option priced at bar extremes.

    und_stop: underlying level; a bar CLOSE beyond it exits (structure stop).
    trail_pct: once the option is up >= trail_pct, stop trails at peak*(1-trail_pct).
    """
    pick = choose_contract(day, i, kind, budget, min_delta)
    if not pick:
        return None
    k, mid, delta = pick
    entry = mid + half_spread(mid, day.sym)
    stop = entry * (1 - stop_pct) if stop_pct else -1
    target = entry * (1 + target_pct) if target_pct else float("inf")
    peak = entry
    for j in range(i + 1, exit_bar + 1):
        t, iv = t_years(day, j), iv_at(day, j)
        adverse = day.l[j] if kind == "C" else day.h[j]
        favour = day.h[j] if kind == "C" else day.l[j]
        worst = bs(adverse, k, t, iv, kind)[0]
        best = bs(favour, k, t, iv, kind)[0]
        worst -= half_spread(worst, day.sym)
        best -= half_spread(best, day.sym)
        if worst <= stop:
            return Result(day.sym, day.date, kind, entry, stop, stop / entry - 1, "stop", delta, i, j)
        if best >= target:
            return Result(day.sym, day.date, kind, entry, target, target / entry - 1, "target", delta, i, j)
        peak = max(peak, best)
        if trail_pct and peak >= entry * (1 + trail_pct):
            stop = max(stop, peak * (1 - trail_pct))
        close_val = bs(day.c[j], k, t, iv, kind)[0]
        close_val -= half_spread(close_val, day.sym)
        if und_stop is not None and ((kind == "C" and day.c[j] < und_stop) or (kind == "P" and day.c[j] > und_stop)):
            return Result(day.sym, day.date, kind, entry, close_val, close_val / entry - 1, "structure", delta, i, j)
    t, iv = t_years(day, exit_bar), iv_at(day, exit_bar)
    val = bs(day.c[exit_bar], k, t, iv, kind)[0]
    val -= half_spread(val, day.sym)
    val = max(val, 0.0)
    return Result(day.sym, day.date, kind, entry, val, val / entry - 1, "time", delta, i, exit_bar)


def summarize(results, label=""):
    if not results:
        return f"{label:<44} n=0"
    r = np.array([x.ret for x in results])
    tr = np.array([x.ret for x in results if x.date < SPLIT])
    te = np.array([x.ret for x in results if x.date >= SPLIT])

    def part(a):
        if len(a) == 0:
            return "n=0"
        t = a.mean() / (a.std(ddof=1) / math.sqrt(len(a))) if len(a) > 1 and a.std() > 0 else 0
        return f"n={len(a):4d} win {np.mean(a > 0):4.0%} avg {a.mean():+6.1%} t {t:+5.2f}"

    return f"{label:<44} ALL {part(r)} | TRAIN {part(tr)} | TEST {part(te)}"

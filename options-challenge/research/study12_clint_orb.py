"""Study 12: the opening-range method from Clint Awana's video "How to Trade the Opening Range" (2026-09-28).

His rules, as coded here (SPY and QQQ, 5-min bars, Oct 2025 - Sep 2026):
  range     high/low of 9:30-9:45 ET (first three 5-min candles)
  entry     first 5-min CLOSE outside the range, before 11:30 ET (10:30 CT)
  filters   (each tested alone and all together)
            vol   - breakout candle volume rising (above the prior candle and above its 20-day average for that time)
            rsi   - RSI(14) moving the trade's way and not stretched (calls: 50-70 and rising; puts: 30-50 and falling)
            both  - SPY and QQQ both closed outside their ranges in the same direction (no opposite break)
            narrow- range narrower than the median of the prior 10 days' ranges
            skip  - no monthly OPEX (3rd Friday) or FOMC days
  exit      (his) take profit at the next standard floor pivot beyond the entry (P, R1-R3, S1-S3 from the prior
            day), out if a 5-min candle closes back inside the range, out at 11:30 ET if neither happened
            (he says catch the first move, don't hold all day). Also reported: the Trade Guardian's exits.
Not coded: premarket high/low targets (the data has no premarket bars), Mag-7 confirmation, trims/runners.
Options: same-day contract ~$0.50 (BUDGET env var), lab.py's Black-Scholes model, conservative fills.

Run:  python study12_clint_orb.py
"""
import os
from collections import defaultdict

import numpy as np
import pandas as pd

import lab
import study11_september as S

SYMS = ["SPY", "QQQ"]
BUDGET = float(os.environ.get("BUDGET", "0.50"))
LAST = 23  # bar closing 11:30 ET / 10:30 CT
FOMC = {"2025-10-29", "2025-12-10", "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29",
        "2026-09-16"}


def opex(date):
    return date.dayofweek == 4 and 15 <= date.day <= 21


def pivots(d):
    h, l, c = d.prev_high, d.prev_low, d.prev_close
    p = (h + l + c) / 3
    return sorted([p, 2 * p - l, 2 * p - h, p + (h - l), p - (h - l), h + 2 * (p - l), l - 2 * (h - p)])


def signal(d, prev_c, other, width_med):
    """Returns (bar, kind, flags) for the first close outside the range, or None."""
    hi, lo = d.h[:3].max(), d.l[:3].min()
    r = S.rsi(np.concatenate([prev_c, d.c]))[len(prev_c):]
    for i in range(3, LAST + 1):
        kind = "C" if d.c[i] > hi else "P" if d.c[i] < lo else None
        if not kind:
            continue
        up = kind == "C"
        oh, ol = other.h[:3].max(), other.l[:3].min()
        o_same = any((other.c[j] > oh) if up else (other.c[j] < ol) for j in range(3, i + 1))
        o_opp = any((other.c[j] < ol) if up else (other.c[j] > oh) for j in range(3, i + 1))
        flags = dict(
            vol=d.v[i] > d.v[i - 1] and d.v[i] > d.avgvol20[i],
            rsi=(50 < r[i] < 70 and r[i] > r[i - 1]) if up else (30 < r[i] < 50 and r[i] < r[i - 1]),
            both=o_same and not o_opp,
            narrow=(hi - lo) / d.o[0] < width_med,
            skip=not (opex(d.date) or d.date.strftime("%Y-%m-%d") in FOMC),
        )
        return i, kind, flags
    return None


def his_exit(d, i, kind, budget=BUDGET):
    """Target = next pivot beyond entry; out on a close back inside the range; out at 11:30 ET."""
    pick = lab.choose_contract(d, i, kind, budget)
    if not pick:
        return None
    k, mid, _ = pick
    entry = mid + lab.half_spread(mid, d.sym)
    hi, lo = d.h[:3].max(), d.l[:3].min()
    piv = pivots(d)
    e = d.c[i]
    tgt = next((p for p in piv if p > e + 0.05), None) if kind == "C" else next((p for p in piv[::-1] if p < e - 0.05), None)
    for j in range(i + 1, LAST + 1 + 12):  # a little past 11:30 so late entries get time too
        if tgt is not None and ((kind == "C" and d.h[j] >= tgt) or (kind == "P" and d.l[j] <= tgt)):
            return (S.opt_px(d, j, tgt, k, kind) - entry) * 100, (tgt / e - 1) * (1 if kind == "C" else -1) * 1e4, "target"
        if (kind == "C" and d.c[j] < hi) or (kind == "P" and d.c[j] > lo):
            return (S.opt_px(d, j, d.c[j], k, kind) - entry) * 100, (d.c[j] / e - 1) * (1 if kind == "C" else -1) * 1e4, "failed"
        if j >= max(LAST, i + 6):
            return (S.opt_px(d, j, d.c[j], k, kind) - entry) * 100, (d.c[j] / e - 1) * (1 if kind == "C" else -1) * 1e4, "time"
    return None


def main():
    days = lab.universe(SYMS)
    by = defaultdict(dict)
    for d in days:
        by[d.sym][d.date] = d
    rows = []
    for sym in SYMS:
        other_sym = "QQQ" if sym == "SPY" else "SPY"
        dates = sorted(by[sym])
        for n, date in enumerate(dates):
            if n < 11 or date not in by[other_sym]:
                continue
            d, prev = by[sym][date], by[sym][dates[n - 1]]
            widths = [(by[sym][x].h[:3].max() - by[sym][x].l[:3].min()) / by[sym][x].o[0] for x in dates[n - 10:n]]
            sig = signal(d, prev.c, by[other_sym][date], np.median(widths))
            if not sig:
                continue
            i, kind, flags = sig
            h = his_exit(d, i, kind)
            g = S.trade(d, i, kind)
            if h is None or g is None:
                continue
            rows.append(dict(sym=sym, date=date, month=date.strftime("%Y-%m"), bar=i, kind=kind, his=h[0], und=h[1],
                             how=h[2], guard=g, **flags))
    df = pd.DataFrame(rows)
    df["all"] = df.vol & df.rsi & df.both & df.narrow & df.skip
    df["vol_rsi_both"] = df.vol & df.rsi & df.both
    df["per"] = np.where(df.date >= pd.Timestamp("2026-09-01"), "SEP", "PRIOR")
    print(f"budget ${BUDGET:.2f}, IV x{lab.MODEL['iv_mult']}, SPY+QQQ, {df.date.min():%Y-%m-%d} .. {df.date.max():%Y-%m-%d}")
    print(f"\n{'filter':<22}{'per':<6}{'n':>4}{'win':>6}{'und bps':>9}{'his $':>8}{'total':>8}{'guard $':>9}   exits (target/failed/time)")
    for name, mask in [("plain ORB (no filter)", df.index == df.index), ("+ volume", df.vol), ("+ RSI", df.rsi),
                       ("+ SPY&QQQ agree", df.both), ("+ narrow range", df.narrow), ("+ skip OPEX/FOMC", df.skip),
                       ("volume+RSI", df.vol & df.rsi), ("volume+RSI+agree", df.vol_rsi_both), ("ALL his rules", df["all"])]:
        for per in ("SEP", "PRIOR"):
            x = df[mask & (df.per == per)]
            if not len(x):
                print(f"{name:<22}{per:<6}   0")
                continue
            c = x.how.value_counts()
            print(f"{name:<22}{per:<6}{len(x):>4}{(x.his > 0).mean():>6.0%}{x.und.mean():>+9.1f}{x.his.mean():>+8.2f}"
                  f"{x.his.sum():>+8.0f}{x.guard.mean():>+9.2f}   {c.get('target', 0)}/{c.get('failed', 0)}/{c.get('time', 0)}")
    a = df[df["all"]]
    print("\nALL-rules trades by month ($/trade his exit, n):")
    print(a.groupby("month").his.agg(["count", "mean", "sum"]).round(2).to_string())
    print("\nALL-rules trades in September:")
    print(a[a.per == "SEP"][["date", "sym", "bar", "kind", "und", "how", "his", "guard"]].to_string(index=False))
    return df


if __name__ == "__main__":
    main()

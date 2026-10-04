"""Study 14: systematic search over ICT-style setups (fair value gaps, order blocks, liquidity sweeps, market
structure shifts) on 5-minute bars, with an honest train/test split.

Data: SPY/QQQ/IWM 5-min regular-session bars, Sep 2025 - Sep 2026 (stocks used only as a robustness check).
TRAIN = before 2026-05-01 (config selection), TEST = 2026-05-01 on (never used to pick anything).

Building blocks (all computed only from bars already closed at decision time):
  displacement  a candle whose body >= DISP x the average bar range so far today
  FVG           3-candle gap with a displacement middle candle; bull: high[k-2] < low[k]
  swing         2-bar fractal high/low (confirmed 2 bars later)
  MSS           the displacement candle closes beyond the latest confirmed swing in the trade direction
  sweep         a candle trades through a liquidity level (prior-day high/low, opening-range high/low)
                and closes back on the other side
  order block   the last opposite-colour candle before the displacement leg

Setups:
  fvg      enter on the first retrace into a fresh displacement FVG (limit at the near edge)
  sweep    liquidity sweep -> MSS displacement leaving an FVG within 8 bars -> enter on retrace into the FVG,
           stop beyond the sweep extreme ("ICT 2022 model" / silver-bullet style)
  ob       MSS displacement -> enter on retrace into the order block, stop beyond the block
  mom      enter at the close of an MSS displacement candle that leaves an FVG (no retrace)

Outcomes are measured in R on the underlying (risk = entry - stop), first-touch, stop checked first when a
bar touches both, $0.01/share cost each way, time exit 15:50 ET. Max one trade per symbol per day.

Run:  python study14_ict_search.py            (prints the search summary and the top train configs on test)
"""
import itertools
import os

import numpy as np
import pandas as pd

import lab

SPLIT = pd.Timestamp("2026-05-01")
ETF = ["SPY", "QQQ", "IWM"]
LAST = 76  # bar closing 15:50 ET
WINDOWS = {"open": (3, 17), "sb": (6, 17), "all": (3, 65), "pm": (48, 65)}  # signal bar index range
COST = 0.01


# ------------------------------------------------------------------ features
def day_feats(d):
    o, h, l, c = d.o, d.h, d.l, d.c
    n = len(c)
    rng = h - l
    ar = np.array([rng[:max(i, 1)].mean() if i >= 1 else rng[0] for i in range(n)])  # avg range of prior bars
    body = np.abs(c - o)
    sh = np.full(n, np.nan)  # latest confirmed swing high known at bar i
    sl = np.full(n, np.nan)
    last_h = last_l = np.nan
    for i in range(n):
        j = i - 2
        if j >= 2 and h[j] == h[j - 2:j + 3].max():
            last_h = h[j]
        if j >= 2 and l[j] == l[j - 2:j + 3].min():
            last_l = l[j]
        sh[i], sl[i] = last_h, last_l
    return dict(ar=ar, body=body, sh=sh, sl=sl, vw=d.vwap)


def fvgs(d, f, k, disp):
    """FVG completed at bar k (3rd candle). Returns (dir, lo, hi) or None."""
    if k < 2 or f["body"][k - 1] < disp * f["ar"][k - 1]:
        return None
    if d.h[k - 2] < d.l[k] and d.c[k - 1] > d.o[k - 1]:
        return 1, d.h[k - 2], d.l[k]
    if d.l[k - 2] > d.h[k] and d.c[k - 1] < d.o[k - 1]:
        return -1, d.h[k], d.l[k - 2]
    return None


def mss(d, f, k, side):
    """Did the displacement candle k-1 close beyond the swing known before the leg?"""
    ref = f["sl"][k - 2] if side < 0 else f["sh"][k - 2]
    return not np.isnan(ref) and (d.c[k - 1] < ref if side < 0 else d.c[k - 1] > ref)


def order_block(d, k, side):
    """Last opposite candle before the displacement candle k-1 (search back 6 bars)."""
    for j in range(k - 2, max(-1, k - 8), -1):
        if (side > 0 and d.c[j] < d.o[j]) or (side < 0 and d.c[j] > d.o[j]):
            return d.l[j], d.h[j]
    return None


# ------------------------------------------------------------------ signals: return (sig_bar, side, entry, stop, kind)
def setups(d, f, cfg, levels):
    a, b = WINDOWS[cfg["win"]]
    disp, st = cfg["disp"], cfg["setup"]
    swept = {}  # side -> (bar, extreme)
    for k in range(2, b + 1):
        if st == "sweep":
            for lv in levels(k):
                if d.h[k] > lv and d.c[k] < lv:
                    swept[-1] = (k, max(d.h[k], swept.get(-1, (0, 0))[1]))
                if d.l[k] < lv and d.c[k] > lv:
                    swept[1] = (k, min(d.l[k], swept.get(1, (0, 1e9))[1]))
        g = fvgs(d, f, k, disp)
        if g is None or k < a:
            continue
        side, lo, hi = g
        if st == "fvg":
            entry = hi if side > 0 else lo
            stop = lo - 0.25 * (hi - lo) if side > 0 else hi + 0.25 * (hi - lo)
            yield k, side, entry, stop, "limit"
        elif st == "mom":
            if mss(d, f, k, side):
                stop = d.l[k - 1] if side > 0 else d.h[k - 1]
                yield k, side, d.c[k], stop, "market"
        elif st == "ob":
            if mss(d, f, k, side):
                ob = order_block(d, k, side)
                if ob:
                    olo, ohi = ob
                    yield k, side, (ohi if side > 0 else olo), (olo if side > 0 else ohi), "limit"
        elif st == "sweep":
            sw = swept.get(side)
            if sw and k - sw[0] <= cfg.get("lb", 8) and (not cfg.get("mss", True) or mss(d, f, k, side)):
                entry = hi if side > 0 else lo
                stop = sw[1] - 0.02 if side > 0 else sw[1] + 0.02
                yield k, side, entry, stop, "limit"


def bias_ok(d, f, k, side, bias, trend):
    if bias in ("vwap", "both") and (d.c[k] - f["vw"][k]) * side <= 0:
        return False
    if bias in ("trend", "both") and trend * side <= 0:
        return False
    return True


def simulate(d, k, side, entry, stop, kind, tgt, levels, wait=12, maxbars=None):
    """Returns (R, fill_bar, exit_bar, exit_px) or None if never filled / invalid."""
    risk = (entry - stop) * side
    if risk <= max(0.0002 * entry, 0.03):
        return None
    if kind == "market":
        e = k
    else:
        e = None
        for j in range(k + 1, min(k + 1 + wait, LAST)):
            touched = d.l[j] <= entry if side > 0 else d.h[j] >= entry
            if touched:
                e = j
                if (d.o[j] - entry) * side < 0:  # gapped through the limit: fill at the open
                    entry = d.o[j]
                    risk = (entry - stop) * side
                    if risk <= 0:
                        return None
                break
        if e is None:
            return None
    if tgt == "liq":
        cands = [x for x in levels(e) if (x - entry) * side >= risk]
        if not cands:
            return None
        target = min(cands, key=lambda x: abs(x - entry))
    else:
        target = entry + side * float(tgt) * risk
    start = e if kind == "limit" else e + 1
    last = LAST if maxbars is None else min(LAST, e + maxbars)
    for j in range(start, last + 1):
        hit_stop = d.l[j] <= stop if side > 0 else d.h[j] >= stop
        hit_tgt = d.h[j] >= target if side > 0 else d.l[j] <= target
        if j == e and kind == "limit":
            hit_tgt = hit_tgt and (d.c[j] - target) * side >= 0  # on the fill bar only trust a close beyond
        if hit_stop:
            px = stop if not (j > e and (d.o[j] - stop) * side < 0) else d.o[j]
            return (px - entry) * side / risk - 2 * COST / risk, e, j, px
        if hit_tgt:
            return (target - entry) * side / risk - 2 * COST / risk, e, j, target
    px = d.c[last]
    return (px - entry) * side / risk - 2 * COST / risk, e, last, px


def run_config(days_by_sym, feats, trends, cfg):
    out = []
    for sym, days in days_by_sym.items():
        for d in days:
            f = feats[(sym, d.date)]
            or_hi, or_lo = d.h[:3].max(), d.l[:3].min()
            lv_set = cfg["levels"]

            def levels(k, d=d, or_hi=or_hi, or_lo=or_lo):
                xs = []
                if lv_set in ("pd", "both"):
                    xs += [d.prev_high, d.prev_low]
                if lv_set in ("or", "both") and k >= 3:
                    xs += [or_hi, or_lo]
                return xs

            for k, side, entry, stop, kind in setups(d, f, cfg, levels):
                if not bias_ok(d, f, k, side, cfg["bias"], trends[(sym, d.date)]):
                    continue
                r = simulate(d, k, side, entry, stop, kind, cfg["tgt"], levels, maxbars=cfg.get("maxbars"))
                if r is None:
                    continue
                out.append(dict(sym=sym, date=d.date, side=side, R=r[0], k=k, fill=r[1], exit=r[2],
                                entry=entry, stop=stop, exit_px=r[3]))
                break  # one trade per symbol per day
    return out


def stats(rows):
    if not rows:
        return dict(n=0, avgR=np.nan, win=np.nan, pf=np.nan)
    R = np.array([x["R"] for x in rows])
    gains, losses = R[R > 0].sum(), -R[R < 0].sum()
    return dict(n=len(R), avgR=R.mean(), win=(R > 0).mean(), pf=gains / losses if losses else np.inf)


def load_all(syms):
    days_by_sym, feats, trends = {}, {}, {}
    for s in syms:
        ds = sorted(lab.universe([s]), key=lambda x: x.date)
        days_by_sym[s] = ds
        closes = [x.prev_close for x in ds]
        for i, d in enumerate(ds):
            feats[(s, d.date)] = day_feats(d)
            sma = np.mean(closes[max(0, i - 19):i + 1])
            trends[(s, d.date)] = 1 if d.prev_close > sma else -1
    return days_by_sym, feats, trends


GRID = dict(setup=["fvg", "sweep", "ob", "mom"], win=list(WINDOWS), bias=["none", "vwap", "trend", "both"],
            tgt=["1", "1.5", "2", "3", "liq"], disp=[1.5, 2.5], levels=["pd", "or", "both"])


def configs():
    for vals in itertools.product(*GRID.values()):
        cfg = dict(zip(GRID, vals))
        if cfg["setup"] != "sweep" and cfg["levels"] != "both":
            continue  # levels only matter for sweeps (and 'liq' targets use both)
        yield cfg


def main():
    days_by_sym, feats, trends = load_all(ETF)
    rows = []
    for cfg in configs():
        tr = run_config(days_by_sym, feats, trends, cfg)
        a = stats([x for x in tr if x["date"] < SPLIT])
        b = stats([x for x in tr if x["date"] >= SPLIT])
        rows.append({**cfg, **{f"tr_{k}": v for k, v in a.items()}, **{f"te_{k}": v for k, v in b.items()}})
    df = pd.DataFrame(rows)
    ok = df[(df.tr_n >= 40) & (df.te_n >= 20)]
    print(f"{len(df)} configs, {len(ok)} with >= 40 train and >= 20 test trades")
    print(f"share positive in TRAIN: {(ok.tr_avgR > 0).mean():.0%}   in TEST: {(ok.te_avgR > 0).mean():.0%}   "
          f"both: {((ok.tr_avgR > 0) & (ok.te_avgR > 0)).mean():.0%}")
    print(f"correlation train avgR vs test avgR: {ok.tr_avgR.corr(ok.te_avgR):+.2f}")
    top = ok.sort_values("tr_avgR", ascending=False).head(15)
    cols = ["setup", "win", "bias", "tgt", "disp", "levels", "tr_n", "tr_avgR", "tr_win", "te_n", "te_avgR", "te_win"]
    print("\nTop 15 by TRAIN avg R, with their untouched TEST result:")
    print(top[cols].round(3).to_string(index=False))
    print("\nBy setup (median avg R across configs):")
    print(ok.groupby("setup")[["tr_avgR", "te_avgR"]].median().round(3))
    df.to_csv(os.path.join(os.path.dirname(__file__), "out", "study14_grid.csv"), index=False)
    return df


if __name__ == "__main__":
    main()

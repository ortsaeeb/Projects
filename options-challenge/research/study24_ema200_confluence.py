"""Study 24: which indicators or levels make a 200 EMA bounce / rejection work?

Every 200 EMA "hold" candle from study 23 (wick touches the EMA, closes back on the side it came from; entries
8:45-14:00 CT), traded the same way (enter at the close, stop 1 cent past the wick, 2R target, out after 60 min).
At the moment of the signal, ~40 indicator readings are taken, all oriented so that the number means the same thing
for calls and puts (e.g. "RSI vs bounce" = RSI for a call setup, 100 - RSI for a put setup: low = stretched against
the bounce = oversold for a call, overbought for a put).

  1. One at a time: each indicator split into thirds (cut points from TRAIN only) or yes/no; the best third on TRAIN
     vs the rest, then the same split on TEST. An indicator that matters should help on both.
  2. All at once: a gradient-boosted tree and a logistic regression trained on TRAIN to predict a winning trade,
     scored on TEST (AUC 0.5 = no better than a coin flip), plus the P&L of only taking the trades the model likes.
Train < 2026-05-01 <= test. 5 and 15-min charts from data/{SPY,QQQ}_M5.csv; 1-min from the Dukascopy CFD
(Jun-Oct 2026, split in half by date).

Run:  python study24_ema200_confluence.py
"""
import math
import sys

import numpy as np
import pandas as pd

import lab
import market_iv
import study23_ema200 as S


def rsi(c, n):
    d = np.diff(c, prepend=c[0])
    up = pd.Series(np.where(d > 0, d, 0.0)).ewm(alpha=1 / n, adjust=False).mean()
    dn = pd.Series(np.where(d < 0, -d, 0.0)).ewm(alpha=1 / n, adjust=False).mean()
    return (100 - 100 / (1 + up / dn.replace(0, np.nan))).fillna(50).values


def adx(h, l, c, n=14):
    up, dn = np.diff(h, prepend=h[0]), -np.diff(l, prepend=l[0])
    pdm = np.where((up > dn) & (up > 0), up, 0.0)
    ndm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = np.maximum(h - l, np.maximum(abs(h - np.roll(c, 1)), abs(l - np.roll(c, 1))))
    w = lambda x: pd.Series(x).ewm(alpha=1 / n, adjust=False).mean().values
    atr = np.fmax(w(tr), 1e-9)
    pdi, ndi = 100 * w(pdm) / atr, 100 * w(ndm) / atr
    return w(100 * abs(pdi - ndi) / np.fmax(pdi + ndi, 1e-9))


def indicators(b):
    """Chart indicators on one symbol's bars of one timeframe (carried across days, like a chart)."""
    c, h, l, o, v = b.c.values, b.h.values, b.l.values, b.o.values, b.v.values.astype(float)
    ema = lambda n: b.c.ewm(span=n, adjust=False).mean().values
    f = pd.DataFrame(index=b.index)
    f["rsi14"], f["rsi2"] = rsi(c, 14), rsi(c, 2)
    ll, hh = b.l.rolling(14).min().values, b.h.rolling(14).max().values
    f["stoch"] = pd.Series((c - ll) / np.fmax(hh - ll, 1e-9) * 100).rolling(3).mean().values
    macd = ema(12) - ema(26)
    sig = pd.Series(macd).ewm(span=9, adjust=False).mean().values
    f["macdh"], f["macdh_prev"] = macd - sig, np.roll(macd - sig, 1)
    for n in (9, 20, 50):
        f[f"ema{n}"] = ema(n)
    sma20, sd20 = b.c.rolling(20).mean().values, b.c.rolling(20).std().values
    f["bb_lo"], f["bb_hi"] = sma20 - 2 * sd20, sma20 + 2 * sd20
    f["adx"] = adx(h, l, c)
    tp = (h + l + c) / 3
    f["vwap"] = (pd.Series(tp * v).groupby(b.date.values).cumsum() / pd.Series(v).groupby(b.date.values).cumsum()).values
    # volume vs the average of the same time slot over the prior 20 days (the open is always busy)
    f["volx"] = v / b.assign(v=v).groupby("slot").v.transform(lambda s: s.shift(1).rolling(20, min_periods=5).mean()).values
    f["rngx"] = (h - l) / pd.Series(h - l).rolling(20).mean().shift(1).values
    f["day_open"] = b.groupby("date").o.transform("first").values
    f["ema200"] = ema(200)
    sign = np.sign(c - f.ema200.values)
    f["last_cross"] = pd.Series(np.where(sign != np.roll(sign, 1), np.arange(len(b)), np.nan)).ffill().values
    return f


def daily_context(sym):
    d = pd.read_csv(f"{lab.DATA}/{sym}_D.csv", parse_dates=["date"]).set_index("date")
    x = pd.DataFrame(index=d.index)
    x["prev_close"], x["prev_high"], x["prev_low"] = d.close.shift(1), d.high.shift(1), d.low.shift(1)
    x["prev_ret"] = d.close.shift(1) / d.close.shift(2) - 1
    x["ret5"] = d.close.shift(1) / d.close.shift(6) - 1
    x["above_sma50"] = d.close.shift(1) > d.close.rolling(50).mean().shift(1)
    x["above_sma200d"] = d.close.shift(1) > d.close.rolling(200).mean().shift(1)
    p = (x.prev_high + x.prev_low + x.prev_close) / 3
    x["P"], x["R1"], x["S1"] = p, 2 * p - x.prev_low, 2 * p - x.prev_high
    return x


def features(tf, base_loader=S.base_m5, step=5, hold_min=60):
    """study23 trades for every hold candle, with the indicator readings at the signal."""
    x = S.build(tf, base_loader=base_loader, step=step, hold_min=hold_min)
    x = x[x.hold & (x.end >= 15) & (x.end <= 330)].copy()
    out = []
    for sym in S.SYMS:
        base = base_loader(sym)
        b = S.resample(base, tf, step)
        f = indicators(b)
        b30 = S.resample(base, 30, step)
        b30["ema200"] = b30.c.ewm(span=200, adjust=False).mean()
        b30["key"] = b30.date + pd.to_timedelta(b30.end, "min")
        orr = base[base["mod"] < 15].groupby("date").agg(ORH=("h", "max"), ORL=("l", "min"))
        dc = daily_context(sym)
        y = x[x.sym == sym].copy()
        g = f.loc[y.idx.values].reset_index(drop=True)
        y = y.reset_index(drop=True)
        s, e, px, rng = y.side.values, y.ema.values, y.entry.values, y.rng.values
        o = pd.DataFrame(index=y.index)
        o["rsi14"] = np.where(s > 0, g.rsi14, 100 - g.rsi14)
        o["rsi2"] = np.where(s > 0, g.rsi2, 100 - g.rsi2)
        o["stoch"] = np.where(s > 0, g.stoch, 100 - g.stoch)
        o["macd_hist_my_way"] = g.macdh.values * s > 0
        o["macd_hist_turning"] = (g.macdh.values - g.macdh_prev.values) * s > 0
        o["above_vwap"] = (px - g.vwap.values) * s > 0
        o["vwap_dist"] = (px - g.vwap.values) * s / rng
        for n in (9, 20, 50):
            o[f"beyond_ema{n}"] = (px - g[f"ema{n}"].values) * s > 0
        o["ema20_over_50"] = (g.ema20.values - g.ema50.values) * s > 0
        o["ema50_over_200"] = (g.ema50.values - e) * s > 0
        o["outside_bband"] = np.where(s > 0, y.wick.values < g.bb_lo.values, y.wick.values > g.bb_hi.values)
        o["adx"] = g.adx.values
        o["volume_x"] = g.volx.values
        o["candle_range_x"] = g.rngx.values
        o["vs_day_open"] = (px - g.day_open.values) * s / rng
        allt = S.events(b)  # every touch, held or not, to count which test of the EMA this is since price crossed it
        o["test_no"] = [int(((allt.side == y.side[i]) & (allt.idx > g.last_cross[i]) & (allt.idx <= y.idx[i])).sum())
                        for i in range(len(y))]
        o["first_test"] = o.test_no == 1
        o["slope200"], o["away"], o["bars_away"] = y.slope.values, y.away.values, y.bars_away.values
        o["closepos"], o["colour_my_way"] = y.closepos.values, y.green.values
        body = np.abs(y.entry.values - b.o.values[y.idx.values])
        tail = np.where(s > 0, np.minimum(b.o.values[y.idx.values], px) - y.wick.values,
                        y.wick.values - np.maximum(b.o.values[y.idx.values], px))
        o["hammer"] = (tail >= 2 * body) & (y.closepos.values > 0.6)
        po, pc = b.o.values[y.idx.values - 1], b.c.values[y.idx.values - 1]
        bo = b.o.values[y.idx.values]
        o["engulfing"] = np.where(s > 0, (pc < po) & (px > bo) & (px >= po) & (bo <= pc),
                                  (pc > po) & (px < bo) & (px <= po) & (bo >= pc))
        k30 = np.searchsorted(b30.key.values, (y.date + pd.to_timedelta(y.end, "min")).values, side="right") - 1
        o["above_30m_ema200"] = np.where(k30 >= 600, ((px - b30.ema200.values[k30]) * s > 0).astype(float), np.nan)
        o["approach_speed"] = (b.c.values[y.idx.values - 5] - px) * s / rng
        o["minute"] = y.end.values
        dd = dc.reindex(y.date)
        o["gap"] = (g.day_open.values / dd.prev_close.values - 1) * s * 1e4
        o["prev_day_ret"] = dd.prev_ret.values * s * 1e4
        o["ret_5d"] = dd.ret5.values * s * 1e4
        o["daily_sma50_my_way"] = np.where(s > 0, dd.above_sma50.values, ~dd.above_sma50.values.astype(bool))
        o["daily_sma200_my_way"] = np.where(s > 0, dd.above_sma200d.values, ~dd.above_sma200d.values.astype(bool))
        o["vix1d"] = market_iv.V1D.OPEN.reindex(y.date).values
        lv = np.column_stack([dd.prev_high, dd.prev_low, dd.prev_close, dd.P, dd.R1, dd.S1,
                              orr.ORH.reindex(y.date), orr.ORL.reindex(y.date)])
        near = np.abs(lv - e[:, None]) / rng[:, None]
        o["near_any_level"] = np.nanmin(near, axis=1) <= 1
        o["near_prev_day_hl"] = np.nanmin(near[:, :2], axis=1) <= 1
        o["near_prev_close"] = near[:, 2] <= 1
        o["near_pivots"] = np.nanmin(near[:, 3:6], axis=1) <= 1
        o["near_opening_range"] = np.nanmin(near[:, 6:8], axis=1) <= 1
        o["calls"] = s > 0
        out.append(pd.concat([y[["sym", "date", "end", "side", "R", "fwd", "usd"]], o], axis=1))
    return pd.concat(out, ignore_index=True)


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 3 or len(b) < 3:
        return 0.0
    return (a.mean() - b.mean()) / math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))


def screen(x, split=lab.SPLIT):
    """Each indicator: best bucket on TRAIN vs the rest, and the same bucket on TEST."""
    tr, te = x[x.date < split], x[x.date >= split]
    rows = []
    for col in x.columns[7:]:
        v = x[col]
        if v.dtype == bool or set(pd.unique(v.dropna())) <= {0, 1, True, False}:
            buckets = [("yes", lambda z: z[col].astype(float) == 1), ("no", lambda z: z[col].astype(float) == 0)]
        else:
            q1, q2 = tr[col].quantile([1 / 3, 2 / 3])
            buckets = [(f"low (<{q1:.3g})", lambda z, q1=q1: z[col] < q1),
                       (f"mid", lambda z, q1=q1, q2=q2: (z[col] >= q1) & (z[col] < q2)),
                       (f"high (>={q2:.3g})", lambda z, q2=q2: z[col] >= q2)]
        best = max(buckets, key=lambda bk: tr[bk[1](tr)].R.mean() if bk[1](tr).sum() >= 10 else -9)
        name, m = best
        rest = lambda z: z[col].notna() & ~m(z)
        a, b_ = tr[m(tr)], tr[rest(tr)]
        c, d = te[m(te)], te[rest(te)]
        rows.append(dict(indicator=col, bucket=name, n_tr=len(a), R_tr=a.R.mean(), rest_tr=b_.R.mean(),
                         t_tr=welch(a.R, b_.R), n_te=len(c), R_te=c.R.mean(), rest_te=d.R.mean(),
                         t_te=welch(c.R, d.R), usd_te=c.usd.mean()))
    return pd.DataFrame(rows).sort_values("t_tr", ascending=False)


def models(x, split=lab.SPLIT):
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.impute import SimpleImputer
    cols = list(x.columns[7:])
    tr, te = x[x.date < split], x[x.date >= split]
    X = lambda z: z[cols].astype(float).values
    out = []
    for name, mdl in (("boosted trees", HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=150,
                                                                       min_samples_leaf=20, random_state=0)),
                      ("logistic regression", make_pipeline(SimpleImputer(), StandardScaler(),
                                                            LogisticRegression(C=0.1, max_iter=2000)))):
        mdl.fit(X(tr), tr.R.values > 0)
        p_tr, p_te = mdl.predict_proba(X(tr))[:, 1], mdl.predict_proba(X(te))[:, 1]
        cut = np.quantile(p_tr, 2 / 3)
        pick = te[p_te >= cut]
        out.append(f"{name:<20} AUC train {roc_auc_score(tr.R > 0, p_tr):.2f}  test {roc_auc_score(te.R > 0, p_te):.2f}"
                   f"  | TEST trades it likes (top third): n={len(pick)} win {np.mean(pick.R > 0):.0%} "
                   f"{pick.R.mean():+.2f}R ${np.nanmean(pick.usd):+.2f}/trade vs all {te.R.mean():+.2f}R "
                   f"${np.nanmean(te.usd):+.2f}")
    return out


def report(x, label, split=lab.SPLIT):
    tr, te = x[x.date < split], x[x.date >= split]
    print(f"\n===== {label}: {len(x)} hold candles (TRAIN {len(tr)}, TEST {len(te)}) =====")
    print(f"baseline  TRAIN {tr.R.mean():+.2f}R win {np.mean(tr.R > 0):.0%} | TEST {te.R.mean():+.2f}R "
          f"win {np.mean(te.R > 0):.0%} ${np.nanmean(te.usd):+.2f}/trade")
    s = screen(x, split)
    print(f"{'indicator':<22}{'best third on TRAIN':<22}{'n':>5}{'R':>7}{'rest':>7}{'t':>6}   |{'TEST n':>7}"
          f"{'R':>7}{'rest':>7}{'t':>6}{'$/tr':>8}")
    for r in s.itertuples():
        flag = "  <- helps on both" if r.t_tr > 2 and r.t_te > 2 else ""
        print(f"{r.indicator:<22}{r.bucket:<22}{r.n_tr:>5}{r.R_tr:>+7.2f}{r.rest_tr:>+7.2f}{r.t_tr:>+6.1f}   |"
              f"{r.n_te:>7}{r.R_te:>+7.2f}{r.rest_te:>+7.2f}{r.t_te:>+6.1f}{r.usd_te:>+8.2f}{flag}")
    for m in models(x, split):
        print(m)
    return s


def main():
    market_iv.install()
    for tf in (5, 15):
        report(features(tf), f"{tf}-min chart")
    # 1-min: the CFD data starts in June 2026, so TRAIN / TEST here = first / second half of its days.
    # Its volume is the CFD's tick count (a stand-in for exchange volume, which feeds VWAP and volume_x).
    x = features(1, base_loader=S.base_m1, step=1)
    days = np.sort(x.date.unique())
    split = pd.Timestamp(days[len(days) // 2])
    report(x, f"1-min chart ({pd.Timestamp(days[0]):%b %d} - {pd.Timestamp(days[-1]):%b %d}, split {split:%b %d})", split)


if __name__ == "__main__":
    main()

"""Study 23: bounces and rejections off the 200 EMA (the trader's own setup).

The setup, as described with chart examples on 2026-10-09:
  price trending above the 200 EMA pulls back, wicks into it and bounces -> calls;
  price below the 200 EMA rallies up, wicks into it and gets rejected  -> puts.

Definitions (on each chart timeframe, regular-hours bars, EMA carried across days like a chart does):
  touch     the previous M bars all CLOSED on one side of the EMA, and this bar's wick reaches the EMA
            (low <= EMA from above, high >= EMA from below)
  hold      the touch bar closes back on the side it came from (the bounce / rejection candle)
  break     the touch bar closes through the EMA
Trade (base version, before any filters): enter at the hold candle's close, stop 1 cent past its wick, target
2R, otherwise out after 60 minutes (or at 15:55 ET). Stops and targets are checked on 5-min bars (1-min bars for the
1-min chart), stop first when both are inside the same bar. Option P&L: same-day contract, nearest strike whose ask
is <= $0.30, priced at market IV (VIX1D, market_iv.py) with lab.py's bid/ask spread.
Train < 2026-05-01 <= test. 5/15/30-min from data/{SPY,QQQ}_M5.csv; 1-min from Dukascopy index CFDs (see main()).

Run:  python study23_ema200.py
"""
import math
import os
import sys

import numpy as np
import pandas as pd

import lab
import market_iv

SYMS = ["SPY", "QQQ"]
BUDGET = 0.30


def tstat(a):
    a = np.asarray(a, float)
    a = a[~np.isnan(a)]
    return a.mean() / (a.std(ddof=1) / math.sqrt(len(a))) if len(a) > 2 and a.std() > 0 else 0.0


def base_m5(sym):
    df = pd.read_csv(os.path.join(lab.DATA, f"{sym}_M5.csv"), parse_dates=["time_et"])
    df["date"] = df.time_et.dt.normalize()
    df["mod"] = df.time_et.dt.hour * 60 + df.time_et.dt.minute - 570
    df = df[df.groupby("date").time_et.transform("size") == 78]
    df = df.rename(columns={"open": "o", "high": "h", "low": "l", "close": "c", "volume": "v"})
    return df[["date", "mod", "o", "h", "l", "c", "v"]]


DUKA = {"SPY": "USA500IDXUSD", "QQQ": "USATECHIDXUSD"}


def base_m1(sym, ext=False):
    """1-min bars from the Dukascopy index CFD (tools/build_ext_m5.py explains the data), scaled to the ETF's price by
    the previous day's ETF close / CFD 16:00 price. ext=True keeps 4:00-20:00 ET (a chart with extended hours on),
    otherwise 9:30-16:00 only. `mod` = minutes after 9:30 (negative in the premarket)."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
    from build_ext_m5 import minutes
    src = os.path.join(lab.DATA, "dukascopy", DUKA[sym])
    daily = pd.read_csv(os.path.join(lab.DATA, f"{sym}_D.csv"), parse_dates=["date"]).set_index("date").close
    out, ratio = [], None
    for f in sorted(os.listdir(src)):
        day = pd.Timestamp(f[:10])
        if not f.endswith(".bi5") or day < pd.Timestamp("2026-01-01"):
            continue
        m = minutes(os.path.join(src, f), day)
        if m is None:
            continue
        m["mod"] = ((m.time - (day + pd.Timedelta(hours=9, minutes=30))).dt.total_seconds() // 60).astype(int)
        m = m[(m.time.dt.normalize() == day) & (m["mod"] >= (-330 if ext else 0)) & (m["mod"] < (630 if ext else 390))]
        rth = m[(m["mod"] >= 0) & (m["mod"] < 390)]
        if len(rth) < 380:
            continue
        today = daily.get(day) / rth.close.iloc[-1] if day in daily.index else None
        use, ratio = ratio or today, today or ratio
        if not use:
            continue
        m = m.assign(date=day, o=m.open * use, h=m.high * use, l=m.low * use, c=m.close * use, v=m.volume)
        out.append(m[["date", "mod", "o", "h", "l", "c", "v"]])
    return pd.concat(out, ignore_index=True)


def resample(base, tf, step):
    """Chart bars of `tf` minutes from base bars of `step` minutes; `end` = minutes after 9:30 at the bar's close."""
    g = base.assign(slot=base["mod"] // tf).groupby(["date", "slot"], sort=True)
    b = g.agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"), v=("v", "sum"),
              n=("c", "size")).reset_index()
    b = b[b.n >= max(1, tf // step - 1)].reset_index(drop=True)
    b["end"] = (b.slot + 1) * tf
    return b


def events(b, length=200, m=3, warm=3, shift=0.0):
    """Every touch of the EMA after a warm-up of warm*length bars. shift moves the line by that many average bar
    ranges (a placebo line: if the 200 EMA itself matters, touches of shifted lines should behave worse)."""
    o, c, h, l = b.o.values, b.c.values, b.h.values, b.l.values
    e = b.c.ewm(span=length, adjust=False).mean().values
    rng = np.fmax(pd.Series(h - l).rolling(20).mean().values, 1e-4)
    e = e + shift * np.concatenate([[np.nan], rng[:-1]])
    out = []
    for t in range(max(warm * length, m + 20), len(b)):
        above = all(c[t - k] > e[t - k] for k in range(1, m + 1))
        below = all(c[t - k] < e[t - k] for k in range(1, m + 1))
        if above and l[t] <= e[t]:
            side, wick = 1, l[t]
        elif below and h[t] >= e[t]:
            side, wick = -1, h[t]
        else:
            continue
        hold = (c[t] > e[t]) if side > 0 else (c[t] < e[t])
        # how far price had travelled away from the EMA since it last touched it, in average bars
        k = t - 1
        while k > 0 and ((side > 0 and l[k] > e[k]) or (side < 0 and h[k] < e[k])):
            k -= 1
        seg = (h[k + 1:t] - e[k + 1:t]) if side > 0 else (e[k + 1:t] - l[k + 1:t])
        away = seg.max() / rng[t - 1] if len(seg) else 0.0
        out.append(dict(date=b.date[t], end=int(b.end[t]), side=side, hold=hold, entry=c[t], wick=wick, ema=e[t],
                        slope=(e[t] - e[t - 20]) / rng[t - 1] * side, away=away, bars_away=t - 1 - k, rng=rng[t - 1],
                        idx=t, closepos=((c[t] - l[t]) if side > 0 else (h[t] - c[t])) / max(h[t] - l[t], 1e-9),
                        green=(c[t] > o[t]) if side > 0 else (c[t] < o[t]), far=h[t] if side > 0 else l[t]))
    return pd.DataFrame(out)


def walk(base_day, step, ev, target_r=2.0, hold_min=60):
    """Underlying trade from the signal bar's close. Returns (R, exit_px, exit_end_minute, reason)."""
    side, entry = ev.side, ev.entry
    stop = ev.wick - 0.01 * side
    risk = (entry - stop) * side
    if risk <= 0:
        return None
    tgt = entry + target_r * risk * side
    last = min(ev.end + hold_min, 385)
    x = base_day[(base_day["mod"] >= ev.end) & (base_day["mod"] + step <= last)]
    for r in x.itertuples():
        if (side > 0 and r.l <= stop) or (side < 0 and r.h >= stop):
            return -1.0, stop, r.mod + step, "stop"
        if (side > 0 and r.h >= tgt) or (side < 0 and r.l <= tgt):
            return target_r, tgt, r.mod + step, "target"
    if len(x) == 0:
        return None
    px = x.c.values[-1]
    return (px - entry) * side / risk, px, int(x["mod"].values[-1] + step), "time"


def option_usd(day, side, entry_px, entry_end, exit_px, exit_end, scale=1.0):
    """$ result of one same-day contract, ask <= BUDGET at entry. Prices passed at SPY/QQQ scale."""
    kind = "C" if side > 0 else "P"
    i0, i1 = max(0, entry_end // 5 - 1), min(77, max(0, exit_end // 5 - 1))
    t0, t1 = (390 - entry_end) / (390 * 252), max(390 - exit_end, 0.5) / (390 * 252)
    iv0, iv1 = lab.iv_at(day, i0), lab.iv_at(day, i1)
    k = math.ceil(entry_px) if kind == "C" else math.floor(entry_px)
    for _ in range(80):
        mid = lab.bs(entry_px, k, t0, iv0, kind)[0]
        if mid + lab.half_spread(mid, day.sym) <= BUDGET:
            break
        k += 1 if kind == "C" else -1
    if mid < 0.05:
        return np.nan
    paid = mid + lab.half_spread(mid, day.sym)
    val = lab.bs(exit_px, k, t1, iv1, kind)[0]
    return (max(0.0, val - lab.half_spread(val, day.sym)) - paid) * 100


def confirm(base_day, step, tf, ev):
    """Confirmation entry: price must take out the signal candle's high (calls) / low (puts) during the next chart
    bar; entry at that price + 1 cent. Returns the event with entry/end moved, or None if it never triggers."""
    lvl = ev.far + 0.01 * ev.side
    x = base_day[(base_day["mod"] >= ev.end) & (base_day["mod"] < ev.end + tf)]
    for r in x.itertuples():
        if (ev.side > 0 and r.h >= lvl) or (ev.side < 0 and r.l <= lvl):
            return ev._replace(entry=max(lvl, r.o) if ev.side > 0 else min(lvl, r.o), end=int(r.mod + step))
    return None


def build(tf, length=200, target_r=2.0, hold_min=60, base_loader=base_m5, step=5, syms=SYMS, shift=0.0,
          confirmed=False):
    rows = []
    byday = {(d.sym, d.date): d for d in lab.universe(syms)}
    for sym in syms:
        base = base_loader(sym)
        days = dict(tuple(base.groupby("date")))
        ev = events(resample(base, tf, step), length, shift=shift)
        for e in ev.itertuples():
            if e.end > 385 - step or e.end < step:
                continue
            if confirmed:
                e = confirm(days[e.date], step, tf, e)
                if e is None or e.end > 385 - step:
                    continue
            res = walk(days[e.date], step, e, target_r, hold_min)
            if res is None:
                continue
            R, px, xend, why = res
            d = byday.get((sym, e.date))
            usd = option_usd(d, e.side, e.entry, e.end, px, xend) if d is not None else np.nan
            bd = days[e.date]
            fwd = bd[bd["mod"] + step <= min(e.end + 60, 390)].c.values[-1]
            rows.append(dict(sym=sym, tf=tf, **{k: getattr(e, k) for k in ev.columns}, R=R, why=why, usd=usd,
                             fwd=(fwd / e.entry - 1) * e.side * 1e4))
    return pd.DataFrame(rows)


def line(x, label):
    if len(x) == 0:
        return f"{label:<34} n=0"
    tr, te = x[x.date < lab.SPLIT], x[x.date >= lab.SPLIT]

    def part(y):
        if len(y) == 0:
            return f"{'n=0':>38}"
        return (f"n={len(y):4d} win {np.mean(y.R > 0):4.0%} {y.R.mean():+.2f}R t{tstat(y.R):+5.1f} "
                f"${np.nanmean(y.usd):+6.2f}")

    return f"{label:<34} TRAIN {part(tr)} | TEST {part(te)}"


def main():
    market_iv.install()
    m1_ext = lambda sym: base_m1(sym, ext=True)
    charts = [(30, base_m5, 5, "30-min"), (15, base_m5, 5, "15-min"), (5, base_m5, 5, "5-min"),
              (1, base_m1, 1, "1-min (EMA on regular hours)"), (1, m1_ext, 1, "1-min (EMA with extended hours)")]
    for tf, loader, step, name in charts:
        x = build(tf, base_loader=loader, step=step)
        x = x[(x.end >= 15) & (x.end <= 330)]  # entries 8:45-14:00 CT
        days = x.date.nunique()
        print(f"\n===== {name} chart: {len(x)} touches of the 200 EMA on {days} days "
              f"({len(x) / days / len(SYMS):.1f} per symbol-day), {x.hold.mean():.0%} closed back = hold =====")
        h = x[x.hold]
        for side, nm in ((1, "bounce from above (calls)"), (-1, "rejection from below (puts)")):
            print(line(h[h.side == side], nm))
        print(line(h, "all holds"))
        if tf in (5, 15):
            print(line(build(tf, confirmed=True).query("hold and 15 <= end <= 330"), "all holds, confirmation entry"))
        print("  is the 200 special?  hold rate / avg R of holds / next-hour move after a hold (bp):")
        for label, kw in (("EMA 100", dict(length=100)), ("EMA 200", {}), ("EMA 300", dict(length=300)),
                          ("fake line 1/2 bar below the 200", dict(shift=-0.5)),
                          ("fake line 1/2 bar above the 200", dict(shift=0.5))):
            y = build(tf, base_loader=loader, step=step, **kw).query("15 <= end <= 330")
            hh = y[y.hold]
            print(f"    {label:<34} hold {y.hold.mean():4.0%}   {hh.R.mean():+.2f}R   {hh.fwd.mean():+5.1f}bp"
                  f" (t {tstat(hh.fwd):+.1f})")


if __name__ == "__main__":
    main()

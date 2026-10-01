"""Study 13: the user's premarket fair-value-gap (FVG) idea (2026-10-01).

Rules as coded:
  gap     15-min PREMARKET candles 4:00-9:15 ET. Bullish FVG: high[c1] < low[c3] (zone high[c1]..low[c3]);
          bearish FVG: low[c1] > high[c3] (zone high[c3]..low[c1]). The most recent one whose 3rd candle closes by
          9:15 ET is used (variant: the largest).
  entry   5-min RTH candles 9:30-10:30 ET, first event wins:
            push   - a close above the zone -> call, a close below the zone -> put
            reject - the candle tags the zone from below and closes below it -> put (from above, closes above -> call)
  exits   quick: next floor pivot = take profit; a close back through the zone's far side = out; out by 11:30 ET.
          guardian: the live Trade Guardian's stops.
Same-day ~$0.50 option, lab.py pricing (IV x1.15). Data: Nov 2025 - Sep 2026 (premarket bars from Webull).

Run:  python study13_fvg.py
"""
import os
import numpy as np, pandas as pd
import lab, study11_september as S, study12_clint_orb as C

D = os.path.join(os.path.dirname(__file__), "..", "data")
SYMS = ["QQQ", "SPY", "IWM"]


def fvgs(pre):
    out = []
    b = pre.reset_index(drop=True)
    for k in range(2, len(b)):
        t3 = b.time_et[k]
        if t3.strftime("%H:%M") > "09:00":  # 3rd candle must close by 9:15
            continue
        h1, l1, h3, l3 = b.high[k - 2], b.low[k - 2], b.high[k], b.low[k]
        if h1 < l3:
            out.append(("bull", h1, l3, t3))
        elif l1 > h3:
            out.append(("bear", h3, l1, t3))
    return out


def signal(d, zone, mode):
    lo, hi = zone
    for i in range(0, 12):
        o, h, l, c = d.o[i], d.h[i], d.l[i], d.c[i]
        if mode in ("both", "push"):
            if c > hi and (i == 0 and d.o[0] <= hi or i > 0 and d.c[i - 1] <= hi):
                return i, "C", "push"
            if c < lo and (i == 0 and d.o[0] >= lo or i > 0 and d.c[i - 1] >= lo):
                return i, "P", "push"
        if mode in ("both", "reject"):
            if h >= lo and c < lo and (i == 0 and d.o[0] < lo or i > 0 and d.c[i - 1] < lo):
                return i, "P", "reject"
            if l <= hi and c > hi and (i == 0 and d.o[0] > hi or i > 0 and d.c[i - 1] > hi):
                return i, "C", "reject"
    return None


def quick_exit(d, i, kind, zone):
    pick = lab.choose_contract(d, i, kind, 0.50)
    if not pick:
        return None
    k, mid, _ = pick
    entry = mid + lab.half_spread(mid, d.sym)
    piv = C.pivots(d)
    e = d.c[i]
    tgt = next((p for p in piv if p > e + 0.05), None) if kind == "C" else next((p for p in piv[::-1] if p < e - 0.05), None)
    lo, hi = zone
    for j in range(i + 1, 36):
        if tgt is not None and ((kind == "C" and d.h[j] >= tgt) or (kind == "P" and d.l[j] <= tgt)):
            return (S.opt_px(d, j, tgt, k, kind) - entry) * 100
        if (kind == "C" and d.c[j] < lo) or (kind == "P" and d.c[j] > hi):
            return (S.opt_px(d, j, d.c[j], k, kind) - entry) * 100
        if j >= max(23, i + 6):
            return (S.opt_px(d, j, d.c[j], k, kind) - entry) * 100


def main():
    rows = []
    for sym in SYMS:
        pre = pd.read_csv(os.path.join(D, f"{sym}_PRE_M15.csv"), parse_dates=["time_et"])
        pre["date"] = pre.time_et.dt.normalize()
        bydate = {k: g for k, g in pre.groupby("date")}
        for d in lab.universe([sym]):
            g = bydate.get(d.date)
            if g is None or len(g) < 6:
                continue
            fs = fvgs(g)
            if not fs:
                rows.append(dict(sym=sym, date=d.date, has=False))
                continue
            for pick in ("latest", "largest"):
                f = fs[-1] if pick == "latest" else max(fs, key=lambda x: x[2] - x[1])
                zone = (f[1], f[2])
                for mode in ("both", "push", "reject"):
                    s = signal(d, zone, mode)
                    if not s:
                        continue
                    i, kind, how = s
                    q = quick_exit(d, i, kind, zone)
                    g_ = S.trade(d, i, kind)
                    if q is None or g_ is None:
                        continue
                    j = min(i + 12, 77)
                    f1h = (d.c[j] / d.c[i] - 1) * (1 if kind == "C" else -1) * 1e4
                    rows.append(dict(sym=sym, date=d.date, has=True, pick=pick, mode=mode, how=how, kind=kind,
                                     ftype=f[0], q=q, g=g_, f1h=f1h, size=(f[2] - f[1]) / d.o[0] * 1e4))
    df = pd.DataFrame(rows)
    days = df.groupby(["sym", "date"]).size().shape[0]
    print(f"days with premarket data: {days}; days with an FVG: {df[df.has].groupby(['sym','date']).size().shape[0]}")
    t = df[df.has]
    t["per"] = np.where(t.date >= pd.Timestamp("2026-06-01"), "Jun-Sep", "Nov-May")
    print(f"\n{'FVG':<8}{'entry':<8}{'period':<9}{'n':>4}{'win':>6}{'quick $':>9}{'guardian $':>11}{'right 1h':>10}{'1h bps':>8}")
    for (pick, mode), x in t.groupby(["pick", "mode"]):
        for per, y in list(x.groupby("per")) + [("ALL", x)]:
            print(f"{pick:<8}{mode:<8}{per:<9}{len(y):>4}{(y.q>0).mean():>6.0%}{y.q.mean():>+9.2f}{y.g.mean():>+11.2f}"
                  f"{(y.f1h>0).mean():>10.0%}{y.f1h.mean():>+8.1f}")
    x = t[(t.pick == "latest") & (t.mode == "both")]
    print("\nlatest/both split by event and FVG type:")
    print(x.groupby(["how", "ftype", "kind"]).agg(n=("q", "size"), quick=("q", "mean"), right1h=("f1h", lambda s: (s > 0).mean())).round(2))
    return t


if __name__ == "__main__":
    main()


def filtered(min_bps=10, start="08:00", need_vol=True, need_rsi=True, modes=("push",)):
    """Late, large premarket FVG + the opening-range checks (volume, RSI zone) on the entry candle."""
    rows = []
    for sym in SYMS:
        pre = pd.read_csv(os.path.join(D, f"{sym}_PRE_M15.csv"), parse_dates=["time_et"])
        pre["date"] = pre.time_et.dt.normalize()
        bydate = {k: g for k, g in pre.groupby("date")}
        days = sorted(lab.universe([sym]), key=lambda x: x.date)
        for prev, d in zip(days[:-1], days[1:]):
            g = bydate.get(d.date)
            if g is None or len(g) < 6:
                continue
            fs = [f for f in fvgs(g) if f[3].strftime("%H:%M") >= start and (f[2] - f[1]) / d.o[0] * 1e4 >= min_bps]
            if not fs:
                continue
            f = max(fs, key=lambda x: x[2] - x[1])
            zone = (f[1], f[2])
            r = S.rsi(np.concatenate([prev.c, d.c]))[len(prev.c):]
            for mode in modes:
                s = signal(d, zone, mode)
                if not s:
                    continue
                i, kind, how = s
                up = kind == "C"
                vol_ok = d.v[i] > d.avgvol20[i] and (i == 0 or d.v[i] > d.v[i - 1])
                rsi_ok = (50 < r[i] < 70 and r[i] > r[i - 1]) if up else (30 < r[i] < 50 and r[i] < r[i - 1])
                if (need_vol and not vol_ok) or (need_rsi and not rsi_ok):
                    continue
                q = quick_exit(d, i, kind, zone)
                g_ = S.trade(d, i, kind)
                if q is None or g_ is None:
                    continue
                j = min(i + 12, 77)
                rows.append(dict(sym=sym, date=d.date, mode=mode, kind=kind, i=i, q=q, g=g_, zlo=zone[0], zhi=zone[1],
                                 ftime=f[3], f1h=(d.c[j] / d.c[i] - 1) * (1 if up else -1) * 1e4))
    return pd.DataFrame(rows)


def bias(entry="first", agree_type=True):
    """Bias version: where the 9:30 open sits vs the latest premarket FVG sets the direction.
    entry=first -> trade at the first 5-min close; entry=orb -> wait for an opening-range break in that direction."""
    rows = []
    for sym in SYMS:
        pre = pd.read_csv(os.path.join(D, f"{sym}_PRE_M15.csv"), parse_dates=["time_et"])
        pre["date"] = pre.time_et.dt.normalize()
        bydate = {k: g for k, g in pre.groupby("date")}
        for d in lab.universe([sym]):
            g = bydate.get(d.date)
            if g is None:
                continue
            fs = fvgs(g)
            if not fs:
                continue
            t, lo, hi, _ = fs[-1]
            if d.o[0] > hi and (t == "bull" or not agree_type):
                kind = "C"
            elif d.o[0] < lo and (t == "bear" or not agree_type):
                kind = "P"
            else:
                continue
            if entry == "first":
                i = 0
            else:
                oh, ol = d.h[:3].max(), d.l[:3].min()
                i = next((k for k in range(3, 24) if (d.c[k] > oh if kind == "C" else d.c[k] < ol)), None)
                if i is None:
                    continue
            q = quick_exit(d, i, kind, (lo, hi))
            g_ = S.trade(d, i, kind)
            if q is None or g_ is None:
                continue
            j = min(i + 12, 77)
            rows.append(dict(sym=sym, date=d.date, kind=kind, q=q, g=g_,
                             f1h=(d.c[j] / d.c[i] - 1) * (1 if kind == "C" else -1) * 1e4))
    return pd.DataFrame(rows)

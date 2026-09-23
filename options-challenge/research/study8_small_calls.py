"""Step 8: RSI(2) signal with long calls that fit a small budget (Options Level 2, no spreads).

For each signal buy the nearest-the-money call whose ask x 100 <= budget (walking OTM if needed,
skip if delta < min_delta), expiry `dte` trading days out, sell at the signal exit or expiry.
"""
import math
import sys

import numpy as np
import pandas as pd

import study5_daily as s5
import study6_rsi2_options as s6

BIG = ["SPY", "QQQ", "IWM"]
CHEAP = ["XLF", "EEM", "XLE", "KRE", "XLU", "XLI", "SLV", "GDX", "TLT", "HYG"]


def step(px):
    return 0.5 if px < 50 else 1.0


def delta_call(s, k, t, iv):
    sd = iv * math.sqrt(max(t, 1e-6))
    return s6.ncdf((math.log(s / k) + 0.5 * sd * sd) / sd)


def run(syms, budget, dte, ivr, min_delta=0.2, thr=10):
    out = []
    for sym in syms:
        df = s5.load(sym)
        df["rsi2"] = np.where(df.rsi2 < thr, 0, 50)
        c, rv = df.close.values, df.rv20.values
        for d0, _, held, ret, i, j in s5.trades(df, "rsi2"):
            j = min(j, i + dte)
            s0, s1 = c[i], c[j]
            t0, t1 = dte / 252, (dte - (j - i)) / 252
            iv0, iv1 = rv[i] * ivr, rv[j] * ivr
            st = step(s0)
            k = math.ceil(s0 / st) * st
            pick = None
            for _ in range(30):
                mid = s6.bs(s0, k, t0, iv0, "C")
                ask = mid + s6.hs(mid)
                if ask * 100 <= budget:
                    if delta_call(s0, k, t0, iv0) >= min_delta and mid >= 0.05:
                        pick = (k, ask, delta_call(s0, k, t0, iv0))
                    break
                k += st
            if not pick:
                continue
            k, ask, dl = pick
            mid1 = s6.bs(s1, k, t1, iv1, "C")
            bid1 = max(mid1 - s6.hs(mid1), 0)
            out.append(dict(sym=sym, date=d0, und=ret, k=k, delta=dl, cost=ask * 100,
                            pnl=(bid1 - ask) * 100, ret=bid1 / ask - 1))
    return pd.DataFrame(out)


def fmt(x):
    if len(x) < 3:
        return f"n={len(x):3d}"
    t = x.ret.mean() / x.ret.std(ddof=1) * math.sqrt(len(x))
    return (f"n={len(x):3d} win {np.mean(x.ret > 0):4.0%} avg {x.ret.mean():+6.1%} t {t:+5.2f} "
            f"cost ${x.cost.mean():3.0f} d {x.delta.mean():.2f}")


if __name__ == "__main__":
    print("Underlying only (RSI2<10 & >SMA200), cheap ETFs:")
    for s in CHEAP:
        ts = s5.trades(s5.load(s), "rsi2")
        tr = np.array([t[3] for t in ts if t[0] < s5.SPLIT])
        te = np.array([t[3] for t in ts if t[0] >= s5.SPLIT])
        f = lambda a: f"n={len(a):2d} win {np.mean(a > 0):4.0%} avg {a.mean():+6.2%}" if len(a) else "n= 0"
        print(f"  {s:<4} TRAIN {f(tr)} | TEST {f(te)}")
    print()
    for ivr in (1.1, 1.3, 1.5):
        print(f"=== IV {ivr}x realised ===")
        for group, syms in (("BIG", BIG), ("CHEAP", CHEAP)):
            for budget in (100, 150):
                for dte in (5, 10, 15):
                    df = run(syms, budget, dte, ivr)
                    tr, te = df[df.date < s5.SPLIT], df[df.date >= s5.SPLIT]
                    print(f"{group:<5} ${budget} dte={dte:2d} | TRAIN {fmt(tr)} | TEST {fmt(te)}")
        print()

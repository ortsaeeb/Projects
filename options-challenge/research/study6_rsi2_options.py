"""Step 6: express the RSI(2) pullback signal with options on SPY / QQQ / IWM.

Entry at the signal day's close, exit at the signal's exit-day close (1-5 trading days).
Options priced with Black-Scholes, IV = 20-day realised vol x IVR (sensitivity), 1% half-spread per
leg (x0.7 for spreads, min $0.01). Expiry = N trading days after entry.

Structures (per 1 contract / spread):
  call       long nearest-money call
  cds_w      call debit spread: long nearest-money call, short call w dollars higher
  pcs_w      bull put credit spread: short put at nearest strike below spot, long put w dollars lower
Return = P/L / capital at risk (debit paid, or width - credit for credit spreads).
"""
import math
import sys

import numpy as np
import pandas as pd

import study5_daily as s5

SQ2 = math.sqrt(2)


def ncdf(x):
    return 0.5 * (1 + math.erf(x / SQ2))


def bs(s, k, t, iv, kind):
    t = max(t, 1e-6)
    sd = iv * math.sqrt(t)
    d1 = (math.log(s / k) + 0.5 * sd * sd) / sd
    d2 = d1 - sd
    if kind == "C":
        return s * ncdf(d1) - k * ncdf(d2)
    return k * ncdf(-d2) - s * ncdf(-d1)


def hs(p):
    return max(0.01, 0.01 * p)


def price(legs, s, t, iv, sign):
    """sign=+1 buying the structure (pay ask), -1 selling it (receive bid). Returns net debit."""
    mid = sum(q * bs(s, k, t, iv, kd) for k, kd, q in legs)
    cost = sum(abs(q) * hs(bs(s, k, t, iv, kd)) for k, kd, q in legs) * (0.7 if len(legs) > 1 else 1)
    return mid + sign * cost


def run(structure, w, ivr, dte, syms=("SPY", "QQQ", "IWM"), thr=10, trend=True):
    out = []
    for sym in syms:
        df = s5.load(sym)
        if not trend:
            df["sma200"] = 0
        df["rsi2"] = np.where(df.rsi2 < thr, 0, 50)
        c = df.close.values
        rv = df.rv20.values
        for d0, direction, held, ret, i, j in s5.trades(df, "rsi2"):
            j = min(j, i + dte)  # position is closed at expiry if the signal hasn't exited by then
            s0, s1 = c[i], c[j]
            iv0, iv1 = rv[i] * ivr, rv[j] * ivr
            t0, t1 = dte / 252, (dte - (j - i)) / 252
            if structure == "call":
                legs = [(math.ceil(s0), "C", 1)]
            elif structure == "cds":
                legs = [(math.ceil(s0), "C", 1), (math.ceil(s0) + w, "C", -1)]
            else:  # pcs: short put below spot, long put w lower -> this is a credit (negative debit)
                k = math.floor(s0)
                legs = [(k, "P", -1), (k - w, "P", 1)]
            debit = price(legs, s0, t0, iv0, +1)    # enter legs as listed (negative = credit received)
            value = price(legs, s1, t1, iv1, -1)    # exit: close the same legs at the bid side
            pnl = value - debit
            risk = w + debit if structure == "pcs" else debit
            out.append(dict(sym=sym, date=d0, held=j - i, und=ret, pnl=pnl * 100, risk=risk * 100, ret=pnl / risk))
    return pd.DataFrame(out)


def summary(df):
    tr, te = df[df.date < s5.SPLIT], df[df.date >= s5.SPLIT]

    def f(x):
        if len(x) < 3:
            return "n/a"
        t = x.ret.mean() / x.ret.std(ddof=1) * math.sqrt(len(x))
        return (f"n={len(x):3d} win {np.mean(x.ret > 0):4.0%} avg {x.ret.mean():+6.1%} t {t:+5.2f} "
                f"risk ${x.risk.mean():5.0f} worst {x.ret.min():+5.0%}")
    return f"TRAIN {f(tr)} | TEST {f(te)}"


if __name__ == "__main__":
    for ivr in (1.1, 1.3, 1.5):
        print(f"=== IV = {ivr} x 20-day realised vol ===")
        for dte in (5, 10):
            for structure, w in (("call", 0), ("cds", 2), ("cds", 5), ("pcs", 2), ("pcs", 5)):
                df = run(structure, w, ivr, dte)
                print(f"{structure:<4} w={w} dte={dte:2d} | {summary(df)}")
        print()

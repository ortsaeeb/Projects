"""Study 14c: re-price the sweep model's same-day options with the market's own 1-day implied vol (Cboe VIX1D)
instead of lab.py's model IV.

VIX1D (data/VIX1D_cboe.csv) is the S&P 500's 1-day implied vol, annualised on a 365-day clock. Its variance over
1 day matched SPY's realised 10:00-16:00 variance (ratio 1.00, 246 days), so it is used as the session's IV,
converted to lab.py's trading-time clock (x sqrt(252/365)) and moved linearly from its open to its close through the
day. VIX1D is the S&P's; QQQ and IWM normally carry higher IV, so the 3-ETF line is optimistic and SPY is the
cleaner check.

Run:  python study14c_real_iv.py
"""
import math
import os

import pandas as pd

import lab

V1 = pd.read_csv(os.path.join(os.path.dirname(__file__), "..", "data", "VIX1D_cboe.csv"),
                 parse_dates=["DATE"]).set_index("DATE")


def iv_vix1d(day, i, mult=1.0):
    r = V1.loc[day.date]
    return (r.OPEN + (r.CLOSE - r.OPEN) * (i + 1) / 78) / 100 * math.sqrt(252 / 365) * mult


def main():
    import study14_ict_search as S
    import study14b_sweep_model as B
    model_sd, vix_sd = [], []
    for d in lab.universe(["SPY"]):
        model_sd.append(lab.iv_at(d, 5))
        vix_sd.append(iv_vix1d(d, 5))
    print(f"SPY at 10:00 ET: model IV median {pd.Series(model_sd).median():.3f}, "
          f"VIX1D-based IV median {pd.Series(vix_sd).median():.3f}")
    for mult in (1.0, 1.2):
        lab.iv_at = lambda d, i, m=mult: iv_vix1d(d, i, m)
        for syms in (["SPY"], S.ETF):
            for budget in (0.30, 0.60):
                B.BUDGET = budget
                e, _ = B.run(syms)
                e = e.dropna(subset=["usd"])
                a, t = e[e.date < S.SPLIT], e[e.date >= S.SPLIT]
                print(f"IV = VIX1D x{mult}  {'/'.join(syms):<12} ${budget:.2f}: TRAIN n={len(a)} ${a.usd.mean():+.2f} "
                      f"win {(a.usd > 0).mean():.0%} | TEST n={len(t)} ${t.usd.mean():+.2f} win {(t.usd > 0).mean():.0%}")


if __name__ == "__main__":
    main()

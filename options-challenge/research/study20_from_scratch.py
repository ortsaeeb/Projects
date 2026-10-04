"""Study 20: a SPY/QQQ strategy built from scratch, from price behaviour alone (no borrowed indicators or setups).

Every 5-min bar close from 9:50 to 15:00 ET (8:50-14:00 CT) is a decision point, described only by what the chart
shows at that moment (no volume, so the same rules can be checked on the volume-less 2023-25 index data):
  tod      bar index (time of day)
  gap_z    today's open vs yesterday's close          } in units of the day's expected move,
  day_z    now vs yesterday's close                   } sd = VIX1D-implied session move (QQQ x VXN/VIX),
  open_z   now vs today's open                        } known at the open
  m3/m6/m12  the last 15 / 30 / 60 minutes, in units of the expected move over that many minutes
  rpos     where price sits in today's range so far (0 = at the low, 1 = at the high)
  pdpos    where price sits vs yesterday's range (0 = yesterday's low, 1 = yesterday's high)
  hi_z/lo_z  distance below today's high / above today's low so far
  act      how active the day has been: realised move so far / the move the options market expected so far
What happened next: f12 = next-hour return in expected-move units; and the $ result of buying a same-day call or put
at that bar (market IV, market_iv.py), sold 1 hour later.

Discovery: Sep 2025 - Apr 2026 (find), May - Sep 2026 (must repeat). Holdout: May 2023 - Aug 2025 (index-CFD bars).
"""
import math
import os

import numpy as np
import pandas as pd

import lab
import market_iv
import study11_september as S11

OUT = os.path.join(os.path.dirname(__file__), "out")
FIRST, LAST_SIG, HOLD = 3, 65, 12


def session_sd(d):
    r = market_iv.V1D.OPEN.get(d.date)
    if r is None or r != r:
        return None
    sd = r / 100 * math.sqrt(1 / 365)
    if d.sym in market_iv.RATIO:
        q = market_iv.RATIO[d.sym].get(d.date)
        sd *= q if q == q and q is not None else 1.3
    return sd


def opt_1h(d, i, kind, budget=0.50):
    pick = lab.choose_contract(d, i, kind, budget)
    if not pick:
        return np.nan
    k, mid, _ = pick
    entry = mid + lab.half_spread(mid, d.sym)
    j = min(i + HOLD, S11.FLAT)
    return (S11.opt_px(d, j, d.c[j], k, kind) - entry) * 100


def build(days, with_options=True):
    rows = []
    for d in days:
        sd = session_sd(d)
        if not sd:
            continue
        lc = np.log(d.c)
        r5 = np.diff(np.log(np.concatenate([[d.o[0]], d.c])))
        prof = market_iv._profile.get(d.sym)
        share = 1 - (prof ** 2) * ((lab.BARS - 1 - np.arange(lab.BARS)) / lab.BARS) if prof is not None else None
        hi = np.maximum.accumulate(d.h)
        lo = np.minimum.accumulate(d.l)
        pdr = d.prev_high - d.prev_low
        for i in range(FIRST, LAST_SIG + 1):
            j = min(i + HOLD, 76)
            so_far = share[i] if share is not None else (i + 1) / lab.BARS
            row = dict(sym=d.sym, date=d.date, tod=i,
                       gap_z=math.log(d.o[0] / d.prev_close) / sd,
                       day_z=(lc[i] - math.log(d.prev_close)) / sd,
                       open_z=(lc[i] - math.log(d.o[0])) / sd,
                       m3=(lc[i] - lc[i - 3]) / (sd * math.sqrt(3 / 78)),
                       m6=(lc[i] - lc[max(i - 6, 0)]) / (sd * math.sqrt(min(6, i) / 78)),
                       m12=(lc[i] - lc[max(i - 12, 0)]) / (sd * math.sqrt(max(min(12, i), 1) / 78)),
                       rpos=(d.c[i] - lo[i]) / (hi[i] - lo[i]) if hi[i] > lo[i] else 0.5,
                       pdpos=(d.c[i] - d.prev_low) / pdr if pdr > 0 else 0.5,
                       hi_z=math.log(hi[i] / d.c[i]) / sd, lo_z=math.log(d.c[i] / lo[i]) / sd,
                       act=math.sqrt(np.sum(r5[:i + 1] ** 2) / max(so_far, 1e-6)) / sd,
                       f12=(lc[j] - lc[i]) / (sd * math.sqrt((j - i) / 78)), f12_raw=lc[j] - lc[i])
            if with_options:
                row["call"] = opt_1h(d, i, "C")
                row["put"] = opt_1h(d, i, "P")
            rows.append(row)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    market_iv.install(1.0)
    for s in ("SPY", "QQQ"):
        market_iv.clock_factor(s, 0)
    df = build(lab.universe(["SPY", "QQQ"]))
    df.to_parquet(os.path.join(OUT, "study20_real.parquet")) if hasattr(df, "to_parquet") else None
    df.to_csv(os.path.join(OUT, "study20_real.csv"), index=False)
    print(len(df), "decision points;", df.date.nunique(), "days")

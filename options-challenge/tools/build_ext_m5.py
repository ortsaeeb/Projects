"""Turn Dukascopy 1-minute index-CFD candles (data/dukascopy/) into 5-minute regular-session bars at SPY / QQQ scale,
in the same format as data/SPY_M5.csv, written to data/ext/<SYM>_M5.csv.

  S&P 500 CFD (USA500IDXUSD)    -> SPY scale    Nasdaq-100 CFD (USATECHIDXUSD) -> QQQ scale
  scale = the ETF's previous daily close / the CFD's previous 16:00 ET price (only sets the price level, so strikes
          are spaced like the ETF's; the intraday path is the CFD's own)
  volume = the CFD's tick volume x 1e6: NOT exchange volume, so volume / VWAP rules can't be tested on this data.

Run:  python tools/build_ext_m5.py
"""
import lzma
import os
import struct
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
ET = ZoneInfo("America/New_York")
PAIRS = {"SPY": "USA500IDXUSD", "QQQ": "USATECHIDXUSD"}


def minutes(path, day):
    blob = open(path, "rb").read()
    if not blob:
        return None
    raw = lzma.decompress(blob, format=lzma.FORMAT_ALONE)
    rec = np.frombuffer(raw, dtype=">i4").reshape(-1, 6)
    sec = rec[:, 0].astype(np.int64)
    px = rec[:, 1:5].astype(float) / 1000.0  # open, close, low, high
    vol = np.frombuffer(raw, dtype=">f4").reshape(-1, 6)[:, 5].astype(float)
    t0 = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    et = [(t0 + timedelta(seconds=int(s))).astimezone(ET) for s in sec]
    df = pd.DataFrame(dict(time=[e.replace(tzinfo=None) for e in et], open=px[:, 0], close=px[:, 1], low=px[:, 2],
                           high=px[:, 3], volume=vol))
    return df


def build(sym):
    src = os.path.join(ROOT, "data", "dukascopy", PAIRS[sym])
    daily = pd.read_csv(os.path.join(ROOT, "data", f"{sym}_D.csv"), parse_dates=["date"]).set_index("date").close
    rows, prev_ratio = [], None
    for f in sorted(os.listdir(src)):
        if not f.endswith(".bi5"):
            continue
        day = pd.Timestamp(f[:10])
        m = minutes(os.path.join(src, f), day)
        if m is None:
            continue
        s = pd.Timestamp(day.date()) + pd.Timedelta(hours=9, minutes=30)
        rth = m[(m.time >= s) & (m.time < s + pd.Timedelta(hours=6, minutes=30))].copy()
        if len(rth) < 380:  # half days and gaps in the feed are skipped (lab.py also needs 78 bars)
            continue
        rth["slot"] = ((rth.time - s).dt.total_seconds() // 300).astype(int)
        g = rth.groupby("slot").agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
                                    close=("close", "last"), volume=("volume", "sum"))
        if len(g) != 78:
            continue
        ratio = daily.get(day) / g.close.iloc[-1] if day in daily.index else None
        use = prev_ratio if prev_ratio else ratio
        prev_ratio = ratio or prev_ratio
        if not use:
            continue
        g[["open", "high", "low", "close"]] *= use
        g["volume"] = (g.volume * 1e6).round().astype(int)
        g["time_et"] = [(s + pd.Timedelta(minutes=5 * k)).strftime("%Y-%m-%d %H:%M") for k in g.index]
        rows.append(g[["time_et", "open", "high", "low", "close", "volume"]])
    out = pd.concat(rows)
    os.makedirs(os.path.join(ROOT, "data", "ext"), exist_ok=True)
    out.round(4).to_csv(os.path.join(ROOT, "data", "ext", f"{sym}_M5.csv"), index=False)
    print(f"{sym}: {len(rows)} days, {out.time_et.iloc[0][:10]} .. {out.time_et.iloc[-1][:10]}")


if __name__ == "__main__":
    for s in PAIRS:
        if os.path.isdir(os.path.join(ROOT, "data", "dukascopy", PAIRS[s])):
            build(s)

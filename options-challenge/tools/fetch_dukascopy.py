"""Download Dukascopy 1-minute BID candles for the S&P 500 / Nasdaq-100 index CFDs (free public datafeed) and save
one compressed .bi5 per UTC day under data/dukascopy/<SYMBOL>/YYYY-MM-DD.bi5.

  python tools/fetch_dukascopy.py 2023-05-01 2025-08-29 2025-09-02 2025-10-03
      (newest day first back to the start, after the optional check window; trading days from data/SPY_D.csv)

Polite: one request at a time, ~1 s apart, long back-off on HTTP 429. Re-running skips files already saved.
"""
import os
import subprocess
import sys
import time

import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
SYMS = {"USA500IDXUSD": "SPX", "USATECHIDXUSD": "NDX"}
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Referer": "https://www.dukascopy.com/"}


def fetch(sym, day, path):
    """curl gets through where urllib is throttled; returns the HTTP status."""
    url = (f"https://datafeed.dukascopy.com/datafeed/{sym}/{day.year}/{day.month - 1:02d}/{day.day:02d}/"
           f"BID_candles_min_1.bi5")
    for attempt in range(6):
        r = subprocess.run(["curl", "-sS", "-m", "30", "-A", UA["User-Agent"], "-H", f"Referer: {UA['Referer']}",
                            "-o", path + ".part", "-w", "%{http_code}", url], capture_output=True, text=True)
        code = r.stdout.strip()
        if code == "200":
            os.replace(path + ".part", path)
            return code
        if code == "404":
            open(path, "wb").close()
            return code
        time.sleep(60 * (attempt + 1) if code == "429" else 5 * (attempt + 1))
    raise RuntimeError(f"gave up on {url} (last status {code})")


def main(start, end, check_start=None, check_end=None):
    """Most useful first: an optional overlap window (to check the CFD bars against real SPY/QQQ bars), then every
    day from `end` back to `start`, both symbols per day, so any stopping point leaves a clean recent block."""
    days = pd.read_csv(os.path.join(ROOT, "data", "SPY_D.csv"), parse_dates=["date"]).date
    order = []
    if check_start:
        order += [d for d in days if pd.Timestamp(check_start) <= d <= pd.Timestamp(check_end)]
    order += [d for d in reversed(list(days)) if pd.Timestamp(start) <= d <= pd.Timestamp(end)]
    code = "-"
    for n, d in enumerate(order):
        for sym in SYMS:
            out = os.path.join(ROOT, "data", "dukascopy", sym)
            os.makedirs(out, exist_ok=True)
            path = os.path.join(out, f"{d:%Y-%m-%d}.bi5")
            if os.path.exists(path):
                continue
            code = fetch(sym, d, path)
            time.sleep(0.5)
        if n % 20 == 0:
            print(f"{d:%Y-%m-%d} ({n + 1}/{len(order)} days) HTTP {code}", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:5])

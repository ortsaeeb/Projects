"""Download daily (or other interval) candles for crypto pairs from Binance's public market-data API
(data-api.binance.vision, no key needed) into data/crypto/<COIN>_<interval>.csv.

  python tools/fetch_crypto.py 1d DOGE SHIB PEPE ...

Prices are in USDT (a dollar stablecoin). Only coins listed on Binance appear here, i.e. memecoins that already
became big enough to list: the many that died before listing are missing (survivorship bias, noted in the study).
"""
import json
import os
import sys
import time
import urllib.request

import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
URL = "https://data-api.binance.vision/api/v3/klines?symbol={s}USDT&interval={i}&limit=1000&startTime={t}"


def fetch(coin, interval):
    rows, start = [], 0
    while True:
        req = urllib.request.Request(URL.format(s=coin, i=interval, t=start), headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            batch = json.loads(r.read())
        if not isinstance(batch, list) or not batch:
            break
        rows += batch
        if len(batch) < 1000:
            break
        start = batch[-1][0] + 1
        time.sleep(0.2)
    df = pd.DataFrame(rows, columns=["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume",
                                     "trades", "tb_base", "tb_quote", "ignore"])
    df["date"] = pd.to_datetime(df.open_time, unit="ms")
    for c in ("open", "high", "low", "close", "volume", "quote_volume"):
        df[c] = df[c].astype(float)
    return df[["date", "open", "high", "low", "close", "volume", "quote_volume", "trades"]]


if __name__ == "__main__":
    interval, coins = sys.argv[1], sys.argv[2:]
    for c in coins:
        try:
            df = fetch(c, interval)
        except Exception as e:
            print(f"{c}: failed ({e})")
            continue
        if df.empty:
            print(f"{c}: not listed")
            continue
        df.to_csv(os.path.join(ROOT, "data", "crypto", f"{c}_{interval}.csv"), index=False)
        print(f"{c}: {len(df)} bars {df.date.iloc[0]:%Y-%m-%d} .. {df.date.iloc[-1]:%Y-%m-%d}")

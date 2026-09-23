"""RSI(2) pullback scanner for SPY / QQQ / IWM.

Usage:
    python rsi2_scan.py [live_prices]      e.g.  python rsi2_scan.py SPY=761.2,QQQ=730.5

Reads data/{SYM}_D.csv (Webull daily bars). If live prices are given (run ~15:45 ET),
today's close is replaced by the live price so the signal can be acted on before the bell.

ENTRY  RSI(2) < 10  and  close > 200-day SMA
EXIT   close > 5-day SMA, or the spread's expiry (5 trading days), whichever first
TRADE  bull put credit spread: short put at the first strike below price, long put `width` lower,
       expiry ~5 trading days out
"""
import math
import os
import sys

import pandas as pd

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def rsi2(close):
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=0.5, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=0.5, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)


def width_for(equity):
    return 1 if equity < 250 else 2 if equity < 600 else 5


def main():
    live = {}
    if len(sys.argv) > 1:
        for kv in sys.argv[1].split(","):
            k, v = kv.split("=")
            live[k.upper()] = float(v)
    for sym in ("SPY", "QQQ", "IWM"):
        df = pd.read_csv(os.path.join(DATA, f"{sym}_D.csv"), parse_dates=["date"])
        c = df.close.copy()
        if sym in live:
            c.iloc[-1] = live[sym]
        r = rsi2(c).iloc[-1]
        sma200 = c.rolling(200).mean().iloc[-1]
        sma5 = c.rolling(5).mean().iloc[-1]
        px = c.iloc[-1]
        signal = r < 10 and px > sma200
        print(f"{sym}  {df.date.iloc[-1]:%Y-%m-%d}  price {px:.2f}  RSI2 {r:5.1f}  SMA200 {sma200:.2f}  "
              f"SMA5 {sma5:.2f}  -> {'ENTRY SIGNAL' if signal else 'exit zone (above SMA5)' if px > sma5 else 'no signal'}")
        if signal:
            k = math.floor(px)
            print(f"      sell {sym} {k}P / buy {k - 1}P (1 wide) or {k}P/{k - 2}P (2 wide), ~5 trading days to expiry")


if __name__ == "__main__":
    main()

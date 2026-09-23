"""Technical read-out for a Webull bars dump.

Usage:
    python indicators.py bars.json [SYMBOL]

bars.json is the raw response of Webull get_stock_bars (newest bar first), or a
plain list of {time, open, high, low, close, volume} bars. Prints trend, momentum,
volatility, volume and structure so every trade card uses the same numbers.
"""
import json
import sys
from datetime import datetime


def load_bars(path, symbol=None):
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, dict) and "result" in data:
        groups = data["result"]
        group = next((g for g in groups if symbol is None or g["symbol"] == symbol), groups[0])
        symbol, raw = group["symbol"], group["result"]
    else:
        raw = data
    bars = [
        {
            "time": datetime.fromisoformat(b["time"].replace("+0000", "+00:00")),
            "open": float(b["open"]),
            "high": float(b["high"]),
            "low": float(b["low"]),
            "close": float(b["close"]),
            "volume": float(b["volume"]),
        }
        for b in raw
    ]
    bars.sort(key=lambda b: b["time"])  # oldest first
    return symbol or "?", bars


def ema(values, n):
    k, out = 2 / (n + 1), []
    for v in values:
        out.append(v if not out else v * k + out[-1] * (1 - k))
    return out


def rsi(closes, n=14):
    if len(closes) <= n:
        return None
    gains = [max(closes[i] - closes[i - 1], 0) for i in range(1, len(closes))]
    losses = [max(closes[i - 1] - closes[i], 0) for i in range(1, len(closes))]
    avg_g, avg_l = sum(gains[:n]) / n, sum(losses[:n]) / n
    for g, l in zip(gains[n:], losses[n:]):
        avg_g, avg_l = (avg_g * (n - 1) + g) / n, (avg_l * (n - 1) + l) / n
    return 100.0 if avg_l == 0 else 100 - 100 / (1 + avg_g / avg_l)


def atr(bars, n=14):
    trs = [
        max(b["high"] - b["low"], abs(b["high"] - p["close"]), abs(b["low"] - p["close"]))
        for p, b in zip(bars, bars[1:])
    ]
    if len(trs) < n:
        return None
    a = sum(trs[:n]) / n
    for tr in trs[n:]:
        a = (a * (n - 1) + tr) / n
    return a


def session_vwap(bars):
    last_day = bars[-1]["time"].date()
    pv = vol = 0.0
    for b in bars:
        if b["time"].date() == last_day:
            typical = (b["high"] + b["low"] + b["close"]) / 3
            pv, vol = pv + typical * b["volume"], vol + b["volume"]
    return pv / vol if vol else None


def swings(bars, k=2):
    """Pivot highs/lows: a bar higher/lower than the k bars on each side."""
    highs, lows = [], []
    for i in range(k, len(bars) - k):
        window = bars[i - k : i + k + 1]
        if bars[i]["high"] == max(b["high"] for b in window):
            highs.append((bars[i]["time"], bars[i]["high"]))
        if bars[i]["low"] == min(b["low"] for b in window):
            lows.append((bars[i]["time"], bars[i]["low"]))
    return highs, lows


def report(symbol, bars):
    closes = [b["close"] for b in bars]
    last = bars[-1]
    price = last["close"]
    out = [f"{symbol}  last {price:.2f}  @ {last['time']:%Y-%m-%d %H:%M} UTC  ({len(bars)} bars)"]

    # Trend
    e9, e21 = ema(closes, 9)[-1], ema(closes, 21)[-1]
    e50 = ema(closes, 50)[-1] if len(closes) >= 50 else None
    vwap = session_vwap(bars)
    trend = "UP" if price > e9 > e21 else "DOWN" if price < e9 < e21 else "MIXED"
    out.append(
        f"Trend    EMA9 {e9:.2f}  EMA21 {e21:.2f}"
        + (f"  EMA50 {e50:.2f}" if e50 else "")
        + (f"  VWAP {vwap:.2f} ({'above' if price > vwap else 'below'})" if vwap else "")
        + f"  -> {trend}"
    )

    # Momentum
    r = rsi(closes)
    macd_line = [a - b for a, b in zip(ema(closes, 12), ema(closes, 26))]
    signal = ema(macd_line, 9)
    hist, prev_hist = macd_line[-1] - signal[-1], macd_line[-2] - signal[-2]
    cross = ""
    if hist > 0 >= prev_hist:
        cross = "  bullish cross"
    elif hist < 0 <= prev_hist:
        cross = "  bearish cross"
    rsi_note = "" if r is None else " overbought" if r >= 70 else " oversold" if r <= 30 else ""
    out.append(
        f"Momentum RSI14 {r:.1f}{rsi_note}  " if r is not None else "Momentum RSI14 n/a  "
    )
    out[-1] += f"MACD {macd_line[-1]:.3f} sig {signal[-1]:.3f} hist {hist:+.3f} ({'rising' if hist > prev_hist else 'falling'}){cross}"

    # Volatility
    a = atr(bars)
    if len(closes) >= 20:
        window = closes[-20:]
        mid = sum(window) / 20
        sd = (sum((c - mid) ** 2 for c in window) / 20) ** 0.5
        pos = (price - (mid - 2 * sd)) / (4 * sd) if sd else 0.5
        bb = f"  BB20 {mid - 2 * sd:.2f}/{mid:.2f}/{mid + 2 * sd:.2f} (pos {pos:.0%}, width {4 * sd / mid:.2%})"
    else:
        bb = ""
    out.append(f"Vol      ATR14 {a:.2f}" + bb if a else "Vol      ATR14 n/a" + bb)

    # Volume
    vols = [b["volume"] for b in bars]
    if len(vols) > 20:
        avg20 = sum(vols[-21:-1]) / 20
        out.append(f"Volume   last {vols[-1]:,.0f}  avg20 {avg20:,.0f}  RVOL {vols[-1] / avg20:.2f}x")

    # Structure
    highs, lows = swings(bars)
    if highs and lows:
        sh, sl = highs[-1][1], lows[-1][1]
        bos = "BOS UP (closed above last swing high)" if price > sh else \
              "BOS DOWN (closed below last swing low)" if price < sl else "inside range"
        hh = len(highs) >= 2 and highs[-1][1] > highs[-2][1]
        hl = len(lows) >= 2 and lows[-1][1] > lows[-2][1]
        seq = "HH+HL (bullish)" if hh and hl else "LH+LL (bearish)" if not hh and not hl else "mixed"
        out.append(f"Structure swing high {sh:.2f}  swing low {sl:.2f}  {seq}  -> {bos}")

    # Opening range and day levels (only meaningful on intraday bars)
    today = [b for b in bars if b["time"].date() == last["time"].date()]
    if len(today) > 1:
        orh, orl = today[0]["high"], today[0]["low"]
        out.append(
            f"Day      open {today[0]['open']:.2f}  OR(first bar) {orl:.2f}-{orh:.2f}  "
            f"HOD {max(b['high'] for b in today):.2f}  LOD {min(b['low'] for b in today):.2f}"
        )
    return "\n".join(out)


if __name__ == "__main__":
    sym, data = load_bars(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print(report(sym, data))

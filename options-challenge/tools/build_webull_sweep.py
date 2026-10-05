"""Generates tools/webull_sweep_indicator.txt, the Sweep Setup indicator for Webull's Script Editor.

Webull scripts (as far as we've seen) only have define(), ind.sma(), plt(), [n] look-backs, ?: and and/or, and a
variable can't refer to its own past values. So rolling highs/lows and "how long ago" are written out as chains.
Levels are typed in as settings each morning (yesterday's high/low from the morning brief, the 8:30-8:45 CT
opening-range high/low at 8:45): a rolling 20-candle high/low stand-in tested at about 0R (no edge), so the
real levels are required. A level below 1 counts as "not set".
"""
import os

N_LEVEL, N_SHIFT, N_SHOW, N_STOP = 20, 7, 12, 8


def ref(s, k):
    return s if k == 0 else f"{s}[{k}]"


def roll(name, src, lo, hi, op):
    """Lines that build name = max/min of src[lo..hi] step by step."""
    cmp = ">" if op == "max" else "<"
    out = [f"{name}_{lo} = {ref(src, lo)}"]
    for k in range(lo + 1, hi + 1):
        prev = f"{name}_{k - 1}"
        out.append(f"{name}_{k} = {prev} {cmp} {ref(src, k)} ? {prev} : {ref(src, k)}")
    out.append(f"{name} = {name}_{hi}")
    return out


def chain(cond, val, default):
    expr = default
    for k in reversed(range(N_SHOW)):
        expr = f"{cond(k)} ? {val(k)} : ({expr})"
    return expr


L = [
    "// Sweep Setup (version 1) - USE ON THE 5-MINUTE CHART ONLY (the timeframe the setup was tested on)",
    "// Each morning type in yesterday's high/low (from the brief) and, at 8:45 CT, the 8:30-8:45 opening-range high/low.",
    "// Put setup: a candle wicks above a level and closes back below it (sweep), then within 6 candles a big red",
    "// candle breaks below the recent lows and leaves a fair value gap. Call setup = the mirror image.",
    "// When a setup appears, three lines show for 12 candles: white = entry (gap edge), orange = stop, green = 2R target.",
    'pdh = define(0.01, name="Yesterday high")',
    'pdl = define(0.01, name="Yesterday low")',
    'orh = define(0.01, name="Opening range high (8:30-8:45 CT)")',
    'orl = define(0.01, name="Opening range low (8:30-8:45 CT)")',
    'dispMul = define(1.25, name="Shift candle = body x avg range")',
    "",
    "avgRng = ind.sma(high - low, 20)",
]
L += ["", "// Recent swing range for the break (candles 1-5 back)"]
L += roll("hi5", "high", 1, 5, "max")
L += roll("lo5", "low", 1, 5, "min")
L += ["", "// Stop reference: extreme wick of the last 8 candles"]
L += roll("hi8", "high", 0, N_STOP - 1, "max")
L += roll("lo8", "low", 0, N_STOP - 1, "min")
L += [
    "",
    "// 1) Sweep: wick through a level, open and close back on the same side (any level, from either side)",
    "sweepHi = " + " or ".join(f"({v} > 1 and high > {v} and open < {v} and close < {v})" for v in ("pdh", "pdl", "orh", "orl")),
    "sweepLo = " + " or ".join(f"({v} > 1 and low < {v} and open > {v} and close > {v})" for v in ("pdh", "pdl", "orh", "orl")),
    "recentSweepHi = " + " or ".join(ref("sweepHi", k) for k in range(1, N_SHIFT + 1)),
    "recentSweepLo = " + " or ".join(ref("sweepLo", k) for k in range(1, N_SHIFT + 1)),
    "",
    "// 2) Shift: the previous candle is big and closes past the recent swing low/high",
    "bigDown = open[1] - close[1] >= dispMul * avgRng[1] and close[1] < lo5[1]",
    "bigUp   = close[1] - open[1] >= dispMul * avgRng[1] and close[1] > hi5[1]",
    "",
    "// 3) Fair value gap left by the shift candle -> setup on this candle",
    "putSetup  = recentSweepHi and bigDown and high < low[2]",
    "callSetup = recentSweepLo and bigUp and low > high[2]",
    "",
    "// Trade lines for the 12 candles after a setup",
    "putEntry  = " + chain(lambda k: ref("putSetup", k), lambda k: ref("high", k), "close"),
    "putStop   = " + chain(lambda k: ref("putSetup", k), lambda k: ref("hi8", k), "close"),
    "putOn     = " + chain(lambda k: ref("putSetup", k), lambda k: "1", "0"),
    "putTarget = putEntry - 2 * (putStop - putEntry)",
    "callEntry = " + chain(lambda k: ref("callSetup", k), lambda k: ref("low", k), "close"),
    "callStop  = " + chain(lambda k: ref("callSetup", k), lambda k: ref("lo8", k), "close"),
    "callOn    = " + chain(lambda k: ref("callSetup", k), lambda k: "1", "0"),
    "callTarget = callEntry + 2 * (callEntry - callStop)",
    "",
    'plt(pdh > 1 ? pdh : close, color=pdh > 1 ? #2196F3 : #00000000, name="Yesterday high")',
    'plt(pdl > 1 ? pdl : close, color=pdl > 1 ? #2196F3 : #00000000, name="Yesterday low")',
    'plt(orh > 1 ? orh : close, color=orh > 1 ? #FFD600 : #00000000, name="Opening range high")',
    'plt(orl > 1 ? orl : close, color=orl > 1 ? #FFD600 : #00000000, name="Opening range low")',
    'plt(putEntry, color=putOn == 1 ? #FFFFFF : #00000000, name="PUT entry")',
    'plt(putStop, color=putOn == 1 ? #FF9100 : #00000000, name="PUT stop")',
    'plt(putTarget, color=putOn == 1 ? #00E676 : #00000000, name="PUT target 2R")',
    'plt(callEntry, color=callOn == 1 ? #FFFFFF : #00000000, name="CALL entry")',
    'plt(callStop, color=callOn == 1 ? #FF9100 : #00000000, name="CALL stop")',
    'plt(callTarget, color=callOn == 1 ? #00E676 : #00000000, name="CALL target 2R")',
]
open(os.path.join(os.path.dirname(__file__), "webull_sweep_indicator.txt"), "w").write("\n".join(L) + "\n")

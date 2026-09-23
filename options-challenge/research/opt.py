"""Option position simulation: single legs and debit verticals, priced with lab's model."""
import math
from dataclasses import dataclass

import lab


@dataclass
class Trade:
    sym: str
    date: object
    kind: str
    structure: str
    cost: float     # $ per 1 contract / spread (x100)
    pnl: float      # $ per 1 contract / spread
    ret: float      # pnl / cost
    reason: str
    entry_bar: int
    exit_bar: int
    delta: float


def legs_value(legs, spot, t, iv):
    """legs: list of (strike, kind, qty). Returns (mid value, total half-spread cost)."""
    val = cost = 0.0
    for k, kind, q in legs:
        p = lab.bs(spot, k, t, iv, kind)[0]
        val += q * p
        cost += abs(q) * lab.half_spread(p, "_")  # placeholder, replaced below
    return val, cost


def value(day, legs, spot, j):
    t, iv = lab.t_years(day, j), lab.iv_at(day, j)
    mid = hs = 0.0
    for k, kind, q in legs:
        p = lab.bs(spot, k, t, iv, kind)[0]
        mid += q * p
        hs += abs(q) * lab.half_spread(p, day.sym)
    if len(legs) > 1:
        hs *= 0.7  # a spread order usually fills better than legging each side at its own bid/ask
    return mid, hs


def build(day, i, kind, structure, budget, width_steps=1):
    """structure: 'single' (nearest-money strike within budget), 'atm' (ignore budget),
    'vertical' (long nearest-money, short `width_steps` strikes further OTM; walk OTM until it fits budget)."""
    spot = day.c[i]
    step = lab.strike_step(spot, day.sym)
    sgn = 1 if kind == "C" else -1
    k0 = math.ceil(spot / step) * step if kind == "C" else math.floor(spot / step) * step
    t, iv = lab.t_years(day, i), lab.iv_at(day, i)
    for n in range(40):
        k = k0 + sgn * n * step
        if structure in ("single", "atm"):
            legs = [(k, kind, 1)]
        else:
            legs = [(k, kind, 1), (k + sgn * width_steps * step, kind, -1)]
        mid, hs = value(day, legs, spot, i)
        ask = mid + hs
        if structure == "atm" or ask * 100 <= budget:
            if mid <= 0.03:
                return None
            delta = sum(q * lab.bs(spot, kk, t, iv, kd)[1] for kk, kd, q in legs)
            return legs, ask, delta
    return None


def run(day, i, kind, structure="vertical", budget=100, width_steps=1, exit_bar=77,
        und_stop=None, stop_pct=None, target_pct=None, trail_pct=None):
    b = build(day, i, kind, structure, budget, width_steps)
    if not b:
        return None
    legs, entry, delta = b
    stop = entry * (1 - stop_pct) if stop_pct else -1e9
    target = entry * (1 + target_pct) if target_pct else 1e9
    peak = entry
    exit_px, reason, jx = None, "time", exit_bar
    for j in range(i + 1, exit_bar + 1):
        adverse = day.l[j] if kind == "C" else day.h[j]
        favour = day.h[j] if kind == "C" else day.l[j]
        wm, wh = value(day, legs, adverse, j)
        bm, bh = value(day, legs, favour, j)
        worst, best = wm - wh, bm - bh
        if worst <= stop:
            exit_px, reason, jx = stop, "stop", j
            break
        if best >= target:
            exit_px, reason, jx = target, "target", j
            break
        peak = max(peak, best)
        if trail_pct and peak >= entry * (1 + trail_pct):
            stop = max(stop, peak * (1 - trail_pct))
        if und_stop is not None and ((kind == "C" and day.c[j] < und_stop) or (kind == "P" and day.c[j] > und_stop)):
            cm, ch = value(day, legs, day.c[j], j)
            exit_px, reason, jx = cm - ch, "structure", j
            break
    if exit_px is None:
        cm, ch = value(day, legs, day.c[exit_bar], exit_bar)
        exit_px = cm - ch
    exit_px = max(exit_px, 0.0)
    return Trade(day.sym, day.date, kind, structure, entry * 100, (exit_px - entry) * 100,
                 exit_px / entry - 1, reason, i, jx, delta)

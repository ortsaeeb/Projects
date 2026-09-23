"""Gamma exposure and positioning from an option chain.

Usage:
    python gex.py SPY [YYYY-MM-DD]            # fetch CBOE delayed chain (needs cdn.cboe.com allowed)
    python gex.py chain.json [YYYY-MM-DD]     # or a saved CBOE chain file

Assumes the usual dealer positioning (dealers long calls / short puts from customer
flow), so call gamma counts positive and put gamma negative. Output: net gamma
exposure, the gamma flip level, call wall, put wall, and where volume is building.
"""
import json
import re
import sys
import urllib.request
from collections import defaultdict

OCC = re.compile(r"^([A-Z.]+?)(\d{6})([CP])(\d{8})$")


def load_chain(arg):
    if arg.endswith(".json"):
        with open(arg) as f:
            return json.load(f)["data"]
    url = f"https://cdn.cboe.com/api/global/delayed_quotes/options/{arg.upper()}.json"
    with urllib.request.urlopen(url, timeout=20) as r:
        return json.load(r)["data"]


def parse(data, expiry=None):
    rows = []
    for o in data["options"]:
        m = OCC.match(o["option"])
        if not m:
            continue
        exp = f"20{m.group(2)[:2]}-{m.group(2)[2:4]}-{m.group(2)[4:]}"
        if expiry and exp != expiry:
            continue
        rows.append({
            "exp": exp,
            "type": m.group(3),
            "strike": int(m.group(4)) / 1000,
            "oi": float(o.get("open_interest") or 0),
            "vol": float(o.get("volume") or 0),
            "gamma": float(o.get("gamma") or 0),
            "iv": float(o.get("iv") or 0),
            "bid": float(o.get("bid") or 0),
            "ask": float(o.get("ask") or 0),
            "delta": float(o.get("delta") or 0),
        })
    return rows


def analyse(spot, rows):
    gex = defaultdict(float)
    call_oi, put_oi, call_vol, put_vol = (defaultdict(float) for _ in range(4))
    for r in rows:
        # dollar gamma for a 1% move, per strike
        g = r["gamma"] * r["oi"] * 100 * spot * spot * 0.01
        if r["type"] == "C":
            gex[r["strike"]] += g
            call_oi[r["strike"]] += r["oi"]
            call_vol[r["strike"]] += r["vol"]
        else:
            gex[r["strike"]] -= g
            put_oi[r["strike"]] += r["oi"]
            put_vol[r["strike"]] += r["vol"]

    strikes = sorted(gex)
    total = sum(gex.values())

    # flip: strike where cumulative GEX (low -> high) changes sign
    flip, running = None, 0.0
    for s in strikes:
        prev, running = running, running + gex[s]
        if prev < 0 <= running or prev > 0 >= running:
            flip = s

    near = [s for s in strikes if abs(s - spot) / spot <= 0.03]
    call_wall = max((s for s in near if s >= spot), key=lambda s: call_oi[s], default=None)
    put_wall = max((s for s in near if s <= spot), key=lambda s: put_oi[s], default=None)
    pin = max(near, key=lambda s: call_oi[s] + put_oi[s], default=None)
    cv, pv = sum(call_vol.values()), sum(put_vol.values())

    lines = [
        f"Spot {spot:.2f}   net GEX ${total / 1e9:+.2f}B per 1% "
        f"({'POSITIVE: dealers dampen moves, expect mean reversion/pinning' if total > 0 else 'NEGATIVE: dealers amplify moves, expect trend/volatility'})",
        f"Gamma flip ~{flip}" if flip else "Gamma flip: none in range",
        f"Call wall (resistance) {call_wall}   Put wall (support) {put_wall}   Max-OI pin {pin}",
        f"Volume  calls {cv:,.0f}  puts {pv:,.0f}  put/call {pv / cv:.2f}" if cv else "Volume  n/a",
        "Top volume strikes: "
        + ", ".join(f"{s:g}C {call_vol[s]:,.0f}" for s in sorted(call_vol, key=call_vol.get, reverse=True)[:3])
        + " | "
        + ", ".join(f"{s:g}P {put_vol[s]:,.0f}" for s in sorted(put_vol, key=put_vol.get, reverse=True)[:3]),
    ]
    return "\n".join(lines)


def cheapest_tradable(rows, spot, max_premium=0.80):
    """Contracts passing the playbook filter: delta 0.30-0.50, premium cap, spread <= 10%/5c."""
    out = []
    for r in rows:
        mid = (r["bid"] + r["ask"]) / 2
        spread = r["ask"] - r["bid"]
        if 0.30 <= abs(r["delta"]) <= 0.50 and 0 < mid <= max_premium and \
                (spread <= 0.05 or spread <= 0.10 * mid) and r["vol"] >= 500:
            out.append(f"{r['exp']} {r['strike']:g}{r['type']}  mid {mid:.2f}  d {r['delta']:+.2f}  "
                       f"vol {r['vol']:,.0f}  OI {r['oi']:,.0f}  IV {r['iv']:.0%}")
    return out


if __name__ == "__main__":
    data = load_chain(sys.argv[1])
    expiry = sys.argv[2] if len(sys.argv) > 2 else None
    rows = parse(data, expiry)
    if not expiry and rows:
        expiry = min(r["exp"] for r in rows)  # default: nearest expiration
        rows = [r for r in rows if r["exp"] == expiry]
    spot = float(data["current_price"])
    print(f"Expiration {expiry}")
    print(analyse(spot, rows))
    picks = cheapest_tradable(rows, spot)
    print("Contracts passing the filter:" if picks else "No contract passes the filter (too expensive or illiquid).")
    for p in picks:
        print("  " + p)

"""Step 7: simulate the real account running the RSI(2) bull put spread plan.

Start $101.30, optional weekly deposit. All SPY/QQQ/IWM signals in date order.
Width grows with the account: $1 wide under $250, $2 under $600, $5 above.
Contracts = floor(max_risk_frac * equity / risk_per_spread), at least 1 if one spread fits in
equity; total open risk capped at `max_open` of equity (signals on the same days are correlated).
"""
import math
import sys

import numpy as np
import pandas as pd

import study5_daily as s5
import study6_rsi2_options as s6


def width_for(equity):
    return 1 if equity < 250 else 2 if equity < 600 else 5


def simulate(ivr=1.3, dte=5, deposit=0.0, start=101.30, max_risk_frac=0.5, max_open=0.8, since="2023-01-01"):
    # pre-compute trades for each width
    tables = {w: s6.run("pcs", w, ivr, dte).set_index(["sym", "date"]) for w in (1, 2, 5)}
    base = tables[1].reset_index()[["sym", "date", "held"]]
    base = base[base.date >= since].sort_values("date")
    equity, open_pos, log = start, [], []
    last_dep = pd.Timestamp(since)
    peak, mdd = start, 0.0
    for _, r in base.iterrows():
        # deposits every 7 days
        while deposit and r.date - last_dep >= pd.Timedelta(days=7):
            equity += deposit
            last_dep += pd.Timedelta(days=7)
        # settle positions that closed before this entry
        still = []
        for p in open_pos:
            if p["exit"] <= r.date:
                equity += p["pnl"]
            else:
                still.append(p)
        open_pos = still
        w = width_for(equity)
        t = tables[w].loc[(r.sym, r.date)]
        risk_open = sum(p["risk"] for p in open_pos)
        n = math.floor(max_risk_frac * equity / t.risk)
        if n == 0 and t.risk <= equity - risk_open:
            n = 1
        n = min(n, math.floor((max_open * equity - risk_open) / t.risk))
        if n <= 0:
            continue
        exit_date = r.date + pd.tseries.offsets.BDay(int(min(r.held, dte)))
        open_pos.append(dict(exit=exit_date, pnl=n * t.pnl, risk=n * t.risk))
        log.append(dict(date=r.date, sym=r.sym, w=w, n=n, risk=n * t.risk, pnl=n * t.pnl, equity_before=equity))
        peak = max(peak, equity)
        mdd = max(mdd, 1 - equity / peak)
    for p in open_pos:
        equity += p["pnl"]
    df = pd.DataFrame(log)
    return equity, df, mdd


if __name__ == "__main__":
    print("Account simulation, RSI(2) bull put spreads on SPY/QQQ/IWM, Jan 2023 - Sep 2026")
    print(f"{'IV':>4} {'dte':>3} {'deposit/wk':>10} | {'trades':>6} {'win':>4} {'deposited':>9} {'final':>9} {'max DD':>6} {'worst trade':>11}")
    for ivr in (1.1, 1.3, 1.5):
        for dte in (3, 5):
            for dep in (0, 25, 50):
                eq, df, mdd = simulate(ivr, dte, dep)
                weeks = (pd.Timestamp("2026-09-23") - pd.Timestamp("2023-01-01")).days // 7
                print(f"{ivr:>4} {dte:>3} {dep:>10} | {len(df):6d} {np.mean(df.pnl > 0):4.0%} "
                      f"${101.3 + dep * weeks:8.0f} ${eq:8.0f} {mdd:6.0%} ${df.pnl.min():10.0f}")

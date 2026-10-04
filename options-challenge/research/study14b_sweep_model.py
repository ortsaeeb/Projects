"""Study 14b: the one ICT family that survived study14's search - the liquidity sweep + MSS + FVG model -
checked for robustness and converted to option P&L.

The rule set (picked on TRAIN only, from out/study14_sweep.csv; middle-of-the-pack settings, not the best cell):
  1. Liquidity = prior-day high/low and the opening-range (9:30-9:45 ET) high/low.
  2. Sweep: a 5-min candle trades through one of those levels and CLOSES back on the other side.
       swept a high -> look for puts; swept a low -> look for calls.
  3. Within 6 candles: a displacement candle (body >= 1.25x the day's average candle range) that closes beyond
     the latest swing point (market-structure shift) and leaves a fair value gap.
  4. Entry: limit at the near edge of the FVG, valid for 12 candles (1 hour). No fill = no trade.
  5. Stop: 2 cents beyond the sweep's extreme wick. Target: 2R. Otherwise out after 12 candles (1 hour).
     (The 1-hour cap was picked on TRAIN option P&L among 30 min / 1 h / 2 h / hold-to-close.)
  6. One trade per symbol per day. Signals from 9:45 to 14:55 ET (8:45-13:55 CT).

Run:  python study14b_sweep_model.py
"""
import math
import os

import numpy as np
import pandas as pd

import lab
import study11_september as G
import study14_ict_search as S

CFG = dict(setup="sweep", win="all", bias="none", tgt="2", disp=1.25, levels="both", mss=True, lb=6, maxbars=12)
BUDGET = float(os.environ.get("BUDGET", "0.60"))


def tstat(a):
    a = np.asarray(a)
    return a.mean() / (a.std(ddof=1) / math.sqrt(len(a))) if len(a) > 1 else 0.0


def opt_trade(d, t):
    """Buy the nearest strike with ask <= BUDGET when the limit fills; sell at the stop/target/time price."""
    kind = "C" if t["side"] > 0 else "P"
    e, j = t["fill"], t["exit"]
    spot = t["entry"]
    step = lab.strike_step(spot, d.sym)
    te, ive = lab.t_years(d, e), lab.iv_at(d, e)
    k = math.ceil(spot / step) * step if kind == "C" else math.floor(spot / step) * step
    for _ in range(60):
        mid = lab.bs(spot, k, te, ive, kind)[0]
        if mid + lab.half_spread(mid, d.sym) <= BUDGET:
            break
        k += step if kind == "C" else -step
    if mid < 0.05:
        return None
    paid = mid + lab.half_spread(mid, d.sym)
    out = lab.bs(t["exit_px"], k, lab.t_years(d, j), lab.iv_at(d, j), kind)[0]
    out = max(0.0, out - lab.half_spread(out, d.sym))
    return (out - paid) * 100, out / paid - 1


def run(syms, cfg=CFG):
    days_by_sym, feats, trends = S.load_all(syms)
    rows = S.run_config(days_by_sym, feats, trends, cfg)
    byday = {(s, d.date): d for s, ds in days_by_sym.items() for d in ds}
    for r in rows:
        o = opt_trade(byday[(r["sym"], r["date"])], r)
        r["usd"], r["opt_ret"] = o if o else (np.nan, np.nan)
    return pd.DataFrame(rows), byday


def report(df, label):
    print(f"\n=== {label} ===")
    for per, x in (("TRAIN", df[df.date < S.SPLIT]), ("TEST", df[df.date >= S.SPLIT]), ("ALL", df)):
        y = x.dropna(subset=["usd"])
        print(f"{per:<6} n={len(x):3d}  win {np.mean(x.R > 0):4.0%}  avg {x.R.mean():+.2f}R (t {tstat(x.R):+.2f})"
              f"  | option ${y.usd.mean():+6.2f}/trade, win {np.mean(y.usd > 0):4.0%}, total ${y.usd.sum():+7.0f}")


def main():
    etf, byday = run(S.ETF)
    stk, _ = run(lab.STOCKS)
    report(etf, "SPY/QQQ/IWM")
    for s in S.ETF:
        report(etf[etf.sym == s], s)
    report(stk, "7 stocks (never used to pick anything; weekly options)")

    print("\nBy month (ETFs): n, avg R, option $ total")
    etf["month"] = etf.date.dt.strftime("%Y-%m")
    etf["guard"] = [G.trade(byday[(t.sym, t.date)], int(t.fill), "C" if t.side > 0 else "P") for t in etf.itertuples()]
    for per, x in (("TRAIN", etf[etf.date < S.SPLIT]), ("TEST", etf[etf.date >= S.SPLIT])):
        x = x.dropna(subset=["guard"])
        print(f"same entries, Trade Guardian exits instead: {per} ${x.guard.mean():+.2f}/trade, win {np.mean(x.guard > 0):.0%}")
    u = etf.dropna(subset=["usd"]).sort_values("usd")
    print(f"median option trade ${u.usd.median():+.2f}; mean without the 3 best trades ${u.usd.iloc[:-3].mean():+.2f}")
    print(etf.groupby("month").agg(n=("R", "size"), avgR=("R", "mean"), usd=("usd", "sum")).round(2).to_string())

    etf["ct"] = etf.fill.map(lambda i: f"{8 + (30 + 5 * i + 5) // 60}:{(30 + 5 * i + 5) % 60:02d}")
    etf["half"] = np.where(etf.fill <= 17, "fill by 10:00 CT", "fill after 10:00 CT")
    print("\nBy fill time (ETFs):")
    print(etf.groupby("half").agg(n=("R", "size"), avgR=("R", "mean"), win=("R", lambda r: (r > 0).mean()),
                                  usd=("usd", "mean")).round(2).to_string())
    print("\nBy direction (ETFs):")
    print(etf.groupby("side").agg(n=("R", "size"), avgR=("R", "mean"), usd=("usd", "mean")).round(2).to_string())

    print("\nOutcome mix (ETFs): target / stop / time")
    tgt = (etf.R > 1.5).sum(); stp = (etf.R < -0.8).sum()
    print(f"  {tgt} / {stp} / {len(etf) - tgt - stp}")
    print(f"  median risk (entry->stop) in $: SPY {(etf[etf.sym=='SPY'].entry - etf[etf.sym=='SPY'].stop).abs().median():.2f}"
          f"  QQQ {(etf[etf.sym=='QQQ'].entry - etf[etf.sym=='QQQ'].stop).abs().median():.2f}")

    # skeptic checks
    print("\nSkeptic checks (ETFs, all dates, avg R):")
    for name, cfg in (("no sweep needed (plain MSS + FVG retrace)", dict(CFG, setup="fvg")),
                      ("sweep but no MSS required", dict(CFG, mss=False)),
                      ("1R target", dict(CFG, tgt="1")), ("3R target", dict(CFG, tgt="3")),
                      ("displacement 1.0x", dict(CFG, disp=1.0)), ("displacement 1.5x", dict(CFG, disp=1.5)),
                      ("only prior-day levels", dict(CFG, levels="pd")), ("only opening-range levels", dict(CFG, levels="or"))):
        x = pd.DataFrame(S.run_config(*S.load_all(S.ETF), cfg))
        a, b = x[x.date < S.SPLIT].R, x[x.date >= S.SPLIT].R
        print(f"  {name:<44} train {a.mean():+.2f}R n={len(a):3d} | test {b.mean():+.2f}R n={len(b):3d}")

    etf.to_csv(os.path.join(os.path.dirname(__file__), "out", "study14b_trades.csv"), index=False)
    return etf, byday


if __name__ == "__main__":
    main()

"""Step 4: search for conditions that make a candidate profitable, selected on TRAIN only.

Rules are one or two feature thresholds (feature quantiles computed on TRAIN).
A rule 'passes' if TRAIN n>=40, TRAIN mean>0 with t>=2.5. We then report its TEST result.
Every rule tried is counted so the multiple-testing risk is visible.
"""
import itertools
import math
import os

import numpy as np
import pandas as pd

import lab

IVM = os.environ.get("IVM", str(lab.MODEL["iv_mult"]))
df = pd.read_csv(os.path.join(os.path.dirname(__file__), "out", f"candidates_iv{float(IVM)}.csv"), parse_dates=["date"])
train = df.date < lab.SPLIT
OUTCOMES = ["o_60m", "o_2h", "o_close_trail", "o100_60m"]
FEATS = ["gap_al", "move_al", "or_rng", "rvol", "vw_dist", "rv20", "bar"]
CATS = {"mkt": [-1, 0, 1], "prev_al": [-1, 1], "dow": [0, 1, 2, 3, 4], "etf": [0, 1]}


def conditions():
    for f in FEATS:
        qs = df.loc[train, f].quantile([0.2, 0.4, 0.6, 0.8]).values
        for q in qs:
            yield (f"{f}>={q:.2f}", df[f] >= q)
            yield (f"{f}<{q:.2f}", df[f] < q)
    for f, vals in CATS.items():
        for v in vals:
            yield (f"{f}=={v}", df[f] == v)


def tstat(a):
    a = a[~np.isnan(a)]
    if len(a) < 3 or a.std() == 0:
        return len(a), np.nan, 0.0
    return len(a), a.mean(), a.mean() / (a.std(ddof=1) / math.sqrt(len(a)))


conds = list(conditions())
tried = 0
passed = []
for cand in ["orb15", "orb30", "pdhl", "vwpb"]:
    base = df.cand == cand
    rules = [(n, m) for n, m in conds] + [
        (f"{a[0]} & {b[0]}", a[1] & b[1]) for a, b in itertools.combinations(conds, 2)
        if a[0].split("<")[0].split(">")[0].split("=")[0] != b[0].split("<")[0].split(">")[0].split("=")[0]
    ]
    for outcome in OUTCOMES:
        for name, mask in rules:
            tried += 1
            m = base & mask
            ntr, mtr, ttr = tstat(df.loc[m & train, outcome].values)
            if ntr < 40 or not (mtr > 0 and ttr >= 2.5):
                continue
            nte, mte, tte = tstat(df.loc[m & ~train, outcome].values)
            passed.append((cand, outcome, name, ntr, mtr, ttr, nte, mte, tte))

print(f"rules tried: {tried:,}   passed on TRAIN: {len(passed)}")
res = pd.DataFrame(passed, columns=["cand", "outcome", "rule", "n_tr", "avg_tr", "t_tr", "n_te", "avg_te", "t_te"])
res.to_csv(os.path.join(os.path.dirname(__file__), "out", f"rules_iv{float(IVM)}.csv"), index=False)
if len(res):
    print(f"of those, TEST avg > 0: {(res.avg_te > 0).mean():.0%}   TEST t >= 2: {(res.t_te >= 2).mean():.0%}")
    pd.set_option("display.width", 200)
    print(res.sort_values("t_te", ascending=False).head(30).round(3).to_string(index=False))

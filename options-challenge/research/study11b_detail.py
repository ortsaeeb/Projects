"""Study 11b: September detail - Guardian $/trade and underlying move by month, the September trades of the
best three rules, results without the single best day, and how often a right-direction trade still lost.

Run:  python study11b_detail.py
"""
import os
from collections import defaultdict
import numpy as np, pandas as pd
import study11_september as S, lab
from study10_volume_profile import profile
days=lab.universe(S.SYMS); by=defaultdict(list)
for d in days: by[d.sym].append(d)
profs={}
for s,ds in by.items():
    ds.sort(key=lambda x:x.date)
    for a,b in zip(ds[:-1],ds[1:]): profs[(s,b.date)]=profile(a)
days=[d for d in days if (d.sym,d.date) in profs]
# monthly table: underlying bps and guardian $ per strategy
rows=[]
for name,fn in S.STRATS.items():
    for d in days:
        sig=fn(d,profs[(d.sym,d.date)])
        if not sig: continue
        i,k=sig; p=S.trade(d,i,k)
        if p is None: continue
        rows.append(dict(strat=name,month=d.date.strftime("%Y-%m"),pnl=p,und=S.und_move(d,i,k),sym=d.sym,date=d.date.date(),bar=i,kind=k))
df=pd.DataFrame(rows)
print("Guardian $/trade by month (last 6 months)")
t=df[df.month>="2026-04"].pivot_table(index="strat",columns="month",values="pnl",aggfunc="mean").round(1)
print(t.to_string())
print("\nUnderlying bps by month")
print(df[df.month>="2026-04"].pivot_table(index="strat",columns="month",values="und",aggfunc="mean").round(0).to_string())
print("\nMonths with positive Guardian $/trade, out of all months:")
m=df.pivot_table(index="strat",columns="month",values="pnl",aggfunc="mean")
print((m>0).sum(axis=1).astype(str)+" / "+m.notna().sum(axis=1).astype(str))
for nm in ["Gap and go (>0.3%)","ORB 15-min breakout","Prior-day value plan (09-29 plan)"]:
    x=df[(df.strat==nm)&(df.month=="2026-09")].sort_values("date")
    print("\n",nm); print(x[["date","sym","bar","kind","und","pnl"]].round(1).to_string(index=False))

print("\n== without the single best day (2026-09-21) ==")
sep=df[df.month=="2026-09"]
for nm,g in sep.groupby("strat"):
    h=g[g.date!=pd.Timestamp("2026-09-21").date()]
    print(f"{nm:<38} all {g.pnl.mean():+6.2f} ({len(g)})   ex-9/21 {h.pnl.mean():+6.2f} ({len(h)})")
print("\n== right direction by 14:50 but still lost (all periods) ==")
right=df[df.und>0]
print(f"trades with underlying in your favour at 14:50: {len(right)} of {len(df)} ({len(right)/len(df):.0%}); of those, lost money: {(right.pnl<0).mean():.0%}")
print("SEP:", f"{(sep.und>0).mean():.0%} right direction; of those lost {(sep[sep.und>0].pnl<0).mean():.0%}")

# Backtest — 2026-09-23

**Data:** Webull 5-min regular-hours bars, SPY / QQQ / IWM, 2026-08-11 → 2026-09-23
(30 sessions; 25 tradable after 5 days of warm-up). Script: `tools/backtest.py`.

**Option pricing is modeled, not real:** Black-Scholes 0DTE, $1 strikes, IV from 5-day realized vol × 1.15
(floored at 12%), $0.02 slippage each side, fills at the trigger bar close, IV held constant.
Real opening IV is higher and drops after the open, so **real results would likely be worse**.

## Results

| Test | Trades | Win rate | Net (1 contract) |
|---|---|---|---|
| Playbook as written (A + B, stop 25% / target 50%, account rules on) | 8 | 12% | **−$48** (circuit breaker by Sep 3) |
| Setup B only, every signal | 18 | **0%** | −$67 |
| Setup A only, every signal, stop 25% / target 50% | 43 | 30% | −$26 |
| Setup A only, every signal, stop 40% / target 100% | 43 | 37% | **+$169** |
| Same, entry filters OFF | 62 | 31% | +$66 |
| Same, IV × 1.6 (closer to real open IV) | 43 | 37% | +$69 |
| Setup A, stop 40% / target 100%, account rules on | 22 | 36% | **+$38** ($101 → $139, peak $245) |

Setup A (stop 40% / target 100%) by ticker: **QQQ +$259**, IWM −$18, SPY −$72.
By period: Aug 18–Sep 3 **−$34**, Sep 4–23 **+$204**.

## What it says

1. **Setup B (power hour, ≤ $0.30 options) lost on all 18 signals.** Cheap late-day options get
   stopped out by noise and time decay. Suspended until reworked.
2. **The +50% target and 25% stop were too tight.** Winners need room: most profit came from
   letting the trade run to the 10:15 time stop. Wider stop / bigger target was better in every
   test.
3. **Volume + VWAP filters help** in every stop/target combination.
4. **The $100 budget forces low-delta contracts** (average |delta| ≈ 0.25, not 0.30–0.50). SPY
   options near the money cost more than $0.80, which is part of why SPY lost.
5. **The edge is not proven.** Almost all profit came from QQQ in one 3-week stretch. 25 days is
   far too few to trust, and the modeled prices flatter the results.

# Trade Journal

| Date | Setup | Ticker / Contract | Entry | Exit | Qty | P/L $ | P/L % | Followed rules? | Notes |
|------|-------|-------------------|-------|------|-----|-------|-------|-----------------|-------|
| 2026-09-24 | News breakout (Trump–Xi rally, 11:15 CT) | SPY 769C 0DTE | 0.58 | ~0.60 | 1 | ~+1.9 | ~+3% | Partly — entry on user's own, no exit order placed | Peaked ~0.97 (+68%) at 11:40 CT when SPY hit 768.88, faded within minutes. Lesson: place OCO (take-profit + stop-limit) immediately after fill. |

## Planned: $50 lottery ticket (Thu 2026-09-24, fallback Fri 2026-09-25)

User's decision: risk $50 of $101.30 on one same-day option aiming for 10x ($1,000 goal).
Backtest odds of a 10x on this setup: ~2% (see RESEARCH.md). $51 stays untouched.

- Levels (Sep 23): SPY high 773.05 / low 766.50 / close 767.81 · QQQ high 747.13 / low 738.19 / close 741.21
- Trigger: after 9:45 ET, 5-min close beyond the 15-min opening range, volume >= 1.5x, correct side of VWAP,
  ideally also beyond the prior-day high/low and with the news direction
- Contract: 1 same-day SPY or QQQ call/put, ask ~$0.45-0.50 (~$6-10 out of the money)
- Exit: GTC sell at 10x ($4.80-5.00) right after the fill; otherwise it rides; no second ticket if it loses
- 10x needs roughly a 1.4-2% move in SPY/QQQ

## Account log

| Date | Event | Amount | Balance | High-water mark |
|------|-------|--------|---------|-----------------|
| 2026-09-23 | Starting balance | — | $101.30 | $101.30 |
| 2026-09-24 | SPY 769C closed | +$1.88 | $103.18 | $103.18 |

## Notes 2026-09-24
- Morning: 6 fake breakouts (4 up, 2 down) skipped by the volume + both-ETFs rule.
- 11:15 CT news spike (SPY +$4, QQQ +$5 in 3 min, 1M+ volume) was the only valid setup.
- New rule: every entry gets an OCO exit placed right after the fill.

## Review every 5 trades

- Win rate:
- Average win / average loss:
- Setup A vs Setup B results:
- Rules broken:
- Change for next 5 trades:

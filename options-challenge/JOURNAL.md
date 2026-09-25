# Trade Journal

| Date | Setup | Ticker / Contract | Entry | Exit | Qty | P/L $ | P/L % | Followed rules? | Notes |
|------|-------|-------------------|-------|------|-----|-------|-------|-----------------|-------|
| 2026-09-24 | News breakout (Trump–Xi rally, 11:15 CT) | SPY 769C 0DTE | 0.58 | ~0.60 | 1 | ~+1.9 | ~+3% | Partly — entry on user's own, no exit order placed | Peaked ~0.97 (+68%) at 11:40 CT when SPY hit 768.88, faded within minutes. Lesson: place OCO (take-profit + stop-limit) immediately after fill. |
| 2026-09-25 | Manual (user) — gap-fill fade at the open | QQQ 740P 0DTE | 0.59 | ~0.89 (stop-limit 0.91/0.88) | 1 | +29.88 (day) | ~+51% | Partly — manual trade while the bot ran; stop placed and trailed | Peaked 1.33 (+125%) at 9:05 CT as QQQ hit 741.29 (just above yday close 741.10), stopped out on the bounce. Bot skipped two weak QQQ call breakouts (low volume) and was switched off at ~9:06. |
| 2026-09-25 | Manual (user) — early call before confirmation | QQQ 745C 0DTE | 0.53 | ~0.37 | 1 | −16.12 | ~−30% | No — bought below the 742.95 confirmation level, no stop placed | Bought ~9:25 CT with QQQ ~741.3; rejected at 741.90 and faded. |
| 2026-09-25 | Manual (user) — re-entry, same setup | QQQ 745C 0DTE | 0.54 | ~0.49 (stop) | 1 | −5.12 | ~−9% | Partly — stop placed (tight), still no confirmation | QQQ never closed above 742.95; stopped at 9:41 CT. |
| 2026-09-25 | Manual (user) — lottery put | QQQ 733P 0DTE | 0.17 | ~0.13 | 1 | −4.12 | ~−24% | No setup | Bought ~9:43 CT in chop, sold ~9:46 CT. |
| 2026-09-25 | Manual (user) — breakout above 742.95 | QQQ 746C 0DTE | 0.43 | ~0.51 (trailed stop) | 1 | +7.83 | ~+18% | Yes — stop placed, trailed to breakeven then +$7 | Peaked 0.62 at 10:05 CT (QQQ 744.06), stopped on the pullback. |
| 2026-09-25 | Manual (user) — fade from 744 | QQQ 739P 0DTE | 0.35 | ~0.37 | 1 | +1.93 | ~+5% | Yes — stop placed | Sold ~10:13 CT with QQQ at 742.7. |
| 2026-09-25 | Manual (user) — midday call, 2 contracts | QQQ 747C 0DTE | 0.25 | ~0.19 (stop) | 2 | −12.21 | ~−24% | Partly — stop placed; low-volume midday, no confirmation | Stopped ~10:19 CT as QQQ slipped to 742.47. |
| 2026-09-25 | Manual (user) — bought the failed pop | QQQ 744C 0DTE | 0.62 | ~0.44 | 1 | −18.12 | ~−29% | No — bought into resistance, no stop, 2/3 of account | Bought ~10:35 CT near the rejected 10:05 high; sold ~10:43 CT with QQQ 741.5. |
| 2026-09-25 | Manual (user) — re-entry at support, rode the 11:00 breakout | QQQ 744C 0DTE | 0.56 | ~1.74 | 1 | +117.88 | ~+210% | Partly — no stop for the first part; stops placed/trailed after +84% | Bought ~10:55 CT at yday close support (QQQ 741); QQQ broke the 744.6 opening-range high at 11:00 on heavy volume; option peaked ~2.52 (+350%); closed ~11:17 CT. |
| 2026-09-25 | Manual (user) — failed-breakout put | QQQ 741P 0DTE | 0.43 | ~0.36 | 1 | −7.12 | ~−16% | Partly — half-confirmed (QQQ < 744.6, SPY held 770.1), no stop | Sold ~11:25 CT as QQQ bounced back to 744.2. |

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
| 2026-09-24 | End of day (Webull: day P/L +$10.76; second trade details pending) | +$8.88 | $112.06 | $112.06 |
| 2026-09-24 | Late-day manual trade(s), details pending | −$21.24 | $90.82 | $112.06 |
| 2026-09-25 | QQQ 740P closed | +$29.88 | $120.70 | $120.70 |
| 2026-09-25 | QQQ 745C closed | −$16.12 | $104.58 | $120.70 |
| 2026-09-25 | QQQ 745C (2nd) stopped | −$5.12 | $99.46 | $120.70 |
| 2026-09-25 | QQQ 733P closed | −$4.12 | $95.34 | $120.70 |
| 2026-09-25 | QQQ 746C closed | +$7.83 | $103.17 | $120.70 |
| 2026-09-25 | QQQ 739P closed | +$1.93 | $105.10 | $120.70 |
| 2026-09-25 | QQQ 747C x2 stopped | −$12.21 | $92.89 | $120.70 |
| 2026-09-25 | QQQ 744C closed | −$18.12 | $74.77 | $120.70 |
| 2026-09-25 | QQQ 744C (2nd) closed | +$117.88 | $192.65 | $192.65 |
| 2026-09-25 | QQQ 741P closed | −$7.12 | $185.53 | $192.65 |

## Notes 2026-09-24
- Morning: 6 fake breakouts (4 up, 2 down) skipped by the volume + both-ETFs rule.
- 11:15 CT news spike (SPY +$4, QQQ +$5 in 3 min, 1M+ volume) was the only valid setup.
- New rule: every entry gets an OCO exit placed right after the fill.
- Afternoon: SPY/QQQ chopped in a ~$1.50 range after 12:15 CT; power-hour scan = no trend day, no trade.
- OpenAPI market data active: Nasdaq Basic (free) + OPRA real-time ($4.99/month, a fixed cost the account has to beat). Bot `auto` mode ready for its first live day Fri 2026-09-25.

## Notes 2026-09-25
- By 10:45 CT: 9 manual trades, 4 wins / 5 losses, day −$16.05. The only big winner (QQQ 740P +$29.88) came in the first
  30 minutes with the trend. Every trade after 9:15 CT was taken in a ~$3 chop range; losers were mostly
  entered before a 5-min close confirmed and/or without a stop.
- Account fell from a $120.70 high to $74.77 in ~90 minutes of overtrading.
- 11:00 CT: QQQ/SPY broke their opening-range highs on heavy volume; QQQ 744C +$117.88 turned the day to +$101.83.
- Rules for next session: max 2 trades/day; stop placed immediately; no entries 10:30–13:30 CT; stop for the
  day after 2 losses or when green after a winner.

## Review every 5 trades

- Win rate:
- Average win / average loss:
- Setup A vs Setup B results:
- Rules broken:
- Change for next 5 trades:

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
| 2026-09-25 | Manual (user) — far OTM call in lunch drift | QQQ 748C 0DTE | 0.35 | ~0.22 | 1 | −13.12 | ~−37% | No — $3 OTM, low volume, no stop | Sold ~11:33 CT with QQQ 745.4. |
| 2026-09-25 | Manual (user) — second failed-breakout put, last trade | QQQ 741P 0DTE | 0.26 | ~0.16 | 1 | −10.12 | ~−38% | Partly — half-confirmed, no stop, lunch chop | SPY held 770.1; closed ~12:01 CT. User stopped for the day. |
| 2026-09-28 | Manual — put, entered before the 5-min close confirmed | QQQ 730P 0DTE | 0.22 | 0.13 | 1 | −9.12 | −41% | Partly — Guardian stop placed in 4 s; sold by hand after 90 s | 8:52–8:53 CT. $7 OTM. QQQ fell to 731.6 later: holding would have paid. |
| 2026-09-28 | Manual — put re-entry | QQQ 731P 0DTE | 0.20 | 0.15 | 1 | −5.12 | −25% | Partly — stop placed in 5 s; sold by hand | 8:56–8:58 CT, during the 3rd failed breakdown. |
| 2026-09-28 | Manual — put after the confirmed 9:05 break (trade #3) | QQQ 731P 0DTE | 0.40 | 0.29 | 1 | −11.12 | −28% | No — over the 2-trade max; sold by hand | 9:14–9:16 CT, bought after the move, sold on the bounce. |
| 2026-09-28 | Manual — call against the trend (#4) | QQQ 741C 0DTE | 0.34 | 0.24 (Guardian stop) | 1 | −10.12 | −29% | No — no call trigger, over max | 9:18–9:29 CT. Stop worked as designed. |
| 2026-09-28 | Manual — call against the trend (#5) | QQQ 740C 0DTE | 0.41 | 0.29 (Guardian stop) | 1 | −12.12 | −29% | No | 9:33–9:37 CT. |
| 2026-09-28 | Manual — bounce call (#6) | QQQ 738C 0DTE | 0.31 | 0.25 | 1 | −6.12 | −19% | No — sold by hand | 9:50–9:54 CT. |
| 2026-09-28 | Manual — same contract re-bought (#7) | QQQ 738C 0DTE | 0.32 | 0.31 (Guardian trail stop) | 1 | −1.12 | −3% | Stop managed it | 10:00–10:17 CT. Peaked 0.48 (+48%); first live TRAIL moved the stop to breakeven 0.32; filled 0.31. |
| 2026-09-28 | Manual — put (#8) | QQQ 729P 0DTE | 0.28 | 0.26 | 1 | −2.12 | −7% | No — and no Guardian stop was placed | 10:18 CT, held 20 s. Guardian window likely paused (see notes). |
| 2026-09-28 | Manual — call (#9) | QQQ 740C 0DTE | 0.22 | 0.12 (Guardian stop) | 1 | −10.12 | −45% | No | 10:25–10:43 CT. Guardian stop placed 1 m 43 s after the fill (window paused?). |
| 2026-09-28 | Manual — call (#10) | QQQ 739C 0DTE | 0.21 | 0.44 (Guardian trail stop) | 1 | +22.88 | +110% | Stop managed it | 10:48–11:19 CT. Trailed 0.11 → 0.21 → 0.27 → 0.41 → 0.44. |
| 2026-09-28 | Manual — call, added a 2nd contract (#11) | QQQ 744C 0DTE | 0.135 avg | 0.09 (Guardian stop) | 2 | −9.24 | −33% | No | 11:21–11:23 CT. |
| 2026-09-28 | Manual — call (#12) | QQQ 741C 0DTE | 0.40 | 0.79 (Guardian safety-net sell) | 1 | +38.88 | +98% | Stop managed it | 11:24–11:29 CT. Unprotected 11:24–11:28 (window paused); on resume trailed 0.28 → 0.77 → 0.80, stop-limit rejected above market, safety net sold at 0.79. Best was +$66. |
| 2026-09-28 | Manual — put (#13) | QQQ 733P 0DTE | 0.23 | 0.13 | 1 | −10.12 | −43% | No | 12:01–12:24 CT. Guardian stop only from 12:20 (window paused 47 min). |
| 2026-09-28 | Manual — call (#14) | QQQ 741C 0DTE | 0.37 | 0.25 (stop) | 1 | −12.12 | −32% | No | 12:25–12:26 CT. |
| 2026-09-28 | Manual — call (#15) | QQQ 741C 0DTE | 0.29 | 0.31 | 1 | +1.88 | +7% | No | 12:31–12:34 CT, sold by hand. |
| 2026-09-28 | Manual — call (#16) | QQQ 742C 0DTE | 0.23 | 0.22 | 1 | −1.12 | −4% | No | 12:35–12:37 CT, sold by hand. |
| 2026-09-28 | Power hour — put on the 2:05 trigger (#17) | QQQ 736P 0DTE | 0.42 | 0.31 (user's own stop order) | 1 | −11.12 | −26% | Partly — valid trigger (1-cent close), but $42 = 75% of the account and no Guardian stop | 14:15–14:17 CT. QQQ then fell to 736.1 by 14:40. |

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
| 2026-09-25 | QQQ 748C closed | −$13.12 | $172.41 | $192.65 |
| 2026-09-25 | QQQ 741P closed — done for the day | −$10.12 | $162.29 | $192.65 |
| 2026-09-28 | Start of day per Webull ($162.29 − $122.57 = −$39.72 not reconciled: not in the Webull order history for today; check Friday after 12:01 CT / transfers) | −$39.72 | $122.57 | $192.65 |
| 2026-09-28 | Morning: 9 trades (8 losses, 1 at −$1) | −$67.08 | $55.49 | $192.65 |
| 2026-09-28 | After 10:30: 8 more trades (3 wins: +$22.88, +$38.88, +$1.88) | +$19.95 | $75.44 | $192.65 |

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
- Final 2026-09-25: 12 trades (4 wins, 8 losses), day +$71.47, balance $162.29 (+60% vs $101.30 start on 09-23).
  Two trades made the day (740P +$29.88 at the open, 744C +$117.88 on the 11:00 breakout); the other 10 net −$76.
- Rules for next session: max 2 trades/day; stop placed immediately; no entries 10:30–13:30 CT; stop for the
  day after 2 losses or when green after a winner.

## Notes 2026-09-28 (first live day of the Trade Guardian)
- Plan: max 2 trades; QQQ/SPY levels from the volume profile (QQQ calls > 741.30, puts < 737.50, no-trade 737.5–741.3).
- Market: gap down, 3 failed breakdowns 8:31–8:53 CT, then a real break at 9:05 CT; QQQ trended from 737.5 to 731.6 by 9:48.
- Result: 9 trades, all closed at a loss (one −$1.12 at breakeven), day −$67.08 (Webull), balance $55.49.
- What went wrong: 7 trades over the 2-trade max; the two puts taken in the right direction were sold by hand within
  1–2 minutes instead of being left to the stop; calls #4–#7 were bought against the trend with no trigger.
- What worked (Guardian, all proven live): 8:30 order test passed; stop orders accepted by Webull (STOP ORDER CONFIRMED);
  stops placed 1–5 s after fills on trades 1–7; stepped aside when the user sold by hand; protected a re-bought contract;
  first live TRAIL (stop 0.22 → 0.32 breakeven at +40%) turned a +48% peak into −$1 instead of a loss; 4 stop fills
  capped losses at the planned ~$10–12.
- Bug/issue to fix: after ~10:10 CT the Guardian went quiet (user's window output stopped at 10:09; trade #8 got no stop,
  trade #9's stop came 1 m 43 s late). Most likely cause: selecting text in the cmd window (Windows "QuickEdit") pauses
  the program until Esc/Enter. Fix candidate: turn QuickEdit off at Guardian startup.
- Afternoon (after the notes above): 8 more trades, net +$19.95. Both real winners (739C +$22.88, 741C +$38.88) were
  exited by the Guardian's trailing stop / safety net. Final day per Webull: 17 trades, −$47.13, balance $75.44.
- Guardian pauses confirmed from Webull timestamps: 11:23–11:28 CT and 11:33–12:20 CT (no heartbeat lines) while the
  user copied text from the window. Fixed 09-28 night: QuickEdit is turned off at startup, a restarted Guardian picks
  up its own stop orders (state in logs/guard-state-DATE.json), and any pause over ~40 s is reported when it wakes.
- Rules for next session: max 2 trades, enforced — lockout on (sell anything past trade 2) or KILL.bat after trade 2;
  no selling by hand while the Guardian's stop is on; only trade the trigger direction; default quantity 1.

## Review every 5 trades

- Win rate:
- Average win / average loss:
- Setup A vs Setup B results:
- Rules broken:
- Change for next 5 trades:

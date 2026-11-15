# Apex Basketball System — Phases 3 to 10
Date: 2026-11-04 night (Central). Everything below was run on the history already on the Mac: 2 seasons, 20,837 clean PrizePicks NBA props, 66,916 player box scores, book lines before tip. Nothing touched Apex Tennis. Nothing is live.

Test standard used everywhere: split the props into an OLDER half (before 2025-11-10, 7,605 props) and a NEWER half (2025-11-10 onward, 8,026 props). A rule PASSES only if it wins 55%+ in BOTH halves with 60+ picks in each. 55% is about break-even on a PrizePicks standard 3-pick slip.

Full number tables (on the Mac, ~/ApexSports/basketball/reports/):
- 2026-11-04_phase3_edges.md — every single fact alone
- 2026-11-04_phase3b_boards.md — combined rules, rankings, board sizes, honest probability
- 2026-11-04_phase3c_goblin_demon.md — Goblin/Demon estimate

---
## PHASE 3 — Edge discovery (DONE)

### The from-scratch projection
Minutes = 60% last 5 games + 40% last 10. Per-minute rate = 40% last 5, 35% last 10, 25% last 40. Opponent factor = what the opponent allowed in its last 15 games vs league average. Spread of outcomes = spread of the last 10 games. Side = MORE if projection is above the PrizePicks line. 15,631 props projected (3,038 free-throw props skipped: no free-throw numbers in the box scores; 1,991 skipped: player had no box score that game, mostly did-not-play).

### What matters (evidence, both halves)
1. **PrizePicks line vs book line ("room") — the strongest fact.** When the PP line sits 1+ below the books and you take MORE: 426-344 older, 521-404 newer (56%). When PP sits 1+ above the books and you take LESS: 468-338 older, 409-314 newer (57%). No projection needed. Sample 1,900+. Confidence: HIGH (same as tennis: room is the lead). Risk: PP may tighten these lines; one book only on 60% of props.
2. **Books leaning against the projection kills it.** Projection against the room: 309-374 older, 346-434 newer (45%). Never pick against the room. Confidence: HIGH.
3. **Hot player + LESS.** Player 15%+ above his 40-game average over the last 5 games, projection says LESS: 408-279 older, 385-306 newer (58%). Hot + LESS with room agreeing: 73-47 and 70-44 (61%). Hot + MORE is 50%. Streaks fade. Sample 1,378. Confidence: MEDIUM-HIGH.
4. **LESS beats MORE across the board.** All projection LESS picks 54%/53%; MORE 49%/51%. Betting LESS on every prop blind: 52%/51%. PrizePicks NBA lines lean high. Confidence: HIGH.
5. **Room size.** Room 1.5+: 80-56 and 103-59 (61%). Room 2+: 63-45 and 80-45 (61%). Bigger gap, better. Sample 298. Confidence: MEDIUM (small).
6. **Stat types with room:** assists 55-37 / 57-35 (61%) PASS; points+assists 60-36 / 52-26 (64%) PASS; rebounds 56%/61% PASS; PRA 56%/59% PASS. Points alone only 52%/53% (fail). Three-pointers with room 47%/39% (fail; avoid). Confidence: MEDIUM.

### What does not matter (or hurts)
- **The projection by itself: 52%/52%.** Its "80%+ sure" bucket wins only 57%/55%. Raw projection chance is NOT honest (Brier 0.266, worse than a flat 52%). Confidence: HIGH. Meaning: a box-score projection alone cannot be the score. The market already knows the box scores.
- Back-to-back (55% then 48%: flips), rest days (50-53%), home/away (52/52), opening spread (50-54%, newer half only, no spread on file for the older half), game total (50-52%), minutes trend (54/53 up, 51/52 down: small), cold form (52/52), player history length. None passes. Pace proxy (game total) shows nothing.
- Pinnacle lines: on file for only 58 props. Cannot judge yet.
- Line move open→close (CLV): 53% toward us, 50% against; known only after tip, not usable pre-tip.

### Not testable yet (literally no data)
Injuries, lineups, usage rate, defensive rating, travel, Fantasy Score lines, real Goblin/Demon lines (collectors started 2026-11-04 and are saving all of it).

### Goblin and Demon estimate (Phase 3c)
Real PrizePicks gaps measured tonight: Goblin line is about 5 below standard on points, 6 on PRA, 2 on assists/rebounds, 1 on threes. Demon is about 1 above on everything, 1.5 on PRA. Applying those gaps to the history:
- Goblin MORE, every prop: 5208-1363 / 4020-1017 (79-80%). Break-even on a 3-pick Goblin at 2x is 79%. PrizePicks prices Goblins exactly at break-even.
- Goblin MORE with projection MORE 60%+: 1384-297 / 1124-203 (82-85%). Room favors MORE and projection MORE: 82%/84%. Assists Goblin alone 87%/85%.
- Demon MORE every prop 36%/37%; best filter (room favors MORE) 44%/44%, under the 47% needed. Demons are a losing product on NBA.
Confidence: LOW-MEDIUM. The gap came from one night and PP decides WHICH players get a Goblin line, so real Goblin hit rates will differ. The saver is recording real Goblin lines from now on; re-run this in 2-3 weeks on real lines.

---
## PHASE 4 — Simulation engine design (DESIGNED)
Purpose: turn the facts above into one chance number per prop and per side, then let boards and calibration use it.

**Inputs (per prop, all available now):** PrizePicks line, odds type (standard/goblin/demon), stat; player last 40 box scores (minutes, points, rebounds, assists, threes, steals, blocks, turnovers, FGM); opponent last 15 team games; book lines before tip (median, count, Pinnacle when present); game spread and total; rest days, back-to-back, home/away; form (last 5 vs last 40). **Plug-in slots (filled later by the collectors):** injury status of the player and his top-3 teammates by minutes, confirmed starters, travel distance, Fantasy Score lines.

**Flow:**
1. Minutes model: expected minutes = 60/40 blend of last 5/10 (as tested). Later: cut when Questionable/Out teammate data exists (slot).
2. Rate model: per-minute rate 40/35/25 blend × opponent factor (0.8-1.2 cap).
3. Market anchor: the book median line is treated as a second projection with weight 0.6 (the projection alone was 52%; the books are better). Anchored projection = 0.4 × ours + 0.6 × book line (book line is the market's median outcome). When no book line: ours only, flagged "no book".
4. Distribution: Normal for points, PRA, PR, PA, RA, fantasy (continuous, spread = last-10 spread, floor 1). Poisson-style (discrete) for assists, rebounds, threes, steals, blocks, blocks+steals, FGM with mean = anchored projection, because low counts are skewed. Variance inflated 10% on back-to-back and 15% when the spread is 10+ (blowout minutes risk), both flagged, until injury data proves otherwise.
5. Raw chance per side = tail of that distribution past the line (MORE: P(X > line), LESS: P(X < line); whole-number lines carry a push chance).
6. Honest chance = raw chance mapped through the calibration table (Phase 7). This is the number boards use.
7. Output per prop: player, team, opponent, stat, line, odds type, side, raw chance, honest chance, room (PP minus book), room side, hot/cold flag, b2b flag, blowout flag, no-book flag, data-age flag.

**Assumptions:** box scores complete; book lines before tip reflect the market; player will play (until injury slot is live, a player with no box score in his team's last game is held OFF the board: this removes most of the 1,991 did-not-play props). **Variance modeling:** last-10 spread, never under 1; inflation rules above. Monte Carlo is not needed: closed-form tails of Normal/Poisson are exact and instant (he hates slow jobs).

Evidence: the pieces were each tested in Phase 3 (projection alone 52%, book anchor 57% with room). Confidence MEDIUM for the design, HIGH that it runs fast. Risk: anchoring on books makes us close to the market; the edge must come from room and the fade-the-hot-streak rule, not from beating the books. Next: code it as code/sim_engine.py, run over all 15,631 props, confirm the honest chance buckets line up (Phase 7).

---
## PHASE 5 — Scoring framework (DESIGNED, NBA evidence)
Question: rank by what? Tested rankings (whole-board results in Phase 6 below):
- A. Projection chance only → worst board (Top 3 days 54-263, 17%).
- B. Room first, then projection → Top 3 42-159 (21%).
- D. Room 1+ agrees, projection order → Top 3 45-146 (24%).
- E. Room agrees, LESS only → Top 3 32-96 (25%), fewest days.

**Decision: NBA has its own score, not the tennis Apex Score.** NBA Score = honest chance (from Phase 7 table) ranked high to low, with eligibility gates, not point bonuses. Gates (a pick must pass all to be on any board, same for every board, every pick, all day):
1. Room agrees with the side (PP line on the easy side of the book median), room 0.5+.
2. Not against the books (automatic from gate 1).
3. Played in his team's last game (did-not-play guard) until injury data arrives.
4. Stat type not three-pointers (47%/39% with room).
Informational flags on the card, no score change: 🔥 hot player (supports LESS), 📅 back-to-back (room agrees + b2b 53%/53%: warning), 🏟 spread 10+ (blowout minutes risk), 📚 book count (1 book vs 2+: 56% vs 57%; 2+ slightly better), 🟢 Goblin estimate.
Score as filter vs information: the gates ARE the filter; the honest chance is the order. Evidence: room-gated boards beat projection-ranked boards in both halves at every size. Confidence MEDIUM-HIGH. Risk: gate 1 leaves ~700 eligible picks per half (~5 per day); some days will have under 3 picks → post "no board today" (he prefers no pick over a bad pick). Next: encode gates in code/score_board.py v2 and re-run the day-by-day replay.

---
## PHASE 6 — Board framework (TESTED on history)
One slip per day, top N by rule, every leg must win (days won-lost, older / newer half):

| Board | Rule D (room 1+, projection order) | Rule E (room agrees, LESS only) | Rule A (projection only) |
|---|---|---|---|
| Top 3 | 20-67 / 25-79 | 18-49 / 14-47 | 24-107 / 30-156 |
| Top 5 | 6-59 / 5-65 (+35 days at 4 of 5) | 6-34 / 6-38 (+11 at 4/5) | 6-124 / 9-163 |
| Top 6 | 2-54 / 3-58 (+17 days at 5 of 6) | 5-30 / 5-31 (+7 at 5/6) | 2-126 / 4-160 |
| Top 10 | 0-33 / 0-36 | 0-21 / 0-16 | 0-116 / 1-150 |

Money check at $[amount] a day with real PrizePicks payouts (3-pick Power 6x, 5-pick Flex 10x/2x, 6-pick Flex 25x/2x; 4-of-6 refund not counted):
- Top 3, rule D: 45 wins × $[amount] = $[amount] on $[amount] staked → $[amount] over 191 days. Rule E: $[amount] over 128 days. Rule A: $[amount] over 317 days (coin flip).
- Top 5 Flex, rule E: $[amount] over 84 days. Rule A: $[amount].
- Top 6 Flex, rule E: $[amount] over 71 days; rule D $[amount] over 117; rule A $[amount] over 292.
- Top 10: 1 full win in 1,000+ board-days under any rule. Dead.

**Recommendations:** best board size = Top 3 (most days, best full-win rate 24-25%). Best slip structure = 3-pick Power on standard lines; 6-pick Flex only on days with 6 gated picks (rare). Standard structure = room-gated LESS-leaning picks (rule E when 3+ exist, else rule D). Goblin structure = MORE picks with projection 60%+ and room favoring MORE (estimated 82-84% per leg vs 79% needed) — a Best Goblin 2- or 3-pick card, test on real Goblin lines first. Demon structure = none; every Demon filter fell under break-even (44% vs 47% needed). Tennis sizes (Top 3 / Elite 5 / Elite 6) do not carry over: NBA Top 6 full wins are 4-14% of days. Confidence MEDIUM (191 board-days for Top 3; rule E only 128). Risks: payout table changes; days with under 3 gated picks; real Goblin lines differ from the estimate. Next: Phase 8 shadow replay day by day with the full engine, then shadow-post in the TEST Discord server.

---
## PHASE 7 — Calibration design (BUILT, first result)
- **Raw probability** = the engine's distribution tail (Phase 4).
- **Honest probability** = won-lost rate of picks in the same bucket (room size × raw chance bucket × side) over the training window, with a light shrink toward 52%. Built tonight: learned on the older half, applied to the newer half. Brier: raw 0.2655, honest 0.2496, flat-52% 0.2497. Honest beats raw clearly; it only equals flat because the current raw chance carries almost no information. Once the engine anchors on books (Phase 4) the raw number should improve and honest should separate from flat. Buckets that held up out of sample: room 1+ / MORE / raw 55-60: 70-45 older → 73-41 newer (64%); room 1+ / MORE / raw 70+: 59-45 → 85-52 (62%); against the room: 39-49% in both halves (never pick).
- **Monitoring:** every day the bball bot stores raw chance, honest chance, result per pick (shadow or posted). Weekly card: Brier (raw, honest) on the last 7 and 30 days, bucket table (expected vs actual won-lost), flagged when any bucket with 40+ picks is 8+ points under its label.
- **Promotion requirement for the honest table:** retrained only on completed days; a new table goes live only if it beats the old one on the most recent 30 days (Brier) and no 40+ bucket is 8 points off.
Confidence MEDIUM. Risk: bucket sizes under 60 are noisy; keep 12-24 buckets maximum. Next: code/calibration.py with a stored table (calibration/honest_table.json) and the weekly card.

---
## PHASE 8 — Shadow mode framework (RULES SET)
Lessons from tennis applied: no paper tests when history exists; both halves; whole-board days, not per-pick; never change a live rule on a one-day gap; a rule applies to every board the same way; save point before anything goes live.
- **Replay first:** every candidate board runs on all history (walk-forward: rules fixed on the older half, judged on the newer half) before any shadow posting.
- **Shadow posting:** boards post in the TEST server only (🧪), graded nightly, results stored in shadow_tests/.
- **Sample requirements:** Top 3 needs 40 shadow days; Goblin card 40 days; a single rule change needs 60+ picks each side of the change.
- **Promotion rule (PROMOTION CANDIDATE card):** board beats its baseline (same size, projection-only ranking) on days won in the shadow window AND the full history replay, and wins at least the break-even rate for its payout (Top 3 Power: 1 in 6 days, target 1 in 4).
- **Failure rule (TEST FAILURE card):** under break-even over 40 days, or honest buckets off by 8+, or 0 wins in 15 straight days → stop the test, write the reason to DECISIONS.md.
- **Progress (TEST PROGRESS card):** every 10 shadow days: days W-L, legs W-L, Brier, days left.
- **Validation standard:** the final decision uses real posted boards only; replays are labeled replay.
Confidence HIGH on the rules (they are the tennis standard, already agreed). Risk: 40 shadow days is ~6 weeks; history replay carries the weight until then. Next: code/shadow_runner.py.

---
## PHASE 9 — Discord operations (DESIGNED, Discord-only)
Bot: the existing Apex basketball bot (separate token, separate "Apex basketball" server, currently 🧪 TEST). Channels (same names as tennis so the style matches): #general (boards), #alerts (line drops, injury changes on a board player, late scratches), #slips (grading per board, won/lost per leg), #system (every automatic job posts one line: line saver, injury saver, scoring, calibration; silence is a bug), #pnl (his real slips only, logged from screenshots), #integrity (data checks).
Cards (tennis style, first + last names, won-lost records, no percentages to him on cards unless he asks):
- **Board card** (daily, time to be set by him; data shows most NBA lines land midday): Top 3 on standard lines, each pick: player, team v opponent, stat, line, side, 🟢/🔴 odds type, honest chance, signal line in plain words ("PP line 2 under the books", "hot last 5, fading", "back-to-back ⚠"). Best Goblin card when 2+ qualify. "No board today" when under 3 gated picks.
- **Grading card** nightly in #slips: ✅/❌ per leg, day won/lost, running record since the rule went live.
- **Integrity alerts** in #integrity: line saver missed 2 pulls; injury saver stale 2+ hours; a board player turns Out/Doubtful (also #alerts); PP line moved 1.5+ on a board pick; book line missing on a board pick; grading mismatch between ESPN box and result.
- **Promotion / Test failure / Test progress cards** in #system as defined in Phase 8.
- **Daily status card** 9 AM CT in #system: props saved yesterday, injuries saved, boards posted, graded, Brier 7-day, collectors alive (pids), disk.
- Commands: /nba3 (Top 3 now), /nbagoblin, /nbastatus, /nbatest (test progress). No Mission Control, no web page.
Confidence HIGH (mirrors what already runs for tennis, built separately). Risk: two bots in one Discord account need distinct names/emoji so he never confuses sports. Next: extend discord/bot.py with the card templates; stays 🧪 TEST until his go.

---
## PHASE 10 — Profitability roadmap (from history)
1. **Most promising prop types:** assists (room agrees 60%/62%), points+assists (62%/67%), rebounds (56%/61%), PRA (56%/59%) — standard lines, LESS leaning. Goblin MORE on assists (estimated 85-87%).
2. **Weakest:** three-pointers made (47%/39% even with room), steals and blocks alone (too few props, no edge), points alone (52-53%), turnovers (50 props), any Demon (36-44%, under break-even).
3. **Best board candidates:** (a) NBA Top 3 Power, room-gated, LESS-leaning: 24-25% full-win days vs 17% needed; (b) Best Goblin 3-pick, MORE with projection 60%+ and room favoring MORE: estimated 82-84% per leg vs 79% needed (must be re-tested on real Goblin lines).
4. **Highest expected edge:** room 1.5+ in our favor (61% both halves, 298 picks); hot player + LESS with room agreeing (61%, 234 picks). These are the picks that should sit at #1-#3.
5. **Highest-risk categories:** MORE picks on players with the PP line at the book line (49-52%); any pick against the room (45%); Demons; three-pointers; back-to-back MORE picks; players without a box score in the team's last game (did-not-play risk, 1,991 props); Top 6 and Top 10 boards (full wins 0-7% of days).
Order of work (biggest payoff first): Phase 4 engine → Phase 5/6 replay with the engine → Phase 7 table → Phase 8 shadow in TEST server → his go for a live board.

---
## PHASE 4 FIRST BUILD (ran tonight, code/sim_engine.py, report 2026-11-04_phase4_engine.md)
- Book-anchored engine: raw chance Brier 0.2513 / 0.2514 (was 0.266 for the box-score projection alone); 80%+ bucket now 67% / 68%.
- Gated picks (room agrees 0.5+, not threes): 921-693 older, 1003-769 newer (57% both). Honest table v1 saved to calibration/honest_table_v1.json (learned on the older half only).
- Walk-forward boards on the newer half (rules fixed on the older half): Top 3 ranked by room size then honest chance 35-95 days (27%), $[amount] a day at 6x = $[amount] over 130 days; honest-first 28-102 (22%); all-props baseline 34-152 (18%). Top 5 and Top 6 full wins 4-6 and 3 days: not boards.
- Thin honest slices over-fit (58%+ bucket: 64% older → 54% newer). Honest chance stays a card number, not a gate.
- PrizePicks 0.5/1.5 lines vs book 2.5+ look like promo lines (17-3 total, tiny): flagged separately, not counted as room.
- Days with no board (under 3 gated picks): 69 of 199 newer-half days. Post "no board today".
Next: shadow runner that posts this Top 3 in the TEST server daily and grades it; re-test Goblin card on real Goblin lines after 2-3 weeks of saved lines.

## PHASE 6 WITHOUT BOOK LINES (his 11/4 11:43 PM decision: no book feed)
Report reports/2026-11-04_phase6_no_book_lines.md. No-book rules that pass both halves: hot player (+15% last 5 vs 40) and LESS 408-279 / 385-306; very hot (+25%) and LESS 272-186 / 247-176; projection MORE 80%+ 81-53 / 88-67. Best no-book Top 3 (hot+LESS or projection MORE 80%+, ranked by projection): 18-55 older, 23-73 newer (24-25% of days, break-even 17%), $[amount]/day at 6x = $[amount] over 169 days; 163 of 332 days had under 3 picks (no board). Top 5/6 full wins 2-10%: not boards. Compared with book lines: 24-27%, so little is lost on win rate but half the days go dark.

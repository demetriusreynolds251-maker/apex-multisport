# Apex Basketball - Phase 4 Redesign: Room Qualification -> Projection Ranking -> Board Construction
Date: 2026-11-05 ~7:30 AM CT. Ordered by owner after the Room Edge Study and Board Replay.

## Why the redesign
Historical evidence on 14,157 played, graded NBA props (8 board stats, 331 slate days, both halves, both seasons):
- Projection alone picks the right side 52-54% of the time. That is break-even for a 3-pick Power slip (needs 55% a leg).
- Room Edge 2 (PrizePicks line 1+ above the books -> LESS, or 2+ below -> MORE) wins 58% a leg in every half and every season.
- Projection confirmation adds nothing to Room Edge 2 (58% whether the projection agrees or not), but ranking Room Edge 2 picks by projection chance gives the best Top 3 boards (23-25% of days win in full, break-even is 16.7%).
So the system is no longer projection-first. The market line gap is the edge; the projection only decides the order.

## The new pipeline (every run, every board)
1. ROOM QUALIFICATION (code/room_edge.py, built 11/5)
   Input: every live PrizePicks standard line on the 8 board stats, every live book line for the same player and stat.
   Room = PrizePicks line minus the median book line.
   Room Edge 2 = PP 1+ above -> LESS, or PP 2+ below -> MORE. Board eligible.
   Room Edge 1 = PP exactly 1 below -> MORE. Fill and backups only.
   Room Edge 0 = same line, half-point gap, or no book line. Never on a board.
   Excluded stats: 3-pointers, steals, blocks, turnovers, free throw attempts, blocks+steals. Fantasy Score built separately, not on boards until tested on real lines.
   Output per candidate: edge (0/1/2), side, room, plain-words text ("Room Edge 2: PrizePicks line 1.5 above the books, LESS").

2. PROJECTION RANKING (code/sim_engine.py, repurposed)
   Runs only on candidates with Room Edge 1 or 2, on the side the room says. Never flips the side, never gates.
   Order inside each tier: higher projection chance first. Chance is shown on the card as the Apex number; it is an ordering number, not a win chance promise.
   Removed from Phase 4: projection-as-gate (60%/80% floors), book-blend scoring as the main rank, honest-table gate. The honest table stays as a card number only.
   Phase 4 simulations from here on test ordering rules among room-qualified picks (projection, hot fade, injury/lineup, rest), not discovery.

3. BOARD CONSTRUCTION (code/board_builder.py, to build on his go)
   NBA TOP 3: tier 1 = Room Edge 2 picks ranked by projection; one pick per game, one per player. If fewer than 3, fill from Room Edge 1 picks ranked by projection (see Frequency Study). Fewer than 3 total = "No board today" line (silence is a bug).
   BACKUPS: the next Room Edge 2 and Room Edge 1 picks, in order.
   Flags on every card: Room Edge 2/1 text with the gap, 🔥 hot player (last 5 games 15%+ above last 40) on LESS picks, injury note when the ESPN feed shows Out/Doubtful on a teammate, book count ("3 books").
   No Elite 6, Top 10 or Demon board (0-8% full wins in replay; Demons 36-44% a leg).
   Posting: #bball-picks once lines and book lines are both saved for the slate (biggest PrizePicks drop 12-1 PM CT; board after 4 PM CT when the slate is settled); re-post only if the board changes; one line in #bball-system every run.
   Grading: next morning after 5 AM CT from ESPN box scores; whole-slip won-lost record by day plus legs, both posted to #bball-slips; weekly line in #bball-system.

## Live inputs this needs
- PrizePicks lines: code/line_collector.py (running, every 30 min).
- Book lines: NOT on the machine. SportsGameOdds trial ends 11/6. Plan: The Odds API (free 500 credits a month covers about 4 games a night of player markets; $[amount] a month covers a full slate). Needs his go ("go odds api").
- Injuries and schedule: code/injury_collector.py (running).
- Results: code/espn_results.py.

## What changes in existing code
- shadow_runner.py (no-book Top 3, running since 11/5 12:40 AM CT): contradicts this design. Stop on his word ("stop shadow"), or leave as a comparison board clearly labeled NO-BOOK TEST.
- sim_engine.py: keep math, remove gates, expose rank_chance(candidate) only.
- phase6_nobook.py: archive, no longer part of the design.
- room_board_replay.py / room_frequency_study.py: become the standing replay for any future rule change (TESTING_STANDARD: both halves, 60+ picks, wins on picks and loses no days in either half).

## Evidence, sample, confidence, risks
- Room Edge 2 58% on 1,717 legs; 25% / 21% of Top 3 days in the two halves; $[amount] at $[amount] a day over 154 days. High confidence on direction, moderate on size (real long run about 1 win in 5 days).
- Room Edge 1 fill raises board days from 47% to 62% of slates and kept 25% full wins in both halves ($[amount] total). On added days alone 17-35 (33%) is a small sample; the honest expectation from the 55% leg rate is about 1 win in 5-6 days, so fill adds volume at roughly break-even to slightly positive. Not a profit engine, a frequency engine.
- Hot Fade as fill: legs 58% older half, 54% newer half; added days 8-28 (22%). Weaker and fading. Keep 🔥 as a flag and order tiebreak, not a fill rule.
- Risks: book lines in history came from the SGO archive (median of several books); a different live feed may show different gaps; PrizePicks may already move lines faster live than history suggests; 2026-27 season has 4 days only. Review after 40 board days.

## Gos needed (in order)
1. "go odds api" - set up the live book-line feed, compare one night of lines with SGO before the trial ends.
2. "go board builder" - build code/board_builder.py per section 3, TEST server first.
3. "stop shadow" - turn off the no-book shadow runner (or "keep shadow" to leave it as a labeled comparison).

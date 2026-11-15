# Decisions
Each go from the owner, in his words. All 10/31/2026. The quotes reached this project through the coordinating session.
- "Hi best reach sports test": the best-of-each-sport test. Stopped the same day in favor of doing it the tennis way.
- "Go step 2 1": run Steps 1 and 2 of the plan for NBA, offline.
- "Yes I want this not to touch apex current set up all this should be separate": all work stays outside Apex.
- "Yes this goes for all extend sports each should have its own folder with information professional and cleanly step as if I was a major corporation and had to show others and they can understand what's going on": this layout, for every sport.
- "Step 3" (2:17 PM CT): build basketball Win Probability, offline.
- "Go ... bball bot": build the separate Apex Basketball bot, everything marked 🧪 TEST.

## Build choices on the bot, not his words, open to his change
- Top 3 is Power. Elite 5 and Elite 6 are Flex, as tennis Elite 6 is.
- Promo and flash sale lines are off boards and slips, and show in All Props.
- `/bball-ban` takes off only that player, not the whole game. A basketball game has too many players for the tennis rule.
- A Demon in a Power slip pays the lowest table number, 2.2x, as tennis does. A void or push leg asks for the app amount.
- `/bball-fetch`, ban, unban and cancel are owner only.
- A line on a board needs Win Prob 70 even for backups. All Props also lists lines under 70, marked as off every board, because 70+ is so rare.
- 10/31: Step 5 stop rule hit. Standard Top 3 14 of 108 on unseen games. Next test needs real Goblin labels from the collector.

## 2026-11-05 ~1:30-2:30 PM CT - Probability engine (his 1:24 PM spec)
- Built code/prob_engine.py: for every PrizePicks NBA line a projected result (mean + spread), Over % / Under %, confidence with the factor breakdown
  (base projection, recent form, minutes trend, matchup, pace/blowout, rest/home, teammates out, market consensus), tier A/B/C/D, EDGE SCORE, reasons.
  Goblin / Standard / Demon lines each get their own % (over only on Goblin and Demon). Books are one blended factor, not the gate.
- Fit on the first half of history only (spread scale per stat, book weight); checked on the second half. Report: reports/2026-11-05_prob_engine_backtest.md.
- Nothing on a board. `today` output is a report card to #bball-picks with the TEST footer, only on his go.
- Not available live yet: game totals/spreads (neutral factor), usage/TS%/touches/defensive ratings (no source on the Mac), 3PTM/steals/blocks/turnovers after 10/30 (ESPN box scores carry pts/reb/ast/FG only).

## 2026-11-05 2:19 PM CT - His direction: "Stop focusing on additional prediction features... Priority is making Apex Basketball follow the same production pipeline as Apex Tennis: scheduled fetches, historical storage, rule filtering, Discord posting, automatic grading, daily summaries, performance tracking... using the new probability engine as the decision layer."
- code/engine_scorer.py: the probability engine scores every saved PrizePicks line for the pipeline (Win Prob = engine chance, tier, EDGE SCORE, reasons). Replaces the Step 3 scorer in bball_pipeline.rescore.
- Rules: NBA only, board stats only (Points/Reb/Ast/PRA/PR/PA/RA), Goblin/Demon over only, promo off boards, bans, one pick per game, floor = engine recommend line 60 (data/prob_engine_config.json).
- Bot (discord/bot.py): keeps the three collectors alive (checks every 5 min, restarts, posts to #bball-system); boards post on change, slips in #bball-slips, grading 4 AM (ESPN box scores), settled slips #bball-slips-pnl, 9 AM status line, daily paper P&L, learning card.
- Stopped: shadow_runner (old no-book rule, pid 3606) and the 4:10 PM nba_cards job; the engine boards replace them. Undo: `nohup python3 code/shadow_runner.py --loop &`.
- Commit bf758e8.

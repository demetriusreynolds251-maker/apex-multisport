# Changelog
## 2026-10-31
- Step 1 data check. Read the saved NBA files. Found 20,837 testable props across 1,928 games.
- Step 2 player history. Built `data/processed/nba_history.sqlite`: 66,916 player-games, 677,811 prop lines.
- Moved everything from `~/openclaw/other_sports`, then `~/openclaw_basketball`, into `~/ApexSports/basketball`. Row counts checked after the move.
- Step 3 Win Probability. Added `code/win_probability.py`, `data/processed/step3_predictions.sqlite`, and the Step 3 report.
- Apex Basketball bot built, not started. Added `code/score_board.py`, `code/espn_results.py`, `code/bball_tracker.py`, `code/bball_pipeline.py`, `discord/bot.py`, `discord/cards.py`, `discord/start_bot.sh`, `discord/test_offline.py`, and `data/processed/nba_fgm.sqlite` (73,677 rows). Scoring matches Step 3 on 1,500 real picks.
- 10/31: Step 5 replay: stop rule hit on Standard lines; recommend no Step 6 until real Goblin labels are replayed.
## 2026-11-04
- Apex Basketball System spec received (12 phases, Discord only, no Mission Control, fully separate from tennis). Saved under DECISIONS.md.
- Phase 1 data audit and Phase 2 prop inventory written (reports/2026-11-04_phase1_data_audit.md, reports/2026-11-04_phase2_prop_inventory.md).
- Line collector v2: partner API host, NBA every 30 min 8 AM-midnight CT, keeps Goblin/Demon/Standard labels and PrizePicks game ids. v1 had never saved a line.
- Folder structure per spec added: config/, models/, simulations/, boards/, calibration/, shadow_tests/, notifications/.
- ARCHITECTURE.md added (phases, status, risks).
- Injury + schedule collector (ESPN, free): code/injury_collector.py, every 30 min, data/collected/injuries and data/collected/schedule. First pass 89 listed players, 14 games.

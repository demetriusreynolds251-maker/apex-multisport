# Apex AFL 🏉

Independent Apex Sports system for AFL. Own folder, own history.db, own collectors, scheduler, models, rules, grading, reports, Discord bot and logs. It imports nothing from any other sport, from Apex Tennis or from Apex Basketball; the only shared things are two small PrizePicks pacing flags in `../_shared/`.

## Pipeline

FETCH (collectors/collector.py) -> STORE (database/history.db + database/snapshots, append only) -> PROJECT (models/projection.py + models/sport_factors.py) -> PROBABILITY (models/probability.py) -> RULES (rules/rules.py) -> PICKS (picks/pipeline.py) -> DISCORD (discord/bot.py, discord/cards.py, discord/post.py) -> GRADING (grading/results.py, grading/grade.py) -> TRACKING (reports/report.py) -> IMPROVEMENT (backtesting/backtest.py weekly re-fit).

## Run

```
nohup discord/start.sh >/dev/null 2>&1 &      # scheduler + bot, restarts both; waits for secrets/discord_bot_token.txt
python3 collectors/collector.py all          # one pull by hand
python3 picks/pipeline.py                    # score + print boards
python3 history/build_history.py             # (re)build history from the SportsGameOdds download
python3 backtesting/backtest.py              # fit + calibration report into reports/
python3 grading/results.py && python3 grading/grade.py
python3 reports/report.py daily|weekly|monthly|season
```

## Discord

Channels: #afl-picks, #afl-alerts, #afl-general, #afl-learning-channel, #afl-system, #afl-pnl, #afl-slips. Commands: /afl-fetch, /afl-top3, /afl-elite5, /afl-elite6, /afl-top10, /afl-bestgoblin, /afl-beststandard, /afl-bestdemon, /afl-backups, /afl-picks, /afl-allprops, /afl-pnl, /afl-status, /afl-ban, /afl-unban, /afl-setkey.
Token: paste it in the basketball Discord with /bball-sportkey (sport AFL, Discord bot token). Odds API key: /bball-sportkey or /afl-setkey.

## Stats scored

| stat | PrizePicks names | distribution | on boards |
|---|---|---|---|
| Disposals | disposals | normal | yes |
| Goals | goals | poisson | yes |
| Marks | marks | normal | yes |
| Tackles | tackles | normal | yes |
| Kicks | kicks | normal | yes |
| Handballs | handballs | normal | yes |
| Fantasy Score | fantasy score | normal | no (computed, not on a board) |

## Factors

**Live now:** recent form; season base; opponent allowed; home / away split; PrizePicks standard line anchor.

**Pending (no data on this Mac yet):** inside 50s; time on ground; history (none on the Mac: the engine starts once the collector has saved games).

## Rules

- Floor 70 on Top 3 / Elite 5 / Elite 6 / Top 10 / Best Goblin, 65 on Best Standard, 60 on Best Demon. Tiers A 70+, B 65-69, C 60-64, D under 60.
- Goblin and Demon lines: MORE only. Promo and flash-sale lines off. Banned players off. One pick per game on a numbered board. Players listed Out / Doubtful: no play. Under 6 games of history: no play.

## Data

History: SportsGameOdds download leagues none on the Mac (`history/build_history.py`). Live lines: PrizePicks league ids 165=AFL. Results: ESPN australian-football/afl. Books: The Odds API aussierules_afl (needs this sport's own key in secrets/).

Everything is 🧪 TEST until owner says otherwise. Nothing goes on a board without his go.
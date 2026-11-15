# Apex Rugby League 🏉

Independent Apex Sports system for Rugby League. Own folder, own history.db, own collectors, scheduler, models, rules, grading, reports, Discord bot and logs. It imports nothing from any other sport, from Apex Tennis or from Apex Basketball; the only shared things are two small PrizePicks pacing flags in `../_shared/`.

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

Channels: #rugby-picks, #rugby-alerts, #rugby-general, #rugby-learning-channel, #rugby-system, #rugby-pnl, #rugby-slips. Commands: /rugby-fetch, /rugby-top3, /rugby-elite5, /rugby-elite6, /rugby-top10, /rugby-bestgoblin, /rugby-beststandard, /rugby-bestdemon, /rugby-backups, /rugby-picks, /rugby-allprops, /rugby-pnl, /rugby-status, /rugby-ban, /rugby-unban, /rugby-setkey.
Token: paste it in the basketball Discord with /bball-sportkey (sport Rugby League, Discord bot token). Odds API key: /bball-sportkey or /rugby-setkey.

## Stats scored

| stat | PrizePicks names | distribution | on boards |
|---|---|---|---|
| Tries | tries | poisson | yes |
| Points | points | normal | yes |
| Run Metres | run metres, run meters, metres | normal | yes |
| Tackles | tackles | normal | yes |
| Line Breaks | line breaks | poisson | yes |
| Try Assists | try assists | poisson | yes |
| Offloads | offloads | poisson | yes |
| Runs | runs | normal | no (computed, not on a board) |

## Factors

**Live now:** recent form; season base; opponent allowed; home / away split; PrizePicks standard line anchor.

**Pending (no data on this Mac yet):** carries; tackle counts; minutes; history (none on the Mac); PrizePicks league id (NRL is off season; added when the board appears).

## Rules

- Floor 70 on Top 3 / Elite 5 / Elite 6 / Top 10 / Best Goblin, 65 on Best Standard, 60 on Best Demon. Tiers A 70+, B 65-69, C 60-64, D under 60.
- Goblin and Demon lines: MORE only. Promo and flash-sale lines off. Banned players off. One pick per game on a numbered board. Players listed Out / Doubtful: no play. Under 6 games of history: no play.

## Data

History: SportsGameOdds download leagues none on the Mac (`history/build_history.py`). Live lines: PrizePicks league ids none yet. Results: ESPN rugby-league/3. Books: The Odds API none (needs this sport's own key in secrets/).

Everything is 🧪 TEST until owner says otherwise. Nothing goes on a board without his go.
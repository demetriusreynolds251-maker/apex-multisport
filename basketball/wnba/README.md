# Apex WNBA 🏀

Independent Apex Sports system for WNBA. Own folder, own history.db, own collectors, scheduler, models, rules, grading, reports, Discord bot and logs. It imports nothing from any other sport, from Apex Tennis or from Apex Basketball; the only shared things are two small PrizePicks pacing flags in `../_shared/`.

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

Channels: #wnba-picks, #wnba-alerts, #wnba-general, #wnba-learning-channel, #wnba-system, #wnba-pnl, #wnba-slips. Commands: /wnba-fetch, /wnba-top3, /wnba-elite5, /wnba-elite6, /wnba-top10, /wnba-bestgoblin, /wnba-beststandard, /wnba-bestdemon, /wnba-backups, /wnba-picks, /wnba-allprops, /wnba-pnl, /wnba-status, /wnba-ban, /wnba-unban, /wnba-setkey.
Token: paste it in the basketball Discord with /bball-sportkey (sport WNBA, Discord bot token). Odds API key: /bball-sportkey or /wnba-setkey.

## Stats scored

| stat | PrizePicks names | distribution | on boards |
|---|---|---|---|
| Points | points | normal | yes |
| Rebounds | rebounds | normal | yes |
| Assists | assists | normal | yes |
| Pts+Rebs+Asts | pts+rebs+asts | normal | yes |
| Pts+Rebs | pts+rebs | normal | yes |
| Pts+Asts | pts+asts | normal | yes |
| Rebs+Asts | rebs+asts | normal | yes |
| 3-PT Made | 3-pt made | poisson | no (computed, not on a board) |
| Steals | steals | poisson | no (computed, not on a board) |
| Blocked Shots | blocked shots | poisson | no (computed, not on a board) |
| Turnovers | turnovers | poisson | no (computed, not on a board) |
| FG Made | fg made | normal | no (computed, not on a board) |
| Free Throws Made | free throws made | poisson | no (computed, not on a board) |
| Fantasy Score | fantasy score | normal | no (computed, not on a board) |

## Factors

**Live now:** recent form; season base; minutes trend; opponent allowed; home / away split; teammates out (ESPN injuries); PrizePicks standard line anchor.

**Pending (no data on this Mac yet):** usage %; pace; defense vs position.

## Rules

- Floor 70 on Top 3 / Elite 5 / Elite 6 / Top 10 / Best Goblin, 65 on Best Standard, 60 on Best Demon. Tiers A 70+, B 65-69, C 60-64, D under 60.
- Goblin and Demon lines: MORE only. Promo and flash-sale lines off. Banned players off. One pick per game on a numbered board. Players listed Out / Doubtful: no play. Under 6 games of history: no play.

## Data

History: SportsGameOdds download leagues WNBA (`history/build_history.py`). Live lines: PrizePicks league ids 3=WNBA. Results: ESPN basketball/wnba. Books: The Odds API basketball_wnba (needs this sport's own key in secrets/).

Everything is 🧪 TEST until owner says otherwise. Nothing goes on a board without his go.
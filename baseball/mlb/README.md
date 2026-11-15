# Apex MLB ⚾

Independent Apex Sports system for MLB. Own folder, own history.db, own collectors, scheduler, models, rules, grading, reports, Discord bot and logs. It imports nothing from any other sport, from Apex Tennis or from Apex Basketball; the only shared things are two small PrizePicks pacing flags in `../_shared/`.

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

Channels: #mlb-picks, #mlb-alerts, #mlb-general, #mlb-learning-channel, #mlb-system, #mlb-pnl, #mlb-slips. Commands: /mlb-fetch, /mlb-top3, /mlb-elite5, /mlb-elite6, /mlb-top10, /mlb-bestgoblin, /mlb-beststandard, /mlb-bestdemon, /mlb-backups, /mlb-picks, /mlb-allprops, /mlb-pnl, /mlb-status, /mlb-ban, /mlb-unban, /mlb-setkey.
Token: paste it in the basketball Discord with /bball-sportkey (sport MLB, Discord bot token). Odds API key: /bball-sportkey or /mlb-setkey.

## Stats scored

| stat | PrizePicks names | distribution | on boards |
|---|---|---|---|
| Hits | hits | poisson | yes |
| Runs | runs | poisson | yes |
| RBIs | rbis | poisson | yes |
| Home Runs | home runs | poisson | yes |
| Total Bases | total bases | poisson | no (computed, not on a board) |
| Hits+Runs+RBIs | hits+runs+rbis | poisson | yes |
| Walks | walks | poisson | yes |
| Stolen Bases | stolen bases | poisson | no (computed, not on a board) |
| Singles | singles | poisson | no (computed, not on a board) |
| Doubles | doubles | poisson | no (computed, not on a board) |
| Hitter Strikeouts | hitter strikeouts | poisson | yes |
| Pitcher Strikeouts | pitcher strikeouts | normal | yes |
| Pitching Outs | pitching outs | normal | no (computed, not on a board) |
| Earned Runs Allowed | earned runs allowed | poisson | yes |
| Hits Allowed | hits allowed | normal | yes |
| Walks Allowed | walks allowed | poisson | yes |

## Factors

**Live now:** recent form; season base; opponent team allowed; home / away split; park factor (static table); injury list; PrizePicks standard line anchor.

**Pending (no data on this Mac yet):** opposing pitcher; bullpen strength; batting order; handedness splits; weather.

## Rules

- Floor 70 on Top 3 / Elite 5 / Elite 6 / Top 10 / Best Goblin, 65 on Best Standard, 60 on Best Demon. Tiers A 70+, B 65-69, C 60-64, D under 60.
- Goblin and Demon lines: MORE only. Promo and flash-sale lines off. Banned players off. One pick per game on a numbered board. Players listed Out / Doubtful: no play. Under 6 games of history: no play.

## Data

History: SportsGameOdds download leagues MLB (`history/build_history.py`). Live lines: PrizePicks league ids 2=MLB. Results: ESPN baseball/mlb. Books: The Odds API baseball_mlb (needs this sport's own key in secrets/).

Everything is 🧪 TEST until owner says otherwise. Nothing goes on a board without his go.
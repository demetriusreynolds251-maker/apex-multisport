# Apex NFL 🏈

Independent Apex Sports system for NFL. Own folder, own history.db, own collectors, scheduler, models, rules, grading, reports, Discord bot and logs. It imports nothing from any other sport, from Apex Tennis or from Apex Basketball; the only shared things are two small PrizePicks pacing flags in `../_shared/`.

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

Channels: #nfl-picks, #nfl-alerts, #nfl-general, #nfl-learning-channel, #nfl-system, #nfl-pnl, #nfl-slips. Commands: /nfl-fetch, /nfl-top3, /nfl-elite5, /nfl-elite6, /nfl-top10, /nfl-bestgoblin, /nfl-beststandard, /nfl-bestdemon, /nfl-backups, /nfl-picks, /nfl-allprops, /nfl-pnl, /nfl-status, /nfl-ban, /nfl-unban, /nfl-setkey.
Token: paste it in the basketball Discord with /bball-sportkey (sport NFL, Discord bot token). Odds API key: /bball-sportkey or /nfl-setkey.

## Stats scored

| stat | PrizePicks names | distribution | on boards |
|---|---|---|---|
| Pass Yards | pass yards | normal | yes |
| Pass TDs | pass tds | poisson | yes |
| Pass Completions | pass comp, pass completions | normal | yes |
| Pass Attempts | pass attempts | normal | yes |
| Interceptions | int, interceptions | poisson | no (computed, not on a board) |
| Rush Yards | rush yards | normal | yes |
| Rush Attempts | rush atts, rush attempts | normal | yes |
| Receiving Yards | rec yards, receiving yards | normal | yes |
| Receptions | recs, receptions | normal | yes |
| Targets | rec targets, targets | normal | no (computed, not on a board) |
| Rush+Rec Yards | rush+rec yds, rush+rec yards | normal | yes |
| Pass+Rush Yards | pass+rush yds, pass+rush yards | normal | yes |
| Longest Reception | longest rec, longest reception | normal | yes |
| Longest Rush | longest rush | normal | yes |
| Rush+Rec TDs | anytime tds, rush+rec tds | poisson | yes |
| Receiving TDs | rec tds | poisson | no (computed, not on a board) |
| Rushing TDs | rush tds | poisson | no (computed, not on a board) |
| Tackles+Assists | tackles+ast, tackles + ast | normal | yes |
| Sacks | sacks | poisson | no (computed, not on a board) |
| FG Made | fg made | poisson | no (computed, not on a board) |
| Kicking Points | kicking points | normal | no (computed, not on a board) |
| Fantasy Score | fantasy score | normal | no (computed, not on a board) |

## Factors

**Live now:** recent form (last 5 / 10); season base; opponent defense allowed (last 12); home / away split; game script from the ESPN spread and total (favorites run more, underdogs throw more); injury list (Out / Doubtful = no play); PrizePicks standard line anchor; book lines when a key exists.

**Pending (no data on this Mac yet):** snap share; target share; route participation; red zone usage; weather; quarterback efficiency.

## Rules

- Floor 70 on Top 3 / Elite 5 / Elite 6 / Top 10 / Best Goblin, 65 on Best Standard, 60 on Best Demon. Tiers A 70+, B 65-69, C 60-64, D under 60.
- Goblin and Demon lines: MORE only. Promo and flash-sale lines off. Banned players off. One pick per game on a numbered board. Players listed Out / Doubtful: no play. Under 6 games of history: no play.

## Data

History: SportsGameOdds download leagues NFL (`history/build_history.py`). Live lines: PrizePicks league ids 9=NFL. Results: ESPN football/nfl. Books: The Odds API americanfootball_nfl (needs this sport's own key in secrets/).

Everything is 🧪 TEST until owner says otherwise. Nothing goes on a board without his go.
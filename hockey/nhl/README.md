# Apex NHL 🏒

Independent Apex Sports system for NHL. Own folder, own history.db, own collectors, scheduler, models, rules, grading, reports, Discord bot and logs. It imports nothing from any other sport, from Apex Tennis or from Apex Basketball; the only shared things are two small PrizePicks pacing flags in `../_shared/`.

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

Channels: #nhl-picks, #nhl-alerts, #nhl-general, #nhl-learning-channel, #nhl-system, #nhl-pnl, #nhl-slips. Commands: /nhl-fetch, /nhl-top3, /nhl-elite5, /nhl-elite6, /nhl-top10, /nhl-bestgoblin, /nhl-beststandard, /nhl-bestdemon, /nhl-backups, /nhl-picks, /nhl-allprops, /nhl-pnl, /nhl-status, /nhl-ban, /nhl-unban, /nhl-setkey.
Token: paste it in the basketball Discord with /bball-sportkey (sport NHL, Discord bot token). Odds API key: /bball-sportkey or /nhl-setkey.

## Stats scored

| stat | PrizePicks names | distribution | on boards |
|---|---|---|---|
| Shots On Goal | shots on goal, shots | normal | yes |
| Goals | goals | poisson | yes |
| Assists | assists | poisson | yes |
| Points | points | poisson | yes |
| Goalie Saves | goalie saves, saves | normal | yes |
| Blocked Shots | blocked shots | poisson | yes |
| Hits | hits | poisson | yes |
| Goals Against | goals against | poisson | no (computed, not on a board) |
| Faceoffs Won | faceoffs won | normal | no (computed, not on a board) |
| Power Play Points | power play points | poisson | no (computed, not on a board) |
| Time On Ice | time on ice | normal | no (computed, not on a board) |

## Factors

**Live now:** recent form (last 5 / 10); season base; opponent allowed (last 12); home / away split; back-to-back; goalie starter check (saves only for a goalie who started most of the last 10); injury list; PrizePicks standard line anchor; book lines when a key exists.

**Pending (no data on this Mac yet):** ice time trend (ESPN gives time on ice, wired next); power play usage; goalie matchup (opponent save %).

## Rules

- Floor 70 on Top 3 / Elite 5 / Elite 6 / Top 10 / Best Goblin, 65 on Best Standard, 60 on Best Demon. Tiers A 70+, B 65-69, C 60-64, D under 60.
- Goblin and Demon lines: MORE only. Promo and flash-sale lines off. Banned players off. One pick per game on a numbered board. Players listed Out / Doubtful: no play. Under 6 games of history: no play.

## Data

History: SportsGameOdds download leagues NHL (`history/build_history.py`). Live lines: PrizePicks league ids 8=NHL. Results: ESPN hockey/nhl. Books: The Odds API icehockey_nhl (needs this sport's own key in secrets/).

Everything is 🧪 TEST until owner says otherwise. Nothing goes on a board without his go.
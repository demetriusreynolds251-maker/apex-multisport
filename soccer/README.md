# Apex Soccer ⚽

Independent Apex Sports system for Soccer. Own folder, own history.db, own collectors, scheduler, models, rules, grading, reports, Discord bot and logs. It imports nothing from any other sport, from Apex Tennis or from Apex Basketball; the only shared things are two small PrizePicks pacing flags in `../_shared/`.

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

Channels: #soccer-picks, #soccer-alerts, #soccer-general, #soccer-learning-channel, #soccer-system, #soccer-pnl, #soccer-slips. Commands: /soccer-fetch, /soccer-top3, /soccer-elite5, /soccer-elite6, /soccer-top10, /soccer-bestgoblin, /soccer-beststandard, /soccer-bestdemon, /soccer-backups, /soccer-picks, /soccer-allprops, /soccer-pnl, /soccer-status, /soccer-ban, /soccer-unban, /soccer-setkey.
Token: paste it in the basketball Discord with /bball-sportkey (sport Soccer, Discord bot token). Odds API key: /bball-sportkey or /soccer-setkey.

## Stats scored

| stat | PrizePicks names | distribution | on boards |
|---|---|---|---|
| Shots | shots | poisson | yes |
| Shots On Target | sot, shots on target | poisson | yes |
| Goals | goals | poisson | yes |
| Assists | assists | poisson | yes |
| Goal + Assist | goal + assist, goals + assists, goal+assist | poisson | yes |
| Goalie Saves | goalie saves, saves | normal | yes |
| Fouls | fouls | poisson | yes |
| Tackles | tackles | poisson | no (computed, not on a board) |
| Passes Attempted | passes attempted | normal | no (computed, not on a board) |
| Fantasy Score | fantasy score | normal | no (computed, not on a board) |

## Factors

**Live now:** recent form; season base; opponent allowed; home / away split; starter check (played most of the last 10); PrizePicks standard line anchor.

**Pending (no data on this Mac yet):** expected goals (xG) / assists (xA); possession; league strength; line-up confirmation.

## Rules

- Floor 70 on Top 3 / Elite 5 / Elite 6 / Top 10 / Best Goblin, 65 on Best Standard, 60 on Best Demon. Tiers A 70+, B 65-69, C 60-64, D under 60.
- Goblin and Demon lines: MORE only. Promo and flash-sale lines off. Banned players off. One pick per game on a numbered board. Players listed Out / Doubtful: no play. Under 6 games of history: no play.

## Data

History: SportsGameOdds download leagues EPL, LA_LIGA, IT_SERIE_A, BUNDESLIGA, FR_LIGUE_1, MLS, UEFA_CHAMPIONS_LEAGUE, UEFA_EUROPA_LEAGUE, LIGA_MX, EREDIVISIE, BR_SERIE_A, INTERNATIONAL_SOCCER (`history/build_history.py`). Live lines: PrizePicks league ids 82=SOCCER, 14=EPL, 531=La Liga, 534=Serie A, 6=MLS. Results: ESPN soccer/eng.1, soccer/esp.1, soccer/ger.1, soccer/ita.1, soccer/fra.1, soccer/usa.1, soccer/uefa.champions, soccer/uefa.europa, soccer/mex.1. Books: The Odds API soccer_epl, soccer_spain_la_liga, soccer_germany_bundesliga, soccer_italy_serie_a, soccer_france_ligue_one, soccer_usa_mls, soccer_uefa_champs_league (needs this sport's own key in secrets/).

Everything is 🧪 TEST until owner says otherwise. Nothing goes on a board without his go.
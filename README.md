# apex-multisport

Apex for sports other than tennis. Each league has its own folder built from one template: collectors pull PrizePicks lines and sportsbook prices, a model prices each prop, a scheduler builds boards, a Discord bot posts them, and a grader settles them from official results. It shares no code, database or bot with `apex-tennis`.

> **Note:** Designed and directed by Demetrius Reynolds and built with AI coding assistants. I understand the code and architecture but am not a professional software engineer.

## The Apex system

Apex is a personal hobby project that prices player props (PrizePicks / ParlayPlay style "more or less" lines) by comparing a model probability with sportsbook prices, then posts ranked boards and results to private Discord channels. It is split into these repos:

| Repo | Role |
|---|---|
| `apex-tennis` | Live tennis system: scheduler, model, boards, grading, Discord bot, dashboard |
| `apex-tennis-warehouse` | Collector that keeps the tennis match/stats database up to date |
| `apex-tennis-research` | Backtests, audits and write-ups behind the tennis rules |
| `apex-multisport` | Same idea for other sports (NBA, NFL, NHL, soccer and more), separate from tennis |

Nothing here places bets. It is research and alerting only.

## What is in here

| Folder | League | Status |
|---|---|---|
| `basketball/` (`code/`, `ncaab/`, `wnba/`) | NBA, college basketball, WNBA | NBA research; NCAAB active; WNBA off |
| `football/nfl`, `football/ncaaf` | NFL, college football | active |
| `hockey/nhl` | NHL | active |
| `soccer/` | Soccer | active |
| `baseball/mlb`, `afl/`, `rugby/` | MLB, Aussie rules, rugby | off (`INACTIVE` file) |
| `_shared/` | all | Boot script and launchd job, health reports, line vault (with its own launchd job in `line_vault/deploy/`), the sport template |

Every league folder has the same layout: `collectors/`, `models/`, `rules/`, `picks/`, `scheduler/`, `grading/`, `tracking/`, `discord/`, `config/sport.json`, plus README, PLAN, DECISIONS and CHANGELOG. About 600 files and 32,000 lines of Python.

## Tech

Python 3.9+, SQLite, `discord.py`, `requests`, ESPN and league public endpoints for results, The Odds API / TheOddsGap for prices, macOS launchd.

## Running one league (placeholders)

```bash
pip install -r requirements.txt
cp .env.example .env     # or put files in <league>/secrets/
# set guild_id in soccer/config/sport.json to your Discord server id
nohup soccer/discord/start.sh >/dev/null 2>&1 &   # runs the scheduler and the bot
```

`_shared/boot/apex_boot.sh` starts every active league at login. Paths use `/path/to/home` as a placeholder.

## Known gaps

The SportsGameOdds price reader (`sgo_raw.py`) lives outside this repo, and `_shared/line_vault/vault.py` reads the tennis props database from `apex-tennis`. Both are optional; the boards still run without them.

## License

[Apex Share-Back License 1.1](LICENSE): free to use, study and build on for non-commercial purposes. If you use it, you agree to share your findings and improvements back publicly and for free and credit "Based on Apex by Demetrius Reynolds". Selling it or using it in a paid product needs a written commercial license: [ask on LinkedIn](https://www.linkedin.com/in/demetrius-reynolds/). See the [terms on the site](https://demetriusreynolds251-maker.github.io/apex/#share).

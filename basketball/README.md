# Basketball
**Status:** Steps 1-3 done for NBA. Step 3 result is weak: honest, but almost never confident. Waiting on his call on "go step 4". Nothing is live and nothing touches Apex.

## Results so far
- 3,426 finished NBA games, 1/31/2024 to 10/30/2026. Final player stats are in the download, so no ESPN needed.
- 66,916 player-games, 752 players. 677,811 prop lines.
- 20,837 testable props (PrizePicks line before the start, book line before the start, final result) from 1,928 games and 12,713 player-games.
- By season: 2024-25 4,451. 2025-26 16,171. 2026-27 so far 215. None in 2023-24; no PrizePicks lines yet.
- Biggest props: field goals made 3,441, points 2,142, PRA 2,097, rebounds + assists 2,088, rebounds 1,922.

## Step 3 result
On the check half, 18 picks reached 70 in 179 days and went 9-9. Picks at 60+ went 121-95, about 1 a day. These lines behave like Standard lines; there's no Goblin label. Report: `reports/2026-10-31_step3_win_probability.md`.

## Known gaps
- Most PrizePicks lines were last updated after the start, so they aren't safe to test.
- Spread and total close on 1,994 of 3,426 finished games; open on 785.
- Pinnacle is on only 830 testable lines; bet365 is the main book.
- No Goblin or Demon labels. 2026-27 closes need a look.

## Apex Basketball bot (🧪 TEST, built 10/31, not started)
Its own Discord bot. Separate from Apex: no Apex imports, own tracker, own channels. Nothing here is on the real money record.
- **Lines:** only what `code/line_collector.py` saved. The bot never calls PrizePicks, because the limit is shared with tennis. `/bball-fetch` re-scores saved lines and says when they were saved.
- **Number:** the Step 3 Win Probability, same formula and tuning, for 5 NBA stats. Rank is Win Prob only, floor 70, one per game. Step 3's check half went 9-9 at 70+, about 1 pick every 10 days, so expect empty boards most days. Goblin and Demon were never in that test.
- **Other leagues and stats:** no number, shown in All Props with the reason, and off Top 3 and Elite.
- **Results:** ESPN box scores, once a day at 4 AM, into `data/processed/espn_games.sqlite`. Tracker: `data/processed/bball_tracker.sqlite`.
- **Known limit:** the collector saves new or changed lines only, so a line PrizePicks took down can still show. Cards say when lines were saved and to check the app.
- **Dollars:** paper $[amount] on Top 3 Power only. Elite 5 and Elite 6 have a slip record but no dollars, since no Flex pay table is loaded.

**Start:** the bot must be invited with Manage Channels, Send Messages and application commands. Save its token with tennis `/setkey Basketball bot`, then:
`nohup ~/ApexSports/basketball/discord/start_bot.sh >/dev/null 2>&1 &`
It waits for the token file if it isn't there yet. **Stop:** `kill "$(cat ~/ApexSports/basketball/logs/bball_bot.pid)"`. **Log:** `logs/bball_bot.log`.
**A Mac reboot stops it.** Run the start line again after a reboot. Keeping it up on its own needs a LaunchAgent, which needs his paste.
**Test:** `/usr/bin/python3 discord/test_offline.py`. No network and no Discord login. Field goals made needs `data/processed/nba_fgm.sqlite`, built once with the 2TB drive: `python3 code/score_board.py --build-fgm`.

## Where things are
- `discord/`: the bot, its cards, start script and offline test.
- `PLAN.md`: the plan. `DECISIONS.md`: his gos. `CHANGELOG.md`: what was built.
- `DATA_DICTIONARY.md`: every table and column.
- `code/`: scripts. `data/raw/`: pointer to the 2TB drive. `data/processed/`: built tables, not in git.
- `reports/`: one dated report per step. `logs/`: run logs.

## Rebuild
With the 2TB drive plugged in, from this folder: `python3 code/build_history.py`

Step 5 (10/31): stop rule hit, see reports/2026-10-31_step5_replay.md.

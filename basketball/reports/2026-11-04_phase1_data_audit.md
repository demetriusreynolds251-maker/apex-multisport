# Apex Basketball — Phase 1: NBA data audit (Nov 4, 2026, 10 PM CT)

Plain words first: we have two years of NBA box scores and book lines, and from tonight we save PrizePicks' own NBA lines with their Goblin / Demon / Standard labels. We have no injury, lineup, play-by-play or minutes-projection source on this machine. Those are the gaps that decide Phase 3.

## Sources on this machine

| Source | Where | What it holds | Depth | Reliability | Missing | Quality concerns |
|---|---|---|---|---|---|---|
| SportsGameOdds NBA download (raw) | `/Volumes/2TB Drive/SportsData/sportsgameodds/events/BASKETBALL/NBA/` (592 MB gz, read only) | 3,789 games 1/31/2024 to 11/29/2026 (3,457 with odds); per game: final score, player box lines, every book's latest line per market, blended open/close total and spread, PrizePicks line where it existed | 2024-25 and 2025-26 full, 2026-27 from opening night | Good for results and closes; a book's number is its LATEST (often after tip) so only lines stamped before start are usable | Per-book open/close; Goblin/Demon labels; minutes projections; injuries | Pre-start spreads only from 1/16/2026; closes before that may already reflect the result (leak); plan cap means no refresh |
| `data/processed/nba_history.sqlite` (built from the download) | ApexSports/basketball | games 3,789 (3,426 final, 1,997 with close total+spread); player_games 66,916 rows, 752 players, minutes/pts/reb/ast/3pm/stl/blk/tov, rest days, back-to-back; prop_lines 677,811 | same | Row counts verified after build | Usage rate, pace, shot attempts per player-game (attempts exist only as book markets, not box score) | fantasyScore lines have no result column |
| Testable props (PP line before start + book line before start + result) | same table | 20,837 props, 1,928 games: 2024-25 4,451; 2025-26 16,171; 2026-27 215 | | | ~240k of 277k PrizePicks lines in the download were updated after tip, so unusable | Pinnacle on only 830 lines; bet365 is the main book |
| PrizePicks live feed, NBA (partner API, league 7) | `data/collected/*.jsonl` from tonight | Tonight 10 PM: 1,762 NBA lines, 908 Demon / 558 Goblin / 296 Standard, 30 stat types, 2 games left on the slate | Starts 11/4/2026 | Same host tennis uses; one call per pull | History before tonight (v1 collector never saved a line: wrong host + waited forever on tennis) | Lines move during the day; we keep every change |
| ESPN box scores | `data/processed/espn_games.sqlite` (52 games, 958 player rows) | finals for grading when the download is stale | 10/31/2026 on | Free, no key | Only pulled for scored games | Name matching ESPN vs PrizePicks |
| NBA G League / NCAAB / WNBA downloads | 2TB drive | NCAAB 14,624 games (10,254 with odds); WNBA 960; G League 1,356 (no odds) | 2024-2026 | Not audited beyond counts | NCAAB has no PP lines saved | Out of scope until NBA works |

## Not on this machine (needed by Phase 3)
- Injury report / who is out tonight: none. Free options to add: NBA.com official injury report (PDF, 5x daily), ESPN injuries endpoint, Rotowire lineups page. Needed for "teammate out" and "starting lineup change" tests before tip.
- Starting lineups / confirmed starters: none. Same sources.
- Play-by-play, usage rate, pace, defensive rating per team-game: none. Derivable partly from box scores (team possessions estimate from FGA, FTA, ORB, TOV once attempts are stored per player-game; the download has team totals).
- Closing line value against PrizePicks: book closes exist (blended consensus) for 1,997 games; per-book closes do not.
- Travel distance: derivable from the schedule (home/away + arena cities), not stored yet.
- SportsAPI365 basketball: not subscribed. Not needed while ESPN and the download cover results.

## Bottom line for Phase 1
- Enough history to build a projection and test rest, home/away, form, pace proxies, spread/blowout and PrizePicks room: 20,837 clean props over two seasons.
- Nothing yet to test injuries or lineups pre-tip. That is the biggest known NBA edge in the literature and it needs a new daily feed (free) before Phase 3 can test it.
- Goblin/Demon modelling starts from zero history tonight. Count tomorrow: how many NBA Goblins PrizePicks posts a day.

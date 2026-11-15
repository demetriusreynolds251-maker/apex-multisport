# Apex Line Vault: data dictionary

Every PrizePicks line the Apex bots have seen, one row per line, the same columns for every sport.
Built nightly by `vault.py` from what the bots already saved. It never calls PrizePicks.

- Store: `~/ApexSports/_shared/line_vault/line_vault.sqlite`
- Spreadsheets: `exports/lines_<sport>.csv.gz` (one per sport, rewritten nightly)
- Backup: `/Volumes/2TB Drive/Apex Line Vault/line_vault_YYYY-MM-DD.sqlite` (last 14 nights)

## Table `lines` (one row per PrizePicks line)
| Column | Meaning |
|---|---|
| line_key | `<sport>:<PrizePicks projection id>`. Unique. |
| sport | tennis, nba, nfl, ncaaf, nhl, ncaab, wnba, mlb, soccer, afl, rugby |
| league | PrizePicks league name (NFL, EPL, ...) |
| projection_id | PrizePicks' own id for the line |
| player | Player as PrizePicks lists them |
| team, opponent | Team codes (empty for tennis; tennis opponent is the other player) |
| home_team, away_team | Team codes of the game |
| game_id | PrizePicks game id |
| stat | Stat name as shown on PrizePicks |
| stat_code | Apex's short code for the stat (empty when Apex does not score that stat) |
| kind | standard, goblin or demon |
| less_offered | 1 when PrizePicks sells LESS on it (standard lines), 0 for goblin and demon |
| line_first | The line the first time it was seen |
| line_last | The line the last time it was seen |
| line_at_start | The last line seen before the game started (empty when only seen after) |
| line_moves | How many times the line changed |
| start_utc | Game start, UTC |
| game_date | Game day, Central time (tennis: Apex match date) |
| first_seen, last_seen | First and last time a bot saw the line, UTC |
| status_last | PrizePicks status at last sight (pre_game, ...) |
| promo | 1 when PrizePicks marked it a promo line |
| actual | What the player really did |
| result | more, less, push, void (did not play), pending, or "not graded (...)" with the reason |
| more_won, less_won | 1/0 when graded, empty otherwise |
| graded_at, graded_from | When and from what source the result came |
| source_store | The bot file this row was read from |
| vault_updated | Last time the vault refreshed the row |

Results compare `actual` with `line_at_start` (or the last line when none was seen before the start).

## Table `line_moves` (every line value a projection has shown)
line_key, seen_at (UTC), line, kind, status.

## Table `vault_runs` (one row per sport per nightly run)
run_at, sport, lines, graded, pending, new_lines, note.

## Where results come from
- Tennis: Apex's own settle step (official match stats).
- Team sports: the box scores in each sport's `history.db` (ESPN, plus official NHL / nflverse where loaded).
- NBA: the basketball tracker's graded results.

## Extra stats graded by the vault itself
Some PrizePicks stats are not scored by the bots yet but the saved box scores can answer them. The vault grades these with its own
formulas (`EXTRA` in `vault.py`); `graded_from` ends with "(vault formula)". NHL: SOG, Goals Allowed, Minutes. College basketball: PRA,
3PTM, Blks+Stls, Double-Double (1 = yes). NFL / college football: Pass+Rush+Rec TDs, Completion Percentage, Rush Yards Per Carry.

## Known limits
- NBA lines the tracker did not grade are graded from full NBA box scores (`basketball/data/processed/nba_box_full.sqlite`, every ESPN stat column, saved nightly before the vault runs): threes, steals, blocks, turnovers, fantasy score, 2-pointers, free throws, fouls, offensive / defensive rebounds, double-double, triple-double. Not graded: Dunks and quarter props.
- Team-sport lines exist from Nov 5, 2026 (bots' first day). NBA from Nov 4, 2026. Tennis from Sep 2026.
- Sports Apex does not pull (UFC, golf, esports, ...) are not here.
- A stat Apex does not score yet is saved but marked "not graded (stat not in Apex yet)".

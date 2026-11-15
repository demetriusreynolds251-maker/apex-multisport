# Apex Basketball System — architecture and plan (started Nov 4, 2026)

**One product, separate from Apex Tennis.** Own folder (`~/ApexSports/basketball/`), own git, own data, own models, own bot, own process ids. Nothing imports from `~/openclaw`. The only things shared with tennis are the Discord card style and one read-only look at tennis's PrizePicks pause flag so the two products never hit PrizePicks at the same time. No Mission Control, no web dashboard: Discord is the whole interface.

```
OpenClaw
├── Apex Tennis       ~/openclaw            (untouched)
└── Apex Basketball   ~/ApexSports/basketball
```

## Folder structure
| Folder | Holds |
|---|---|
| `config/` | settings (leagues, pull times, board sizes, floors, channel names) as json; no secrets |
| `data/raw` | pointer to the 2TB SportsGameOdds download (read only) |
| `data/collected/` | every PrizePicks NBA line saved by the collector, append only |
| `data/processed/` | built tables: nba_history.sqlite, espn_games.sqlite, tracker |
| `models/` | projection models (minutes, per-minute rates), calibration tables, fitted parameters |
| `simulations/` | the game simulator (minutes, possessions, usage, shots, assists, rebounds, defense, blowout, injury, lineup) |
| `boards/` | board builder, qualification rules, board history |
| `calibration/` | raw vs honest probability, Brier, expected vs actual, per bucket |
| `shadow_tests/` | every feature under test: sample, promotion and rejection rules, progress |
| `notifications/` | Discord card builders and the daily / alert posters |
| `discord/` | the Apex Basketball bot (own token, own server) |
| `code/` | collectors, builders, graders |
| `reports/` | one dated report per phase |
| `logs/` | run logs, pids, state |
| `secrets/` | bot token only (git ignored) |

## Phases and status
| Phase | What | Status |
|---|---|---|
| 1 Data audit | every NBA source on the machine, gaps | DONE 11/4, `reports/2026-11-04_phase1_data_audit.md` |
| 2 Prop inventory | every PrizePicks NBA market, volume, difficulty | DONE 11/4, `reports/2026-11-04_phase2_prop_inventory.md` |
| 3 Edge discovery | test each fact on clean history (20,837 props) both halves | next; injuries/lineups need a new free feed first |
| 4 Simulation engine | minutes -> possessions -> usage -> shots/assists/rebounds -> stat lines, with blowout/injury/lineup adjustments | after 3 |
| 5 Scoring | probability vs confidence vs edge vs composite; keep what predicts | after 4 |
| 6 Boards | test Top 3 / 5 / 6 / 10 on replays; same card style as tennis | after 5 |
| 7 Calibration | raw and honest probability, Brier, expected vs actual | with 5 |
| 8 Shadow mode | walk-forward, out of sample, replay, shadow | before anything shows on a board |
| 9 Live tracking | board/leg/category records, days won, calibration, CLV, in Discord | with shadow |
| 10 Integrity | missing qualifier, board error, skipped better prop, data issue alerts | with boards |
| 11 Promotion | sample / promotion / rejection rules per feature; PROMOTION CANDIDATE, TEST FAILURE, TEST PROGRESS cards | with shadow |
| 12 Profitability audit | best and worst prop types and board shapes | after a shadow month |

## Methodology (fixed rules, same discipline as tennis)
- Build on older dates, check on newer; report both halves; a feature passes only if it wins picks AND does not lose days in either half.
- Real PrizePicks labels (Goblin/Demon/Standard) decide what goes on a board; history finds ideas.
- Honest probability = raw probability corrected by how past picks at that level actually did (bucketed, rolling).
- Boards: one line per player, one per game by default (tested), floors by label.
- Every automatic job posts a line; silence is a bug.
- Nothing goes on a board without his go after shadow evidence.

## Known risks (Phase 1)
1. No injury / lineup feed on the machine. Without it the biggest NBA edge cannot be tested. Plan: add a free daily pull (NBA.com injury report + ESPN).
2. Goblin/Demon history starts tonight. Replays on real labels need 3-4 weeks of collection.
3. Step 5 (10/31) stop rule: Standard lines with the Step 3 model lost on unseen games (Top 3 14 of 108 days). The model must change, not just the boards.
4. PrizePicks rate limit is shared with tennis; the collector pulls once per 30 minutes and backs off 6 hours on a 429.
5. Processes stop on a Mac reboot (no LaunchAgent yet).

## Expected volume (to be verified)
Full slate: 8,000-12,000 NBA lines a day, ~3,000 Goblins. Board candidates after floors: unknown until Phase 3-5.

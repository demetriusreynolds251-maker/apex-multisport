# Step 4 facts: numbers, 2026-10-31

Backtest only, on the 10160 Step 3 picks. Build half: dates before 2025-11-28. Check half: 2025-11-28 on. A pick won if it beat the PrizePicks line; ties are out, as in Step 3.

## Verdicts

"Helps" means same direction in both halves with 40+ picks on each side in each half.

**At Win Prob 60+ and 70+:** 288 comparisons tested, 0 had enough picks. 0 pass:
- None.

At 70+ the smallest side of the fullest comparison held 4 picks, so no fact can pass at 70+ under this rule.

**Extra, all picks regardless of Win Prob (not what was asked to count; same rule, to show if a fact does anything at all):** 86 comparisons had enough picks, 55 same direction, 31 flip. Same direction happens about half the time by luck. Those passing with combined z of 2 or more are below; about 4 would be expected by luck, and the room rows share the same picks, so they are not separate proofs:
- Teammate out, Reb+Ast LESS all picks: better side "nobody usual is out". Build 138 won, 117 lost vs 54 won, 57 lost. Check 82 won, 53 lost vs 38 won, 45 lost. Gap +5 and +15 points, combined z +2.2.
- Teammate out, FG made LESS all picks: better side "nobody usual is out". Build 38 won, 41 lost vs 19 won, 34 lost. Check 173 won, 165 lost vs 88 won, 114 lost. Gap +12 and +8 points, combined z +2.2.
- Rest days, Points MORE all picks: better side "0-1 days off". Build 211 won, 215 lost vs 84 won, 99 lost. Check 133 won, 104 lost vs 41 won, 56 lost. Gap +4 and +14 points, combined z +2.2.
- Opponent allows, Points LESS all picks: better side "allows little". Build 123 won, 93 lost vs 75 won, 96 lost. Check 67 won, 47 lost vs 43 won, 37 lost. Gap +13 and +5 points, combined z +2.3.
- Opponent allows, PRA LESS all picks: better side "allows little". Build 145 won, 91 lost vs 76 won, 100 lost. Check 43 won, 31 lost vs 59 won, 52 lost. Gap +18 and +5 points, combined z +3.1.
- Opponent allows, All five LESS all picks: better side "allows little". Build 507 won, 389 lost vs 335 won, 380 lost. Check 389 won, 345 lost vs 307 won, 279 lost. Gap +10 and +1 points, combined z +2.9.
- Room vs book median (any gap), PRA MORE all picks: better side "book line favors pick". Build 86 won, 60 lost vs 44 won, 49 lost. Check 42 won, 29 lost vs 22 won, 26 lost. Gap +12 and +13 points, combined z +2.3.
- Room vs book median (any gap), All five MORE all picks: better side "book line favors pick". Build 291 won, 236 lost vs 135 won, 159 lost. Check 238 won, 181 lost vs 102 won, 144 lost. Gap +9 and +15 points, combined z +4.5.
- Room vs book median (any gap), All five LESS all picks: better side "book line favors pick". Build 261 won, 218 lost vs 125 won, 140 lost. Check 166 won, 129 lost vs 101 won, 120 lost. Gap +7 and +11 points, combined z +3.0.
- Room vs book median (1+ gap), All five MORE all picks: better side "1+ in favor". Build 236 won, 191 lost vs 99 won, 126 lost. Check 206 won, 154 lost vs 84 won, 111 lost. Gap +11 and +14 points, combined z +4.2.
- Room vs book median (1+ gap), All five LESS all picks: better side "1+ in favor". Build 224 won, 178 lost vs 102 won, 120 lost. Check 134 won, 104 lost vs 82 won, 98 lost. Gap +10 and +11 points, combined z +3.2.
- Room vs bet365 only, All five MORE all picks: better side "bet365 favors pick". Build 171 won, 115 lost vs 66 won, 74 lost. Check 207 won, 160 lost vs 86 won, 110 lost. Gap +13 and +13 points, combined z +3.7.

Spread cannot pass on Step 3's halves: the build half has no open spread. See the inner split below.

## Data checks

- Step 3 picks reproduced from history: projection off by 0.004 on average (largest 0.02), Win Prob off by 0.026 on average (largest 0.08). Raw field goals read for 73677 player-games.
- Average miss of spread vs final margin, before Feb 2025: close 9.4 on 5 games, open n/a on 0 games. A fair spread misses by about 11-12.
- Average miss of spread vs final margin, Feb 2025 to Jan 2026: close 4.3 on 1321 games, open 11.6 on 117 games. A fair spread misses by about 11-12.
- Average miss of spread vs final margin, Feb 2026 on: close 11.2 on 668 games, open 11.5 on 668 games. A fair spread misses by about 11-12.
- Spread used: open_spread_home only, first on 2026-01-16, so **none of the build half has it**. Closes were not used. Picks with an open spread: 2191 (build 0, check 2191).
- Book lines used: book_lines_json, the books last updated before the start, for picks with pp_before_start=1. Picks with a usable book line 10160 of 10160, 7173 of them with only 1 book, bet365 on 7832, Pinnacle on 298. Average miss vs result: book median 3.55, PrizePicks 3.56; about equal, so nothing like an in-game line showing up. No timestamps are kept, so the PP and book lines may come from different moments before the start: a book that moved late on news against a PP line last touched hours earlier looks like room, and PP may have moved its line before lock.
- Book alone, ignoring our guess, build half: when the book median differs from the PP line, going the way the book points went 851 won, 714 lost. Book miss 4.51, PP miss 4.52 on those rows.
- Book alone, ignoring our guess, check half: when the book median differs from the PP line, going the way the book points went 668 won, 513 lost. Book miss 3.85, PP miss 3.86 on those rows.
- Teammate out counts: build out 958, none 2810, unknown 1423; check out 1187, none 2889, unknown 893. Unknown reasons, with minutes: {'teammate: under 3 recent team games': 801, 'teammate: box incomplete': 1515, 'minutes: under 13 earlier games': 46}.
- Team box scores missing players (under 235 minutes or under 8 players): 2520 of 6505 overall; by month from 2025-02: 2025-02 20/246, 2025-03 97/474, 2025-04 55/298, 2025-05 3/76, 2025-06 0/14, 2025-10 32/158, 2025-11 55/436, 2025-12 40/392, 2026-01 68/464, 2026-02 95/330, 2026-03 132/472, 2026-04 89/284, 2026-05 2/76, 2026-06 0/10, 2026-10 48/162.
- Duplicates: 26 same matchup/date games stored under more than one event id (1 of them from 2025-02 on); 0 Step 3 picks repeat a player, date and stat. Step 3 did not remove these from player history. Same-game picks are not independent, so z numbers run a bit high.
- Names: games and opponents carry both 'LA Clippers' and 'Los Angeles Clippers', and the team column says 'home'/'away' on some Jan-Feb 2025 rows. Step 3's opponent factor treats the Clippers as two teams (small error in Step 3, left as is so Win Prob stays the same); the facts here merge them.
- Cut-offs from the build half: minutes moved-around line 4.88 (spread of last 10 games; at or under = steady). Opponent factor, bottom/top third: {'Points': (0.977, 1.023), 'Rebounds': (0.975, 1.027), 'Reb+Ast': (0.975, 1.03), 'PRA': (0.967, 1.018), 'FG made': (0.996, 1.037)}.

## How each fact is decided

- **Teammate out:** "usual" = another player on the team who played in at least 3 of the team's last 5 complete-box games (within 30 days) and averaged 28+ minutes in them. "Out" = no row with minutes above 0 in this game's box. Games with an incomplete box are left out so missing data is not read as out. **This fact reads this game's box score**, so it is the only one that is not strictly pre-match: late scratches count as known, and a real board would need an injury report at lock.
- **Minutes trend:** average of last 3 games minus average of the 10 before them. Up = +3 or more, down = -3 or less; flat is left out of the comparison. Needs 13 earlier games.
- **Steady vs moved around:** spread of minutes over the last 10 games, cut at the build-half median.
- **Spread:** absolute open spread 10+ vs under 10. Favored vs underdog from the same open spread.
- **Back-to-back / rest:** days between this player's earlier games and this one. A skipped game or a missing box row counts as rest.
- **Opponent:** Step 3's measure, what the team allowed in its last 15 earlier games vs league, cut at the build-half thirds. Team total only: there is no position data. Step 3 already includes half of this, plus back-to-back, so these are tests of what is left over.
- **Room:** book line minus PP line, flipped for LESS, so plus always means the book leaves room for the pick.

## Baseline, no fact

| Win Prob | Stat | Side | Build half | Check half |
|---|---|---|---|---|
| 60+ | Points | MORE | 11 won, 8 lost | 9 won, 6 lost |
| 60+ | Points | LESS | 14 won, 18 lost | 10 won, 9 lost |
| 60+ | PRA | MORE | 11 won, 9 lost | 7 won, 5 lost |
| 60+ | PRA | LESS | 29 won, 26 lost | 19 won, 10 lost |
| 60+ | Rebounds | MORE | 10 won, 2 lost | 6 won, 2 lost |
| 60+ | Rebounds | LESS | 23 won, 10 lost | 4 won, 6 lost |
| 60+ | Reb+Ast | MORE | 11 won, 11 lost | 7 won, 8 lost |
| 60+ | Reb+Ast | LESS | 20 won, 16 lost | 10 won, 6 lost |
| 60+ | FG made | MORE | 13 won, 7 lost | 41 won, 34 lost |
| 60+ | FG made | LESS | 4 won, 3 lost | 8 won, 9 lost |
| 60+ | All five | MORE | 56 won, 37 lost | 70 won, 55 lost |
| 60+ | All five | LESS | 90 won, 73 lost | 51 won, 40 lost |
| 70+ | Points | MORE | 0 won, 0 lost | 0 won, 0 lost |
| 70+ | Points | LESS | 0 won, 1 lost | 0 won, 3 lost |
| 70+ | PRA | MORE | 1 won, 1 lost | 0 won, 0 lost |
| 70+ | PRA | LESS | 4 won, 3 lost | 3 won, 2 lost |
| 70+ | Rebounds | MORE | 0 won, 0 lost | 0 won, 0 lost |
| 70+ | Rebounds | LESS | 4 won, 1 lost | 1 won, 1 lost |
| 70+ | Reb+Ast | MORE | 0 won, 0 lost | 0 won, 1 lost |
| 70+ | Reb+Ast | LESS | 1 won, 1 lost | 4 won, 2 lost |
| 70+ | FG made | MORE | 0 won, 0 lost | 1 won, 0 lost |
| 70+ | FG made | LESS | 0 won, 0 lost | 0 won, 0 lost |
| 70+ | All five | MORE | 1 won, 1 lost | 1 won, 1 lost |
| 70+ | All five | LESS | 9 won, 6 lost | 8 won, 8 lost |
| all | Points | MORE | 295 won, 314 lost | 174 won, 160 lost |
| all | Points | LESS | 304 won, 273 lost | 165 won, 134 lost |
| all | PRA | MORE | 337 won, 301 lost | 160 won, 145 lost |
| all | PRA | LESS | 327 won, 278 lost | 165 won, 129 lost |
| all | Rebounds | MORE | 256 won, 279 lost | 158 won, 166 lost |
| all | Rebounds | LESS | 263 won, 223 lost | 157 won, 153 lost |
| all | Reb+Ast | MORE | 319 won, 329 lost | 191 won, 193 lost |
| all | Reb+Ast | LESS | 266 won, 249 lost | 157 won, 116 lost |
| all | FG made | MORE | 189 won, 174 lost | 873 won, 854 lost |
| all | FG made | LESS | 95 won, 120 lost | 348 won, 371 lost |
| all | All five | MORE | 1396 won, 1397 lost | 1556 won, 1518 lost |
| all | All five | LESS | 1255 won, 1143 lost | 992 won, 903 lost |

## Spread, split inside the dates that have it

Picks with an open spread only, split at 2026-03-03. This is a split of the check half, so it is weaker evidence.

### Spread size

| Win Prob | Stat | Side | Early: spread 10+ | Early: spread under 10 | Late: spread 10+ | Late: spread under 10 | Gap | Verdict |
|---|---|---|---|---|---|---|---|---|
| 60+ | Points | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | - | too few |
| 60+ | Points | LESS | 0 won, 0 lost | 0 won, 2 lost | 3 won, 0 lost | 0 won, 0 lost | - | too few |
| 60+ | PRA | MORE | 0 won, 0 lost | 1 won, 1 lost | 0 won, 0 lost | 1 won, 1 lost | - | too few |
| 60+ | PRA | LESS | 1 won, 0 lost | 1 won, 1 lost | 1 won, 0 lost | 2 won, 0 lost | +50, +0 pts, z +0.6 | flips, too few |
| 60+ | Rebounds | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | 4 won, 0 lost | - | too few |
| 60+ | Rebounds | LESS | 0 won, 0 lost | 1 won, 1 lost | 0 won, 1 lost | 0 won, 0 lost | - | too few |
| 60+ | Reb+Ast | MORE | 0 won, 0 lost | 2 won, 3 lost | 0 won, 1 lost | 1 won, 2 lost | - | too few |
| 60+ | Reb+Ast | LESS | 1 won, 0 lost | 2 won, 0 lost | 1 won, 1 lost | 2 won, 2 lost | +0, +0 pts, z +0.0 | flips, too few |
| 60+ | FG made | MORE | 1 won, 3 lost | 8 won, 11 lost | 4 won, 3 lost | 12 won, 7 lost | -17, -6 pts, z -0.6 | same way, too few |
| 60+ | FG made | LESS | 1 won, 0 lost | 3 won, 1 lost | 1 won, 2 lost | 1 won, 5 lost | +25, +17 pts, z +0.8 | same way, too few |
| 60+ | All five | MORE | 1 won, 3 lost | 11 won, 15 lost | 4 won, 5 lost | 18 won, 11 lost | -17, -18 pts, z -1.1 | same way, too few |
| 60+ | All five | LESS | 3 won, 0 lost | 7 won, 5 lost | 6 won, 4 lost | 5 won, 7 lost | +42, +18 pts, z +1.6 | same way, too few |
| 70+ | Points | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Points | LESS | 0 won, 0 lost | 0 won, 2 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | PRA | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | PRA | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Rebounds | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Rebounds | LESS | 0 won, 0 lost | 1 won, 0 lost | 0 won, 1 lost | 0 won, 0 lost | - | too few |
| 70+ | Reb+Ast | MORE | 0 won, 0 lost | 0 won, 1 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Reb+Ast | LESS | 1 won, 0 lost | 0 won, 0 lost | 1 won, 1 lost | 2 won, 0 lost | - | too few |
| 70+ | FG made | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 1 won, 0 lost | - | too few |
| 70+ | FG made | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | All five | MORE | 0 won, 0 lost | 0 won, 1 lost | 0 won, 0 lost | 1 won, 0 lost | - | too few |
| 70+ | All five | LESS | 1 won, 0 lost | 1 won, 2 lost | 1 won, 2 lost | 2 won, 0 lost | +67, -67 pts, z -0.2 | flips, too few |
| all (extra) | Points | MORE | 7 won, 4 lost | 7 won, 10 lost | 4 won, 4 lost | 9 won, 6 lost | +22, -10 pts, z +0.5 | flips, too few |
| all (extra) | Points | LESS | 3 won, 1 lost | 8 won, 14 lost | 8 won, 6 lost | 10 won, 4 lost | +39, -14 pts, z +0.5 | flips, too few |
| all (extra) | PRA | MORE | 3 won, 4 lost | 15 won, 14 lost | 4 won, 6 lost | 10 won, 12 lost | -9, -5 pts, z -0.5 | same way, too few |
| all (extra) | PRA | LESS | 1 won, 1 lost | 20 won, 15 lost | 11 won, 5 lost | 12 won, 5 lost | -7, -2 pts, z -0.2 | same way, too few |
| all (extra) | Rebounds | MORE | 3 won, 1 lost | 12 won, 20 lost | 4 won, 5 lost | 13 won, 17 lost | +38, +1 pts, z +1.1 | same way, too few |
| all (extra) | Rebounds | LESS | 1 won, 2 lost | 14 won, 13 lost | 4 won, 4 lost | 7 won, 5 lost | -19, -8 pts, z -0.7 | same way, too few |
| all (extra) | Reb+Ast | MORE | 1 won, 1 lost | 16 won, 18 lost | 4 won, 8 lost | 5 won, 17 lost | +3, +11 pts, z +0.5 | same way, too few |
| all (extra) | Reb+Ast | LESS | 6 won, 0 lost | 21 won, 12 lost | 9 won, 5 lost | 9 won, 9 lost | +36, +14 pts, z +1.8 | same way, too few |
| all (extra) | FG made | MORE | 41 won, 57 lost | 224 won, 224 lost | 99 won, 81 lost | 222 won, 221 lost | -8, +5 pts, z -0.3 | flips |
| all (extra) | FG made | LESS | 28 won, 24 lost | 102 won, 97 lost | 41 won, 57 lost | 74 won, 90 lost | +3, -3 pts, z -0.1 | flips |
| all (extra) | All five | MORE | 55 won, 67 lost | 274 won, 286 lost | 115 won, 104 lost | 259 won, 273 lost | -4, +4 pts, z +0.1 | flips |
| all (extra) | All five | LESS | 39 won, 28 lost | 165 won, 151 lost | 73 won, 77 lost | 112 won, 113 lost | +6, -1 pts, z +0.5 | flips |

Passing inside this split: none.

### Player's team favored vs underdog

| Win Prob | Stat | Side | Early: favored | Early: underdog | Late: favored | Late: underdog | Gap | Verdict |
|---|---|---|---|---|---|---|---|---|
| 60+ | Points | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | 0 won, 0 lost | - | too few |
| 60+ | Points | LESS | 0 won, 2 lost | 0 won, 0 lost | 1 won, 0 lost | 2 won, 0 lost | - | too few |
| 60+ | PRA | MORE | 1 won, 0 lost | 0 won, 1 lost | 0 won, 1 lost | 1 won, 0 lost | +100, -100 pts, z +0.0 | flips, too few |
| 60+ | PRA | LESS | 2 won, 0 lost | 0 won, 1 lost | 2 won, 0 lost | 1 won, 0 lost | +100, +0 pts, z +1.2 | flips, too few |
| 60+ | Rebounds | MORE | 0 won, 0 lost | 0 won, 0 lost | 4 won, 0 lost | 0 won, 1 lost | - | too few |
| 60+ | Rebounds | LESS | 1 won, 0 lost | 0 won, 1 lost | 0 won, 0 lost | 0 won, 1 lost | - | too few |
| 60+ | Reb+Ast | MORE | 2 won, 1 lost | 0 won, 2 lost | 1 won, 2 lost | 0 won, 1 lost | +67, +33 pts, z +1.5 | same way, too few |
| 60+ | Reb+Ast | LESS | 2 won, 0 lost | 1 won, 0 lost | 1 won, 1 lost | 2 won, 0 lost | +0, -50 pts, z -0.8 | flips, too few |
| 60+ | FG made | MORE | 6 won, 2 lost | 3 won, 12 lost | 7 won, 7 lost | 9 won, 3 lost | +55, -25 pts, z +0.9 | flips, too few |
| 60+ | FG made | LESS | 2 won, 0 lost | 2 won, 1 lost | 1 won, 4 lost | 1 won, 3 lost | +33, -5 pts, z +0.5 | flips, too few |
| 60+ | All five | MORE | 9 won, 3 lost | 3 won, 15 lost | 12 won, 11 lost | 10 won, 5 lost | +58, -14 pts, z +1.6 | flips, too few |
| 60+ | All five | LESS | 7 won, 2 lost | 3 won, 3 lost | 5 won, 5 lost | 6 won, 4 lost | +28, -10 pts, z +0.5 | flips, too few |
| 70+ | Points | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Points | LESS | 0 won, 2 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | PRA | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | PRA | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Rebounds | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Rebounds | LESS | 1 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | - | too few |
| 70+ | Reb+Ast | MORE | 0 won, 0 lost | 0 won, 1 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Reb+Ast | LESS | 1 won, 0 lost | 0 won, 0 lost | 1 won, 1 lost | 2 won, 0 lost | - | too few |
| 70+ | FG made | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 1 won, 0 lost | - | too few |
| 70+ | FG made | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | All five | MORE | 0 won, 0 lost | 0 won, 1 lost | 0 won, 0 lost | 1 won, 0 lost | - | too few |
| 70+ | All five | LESS | 2 won, 2 lost | 0 won, 0 lost | 1 won, 1 lost | 2 won, 1 lost | - | too few |
| all (extra) | Points | MORE | 6 won, 3 lost | 8 won, 11 lost | 5 won, 6 lost | 8 won, 4 lost | +25, -21 pts, z +0.1 | flips, too few |
| all (extra) | Points | LESS | 5 won, 8 lost | 6 won, 7 lost | 10 won, 5 lost | 8 won, 4 lost | -8, +0 pts, z -0.3 | flips, too few |
| all (extra) | PRA | MORE | 10 won, 8 lost | 8 won, 10 lost | 6 won, 12 lost | 8 won, 6 lost | +11, -24 pts, z -0.5 | flips, too few |
| all (extra) | PRA | LESS | 12 won, 8 lost | 9 won, 8 lost | 11 won, 5 lost | 12 won, 5 lost | +7, -2 pts, z +0.2 | flips, too few |
| all (extra) | Rebounds | MORE | 6 won, 10 lost | 9 won, 11 lost | 11 won, 12 lost | 6 won, 10 lost | -8, +10 pts, z +0.1 | flips, too few |
| all (extra) | Rebounds | LESS | 7 won, 5 lost | 8 won, 10 lost | 5 won, 4 lost | 6 won, 5 lost | +14, +1 pts, z +0.6 | same way, too few |
| all (extra) | Reb+Ast | MORE | 11 won, 6 lost | 6 won, 13 lost | 5 won, 15 lost | 4 won, 10 lost | +33, -4 pts, z +1.2 | flips, too few |
| all (extra) | Reb+Ast | LESS | 13 won, 8 lost | 14 won, 4 lost | 9 won, 9 lost | 9 won, 2 lost | -16, -32 pts, z -2.0 | same way, too few |
| all (extra) | FG made | MORE | 141 won, 137 lost | 121 won, 140 lost | 165 won, 155 lost | 155 won, 146 lost | +4, +0 pts, z +0.7 | HELPS |
| all (extra) | FG made | LESS | 82 won, 61 lost | 46 won, 60 lost | 65 won, 85 lost | 50 won, 60 lost | +14, -2 pts, z +1.3 | flips |
| all (extra) | All five | MORE | 174 won, 164 lost | 152 won, 185 lost | 192 won, 200 lost | 181 won, 176 lost | +6, -2 pts, z +0.8 | flips |
| all (extra) | All five | LESS | 119 won, 90 lost | 83 won, 89 lost | 100 won, 108 lost | 85 won, 76 lost | +9, -5 pts, z +0.6 | flips |

Passing inside this split: FG made MORE all picks.

## Every comparison, Step 3 halves

Gap = first side minus second side, win rate, build then check. "all (extra)" rows are context only.

### Teammate out

| Win Prob | Stat | Side | Build: a usual teammate is out | Build: nobody usual is out | Check: a usual teammate is out | Check: nobody usual is out | Gap | Verdict |
|---|---|---|---|---|---|---|---|---|
| 60+ | Points | MORE | 1 won, 1 lost | 8 won, 3 lost | 1 won, 0 lost | 8 won, 4 lost | -23, +33 pts, z +0.0 | flips, too few |
| 60+ | Points | LESS | 6 won, 7 lost | 1 won, 1 lost | 6 won, 7 lost | 2 won, 1 lost | -4, -21 pts, z -0.5 | same way, too few |
| 60+ | PRA | MORE | 0 won, 1 lost | 5 won, 5 lost | 1 won, 0 lost | 5 won, 5 lost | -50, +50 pts, z +0.0 | flips, too few |
| 60+ | PRA | LESS | 11 won, 11 lost | 6 won, 4 lost | 11 won, 5 lost | 3 won, 2 lost | -10, +9 pts, z -0.1 | flips, too few |
| 60+ | Rebounds | MORE | 1 won, 1 lost | 5 won, 0 lost | 0 won, 0 lost | 3 won, 1 lost | - | too few |
| 60+ | Rebounds | LESS | 4 won, 1 lost | 6 won, 3 lost | 2 won, 4 lost | 2 won, 1 lost | +13, -33 pts, z -0.3 | flips, too few |
| 60+ | Reb+Ast | MORE | 0 won, 0 lost | 7 won, 7 lost | 1 won, 3 lost | 4 won, 4 lost | - | too few |
| 60+ | Reb+Ast | LESS | 6 won, 2 lost | 6 won, 3 lost | 4 won, 3 lost | 4 won, 1 lost | +8, -23 pts, z -0.3 | flips, too few |
| 60+ | FG made | MORE | 3 won, 1 lost | 3 won, 3 lost | 6 won, 9 lost | 30 won, 21 lost | +25, -19 pts, z -0.4 | flips, too few |
| 60+ | FG made | LESS | 3 won, 0 lost | 0 won, 1 lost | 4 won, 3 lost | 2 won, 2 lost | +100, +7 pts, z +1.6 | same way, too few |
| 60+ | All five | MORE | 5 won, 4 lost | 28 won, 18 lost | 9 won, 12 lost | 50 won, 35 lost | -5, -16 pts, z -1.1 | same way, too few |
| 60+ | All five | LESS | 30 won, 21 lost | 19 won, 12 lost | 27 won, 22 lost | 13 won, 7 lost | -2, -10 pts, z -0.7 | same way, too few |
| 70+ | Points | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Points | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 2 lost | 0 won, 0 lost | - | too few |
| 70+ | PRA | MORE | 0 won, 1 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | PRA | LESS | 0 won, 2 lost | 0 won, 0 lost | 1 won, 1 lost | 1 won, 0 lost | - | too few |
| 70+ | Rebounds | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Rebounds | LESS | 0 won, 1 lost | 0 won, 0 lost | 1 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Reb+Ast | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | 0 won, 0 lost | - | too few |
| 70+ | Reb+Ast | LESS | 0 won, 0 lost | 0 won, 0 lost | 1 won, 1 lost | 1 won, 0 lost | - | too few |
| 70+ | FG made | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | FG made | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | All five | MORE | 0 won, 1 lost | 0 won, 0 lost | 0 won, 1 lost | 0 won, 0 lost | - | too few |
| 70+ | All five | LESS | 0 won, 3 lost | 0 won, 0 lost | 3 won, 4 lost | 2 won, 0 lost | - | too few |
| all (extra) | Points | MORE | 38 won, 53 lost | 189 won, 190 lost | 30 won, 27 lost | 122 won, 106 lost | -8, -1 pts, z -1.1 | HELPS |
| all (extra) | Points | LESS | 65 won, 66 lost | 145 won, 112 lost | 62 won, 46 lost | 75 won, 67 lost | -7, +5 pts, z -0.4 | flips |
| all (extra) | PRA | MORE | 51 won, 32 lost | 205 won, 205 lost | 33 won, 25 lost | 108 won, 104 lost | +11, +6 pts, z +1.9 | HELPS |
| all (extra) | PRA | LESS | 81 won, 72 lost | 162 won, 127 lost | 63 won, 46 lost | 71 won, 60 lost | -3, +4 pts, z -0.0 | flips |
| all (extra) | Rebounds | MORE | 45 won, 44 lost | 142 won, 153 lost | 29 won, 33 lost | 106 won, 110 lost | +2, -2 pts, z +0.1 | flips |
| all (extra) | Rebounds | LESS | 47 won, 35 lost | 130 won, 122 lost | 46 won, 38 lost | 81 won, 87 lost | +6, +7 pts, z +1.3 | HELPS |
| all (extra) | Reb+Ast | MORE | 52 won, 57 lost | 192 won, 213 lost | 40 won, 46 lost | 127 won, 126 lost | +0, -4 pts, z -0.4 | flips |
| all (extra) | Reb+Ast | LESS | 54 won, 57 lost | 138 won, 117 lost | 38 won, 45 lost | 82 won, 53 lost | -5, -15 pts, z -2.2 | HELPS |
| all (extra) | FG made | MORE | 30 won, 26 lost | 98 won, 91 lost | 186 won, 152 lost | 525 won, 541 lost | +2, +6 pts, z +1.5 | HELPS |
| all (extra) | FG made | LESS | 19 won, 34 lost | 38 won, 41 lost | 88 won, 114 lost | 173 won, 165 lost | -12, -8 pts, z -2.2 | HELPS |
| all (extra) | All five | MORE | 216 won, 212 lost | 826 won, 852 lost | 318 won, 283 lost | 988 won, 987 lost | +1, +3 pts, z +1.2 | HELPS |
| all (extra) | All five | LESS | 266 won, 264 lost | 613 won, 519 lost | 297 won, 289 lost | 482 won, 432 lost | -4, -2 pts, z -1.6 | HELPS |

### Minutes trend (up vs down)

| Win Prob | Stat | Side | Build: minutes up 3+ | Build: minutes down 3+ | Check: minutes up 3+ | Check: minutes down 3+ | Gap | Verdict |
|---|---|---|---|---|---|---|---|---|
| 60+ | Points | MORE | 5 won, 1 lost | 1 won, 3 lost | 1 won, 2 lost | 3 won, 4 lost | +58, -10 pts, z +1.1 | flips, too few |
| 60+ | Points | LESS | 8 won, 7 lost | 2 won, 4 lost | 3 won, 4 lost | 2 won, 1 lost | +20, -24 pts, z +0.1 | flips, too few |
| 60+ | PRA | MORE | 5 won, 2 lost | 2 won, 1 lost | 4 won, 2 lost | 1 won, 0 lost | +5, -33 pts, z -0.4 | flips, too few |
| 60+ | PRA | LESS | 12 won, 9 lost | 4 won, 5 lost | 3 won, 6 lost | 6 won, 1 lost | +13, -52 pts, z -1.0 | flips, too few |
| 60+ | Rebounds | MORE | 3 won, 1 lost | 1 won, 1 lost | 1 won, 0 lost | 3 won, 0 lost | +25, +0 pts, z +0.4 | flips, too few |
| 60+ | Rebounds | LESS | 5 won, 3 lost | 9 won, 2 lost | 2 won, 3 lost | 2 won, 2 lost | -19, -10 pts, z -0.9 | same way, too few |
| 60+ | Reb+Ast | MORE | 1 won, 1 lost | 3 won, 6 lost | 3 won, 3 lost | 1 won, 2 lost | +17, +17 pts, z +0.6 | same way, too few |
| 60+ | Reb+Ast | LESS | 9 won, 10 lost | 5 won, 3 lost | 5 won, 1 lost | 2 won, 2 lost | -15, +33 pts, z +0.3 | flips, too few |
| 60+ | FG made | MORE | 6 won, 2 lost | 1 won, 1 lost | 15 won, 5 lost | 7 won, 5 lost | +25, +17 pts, z +1.2 | same way, too few |
| 60+ | FG made | LESS | 2 won, 2 lost | 1 won, 0 lost | 3 won, 6 lost | 3 won, 2 lost | -50, -27 pts, z -1.3 | same way, too few |
| 60+ | All five | MORE | 20 won, 7 lost | 8 won, 12 lost | 24 won, 12 lost | 15 won, 11 lost | +34, +9 pts, z +2.2 | same way, too few |
| 60+ | All five | LESS | 36 won, 31 lost | 21 won, 14 lost | 16 won, 20 lost | 15 won, 8 lost | -6, -21 pts, z -1.5 | same way, too few |
| 70+ | Points | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Points | LESS | 0 won, 1 lost | 0 won, 0 lost | 0 won, 2 lost | 0 won, 1 lost | - | too few |
| 70+ | PRA | MORE | 1 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | PRA | LESS | 0 won, 3 lost | 1 won, 0 lost | 0 won, 1 lost | 2 won, 0 lost | -100, -100 pts, z -2.6 | same way, too few |
| 70+ | Rebounds | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Rebounds | LESS | 1 won, 0 lost | 2 won, 0 lost | 0 won, 0 lost | 1 won, 1 lost | - | too few |
| 70+ | Reb+Ast | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | - | too few |
| 70+ | Reb+Ast | LESS | 0 won, 1 lost | 1 won, 0 lost | 2 won, 1 lost | 1 won, 0 lost | -100, -33 pts, z -1.5 | same way, too few |
| 70+ | FG made | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | FG made | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | All five | MORE | 1 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | - | too few |
| 70+ | All five | LESS | 1 won, 5 lost | 4 won, 0 lost | 2 won, 4 lost | 4 won, 2 lost | -83, -33 pts, z -2.6 | same way, too few |
| all (extra) | Points | MORE | 78 won, 75 lost | 60 won, 65 lost | 43 won, 39 lost | 30 won, 30 lost | +3, +2 pts, z +0.6 | HELPS |
| all (extra) | Points | LESS | 94 won, 71 lost | 66 won, 56 lost | 39 won, 41 lost | 33 won, 29 lost | +3, -4 pts, z -0.0 | flips |
| all (extra) | PRA | MORE | 80 won, 72 lost | 79 won, 65 lost | 39 won, 32 lost | 39 won, 24 lost | -2, -7 pts, z -0.8 | HELPS |
| all (extra) | PRA | LESS | 102 won, 87 lost | 60 won, 57 lost | 34 won, 37 lost | 37 won, 24 lost | +3, -13 pts, z -0.7 | flips |
| all (extra) | Rebounds | MORE | 62 won, 93 lost | 64 won, 60 lost | 43 won, 40 lost | 29 won, 35 lost | -12, +6 pts, z -0.8 | flips |
| all (extra) | Rebounds | LESS | 86 won, 67 lost | 61 won, 46 lost | 51 won, 39 lost | 24 won, 30 lost | -1, +12 pts, z +0.9 | flips |
| all (extra) | Reb+Ast | MORE | 76 won, 77 lost | 54 won, 69 lost | 49 won, 39 lost | 37 won, 39 lost | +6, +7 pts, z +1.3 | HELPS |
| all (extra) | Reb+Ast | LESS | 87 won, 75 lost | 49 won, 62 lost | 40 won, 34 lost | 43 won, 23 lost | +10, -11 pts, z +0.2 | flips |
| all (extra) | FG made | MORE | 44 won, 40 lost | 46 won, 46 lost | 198 won, 190 lost | 171 won, 182 lost | +2, +3 pts, z +0.7 | HELPS |
| all (extra) | FG made | LESS | 32 won, 39 lost | 21 won, 28 lost | 80 won, 109 lost | 72 won, 78 lost | +2, -6 pts, z -0.6 | flips |
| all (extra) | All five | MORE | 340 won, 357 lost | 303 won, 305 lost | 372 won, 340 lost | 306 won, 310 lost | -1, +3 pts, z +0.4 | flips |
| all (extra) | All five | LESS | 401 won, 339 lost | 257 won, 249 lost | 244 won, 260 lost | 209 won, 184 lost | +3, -5 pts, z -0.2 | flips |

### Minutes steady vs moved around

| Win Prob | Stat | Side | Build: steady | Build: moved around | Check: steady | Check: moved around | Gap | Verdict |
|---|---|---|---|---|---|---|---|---|
| 60+ | Points | MORE | 1 won, 0 lost | 10 won, 8 lost | 4 won, 3 lost | 5 won, 3 lost | +44, -5 pts, z +0.5 | flips, too few |
| 60+ | Points | LESS | 4 won, 5 lost | 10 won, 12 lost | 3 won, 1 lost | 7 won, 8 lost | -1, +28 pts, z +0.7 | flips, too few |
| 60+ | PRA | MORE | 4 won, 2 lost | 7 won, 7 lost | 1 won, 1 lost | 6 won, 4 lost | +17, -10 pts, z +0.3 | flips, too few |
| 60+ | PRA | LESS | 6 won, 5 lost | 22 won, 20 lost | 4 won, 2 lost | 15 won, 8 lost | +2, +1 pts, z +0.1 | same way, too few |
| 60+ | Rebounds | MORE | 2 won, 1 lost | 8 won, 1 lost | 1 won, 1 lost | 5 won, 1 lost | -22, -33 pts, z -1.3 | same way, too few |
| 60+ | Rebounds | LESS | 4 won, 2 lost | 19 won, 7 lost | 1 won, 1 lost | 3 won, 5 lost | -6, +12 pts, z +0.0 | flips, too few |
| 60+ | Reb+Ast | MORE | 6 won, 4 lost | 5 won, 7 lost | 4 won, 2 lost | 3 won, 6 lost | +18, +33 pts, z +1.5 | same way, too few |
| 60+ | Reb+Ast | LESS | 5 won, 0 lost | 15 won, 16 lost | 1 won, 3 lost | 9 won, 3 lost | +52, -50 pts, z +0.3 | flips, too few |
| 60+ | FG made | MORE | 4 won, 4 lost | 9 won, 3 lost | 21 won, 21 lost | 20 won, 13 lost | -25, -11 pts, z -1.5 | same way, too few |
| 60+ | FG made | LESS | 1 won, 0 lost | 3 won, 3 lost | 2 won, 2 lost | 6 won, 7 lost | +50, +4 pts, z +0.8 | same way, too few |
| 60+ | All five | MORE | 17 won, 11 lost | 39 won, 26 lost | 31 won, 28 lost | 39 won, 27 lost | +1, -7 pts, z -0.5 | flips, too few |
| 60+ | All five | LESS | 20 won, 12 lost | 69 won, 58 lost | 11 won, 9 lost | 40 won, 31 lost | +8, -1 pts, z +0.5 | flips, too few |
| 70+ | Points | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Points | LESS | 0 won, 0 lost | 0 won, 1 lost | 0 won, 0 lost | 0 won, 3 lost | - | too few |
| 70+ | PRA | MORE | 1 won, 0 lost | 0 won, 1 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | PRA | LESS | 2 won, 0 lost | 2 won, 3 lost | 0 won, 0 lost | 3 won, 2 lost | - | too few |
| 70+ | Rebounds | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Rebounds | LESS | 1 won, 0 lost | 3 won, 0 lost | 1 won, 0 lost | 0 won, 1 lost | +0, +100 pts, z +1.0 | flips, too few |
| 70+ | Reb+Ast | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | - | too few |
| 70+ | Reb+Ast | LESS | 0 won, 0 lost | 1 won, 1 lost | 0 won, 1 lost | 4 won, 1 lost | - | too few |
| 70+ | FG made | MORE | 0 won, 0 lost | 0 won, 0 lost | 1 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | FG made | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | All five | MORE | 1 won, 0 lost | 0 won, 1 lost | 1 won, 0 lost | 0 won, 1 lost | +100, +100 pts, z +2.0 | same way, too few |
| 70+ | All five | LESS | 3 won, 0 lost | 6 won, 5 lost | 1 won, 1 lost | 7 won, 7 lost | +45, +0 pts, z +1.0 | flips, too few |
| all (extra) | Points | MORE | 146 won, 166 lost | 148 won, 148 lost | 96 won, 94 lost | 78 won, 64 lost | -3, -4 pts, z -1.1 | HELPS |
| all (extra) | Points | LESS | 149 won, 121 lost | 153 won, 149 lost | 88 won, 71 lost | 75 won, 62 lost | +5, +1 pts, z +0.8 | HELPS |
| all (extra) | PRA | MORE | 176 won, 150 lost | 156 won, 147 lost | 87 won, 87 lost | 73 won, 58 lost | +3, -6 pts, z -0.3 | flips |
| all (extra) | PRA | LESS | 164 won, 132 lost | 161 won, 141 lost | 85 won, 57 lost | 80 won, 70 lost | +2, +7 pts, z +1.2 | HELPS |
| all (extra) | Rebounds | MORE | 127 won, 151 lost | 128 won, 125 lost | 95 won, 96 lost | 63 won, 69 lost | -5, +2 pts, z -0.5 | flips |
| all (extra) | Rebounds | LESS | 112 won, 96 lost | 150 won, 126 lost | 90 won, 84 lost | 67 won, 68 lost | -1, +2 pts, z +0.2 | flips |
| all (extra) | Reb+Ast | MORE | 182 won, 209 lost | 137 won, 118 lost | 121 won, 129 lost | 69 won, 64 lost | -7, -3 pts, z -1.7 | HELPS |
| all (extra) | Reb+Ast | LESS | 126 won, 111 lost | 139 won, 138 lost | 80 won, 57 lost | 77 won, 58 lost | +3, +1 pts, z +0.6 | HELPS |
| all (extra) | FG made | MORE | 99 won, 83 lost | 90 won, 87 lost | 537 won, 513 lost | 336 won, 341 lost | +4, +2 pts, z +0.9 | HELPS |
| all (extra) | FG made | LESS | 39 won, 39 lost | 56 won, 81 lost | 184 won, 195 lost | 164 won, 176 lost | +9, +0 pts, z +1.0 | HELPS |
| all (extra) | All five | MORE | 730 won, 759 lost | 659 won, 625 lost | 936 won, 919 lost | 619 won, 596 lost | -2, -0 pts, z -1.0 | HELPS |
| all (extra) | All five | LESS | 590 won, 499 lost | 659 won, 635 lost | 527 won, 464 lost | 463 won, 434 lost | +3, +2 pts, z +1.6 | HELPS |

### Spread size

| Win Prob | Stat | Side | Build: spread 10+ | Build: spread under 10 | Check: spread 10+ | Check: spread under 10 | Gap | Verdict |
|---|---|---|---|---|---|---|---|---|
| 60+ | Points | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | - | too few |
| 60+ | Points | LESS | 0 won, 0 lost | 0 won, 0 lost | 3 won, 0 lost | 0 won, 2 lost | - | too few |
| 60+ | PRA | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 2 won, 2 lost | - | too few |
| 60+ | PRA | LESS | 0 won, 0 lost | 0 won, 0 lost | 2 won, 0 lost | 3 won, 1 lost | - | too few |
| 60+ | Rebounds | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | 4 won, 0 lost | - | too few |
| 60+ | Rebounds | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | 1 won, 1 lost | - | too few |
| 60+ | Reb+Ast | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | 3 won, 5 lost | - | too few |
| 60+ | Reb+Ast | LESS | 0 won, 0 lost | 0 won, 0 lost | 2 won, 1 lost | 4 won, 2 lost | - | too few |
| 60+ | FG made | MORE | 0 won, 0 lost | 0 won, 0 lost | 5 won, 6 lost | 20 won, 18 lost | - | too few |
| 60+ | FG made | LESS | 0 won, 0 lost | 0 won, 0 lost | 2 won, 2 lost | 4 won, 6 lost | - | too few |
| 60+ | All five | MORE | 0 won, 0 lost | 0 won, 0 lost | 5 won, 8 lost | 29 won, 26 lost | - | too few |
| 60+ | All five | LESS | 0 won, 0 lost | 0 won, 0 lost | 9 won, 4 lost | 12 won, 12 lost | - | too few |
| 70+ | Points | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Points | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 2 lost | - | too few |
| 70+ | PRA | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | PRA | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Rebounds | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Rebounds | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | 1 won, 0 lost | - | too few |
| 70+ | Reb+Ast | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | - | too few |
| 70+ | Reb+Ast | LESS | 0 won, 0 lost | 0 won, 0 lost | 2 won, 1 lost | 2 won, 0 lost | - | too few |
| 70+ | FG made | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 1 won, 0 lost | - | too few |
| 70+ | FG made | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | All five | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 1 won, 1 lost | - | too few |
| 70+ | All five | LESS | 0 won, 0 lost | 0 won, 0 lost | 2 won, 2 lost | 3 won, 2 lost | - | too few |
| all (extra) | Points | MORE | 0 won, 0 lost | 0 won, 0 lost | 11 won, 8 lost | 16 won, 16 lost | - | too few |
| all (extra) | Points | LESS | 0 won, 0 lost | 0 won, 0 lost | 11 won, 7 lost | 18 won, 18 lost | - | too few |
| all (extra) | PRA | MORE | 0 won, 0 lost | 0 won, 0 lost | 7 won, 10 lost | 25 won, 26 lost | - | too few |
| all (extra) | PRA | LESS | 0 won, 0 lost | 0 won, 0 lost | 12 won, 6 lost | 32 won, 20 lost | - | too few |
| all (extra) | Rebounds | MORE | 0 won, 0 lost | 0 won, 0 lost | 7 won, 6 lost | 25 won, 37 lost | - | too few |
| all (extra) | Rebounds | LESS | 0 won, 0 lost | 0 won, 0 lost | 5 won, 6 lost | 21 won, 18 lost | - | too few |
| all (extra) | Reb+Ast | MORE | 0 won, 0 lost | 0 won, 0 lost | 5 won, 9 lost | 21 won, 35 lost | - | too few |
| all (extra) | Reb+Ast | LESS | 0 won, 0 lost | 0 won, 0 lost | 15 won, 5 lost | 30 won, 21 lost | - | too few |
| all (extra) | FG made | MORE | 0 won, 0 lost | 0 won, 0 lost | 140 won, 138 lost | 446 won, 445 lost | - | too few |
| all (extra) | FG made | LESS | 0 won, 0 lost | 0 won, 0 lost | 69 won, 81 lost | 176 won, 187 lost | - | too few |
| all (extra) | All five | MORE | 0 won, 0 lost | 0 won, 0 lost | 170 won, 171 lost | 533 won, 559 lost | - | too few |
| all (extra) | All five | LESS | 0 won, 0 lost | 0 won, 0 lost | 112 won, 105 lost | 277 won, 264 lost | - | too few |

### Player's team favored vs underdog

| Win Prob | Stat | Side | Build: favored | Build: underdog | Check: favored | Check: underdog | Gap | Verdict |
|---|---|---|---|---|---|---|---|---|
| 60+ | Points | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | 0 won, 0 lost | - | too few |
| 60+ | Points | LESS | 0 won, 0 lost | 0 won, 0 lost | 1 won, 2 lost | 2 won, 0 lost | - | too few |
| 60+ | PRA | MORE | 0 won, 0 lost | 0 won, 0 lost | 1 won, 1 lost | 1 won, 1 lost | - | too few |
| 60+ | PRA | LESS | 0 won, 0 lost | 0 won, 0 lost | 4 won, 0 lost | 1 won, 1 lost | - | too few |
| 60+ | Rebounds | MORE | 0 won, 0 lost | 0 won, 0 lost | 4 won, 0 lost | 0 won, 1 lost | - | too few |
| 60+ | Rebounds | LESS | 0 won, 0 lost | 0 won, 0 lost | 1 won, 0 lost | 0 won, 2 lost | - | too few |
| 60+ | Reb+Ast | MORE | 0 won, 0 lost | 0 won, 0 lost | 3 won, 3 lost | 0 won, 3 lost | - | too few |
| 60+ | Reb+Ast | LESS | 0 won, 0 lost | 0 won, 0 lost | 3 won, 1 lost | 3 won, 0 lost | - | too few |
| 60+ | FG made | MORE | 0 won, 0 lost | 0 won, 0 lost | 13 won, 9 lost | 12 won, 15 lost | - | too few |
| 60+ | FG made | LESS | 0 won, 0 lost | 0 won, 0 lost | 3 won, 4 lost | 3 won, 4 lost | - | too few |
| 60+ | All five | MORE | 0 won, 0 lost | 0 won, 0 lost | 21 won, 14 lost | 13 won, 20 lost | - | too few |
| 60+ | All five | LESS | 0 won, 0 lost | 0 won, 0 lost | 12 won, 7 lost | 9 won, 7 lost | - | too few |
| 70+ | Points | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Points | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 2 lost | 0 won, 0 lost | - | too few |
| 70+ | PRA | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | PRA | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Rebounds | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Rebounds | LESS | 0 won, 0 lost | 0 won, 0 lost | 1 won, 0 lost | 0 won, 1 lost | - | too few |
| 70+ | Reb+Ast | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | - | too few |
| 70+ | Reb+Ast | LESS | 0 won, 0 lost | 0 won, 0 lost | 2 won, 1 lost | 2 won, 0 lost | - | too few |
| 70+ | FG made | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 1 won, 0 lost | - | too few |
| 70+ | FG made | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | All five | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 1 won, 1 lost | - | too few |
| 70+ | All five | LESS | 0 won, 0 lost | 0 won, 0 lost | 3 won, 3 lost | 2 won, 1 lost | - | too few |
| all (extra) | Points | MORE | 0 won, 0 lost | 0 won, 0 lost | 11 won, 9 lost | 16 won, 15 lost | - | too few |
| all (extra) | Points | LESS | 0 won, 0 lost | 0 won, 0 lost | 15 won, 13 lost | 14 won, 11 lost | - | too few |
| all (extra) | PRA | MORE | 0 won, 0 lost | 0 won, 0 lost | 16 won, 20 lost | 16 won, 16 lost | - | too few |
| all (extra) | PRA | LESS | 0 won, 0 lost | 0 won, 0 lost | 23 won, 13 lost | 21 won, 13 lost | - | too few |
| all (extra) | Rebounds | MORE | 0 won, 0 lost | 0 won, 0 lost | 17 won, 22 lost | 15 won, 21 lost | - | too few |
| all (extra) | Rebounds | LESS | 0 won, 0 lost | 0 won, 0 lost | 12 won, 9 lost | 14 won, 15 lost | - | too few |
| all (extra) | Reb+Ast | MORE | 0 won, 0 lost | 0 won, 0 lost | 16 won, 21 lost | 10 won, 23 lost | - | too few |
| all (extra) | Reb+Ast | LESS | 0 won, 0 lost | 0 won, 0 lost | 22 won, 17 lost | 23 won, 6 lost | - | too few |
| all (extra) | FG made | MORE | 0 won, 0 lost | 0 won, 0 lost | 306 won, 292 lost | 276 won, 286 lost | - | too few |
| all (extra) | FG made | LESS | 0 won, 0 lost | 0 won, 0 lost | 147 won, 146 lost | 96 won, 120 lost | - | too few |
| all (extra) | All five | MORE | 0 won, 0 lost | 0 won, 0 lost | 366 won, 364 lost | 333 won, 361 lost | - | too few |
| all (extra) | All five | LESS | 0 won, 0 lost | 0 won, 0 lost | 219 won, 198 lost | 168 won, 165 lost | - | too few |

### Back-to-back

| Win Prob | Stat | Side | Build: played yesterday | Build: did not | Check: played yesterday | Check: did not | Gap | Verdict |
|---|---|---|---|---|---|---|---|---|
| 60+ | Points | MORE | 0 won, 0 lost | 11 won, 8 lost | 0 won, 0 lost | 9 won, 6 lost | - | too few |
| 60+ | Points | LESS | 3 won, 5 lost | 11 won, 13 lost | 3 won, 3 lost | 7 won, 6 lost | -8, -4 pts, z -0.4 | same way, too few |
| 60+ | PRA | MORE | 0 won, 1 lost | 11 won, 8 lost | 1 won, 2 lost | 6 won, 3 lost | -58, -33 pts, z -1.5 | same way, too few |
| 60+ | PRA | LESS | 3 won, 7 lost | 26 won, 19 lost | 6 won, 4 lost | 13 won, 6 lost | -28, -8 pts, z -1.4 | same way, too few |
| 60+ | Rebounds | MORE | 0 won, 0 lost | 10 won, 2 lost | 1 won, 0 lost | 5 won, 2 lost | - | too few |
| 60+ | Rebounds | LESS | 3 won, 0 lost | 20 won, 10 lost | 0 won, 3 lost | 4 won, 3 lost | +33, -57 pts, z -0.3 | flips, too few |
| 60+ | Reb+Ast | MORE | 0 won, 0 lost | 11 won, 11 lost | 0 won, 0 lost | 7 won, 8 lost | - | too few |
| 60+ | Reb+Ast | LESS | 4 won, 3 lost | 16 won, 13 lost | 4 won, 4 lost | 6 won, 2 lost | +2, -25 pts, z -0.7 | flips, too few |
| 60+ | FG made | MORE | 3 won, 1 lost | 10 won, 6 lost | 5 won, 10 lost | 36 won, 24 lost | +12, -27 pts, z -1.0 | flips, too few |
| 60+ | FG made | LESS | 1 won, 1 lost | 3 won, 2 lost | 3 won, 1 lost | 5 won, 8 lost | -10, +37 pts, z +0.7 | flips, too few |
| 60+ | All five | MORE | 3 won, 2 lost | 53 won, 35 lost | 7 won, 12 lost | 63 won, 43 lost | -0, -23 pts, z -1.3 | same way, too few |
| 60+ | All five | LESS | 14 won, 16 lost | 76 won, 57 lost | 16 won, 15 lost | 35 won, 25 lost | -10, -7 pts, z -1.2 | same way, too few |
| 70+ | Points | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Points | LESS | 0 won, 0 lost | 0 won, 1 lost | 0 won, 3 lost | 0 won, 0 lost | - | too few |
| 70+ | PRA | MORE | 0 won, 1 lost | 1 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | PRA | LESS | 0 won, 0 lost | 4 won, 3 lost | 1 won, 1 lost | 2 won, 1 lost | - | too few |
| 70+ | Rebounds | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Rebounds | LESS | 0 won, 0 lost | 4 won, 1 lost | 0 won, 0 lost | 1 won, 1 lost | - | too few |
| 70+ | Reb+Ast | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | - | too few |
| 70+ | Reb+Ast | LESS | 0 won, 0 lost | 1 won, 1 lost | 1 won, 0 lost | 3 won, 2 lost | - | too few |
| 70+ | FG made | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 1 won, 0 lost | - | too few |
| 70+ | FG made | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | All five | MORE | 0 won, 1 lost | 1 won, 0 lost | 0 won, 0 lost | 1 won, 1 lost | - | too few |
| 70+ | All five | LESS | 0 won, 0 lost | 9 won, 6 lost | 2 won, 4 lost | 6 won, 4 lost | - | too few |
| all (extra) | Points | MORE | 29 won, 34 lost | 266 won, 280 lost | 17 won, 10 lost | 157 won, 150 lost | -3, +12 pts, z +0.5 | flips, too few |
| all (extra) | Points | LESS | 63 won, 42 lost | 241 won, 231 lost | 25 won, 24 lost | 140 won, 110 lost | +9, -5 pts, z +0.7 | flips |
| all (extra) | PRA | MORE | 44 won, 44 lost | 293 won, 257 lost | 23 won, 25 lost | 137 won, 120 lost | -3, -5 pts, z -0.9 | HELPS |
| all (extra) | PRA | LESS | 53 won, 50 lost | 274 won, 228 lost | 28 won, 31 lost | 137 won, 98 lost | -3, -11 pts, z -1.5 | HELPS |
| all (extra) | Rebounds | MORE | 27 won, 32 lost | 229 won, 247 lost | 20 won, 21 lost | 138 won, 145 lost | -2, +0 pts, z -0.2 | flips |
| all (extra) | Rebounds | LESS | 54 won, 35 lost | 209 won, 188 lost | 27 won, 32 lost | 130 won, 121 lost | +8, -6 pts, z +0.4 | flips |
| all (extra) | Reb+Ast | MORE | 30 won, 42 lost | 289 won, 287 lost | 20 won, 26 lost | 171 won, 167 lost | -9, -7 pts, z -1.6 | HELPS |
| all (extra) | Reb+Ast | LESS | 71 won, 57 lost | 195 won, 192 lost | 27 won, 26 lost | 130 won, 90 lost | +5, -8 pts, z -0.1 | flips |
| all (extra) | FG made | MORE | 35 won, 30 lost | 154 won, 144 lost | 131 won, 114 lost | 742 won, 740 lost | +2, +3 pts, z +0.9 | HELPS |
| all (extra) | FG made | LESS | 20 won, 17 lost | 75 won, 103 lost | 64 won, 73 lost | 284 won, 298 lost | +12, -2 pts, z +0.6 | flips, too few |
| all (extra) | All five | MORE | 165 won, 182 lost | 1231 won, 1215 lost | 211 won, 196 lost | 1345 won, 1322 lost | -3, +1 pts, z -0.3 | flips |
| all (extra) | All five | LESS | 261 won, 201 lost | 994 won, 942 lost | 171 won, 186 lost | 821 won, 717 lost | +5, -5 pts, z +0.1 | flips |

### Rest days

| Win Prob | Stat | Side | Build: 2+ days off | Build: 0-1 days off | Check: 2+ days off | Check: 0-1 days off | Gap | Verdict |
|---|---|---|---|---|---|---|---|---|
| 60+ | Points | MORE | 3 won, 5 lost | 8 won, 3 lost | 4 won, 4 lost | 5 won, 2 lost | -35, -21 pts, z -1.7 | same way, too few |
| 60+ | Points | LESS | 4 won, 3 lost | 10 won, 15 lost | 3 won, 1 lost | 7 won, 8 lost | +17, +28 pts, z +1.3 | same way, too few |
| 60+ | PRA | MORE | 7 won, 2 lost | 4 won, 7 lost | 2 won, 1 lost | 5 won, 4 lost | +41, +11 pts, z +1.5 | same way, too few |
| 60+ | PRA | LESS | 8 won, 3 lost | 21 won, 23 lost | 6 won, 3 lost | 13 won, 7 lost | +25, +2 pts, z +1.1 | same way, too few |
| 60+ | Rebounds | MORE | 3 won, 1 lost | 7 won, 1 lost | 0 won, 1 lost | 6 won, 1 lost | -12, -86 pts, z -1.7 | same way, too few |
| 60+ | Rebounds | LESS | 6 won, 4 lost | 17 won, 6 lost | 2 won, 1 lost | 2 won, 5 lost | -14, +38 pts, z +0.2 | flips, too few |
| 60+ | Reb+Ast | MORE | 3 won, 5 lost | 8 won, 6 lost | 3 won, 5 lost | 4 won, 3 lost | -20, -20 pts, z -1.2 | same way, too few |
| 60+ | Reb+Ast | LESS | 5 won, 4 lost | 15 won, 12 lost | 3 won, 0 lost | 7 won, 6 lost | +0, +46 pts, z +1.1 | flips, too few |
| 60+ | FG made | MORE | 2 won, 4 lost | 11 won, 3 lost | 18 won, 6 lost | 23 won, 28 lost | -45, +30 pts, z +0.3 | flips, too few |
| 60+ | FG made | LESS | 0 won, 1 lost | 4 won, 2 lost | 1 won, 3 lost | 7 won, 6 lost | -67, -29 pts, z -1.6 | same way, too few |
| 60+ | All five | MORE | 18 won, 17 lost | 38 won, 20 lost | 27 won, 17 lost | 43 won, 38 lost | -14, +8 pts, z -0.3 | flips, too few |
| 60+ | All five | LESS | 23 won, 15 lost | 67 won, 58 lost | 15 won, 8 lost | 36 won, 32 lost | +7, +12 pts, z +1.3 | same way, too few |
| 70+ | Points | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Points | LESS | 0 won, 0 lost | 0 won, 1 lost | 0 won, 0 lost | 0 won, 3 lost | - | too few |
| 70+ | PRA | MORE | 1 won, 0 lost | 0 won, 1 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | PRA | LESS | 3 won, 0 lost | 1 won, 3 lost | 1 won, 0 lost | 2 won, 2 lost | +75, +50 pts, z +2.0 | same way, too few |
| 70+ | Rebounds | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Rebounds | LESS | 2 won, 0 lost | 2 won, 1 lost | 0 won, 0 lost | 1 won, 1 lost | - | too few |
| 70+ | Reb+Ast | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | 0 won, 0 lost | - | too few |
| 70+ | Reb+Ast | LESS | 1 won, 0 lost | 0 won, 1 lost | 1 won, 0 lost | 3 won, 2 lost | +100, +40 pts, z +1.5 | same way, too few |
| 70+ | FG made | MORE | 0 won, 0 lost | 0 won, 0 lost | 1 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | FG made | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | All five | MORE | 1 won, 0 lost | 0 won, 1 lost | 1 won, 1 lost | 0 won, 0 lost | - | too few |
| 70+ | All five | LESS | 6 won, 0 lost | 3 won, 6 lost | 2 won, 0 lost | 6 won, 8 lost | +67, +57 pts, z +2.9 | same way, too few |
| all (extra) | Points | MORE | 84 won, 99 lost | 211 won, 215 lost | 41 won, 56 lost | 133 won, 104 lost | -4, -14 pts, z -2.2 | HELPS |
| all (extra) | Points | LESS | 75 won, 71 lost | 229 won, 202 lost | 58 won, 39 lost | 107 won, 95 lost | -2, +7 pts, z +0.5 | flips |
| all (extra) | PRA | MORE | 97 won, 78 lost | 240 won, 223 lost | 57 won, 41 lost | 103 won, 104 lost | +4, +8 pts, z +1.5 | HELPS |
| all (extra) | PRA | LESS | 73 won, 56 lost | 254 won, 222 lost | 54 won, 41 lost | 111 won, 88 lost | +3, +1 pts, z +0.6 | HELPS |
| all (extra) | Rebounds | MORE | 71 won, 69 lost | 185 won, 210 lost | 51 won, 55 lost | 107 won, 111 lost | +4, -1 pts, z +0.4 | flips |
| all (extra) | Rebounds | LESS | 58 won, 54 lost | 205 won, 169 lost | 49 won, 53 lost | 108 won, 100 lost | -3, -4 pts, z -0.9 | HELPS |
| all (extra) | Reb+Ast | MORE | 94 won, 90 lost | 225 won, 239 lost | 71 won, 68 lost | 120 won, 125 lost | +3, +2 pts, z +0.7 | HELPS |
| all (extra) | Reb+Ast | LESS | 62 won, 48 lost | 204 won, 201 lost | 46 won, 32 lost | 111 won, 84 lost | +6, +2 pts, z +1.0 | HELPS |
| all (extra) | FG made | MORE | 44 won, 53 lost | 145 won, 121 lost | 255 won, 267 lost | 618 won, 587 lost | -9, -2 pts, z -1.7 | HELPS |
| all (extra) | FG made | LESS | 21 won, 27 lost | 74 won, 93 lost | 85 won, 96 lost | 263 won, 275 lost | -1, -2 pts, z -0.4 | HELPS |
| all (extra) | All five | MORE | 390 won, 389 lost | 1006 won, 1008 lost | 475 won, 487 lost | 1081 won, 1031 lost | +0, -2 pts, z -0.6 | flips |
| all (extra) | All five | LESS | 289 won, 256 lost | 966 won, 887 lost | 292 won, 261 lost | 700 won, 642 lost | +1, +1 pts, z +0.4 | HELPS |

### Opponent allows

| Win Prob | Stat | Side | Build: allows a lot | Build: allows little | Check: allows a lot | Check: allows little | Gap | Verdict |
|---|---|---|---|---|---|---|---|---|
| 60+ | Points | MORE | 4 won, 4 lost | 3 won, 2 lost | 3 won, 1 lost | 2 won, 4 lost | -10, +42 pts, z +0.7 | flips, too few |
| 60+ | Points | LESS | 2 won, 5 lost | 2 won, 7 lost | 5 won, 2 lost | 4 won, 6 lost | +6, +31 pts, z +1.1 | same way, too few |
| 60+ | PRA | MORE | 4 won, 5 lost | 3 won, 1 lost | 4 won, 0 lost | 1 won, 0 lost | -31, +0 pts, z -0.7 | flips, too few |
| 60+ | PRA | LESS | 9 won, 10 lost | 14 won, 7 lost | 10 won, 5 lost | 1 won, 2 lost | -19, +33 pts, z -0.1 | flips, too few |
| 60+ | Rebounds | MORE | 5 won, 1 lost | 2 won, 0 lost | 2 won, 0 lost | 1 won, 0 lost | -17, +0 pts, z -0.4 | flips, too few |
| 60+ | Rebounds | LESS | 8 won, 3 lost | 8 won, 4 lost | 2 won, 4 lost | 0 won, 1 lost | +6, +33 pts, z +0.7 | same way, too few |
| 60+ | Reb+Ast | MORE | 8 won, 6 lost | 0 won, 1 lost | 4 won, 4 lost | 1 won, 3 lost | +57, +25 pts, z +1.4 | same way, too few |
| 60+ | Reb+Ast | LESS | 7 won, 4 lost | 7 won, 8 lost | 3 won, 2 lost | 5 won, 2 lost | +17, -11 pts, z +0.3 | flips, too few |
| 60+ | FG made | MORE | 4 won, 4 lost | 8 won, 1 lost | 9 won, 11 lost | 18 won, 14 lost | -39, -11 pts, z -1.8 | same way, too few |
| 60+ | FG made | LESS | 2 won, 0 lost | 1 won, 1 lost | 2 won, 5 lost | 4 won, 1 lost | +50, -51 pts, z -0.4 | flips, too few |
| 60+ | All five | MORE | 25 won, 20 lost | 16 won, 5 lost | 22 won, 16 lost | 23 won, 21 lost | -21, +6 pts, z -0.8 | flips, too few |
| 60+ | All five | LESS | 28 won, 22 lost | 32 won, 27 lost | 22 won, 18 lost | 14 won, 12 lost | +2, +1 pts, z +0.2 | same way, too few |
| 70+ | Points | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Points | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | 0 won, 1 lost | - | too few |
| 70+ | PRA | MORE | 0 won, 1 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | PRA | LESS | 1 won, 1 lost | 3 won, 1 lost | 1 won, 1 lost | 0 won, 1 lost | -25, +50 pts, z +0.2 | flips, too few |
| 70+ | Rebounds | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Rebounds | LESS | 1 won, 0 lost | 2 won, 1 lost | 1 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Reb+Ast | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | 0 won, 0 lost | - | too few |
| 70+ | Reb+Ast | LESS | 0 won, 0 lost | 0 won, 1 lost | 1 won, 0 lost | 2 won, 0 lost | - | too few |
| 70+ | FG made | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 1 won, 0 lost | - | too few |
| 70+ | FG made | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | All five | MORE | 0 won, 1 lost | 0 won, 0 lost | 0 won, 1 lost | 1 won, 0 lost | - | too few |
| 70+ | All five | LESS | 2 won, 1 lost | 5 won, 3 lost | 3 won, 2 lost | 2 won, 2 lost | +4, +10 pts, z +0.3 | same way, too few |
| all (extra) | Points | MORE | 110 won, 116 lost | 81 won, 99 lost | 47 won, 46 lost | 61 won, 51 lost | +4, -4 pts, z +0.1 | flips |
| all (extra) | Points | LESS | 75 won, 96 lost | 123 won, 93 lost | 43 won, 37 lost | 67 won, 47 lost | -13, -5 pts, z -2.3 | HELPS |
| all (extra) | PRA | MORE | 128 won, 113 lost | 93 won, 86 lost | 63 won, 47 lost | 43 won, 40 lost | +1, +5 pts, z +0.7 | HELPS |
| all (extra) | PRA | LESS | 76 won, 100 lost | 145 won, 91 lost | 59 won, 52 lost | 43 won, 31 lost | -18, -5 pts, z -3.1 | HELPS |
| all (extra) | Rebounds | MORE | 108 won, 95 lost | 79 won, 87 lost | 51 won, 63 lost | 62 won, 53 lost | +6, -9 pts, z -0.2 | flips |
| all (extra) | Rebounds | LESS | 75 won, 64 lost | 100 won, 75 lost | 55 won, 57 lost | 61 won, 55 lost | -3, -3 pts, z -0.8 | HELPS |
| all (extra) | Reb+Ast | MORE | 112 won, 117 lost | 90 won, 104 lost | 62 won, 62 lost | 51 won, 65 lost | +3, +6 pts, z +1.0 | HELPS |
| all (extra) | Reb+Ast | LESS | 81 won, 78 lost | 101 won, 93 lost | 52 won, 39 lost | 58 won, 36 lost | -1, -5 pts, z -0.6 | HELPS |
| all (extra) | FG made | MORE | 62 won, 63 lost | 55 won, 64 lost | 221 won, 200 lost | 431 won, 413 lost | +3, +1 pts, z +0.7 | HELPS |
| all (extra) | FG made | LESS | 28 won, 42 lost | 38 won, 37 lost | 98 won, 94 lost | 160 won, 176 lost | -11, +3 pts, z -0.4 | flips |
| all (extra) | All five | MORE | 520 won, 504 lost | 398 won, 440 lost | 444 won, 418 lost | 648 won, 622 lost | +3, +0 pts, z +1.2 | HELPS |
| all (extra) | All five | LESS | 335 won, 380 lost | 507 won, 389 lost | 307 won, 279 lost | 389 won, 345 lost | -10, -1 pts, z -2.9 | HELPS |

### Room vs book median (any gap)

| Win Prob | Stat | Side | Build: book line favors pick | Build: book line against pick | Check: book line favors pick | Check: book line against pick | Gap | Verdict |
|---|---|---|---|---|---|---|---|---|
| 60+ | Points | MORE | 4 won, 0 lost | 1 won, 1 lost | 2 won, 3 lost | 0 won, 1 lost | +50, +40 pts, z +1.6 | same way, too few |
| 60+ | Points | LESS | 3 won, 10 lost | 4 won, 2 lost | 3 won, 4 lost | 3 won, 2 lost | -44, -17 pts, z -1.7 | same way, too few |
| 60+ | PRA | MORE | 5 won, 3 lost | 0 won, 0 lost | 2 won, 2 lost | 0 won, 0 lost | - | too few |
| 60+ | PRA | LESS | 5 won, 9 lost | 1 won, 1 lost | 3 won, 6 lost | 1 won, 1 lost | -14, -17 pts, z -0.6 | same way, too few |
| 60+ | Rebounds | MORE | 5 won, 0 lost | 0 won, 0 lost | 5 won, 1 lost | 0 won, 0 lost | - | too few |
| 60+ | Rebounds | LESS | 9 won, 3 lost | 0 won, 0 lost | 1 won, 2 lost | 0 won, 0 lost | - | too few |
| 60+ | Reb+Ast | MORE | 4 won, 3 lost | 0 won, 1 lost | 1 won, 1 lost | 0 won, 1 lost | +57, +50 pts, z +1.4 | same way, too few |
| 60+ | Reb+Ast | LESS | 5 won, 3 lost | 1 won, 0 lost | 3 won, 1 lost | 1 won, 1 lost | -38, +25 pts, z -0.1 | flips, too few |
| 60+ | FG made | MORE | 3 won, 0 lost | 0 won, 1 lost | 7 won, 3 lost | 1 won, 2 lost | +100, +37 pts, z +2.2 | same way, too few |
| 60+ | FG made | LESS | 0 won, 0 lost | 0 won, 1 lost | 2 won, 1 lost | 1 won, 1 lost | - | too few |
| 60+ | All five | MORE | 21 won, 6 lost | 1 won, 3 lost | 17 won, 10 lost | 1 won, 4 lost | +53, +43 pts, z +2.8 | same way, too few |
| 60+ | All five | LESS | 22 won, 25 lost | 6 won, 4 lost | 12 won, 14 lost | 6 won, 5 lost | -13, -8 pts, z -0.9 | same way, too few |
| 70+ | Points | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Points | LESS | 0 won, 1 lost | 0 won, 0 lost | 0 won, 1 lost | 0 won, 1 lost | - | too few |
| 70+ | PRA | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | PRA | LESS | 1 won, 1 lost | 0 won, 0 lost | 0 won, 2 lost | 0 won, 0 lost | - | too few |
| 70+ | Rebounds | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Rebounds | LESS | 2 won, 1 lost | 0 won, 0 lost | 0 won, 1 lost | 0 won, 0 lost | - | too few |
| 70+ | Reb+Ast | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | - | too few |
| 70+ | Reb+Ast | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 1 won, 1 lost | - | too few |
| 70+ | FG made | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | FG made | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | All five | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | - | too few |
| 70+ | All five | LESS | 3 won, 3 lost | 0 won, 0 lost | 0 won, 4 lost | 1 won, 2 lost | - | too few |
| all (extra) | Points | MORE | 75 won, 64 lost | 40 won, 46 lost | 52 won, 42 lost | 30 won, 38 lost | +7, +11 pts, z +1.8 | HELPS |
| all (extra) | Points | LESS | 80 won, 75 lost | 49 won, 40 lost | 45 won, 39 lost | 29 won, 34 lost | -3, +8 pts, z +0.3 | flips |
| all (extra) | PRA | MORE | 86 won, 60 lost | 44 won, 49 lost | 42 won, 29 lost | 22 won, 26 lost | +12, +13 pts, z +2.3 | HELPS |
| all (extra) | PRA | LESS | 71 won, 53 lost | 37 won, 38 lost | 45 won, 33 lost | 31 won, 22 lost | +8, -1 pts, z +0.7 | flips |
| all (extra) | Rebounds | MORE | 60 won, 53 lost | 15 won, 18 lost | 38 won, 23 lost | 12 won, 18 lost | +8, +22 pts, z +2.0 | same way, too few |
| all (extra) | Rebounds | LESS | 46 won, 33 lost | 19 won, 21 lost | 27 won, 18 lost | 12 won, 17 lost | +11, +19 pts, z +1.9 | same way, too few |
| all (extra) | Reb+Ast | MORE | 50 won, 43 lost | 29 won, 35 lost | 21 won, 27 lost | 17 won, 26 lost | +8, +4 pts, z +1.0 | HELPS |
| all (extra) | Reb+Ast | LESS | 61 won, 51 lost | 12 won, 22 lost | 18 won, 15 lost | 14 won, 13 lost | +19, +3 pts, z +1.5 | same way, too few |
| all (extra) | FG made | MORE | 20 won, 16 lost | 7 won, 11 lost | 85 won, 60 lost | 21 won, 36 lost | +17, +22 pts, z +2.8 | same way, too few |
| all (extra) | FG made | LESS | 3 won, 6 lost | 8 won, 19 lost | 31 won, 24 lost | 15 won, 34 lost | +4, +26 pts, z +2.0 | same way, too few |
| all (extra) | All five | MORE | 291 won, 236 lost | 135 won, 159 lost | 238 won, 181 lost | 102 won, 144 lost | +9, +15 pts, z +4.5 | HELPS |
| all (extra) | All five | LESS | 261 won, 218 lost | 125 won, 140 lost | 166 won, 129 lost | 101 won, 120 lost | +7, +11 pts, z +3.0 | HELPS |

### Room vs book median (1+ gap)

| Win Prob | Stat | Side | Build: 1+ in favor | Build: 1+ against | Check: 1+ in favor | Check: 1+ against | Gap | Verdict |
|---|---|---|---|---|---|---|---|---|
| 60+ | Points | MORE | 4 won, 0 lost | 1 won, 0 lost | 1 won, 3 lost | 0 won, 0 lost | - | too few |
| 60+ | Points | LESS | 3 won, 8 lost | 2 won, 1 lost | 3 won, 3 lost | 3 won, 0 lost | -39, -50 pts, z -2.0 | same way, too few |
| 60+ | PRA | MORE | 5 won, 3 lost | 0 won, 0 lost | 2 won, 2 lost | 0 won, 0 lost | - | too few |
| 60+ | PRA | LESS | 5 won, 9 lost | 1 won, 1 lost | 2 won, 5 lost | 1 won, 1 lost | -14, -21 pts, z -0.7 | same way, too few |
| 60+ | Rebounds | MORE | 5 won, 0 lost | 0 won, 0 lost | 5 won, 1 lost | 0 won, 0 lost | - | too few |
| 60+ | Rebounds | LESS | 8 won, 3 lost | 0 won, 0 lost | 1 won, 1 lost | 0 won, 0 lost | - | too few |
| 60+ | Reb+Ast | MORE | 4 won, 2 lost | 0 won, 1 lost | 1 won, 1 lost | 0 won, 1 lost | +67, +50 pts, z +1.5 | same way, too few |
| 60+ | Reb+Ast | LESS | 5 won, 2 lost | 1 won, 0 lost | 3 won, 1 lost | 1 won, 1 lost | -29, +25 pts, z -0.0 | flips, too few |
| 60+ | FG made | MORE | 3 won, 0 lost | 0 won, 1 lost | 6 won, 3 lost | 1 won, 2 lost | +100, +33 pts, z +2.1 | same way, too few |
| 60+ | FG made | LESS | 0 won, 0 lost | 0 won, 1 lost | 2 won, 1 lost | 1 won, 1 lost | - | too few |
| 60+ | All five | MORE | 21 won, 5 lost | 1 won, 2 lost | 15 won, 10 lost | 1 won, 3 lost | +47, +35 pts, z +2.2 | same way, too few |
| 60+ | All five | LESS | 21 won, 22 lost | 4 won, 3 lost | 11 won, 11 lost | 6 won, 3 lost | -8, -17 pts, z -0.9 | same way, too few |
| 70+ | Points | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Points | LESS | 0 won, 1 lost | 0 won, 0 lost | 0 won, 1 lost | 0 won, 0 lost | - | too few |
| 70+ | PRA | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | PRA | LESS | 1 won, 1 lost | 0 won, 0 lost | 0 won, 1 lost | 0 won, 0 lost | - | too few |
| 70+ | Rebounds | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Rebounds | LESS | 2 won, 1 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Reb+Ast | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | - | too few |
| 70+ | Reb+Ast | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 1 won, 1 lost | - | too few |
| 70+ | FG made | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | FG made | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | All five | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | - | too few |
| 70+ | All five | LESS | 3 won, 3 lost | 0 won, 0 lost | 0 won, 2 lost | 1 won, 1 lost | - | too few |
| all (extra) | Points | MORE | 66 won, 51 lost | 32 won, 39 lost | 43 won, 38 lost | 23 won, 31 lost | +11, +10 pts, z +1.9 | HELPS |
| all (extra) | Points | LESS | 75 won, 62 lost | 42 won, 35 lost | 34 won, 28 lost | 22 won, 25 lost | +0, +8 pts, z +0.6 | HELPS |
| all (extra) | PRA | MORE | 71 won, 51 lost | 35 won, 41 lost | 31 won, 23 lost | 20 won, 16 lost | +12, +2 pts, z +1.3 | same way, too few |
| all (extra) | PRA | LESS | 58 won, 48 lost | 30 won, 32 lost | 37 won, 26 lost | 25 won, 17 lost | +6, -1 pts, z +0.5 | flips |
| all (extra) | Rebounds | MORE | 44 won, 43 lost | 7 won, 12 lost | 32 won, 16 lost | 9 won, 11 lost | +14, +22 pts, z +1.9 | same way, too few |
| all (extra) | Rebounds | LESS | 35 won, 25 lost | 13 won, 17 lost | 21 won, 14 lost | 11 won, 13 lost | +15, +14 pts, z +1.7 | same way, too few |
| all (extra) | Reb+Ast | MORE | 39 won, 31 lost | 20 won, 26 lost | 18 won, 17 lost | 11 won, 17 lost | +12, +12 pts, z +1.6 | same way, too few |
| all (extra) | Reb+Ast | LESS | 55 won, 38 lost | 9 won, 19 lost | 12 won, 12 lost | 9 won, 9 lost | +27, +0 pts, z +1.8 | flips, too few |
| all (extra) | FG made | MORE | 16 won, 15 lost | 5 won, 8 lost | 82 won, 60 lost | 21 won, 36 lost | +13, +21 pts, z +2.5 | same way, too few |
| all (extra) | FG made | LESS | 1 won, 5 lost | 8 won, 17 lost | 30 won, 24 lost | 15 won, 34 lost | -15, +25 pts, z +1.3 | flips, too few |
| all (extra) | All five | MORE | 236 won, 191 lost | 99 won, 126 lost | 206 won, 154 lost | 84 won, 111 lost | +11, +14 pts, z +4.2 | HELPS |
| all (extra) | All five | LESS | 224 won, 178 lost | 102 won, 120 lost | 134 won, 104 lost | 82 won, 98 lost | +10, +11 pts, z +3.2 | HELPS |

### Room vs bet365 only

| Win Prob | Stat | Side | Build: bet365 favors pick | Build: bet365 against pick | Check: bet365 favors pick | Check: bet365 against pick | Gap | Verdict |
|---|---|---|---|---|---|---|---|---|
| 60+ | Points | MORE | 2 won, 0 lost | 1 won, 0 lost | 2 won, 2 lost | 1 won, 0 lost | +0, -50 pts, z -0.6 | flips, too few |
| 60+ | Points | LESS | 1 won, 4 lost | 2 won, 0 lost | 3 won, 1 lost | 3 won, 2 lost | -80, +15 pts, z -1.0 | flips, too few |
| 60+ | PRA | MORE | 3 won, 0 lost | 0 won, 0 lost | 2 won, 2 lost | 0 won, 0 lost | - | too few |
| 60+ | PRA | LESS | 2 won, 5 lost | 0 won, 1 lost | 1 won, 3 lost | 2 won, 0 lost | +29, -75 pts, z -0.8 | flips, too few |
| 60+ | Rebounds | MORE | 5 won, 0 lost | 0 won, 0 lost | 5 won, 1 lost | 0 won, 0 lost | - | too few |
| 60+ | Rebounds | LESS | 8 won, 2 lost | 0 won, 0 lost | 0 won, 1 lost | 1 won, 0 lost | - | too few |
| 60+ | Reb+Ast | MORE | 4 won, 2 lost | 0 won, 1 lost | 1 won, 1 lost | 1 won, 1 lost | +67, +0 pts, z +0.9 | flips, too few |
| 60+ | Reb+Ast | LESS | 4 won, 3 lost | 1 won, 0 lost | 1 won, 1 lost | 1 won, 0 lost | -43, -50 pts, z -1.2 | same way, too few |
| 60+ | FG made | MORE | 3 won, 0 lost | 0 won, 1 lost | 7 won, 3 lost | 1 won, 2 lost | +100, +37 pts, z +2.2 | same way, too few |
| 60+ | FG made | LESS | 0 won, 0 lost | 0 won, 1 lost | 2 won, 1 lost | 1 won, 1 lost | - | too few |
| 60+ | All five | MORE | 17 won, 2 lost | 1 won, 2 lost | 17 won, 9 lost | 3 won, 3 lost | +56, +15 pts, z +2.2 | same way, too few |
| 60+ | All five | LESS | 15 won, 14 lost | 3 won, 2 lost | 7 won, 7 lost | 8 won, 3 lost | -8, -23 pts, z -1.1 | same way, too few |
| 70+ | Points | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Points | LESS | 0 won, 1 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | - | too few |
| 70+ | PRA | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | PRA | LESS | 0 won, 1 lost | 0 won, 0 lost | 0 won, 1 lost | 1 won, 0 lost | - | too few |
| 70+ | Rebounds | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Rebounds | LESS | 2 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | 1 won, 0 lost | - | too few |
| 70+ | Reb+Ast | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | - | too few |
| 70+ | Reb+Ast | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 1 won, 0 lost | - | too few |
| 70+ | FG made | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | FG made | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | All five | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | - | too few |
| 70+ | All five | LESS | 2 won, 2 lost | 0 won, 0 lost | 0 won, 2 lost | 3 won, 1 lost | - | too few |
| all (extra) | Points | MORE | 44 won, 22 lost | 28 won, 21 lost | 42 won, 42 lost | 21 won, 27 lost | +10, +6 pts, z +1.2 | HELPS |
| all (extra) | Points | LESS | 33 won, 35 lost | 34 won, 17 lost | 38 won, 28 lost | 23 won, 26 lost | -18, +11 pts, z -0.6 | flips |
| all (extra) | PRA | MORE | 34 won, 17 lost | 12 won, 16 lost | 27 won, 19 lost | 21 won, 19 lost | +24, +6 pts, z +1.9 | same way, too few |
| all (extra) | PRA | LESS | 23 won, 19 lost | 12 won, 8 lost | 36 won, 25 lost | 25 won, 20 lost | -5, +3 pts, z -0.0 | flips, too few |
| all (extra) | Rebounds | MORE | 41 won, 33 lost | 6 won, 10 lost | 32 won, 20 lost | 7 won, 11 lost | +18, +23 pts, z +2.1 | same way, too few |
| all (extra) | Rebounds | LESS | 29 won, 23 lost | 14 won, 15 lost | 20 won, 13 lost | 13 won, 13 lost | +7, +11 pts, z +1.0 | same way, too few |
| all (extra) | Reb+Ast | MORE | 32 won, 27 lost | 13 won, 16 lost | 21 won, 19 lost | 16 won, 17 lost | +9, +4 pts, z +0.8 | same way, too few |
| all (extra) | Reb+Ast | LESS | 26 won, 26 lost | 8 won, 14 lost | 14 won, 10 lost | 12 won, 10 lost | +14, +4 pts, z +0.9 | same way, too few |
| all (extra) | FG made | MORE | 20 won, 16 lost | 7 won, 11 lost | 85 won, 60 lost | 21 won, 36 lost | +17, +22 pts, z +2.8 | same way, too few |
| all (extra) | FG made | LESS | 3 won, 6 lost | 8 won, 19 lost | 31 won, 24 lost | 15 won, 34 lost | +4, +26 pts, z +2.0 | same way, too few |
| all (extra) | All five | MORE | 171 won, 115 lost | 66 won, 74 lost | 207 won, 160 lost | 86 won, 110 lost | +13, +13 pts, z +3.7 | HELPS |
| all (extra) | All five | LESS | 114 won, 109 lost | 76 won, 73 lost | 139 won, 100 lost | 88 won, 103 lost | +0, +12 pts, z +1.8 | HELPS |

### Room vs Pinnacle only

| Win Prob | Stat | Side | Build: Pinnacle favors pick | Build: Pinnacle against pick | Check: Pinnacle favors pick | Check: Pinnacle against pick | Gap | Verdict |
|---|---|---|---|---|---|---|---|---|
| 60+ | Points | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 60+ | Points | LESS | 1 won, 0 lost | 1 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 60+ | PRA | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 60+ | PRA | LESS | 0 won, 0 lost | 0 won, 0 lost | 1 won, 3 lost | 1 won, 0 lost | - | too few |
| 60+ | Rebounds | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 60+ | Rebounds | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 60+ | Reb+Ast | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 60+ | Reb+Ast | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 60+ | FG made | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 60+ | FG made | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 60+ | All five | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 60+ | All five | LESS | 1 won, 0 lost | 1 won, 0 lost | 1 won, 3 lost | 1 won, 0 lost | +0, -75 pts, z -1.0 | flips, too few |
| 70+ | Points | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Points | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | PRA | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | PRA | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | 0 won, 0 lost | - | too few |
| 70+ | Rebounds | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Rebounds | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Reb+Ast | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | Reb+Ast | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | FG made | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | FG made | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | All five | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| 70+ | All five | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | 0 won, 0 lost | - | too few |
| all (extra) | Points | MORE | 8 won, 9 lost | 4 won, 6 lost | 0 won, 0 lost | 1 won, 1 lost | - | too few |
| all (extra) | Points | LESS | 8 won, 5 lost | 11 won, 5 lost | 2 won, 3 lost | 2 won, 3 lost | -7, +0 pts, z -0.3 | flips, too few |
| all (extra) | PRA | MORE | 0 won, 0 lost | 0 won, 0 lost | 3 won, 0 lost | 3 won, 0 lost | - | too few |
| all (extra) | PRA | LESS | 2 won, 0 lost | 0 won, 0 lost | 9 won, 8 lost | 4 won, 1 lost | - | too few |
| all (extra) | Rebounds | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | 0 won, 2 lost | - | too few |
| all (extra) | Rebounds | LESS | 0 won, 0 lost | 1 won, 0 lost | 3 won, 0 lost | 1 won, 0 lost | - | too few |
| all (extra) | Reb+Ast | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| all (extra) | Reb+Ast | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| all (extra) | FG made | MORE | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| all (extra) | FG made | LESS | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | - | too few |
| all (extra) | All five | MORE | 8 won, 9 lost | 4 won, 6 lost | 3 won, 1 lost | 4 won, 3 lost | +7, +18 pts, z +0.7 | same way, too few |
| all (extra) | All five | LESS | 10 won, 5 lost | 12 won, 5 lost | 14 won, 11 lost | 7 won, 4 lost | -4, -8 pts, z -0.5 | same way, too few |

## Goblin estimate

**This is an estimate. The data has no Goblin labels.** Lines were lowered by a fixed amount; real Goblins are set by PrizePicks, pay less and may sit at other distances. Records count only players who played.

Offsets tried: Points and PRA 1, 2, 3, 4. Reb+Ast 1, 1.5, 2, 3. Rebounds and FG made 0.5, 1, 1.5, 2. Ties on the lowered line are left out.

Win Prob is recomputed at each lower line with the Step 3 method: same projection, same spread, same confidence setting (k = 4.0 on all five, tuned on the original lines only, not re-tuned), MORE side only. Inputs were rebuilt from history and checked against the stored Step 3 picks (see Data checks).

### Step 3 MORE picks

| Stat | Lower by | Picks | All picks | Under 70 | 70-74 | 75-79 | 80+ | 70+ build half | 70+ check half |
|---|---|---|---|---|---|---|---|---|---|
| Points | 1 | 943 | 538 won, 405 lost | 538 won, 404 lost | 0 won, 1 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost |
| Points | 2 | 943 | 584 won, 358 lost | 584 won, 356 lost | 0 won, 2 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | 0 won, 1 lost |
| Points | 3 | 943 | 647 won, 296 lost | 636 won, 294 lost | 11 won, 2 lost | 0 won, 0 lost | 0 won, 0 lost | 5 won, 1 lost | 6 won, 1 lost |
| Points | 4 | 935 | 702 won, 232 lost | 674 won, 225 lost | 26 won, 5 lost | 2 won, 2 lost | 0 won, 0 lost | 16 won, 5 lost | 12 won, 2 lost |
| PRA | 1 | 943 | 545 won, 398 lost | 543 won, 397 lost | 1 won, 1 lost | 1 won, 0 lost | 0 won, 0 lost | 1 won, 1 lost | 1 won, 0 lost |
| PRA | 2 | 943 | 588 won, 355 lost | 585 won, 353 lost | 2 won, 2 lost | 0 won, 0 lost | 1 won, 0 lost | 2 won, 2 lost | 1 won, 0 lost |
| PRA | 3 | 943 | 636 won, 307 lost | 629 won, 305 lost | 5 won, 1 lost | 1 won, 1 lost | 1 won, 0 lost | 6 won, 2 lost | 1 won, 0 lost |
| PRA | 4 | 942 | 686 won, 255 lost | 667 won, 248 lost | 16 won, 6 lost | 2 won, 1 lost | 1 won, 0 lost | 11 won, 6 lost | 8 won, 1 lost |
| Reb+Ast | 1 | 1032 | 626 won, 405 lost | 626 won, 404 lost | 0 won, 1 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost |
| Reb+Ast | 1.5 | 1032 | 627 won, 281 lost | 626 won, 280 lost | 1 won, 0 lost | 0 won, 1 lost | 0 won, 0 lost | 1 won, 0 lost | 0 won, 1 lost |
| Reb+Ast | 2 | 1032 | 751 won, 280 lost | 744 won, 279 lost | 7 won, 0 lost | 0 won, 1 lost | 0 won, 0 lost | 6 won, 0 lost | 1 won, 1 lost |
| Reb+Ast | 3 | 1024 | 833 won, 191 lost | 789 won, 187 lost | 39 won, 4 lost | 5 won, 0 lost | 0 won, 0 lost | 25 won, 2 lost | 19 won, 2 lost |
| Rebounds | 0.5 | 852 | 407 won, 315 lost | 407 won, 315 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost |
| Rebounds | 1 | 852 | 537 won, 313 lost | 536 won, 313 lost | 1 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 1 won, 0 lost |
| Rebounds | 1.5 | 836 | 526 won, 180 lost | 522 won, 179 lost | 4 won, 1 lost | 0 won, 0 lost | 0 won, 0 lost | 2 won, 1 lost | 2 won, 0 lost |
| Rebounds | 2 | 836 | 656 won, 179 lost | 638 won, 177 lost | 17 won, 2 lost | 1 won, 0 lost | 0 won, 0 lost | 12 won, 2 lost | 6 won, 0 lost |
| FG made | 0.5 | 2090 | 1062 won, 687 lost | 1061 won, 687 lost | 1 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 1 won, 0 lost |
| FG made | 1 | 2090 | 1403 won, 686 lost | 1393 won, 684 lost | 9 won, 2 lost | 1 won, 0 lost | 0 won, 0 lost | 3 won, 1 lost | 7 won, 1 lost |
| FG made | 1.5 | 2031 | 1358 won, 377 lost | 1328 won, 370 lost | 26 won, 7 lost | 4 won, 0 lost | 0 won, 0 lost | 6 won, 1 lost | 24 won, 6 lost |
| FG made | 2 | 2031 | 1654 won, 375 lost | 1529 won, 352 lost | 110 won, 21 lost | 13 won, 2 lost | 2 won, 0 lost | 15 won, 2 lost | 110 won, 21 lost |

### Same, every Step 3 row whatever side it picked at the original line (real Goblins are MORE-only and do not need our MORE first)

| Stat | Lower by | Picks | All picks | Under 70 | 70-74 | 75-79 | 80+ | 70+ build half | 70+ check half |
|---|---|---|---|---|---|---|---|---|---|
| Points | 1 | 1819 | 992 won, 827 lost | 992 won, 826 lost | 0 won, 1 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost |
| Points | 2 | 1819 | 1103 won, 715 lost | 1103 won, 713 lost | 0 won, 2 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost | 0 won, 1 lost |
| Points | 3 | 1819 | 1232 won, 587 lost | 1221 won, 585 lost | 11 won, 2 lost | 0 won, 0 lost | 0 won, 0 lost | 5 won, 1 lost | 6 won, 1 lost |
| Points | 4 | 1803 | 1327 won, 474 lost | 1299 won, 467 lost | 26 won, 5 lost | 2 won, 2 lost | 0 won, 0 lost | 16 won, 5 lost | 12 won, 2 lost |
| PRA | 1 | 1842 | 1009 won, 833 lost | 1007 won, 832 lost | 1 won, 1 lost | 1 won, 0 lost | 0 won, 0 lost | 1 won, 1 lost | 1 won, 0 lost |
| PRA | 2 | 1842 | 1085 won, 757 lost | 1082 won, 755 lost | 2 won, 2 lost | 0 won, 0 lost | 1 won, 0 lost | 2 won, 2 lost | 1 won, 0 lost |
| PRA | 3 | 1842 | 1174 won, 668 lost | 1167 won, 666 lost | 5 won, 1 lost | 1 won, 1 lost | 1 won, 0 lost | 6 won, 2 lost | 1 won, 0 lost |
| PRA | 4 | 1841 | 1267 won, 573 lost | 1248 won, 566 lost | 16 won, 6 lost | 2 won, 1 lost | 1 won, 0 lost | 11 won, 6 lost | 8 won, 1 lost |
| Reb+Ast | 1 | 1820 | 1072 won, 746 lost | 1072 won, 745 lost | 0 won, 1 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 1 lost |
| Reb+Ast | 1.5 | 1820 | 1074 won, 539 lost | 1073 won, 538 lost | 1 won, 0 lost | 0 won, 1 lost | 0 won, 0 lost | 1 won, 0 lost | 0 won, 1 lost |
| Reb+Ast | 2 | 1820 | 1281 won, 538 lost | 1274 won, 537 lost | 7 won, 0 lost | 0 won, 1 lost | 0 won, 0 lost | 6 won, 0 lost | 1 won, 1 lost |
| Reb+Ast | 3 | 1811 | 1433 won, 378 lost | 1388 won, 374 lost | 40 won, 4 lost | 5 won, 0 lost | 0 won, 0 lost | 26 won, 2 lost | 19 won, 2 lost |
| Rebounds | 0.5 | 1648 | 783 won, 616 lost | 783 won, 616 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost |
| Rebounds | 1 | 1648 | 1032 won, 612 lost | 1031 won, 612 lost | 1 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 1 won, 0 lost |
| Rebounds | 1.5 | 1620 | 1012 won, 368 lost | 1008 won, 367 lost | 4 won, 1 lost | 0 won, 0 lost | 0 won, 0 lost | 2 won, 1 lost | 2 won, 0 lost |
| Rebounds | 2 | 1620 | 1252 won, 366 lost | 1234 won, 364 lost | 17 won, 2 lost | 1 won, 0 lost | 0 won, 0 lost | 12 won, 2 lost | 6 won, 0 lost |
| FG made | 0.5 | 3024 | 1553 won, 993 lost | 1552 won, 993 lost | 1 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 0 won, 0 lost | 1 won, 0 lost |
| FG made | 1 | 3024 | 2031 won, 990 lost | 2021 won, 988 lost | 9 won, 2 lost | 1 won, 0 lost | 0 won, 0 lost | 3 won, 1 lost | 7 won, 1 lost |
| FG made | 1.5 | 2938 | 1968 won, 563 lost | 1938 won, 556 lost | 26 won, 7 lost | 4 won, 0 lost | 0 won, 0 lost | 6 won, 1 lost | 24 won, 6 lost |
| FG made | 2 | 2938 | 2375 won, 560 lost | 2250 won, 537 lost | 110 won, 21 lost | 13 won, 2 lost | 2 won, 0 lost | 15 won, 2 lost | 110 won, 21 lost |

### Pooled, all five stats, by rung (1st to 4th offset)

| Rows | Rung | All picks | 70-74 | 75-79 | 80+ |
|---|---|---|---|---|---|
| MORE picks | 1 | 3178 won, 2210 lost | 2 won, 3 lost | 1 won, 0 lost | 0 won, 0 lost |
| MORE picks | 2 | 3739 won, 1993 lost | 13 won, 6 lost | 1 won, 1 lost | 1 won, 0 lost |
| MORE picks | 3 | 3918 won, 1440 lost | 53 won, 11 lost | 5 won, 2 lost | 1 won, 0 lost |
| MORE picks | 4 | 4531 won, 1232 lost | 208 won, 38 lost | 23 won, 5 lost | 3 won, 0 lost |
| Every row | 1 | 5409 won, 4015 lost | 2 won, 3 lost | 1 won, 0 lost | 0 won, 0 lost |
| Every row | 2 | 6325 won, 3613 lost | 13 won, 6 lost | 1 won, 1 lost | 1 won, 0 lost |
| Every row | 3 | 6667 won, 2724 lost | 53 won, 11 lost | 5 won, 2 lost | 1 won, 0 lost |
| Every row | 4 | 7654 won, 2351 lost | 209 won, 38 lost | 23 won, 5 lost | 3 won, 0 lost |


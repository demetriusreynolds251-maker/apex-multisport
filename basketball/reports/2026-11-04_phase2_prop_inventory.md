# Apex Basketball — Phase 2: NBA prop inventory (Nov 4, 2026)

Two views: what PrizePicks posts tonight (live feed, 10 PM CT, 2 games left) and what we can already test on history (clean props = PrizePicks line before tip + book line before tip + result).

| Market (PrizePicks name) | Tonight (2 games) | Clean history props | Book coverage | Modeling difficulty | Profit potential (judgment, to be proven in Phase 3) |
|---|---|---|---|---|---|
| Points | 222 | 2,142 | every book | medium: minutes x usage x efficiency | high volume; books sharp on stars, softer on bench |
| Pts+Rebs | 202 | 1,810 | most books | medium | combos smooth variance; PrizePicks line often rounds |
| Pts+Rebs+Asts (PRA) | 165 | 2,097 | most books | medium | tennis-like "room" angle works best here in Step 4 lead |
| Rebounds | 165 | 1,922 | every book | medium-high: matchup and lineup driven | coin flip in Step 3; needs opponent rebound rate |
| Rebs+Asts | 133 | 2,088 | most | medium | |
| Pts+Asts | 119 | 1,157 | most | medium | |
| Assists | 116 | 1,443 | every book | high: depends on teammates making shots | |
| 3-PT Made | 116 | 477 | every book | high variance (Poisson-like) | Goblin unders/overs at 0.5-1.5 are the interesting lines |
| Steals | 108 | 533 | fewer books | very high variance | avoid unless Goblin at 0.5 |
| Blks+Stls | 76 | 416 | fewer | very high | avoid |
| Blocked Shots | 71 | 219 | fewer | very high | avoid |
| Fantasy Score | 33 | 3,491 lines, 0 graded (no result column yet) | PrizePicks only | medium (sum of box score) | needs grading code first |
| Two Pointers Made / Attempted | 29 / 16 | none | few | medium | thin |
| Turnovers | 29 | 54 | few | high | thin |
| Free Throws Made / Attempted | 26 / 13 | 1,451 / 1,587 | some | high (foul driven) | thin |
| Double-Double / Triple-Double | 22 / 3 | none | none | yes/no market | small; a Goblin-style line at 0.5 |
| FG Made / FG Attempted | 13 / 15 | 3,441 / 0 | few | medium | biggest clean history sample but coin flip in Step 3 |
| 3-PT Attempted, Fouls, Off/Def Rebounds, Dunks, Combo lines | 2-15 each | none | none | | ignore for now |
| First half / first quarter / team props | not in the single-stat feed tonight | none | | | check the feed in the morning when the full slate is up |

Label split tonight: 908 Demon, 558 Goblin, 296 Standard. PrizePicks only sells LESS on the Standard line (same as tennis); Goblins are MORE at a lowered line, Demons MORE at a raised line.

## What this means
- Volume: with a full slate (10-14 games) expect roughly 8,000 to 12,000 NBA lines a day, about a third Goblin. That is 20x tennis.
- Quality: Points, PRA, Pts+Rebs, Rebs+Asts have the deepest clean history (1,800-2,100 each) and book coverage; they are where Phase 3 starts.
- Difficulty: rebounds, assists, 3-PT, steals, blocks are matchup and variance driven; they go to Phase 3 only with a specific signal (opponent rate, lineup).
- Fantasy Score needs a grading formula (PrizePicks NBA: pts 1, reb 1.2, ast 1.5, stl 3, blk 3, tov -1) added to the history builder before it can be tested.

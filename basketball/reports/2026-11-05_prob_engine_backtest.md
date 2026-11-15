# NBA probability engine backtest - 2026-11-05 1:43 PM CT

Every graded PrizePicks NBA line in the history download with a result and 8+ earlier games for the player: **248622 props**, 2025-01-31 to 2026-10-30.
Skipped: did not play (void) 15302, under 8 games 2805.
First half = before 2025-12-31 (124249 props), second half = 2025-12-31 onward (124373 props). The spread scale per stat and the book weight are FIT ON THE FIRST HALF ONLY and then checked on the second half.
Book lines in history: saved pre-start book lines when there were any, else the opening line, else none (books 174546, none 49959, open 24117).

## Fit (first half only)

Spread scale per stat: Points 2.5, Rebounds 2.5, Assists 2.5, PRA 2.5, Pts+Rebs 2.5, Pts+Asts 2.5, Rebs+Asts 2.5, 3PTM 2.4, Steals 2.5, Blocked Shots 1.3, Turnovers 2.5, Blks+Stls 2.5, Fantasy Score 2.5. Book weight 0.9 (0 = ignore books, 1 = books only).

## First half (fit half)

### All lines, stated confidence vs what happened

| stated confidence | props | actual hit rate |
|---|---|---|
| 50-54% | 86017 | 51% |
| 55-59% | 29674 | 54% |
| 60-64% | 6413 | 57% |
| 65-69% | 1591 | 64% |
| 70-74% | 445 | 73% |
| 75-79% | 63 | 62% |
| 80-99% | 46 | 48% |

### By tier

| tier | props | won-lost | hit rate |
|---|---|---|---|
| A | 554 | 383-169 | 69% |
| B | 1591 | 1011-575 | 64% |
| C | 6413 | 3658-2726 | 57% |
| D | 115691 | 59383-55276 | 52% |

### Tier A and B by stat

| stat | A+B props | won-lost | hit rate |
|---|---|---|---|
| Points | 151 | 76-74 | 51% |
| Rebounds | 91 | 49-40 | 55% |
| Assists | 87 | 61-26 | 70% |
| PRA | 173 | 95-76 | 56% |
| Pts+Rebs | 150 | 77-72 | 52% |
| Pts+Asts | 117 | 71-46 | 61% |
| Rebs+Asts | 82 | 50-32 | 61% |
| 3PTM | 109 | 75-34 | 69% |
| Steals | 94 | 66-28 | 70% |
| Blocked Shots | 823 | 624-199 | 76% |
| Turnovers | 45 | 32-13 | 71% |
| Blks+Stls | 46 | 31-15 | 67% |
| Fantasy Score | 177 | 87-89 | 49% |

### Baselines on the 77129 lines that had a book line

- Books only (take the side the book line points to): 10895-9337 (54%)
- Projection only, no books, any confidence: 40712-35786 (53%)
- Engine tier A+B (projection + books): 997-394 (72%)

### Ladder check (Goblin / Demon style lines around the PrizePicks line)

Same props, lines moved by -6 to +6. Stated over % vs how often the over hit.

| stated over % | lines | over hit |
|---|---|---|
| 0-9% | 50523 | 1% |
| 10-19% | 43167 | 4% |
| 20-29% | 69945 | 11% |
| 30-39% | 159450 | 22% |
| 40-49% | 277255 | 36% |
| 50-59% | 277097 | 58% |
| 60-69% | 175526 | 75% |
| 70-79% | 48058 | 89% |
| 80-89% | 5036 | 95% |
| 90-99% | 91 | 95% |

### Top 3 board test (lines saved before the start only, board stats, tier A then B, best 3 by confidence)

- Days with PrizePicks lines before the start: 185. Boards built: 9. No board: 51.
- Whole board won-lost: **4-5** (44%). Legs 19-8 (70%).

## Second half (unseen)

### All lines, stated confidence vs what happened

| stated confidence | props | actual hit rate |
|---|---|---|
| 50-54% | 56250 | 49% |
| 55-59% | 31857 | 49% |
| 60-64% | 17696 | 49% |
| 65-69% | 9718 | 49% |
| 70-74% | 4986 | 49% |
| 75-79% | 2159 | 51% |
| 80-99% | 1707 | 52% |

### By tier

| tier | props | won-lost | hit rate |
|---|---|---|---|
| A | 8852 | 4452-4398 | 50% |
| B | 9718 | 4721-4996 | 49% |
| C | 17696 | 8605-9086 | 49% |
| D | 88107 | 43206-44732 | 49% |

### Tier A and B by stat

| stat | A+B props | won-lost | hit rate |
|---|---|---|---|
| Points | 2936 | 1418-1517 | 48% |
| Rebounds | 2153 | 1056-1096 | 49% |
| Assists | 1380 | 706-674 | 51% |
| PRA | 2452 | 1154-1297 | 47% |
| Pts+Rebs | 2541 | 1250-1291 | 49% |
| Pts+Asts | 2220 | 1071-1149 | 48% |
| Rebs+Asts | 1999 | 990-1009 | 50% |
| 3PTM | 1637 | 814-823 | 50% |
| Steals | 382 | 221-161 | 58% |
| Blocked Shots | 705 | 401-304 | 57% |
| Turnovers | 19 | 14-5 | 74% |
| Blks+Stls | 79 | 49-30 | 62% |
| Fantasy Score | 67 | 29-38 | 43% |

### Baselines on the 121534 lines that had a book line

- Books only (take the side the book line points to): 38156-39223 (49%)
- Projection only, no books, any confidence: 60046-61317 (49%)
- Engine tier A+B (projection + books): 9119-9342 (49%)

### Ladder check (Goblin / Demon style lines around the PrizePicks line)

Same props, lines moved by -6 to +6. Stated over % vs how often the over hit.

| stated over % | lines | over hit |
|---|---|---|
| 0-9% | 69647 | 2% |
| 10-19% | 69129 | 8% |
| 20-29% | 100462 | 15% |
| 30-39% | 157079 | 25% |
| 40-49% | 218780 | 37% |
| 50-59% | 217659 | 55% |
| 60-69% | 162249 | 71% |
| 70-79% | 69132 | 83% |
| 80-89% | 11896 | 89% |
| 90-99% | 418 | 95% |

### Top 3 board test (lines saved before the start only, board stats, tier A then B, best 3 by confidence)

- Days with PrizePicks lines before the start: 148. Boards built: 1. No board: 17.
- Whole board won-lost: **0-1** (0%). Legs 2-1 (67%).

## Honest notes

- A result exactly on the line is a push and is not counted.
- "Who is out" in history is read from who did not play that night, which includes late scratches nobody knew about before tip. Live, it comes from the ESPN injury feed only.
- History book lines are the saved pre-start lines or the opening line. Live, the engine sees 6 books from The Odds API, which is better than most of history had.
- Game totals and spreads exist for history (1994 games) but are not collected live yet, so live cards use a neutral pace factor until that feed is added.
- The ESPN box scores that fill the last days have points, rebounds, assists and FG only, so 3PTM / steals / blocks / turnovers / fantasy use history up to the last full download.

Ran in 190 seconds.
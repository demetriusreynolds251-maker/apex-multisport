# NBA probability engine backtest (PrizePicks lines saved before the start) - 2026-11-05 1:56 PM CT

Every graded PrizePicks NBA line in the history download with a result and 8+ earlier games for the player: **20560 props**, 2025-01-31 to 2026-10-30.
Skipped: PrizePicks line saved after tip 242846, did not play (void) 3000, under 8 games 323.
First half = before 2025-05-15 (10262 props), second half = 2025-05-15 onward (10298 props). The spread scale per stat and the book weight are FIT ON THE FIRST HALF ONLY and then checked on the second half.
Book lines in history: saved pre-start book lines when there were any, else the opening line, else none (books 12505, none 7513, open 542).

## Fit (first half only)

Fitted on the PrizePicks line and the same line moved -3..+3, so the engine is honest at the line AND on the Goblin/Demon ladder.
Spread scale per stat: Points 1.2, Rebounds 1.0, Assists 1.0, PRA 1.0, Pts+Rebs 1.2, Pts+Asts 1.0, Rebs+Asts 1.0, 3PTM 1.0, Steals 1.0, Blocked Shots 1.0, Turnovers 1.0, Blks+Stls 1.0, Fantasy Score 1.0.
Pull toward the PrizePicks standard line per stat (0 = trust our projection only, 0.9 = almost the line itself): Points 0.9, Rebounds 0.7, Assists 0.9, PRA 0.8, Pts+Rebs 0.9, Pts+Asts 0.8, Rebs+Asts 0.9, 3PTM 0.0, Steals 0.0, Blocked Shots 0.0, Turnovers 0.0, Blks+Stls 0.0, Fantasy Score 0.9.
Book weight 0.5 (0 = ignore books, 1 = books only).

## First half (fit half)

### All lines, stated confidence vs what happened

| stated confidence | props | actual hit rate |
|---|---|---|
| 50-54% | 9842 | 52% |
| 55-59% | 394 | 58% |
| 60-64% | 19 | 47% |
| 65-69% | 7 | 43% |
| 70-74% | 0 | - |
| 75-79% | 0 | - |
| 80-99% | 0 | - |

### By tier

| tier | props | won-lost | hit rate |
|---|---|---|---|
| A | 0 | 0-0 | - |
| B | 7 | 3-4 | 43% |
| C | 19 | 9-10 | 47% |
| D | 10236 | 5341-4882 | 52% |

### Tier A and B by stat

| stat | A+B props | won-lost | hit rate |
|---|---|---|---|
| Rebounds | 3 | 1-2 | 33% |
| Assists | 1 | 1-0 | 100% |
| 3PTM | 3 | 1-2 | 33% |

### Baselines on the 3752 lines that had a book line

- Books only (take the side the book line points to): 579-435 (57%)
- Projection only, no books, any confidence: 1956-1793 (52%)
- Engine tier A+B (projection + books): 1-1 (50%)

### Ladder check (Goblin / Demon style lines around the PrizePicks line)

Same props, lines moved by -6 to +6. Stated over % vs how often the over hit.

| stated over % | lines | over hit |
|---|---|---|
| 0-9% | 4085 | 7% |
| 10-19% | 5477 | 17% |
| 20-29% | 10677 | 25% |
| 30-39% | 17153 | 33% |
| 40-49% | 13899 | 42% |
| 50-59% | 12739 | 56% |
| 60-69% | 17392 | 65% |
| 70-79% | 11181 | 76% |
| 80-89% | 5698 | 85% |
| 90-99% | 3141 | 95% |

### Ladder lines by tier (the engine side, over or under)

| tier | line kind | won-lost | hit rate |
|---|---|---|---|
| A | Demon-style (line above ours) | 16392-3847 | 81% |
| A | Goblin-style (line below ours) | 16288-3732 | 81% |
| B | Demon-style (line above ours) | 5398-2389 | 69% |
| B | Goblin-style (line below ours) | 5392-2517 | 68% |
| C | Demon-style (line above ours) | 6129-3237 | 65% |
| C | Goblin-style (line below ours) | 5974-3509 | 63% |
| D | Demon-style (line above ours) | 8020-5867 | 58% |
| D | Goblin-style (line below ours) | 7177-5574 | 56% |

### Top 3 board test (lines saved before the start only, board stats, tier A then B, best 3 by confidence)

- Days with PrizePicks lines before the start: 96. Boards built: 0. No board: 3.
- Whole board won-lost: **0-0** (-). Legs 0-0 (-).

## Second half (unseen)

### All lines, stated confidence vs what happened

| stated confidence | props | actual hit rate |
|---|---|---|
| 50-54% | 8370 | 53% |
| 55-59% | 1195 | 55% |
| 60-64% | 358 | 54% |
| 65-69% | 205 | 58% |
| 70-74% | 98 | 54% |
| 75-79% | 42 | 67% |
| 80-99% | 30 | 67% |

### By tier

| tier | props | won-lost | hit rate |
|---|---|---|---|
| A | 170 | 101-69 | 59% |
| B | 205 | 118-87 | 58% |
| C | 358 | 193-165 | 54% |
| D | 9565 | 5102-4456 | 53% |

### Tier A and B by stat

| stat | A+B props | won-lost | hit rate |
|---|---|---|---|
| Points | 2 | 1-1 | 50% |
| Rebounds | 16 | 13-3 | 81% |
| PRA | 2 | 1-1 | 50% |
| Pts+Asts | 2 | 2-0 | 100% |
| Rebs+Asts | 1 | 0-1 | 0% |
| 3PTM | 89 | 52-37 | 58% |
| Steals | 78 | 44-34 | 56% |
| Blocked Shots | 49 | 23-26 | 47% |
| Turnovers | 59 | 37-22 | 63% |
| Blks+Stls | 77 | 46-31 | 60% |

### Baselines on the 9295 lines that had a book line

- Books only (take the side the book line points to): 1491-1256 (54%)
- Projection only, no books, any confidence: 4995-4295 (54%)
- Engine tier A+B (projection + books): 193-140 (58%)

### Ladder check (Goblin / Demon style lines around the PrizePicks line)

Same props, lines moved by -6 to +6. Stated over % vs how often the over hit.

| stated over % | lines | over hit |
|---|---|---|
| 0-9% | 14398 | 4% |
| 10-19% | 6939 | 14% |
| 20-29% | 9242 | 23% |
| 30-39% | 11981 | 31% |
| 40-49% | 8720 | 42% |
| 50-59% | 6885 | 56% |
| 60-69% | 12230 | 65% |
| 70-79% | 9941 | 74% |
| 80-89% | 6792 | 85% |
| 90-99% | 4270 | 95% |

### Ladder lines by tier (the engine side, over or under)

| tier | line kind | won-lost | hit rate |
|---|---|---|---|
| A | Demon-style (line above ours) | 26924-3661 | 88% |
| A | Goblin-style (line below ours) | 17168-3829 | 82% |
| B | Demon-style (line above ours) | 4040-1633 | 71% |
| B | Goblin-style (line below ours) | 4044-1904 | 68% |
| C | Demon-style (line above ours) | 4176-2137 | 66% |
| C | Goblin-style (line below ours) | 3883-2394 | 62% |
| D | Demon-style (line above ours) | 5167-3725 | 58% |
| D | Goblin-style (line below ours) | 3749-2964 | 56% |

### Top 3 board test (lines saved before the start only, board stats, tier A then B, best 3 by confidence)

- Days with PrizePicks lines before the start: 237. Boards built: 1. No board: 17.
- Whole board won-lost: **1-0** (100%). Legs 3-0 (100%).

## Honest notes

- A result exactly on the line is a push and is not counted.
- "Who is out" in history is read from who did not play that night, which includes late scratches nobody knew about before tip. Live, it comes from the ESPN injury feed only.
- History book lines are the saved pre-start lines or the opening line. Live, the engine sees 6 books from The Odds API, which is better than most of history had.
- Game totals and spreads exist for history (1994 games) but are not collected live yet, so live cards use a neutral pace factor until that feed is added.
- The ESPN box scores that fill the last days have points, rebounds, assists and FG only, so 3PTM / steals / blocks / turnovers / fantasy use history up to the last full download.

Ran in 101 seconds.
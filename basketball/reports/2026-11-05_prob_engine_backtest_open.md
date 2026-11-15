# NBA probability engine backtest (opening book line as the line) - 2026-11-05 1:59 PM CT

Every graded PrizePicks NBA line in the history download with a result and 8+ earlier games for the player: **107583 props**, 2026-01-16 to 2026-10-30.
Skipped: no opening book line 152271, did not play (void) 6407, under 8 games 468.
First half = before 2026-03-14 (53575 props), second half = 2026-03-14 onward (54008 props). The spread scale per stat and the book weight are FIT ON THE FIRST HALF ONLY and then checked on the second half.
Book lines in history: saved pre-start book lines when there were any, else the opening line, else none (books 83466, open 24117).

## Fit (first half only)

Fitted on the PrizePicks line and the same line moved -3..+3, so the engine is honest at the line AND on the Goblin/Demon ladder.
Spread scale per stat: Points 1.0, Rebounds 1.0, Assists 1.0, PRA 1.2, Pts+Rebs 1.2, Pts+Asts 1.2, Rebs+Asts 1.0, 3PTM 1.2, Steals 1.2, Blocked Shots 1.2, Turnovers 1.0, Blks+Stls 1.2, Fantasy Score 1.2.
Pull toward the PrizePicks standard line per stat (0 = trust our projection only, 0.9 = almost the line itself): Points 0.6, Rebounds 0.7, Assists 0.4, PRA 0.8, Pts+Rebs 0.7, Pts+Asts 0.8, Rebs+Asts 0.8, 3PTM 0.5, Steals 0.7, Blocked Shots 0.7, Turnovers 0.7, Blks+Stls 0.8, Fantasy Score 0.9.
Book weight 1.0 (0 = ignore books, 1 = books only).

## First half (fit half)

### All lines, stated confidence vs what happened

| stated confidence | props | actual hit rate |
|---|---|---|
| 50-54% | 38470 | 52% |
| 55-59% | 10970 | 58% |
| 60-64% | 2810 | 62% |
| 65-69% | 807 | 68% |
| 70-74% | 264 | 69% |
| 75-79% | 111 | 67% |
| 80-99% | 143 | 82% |

### By tier

| tier | props | won-lost | hit rate |
|---|---|---|---|
| A | 518 | 372-146 | 72% |
| B | 807 | 551-256 | 68% |
| C | 2810 | 1748-1062 | 62% |
| D | 49440 | 26414-23012 | 53% |

### Tier A and B by stat

| stat | A+B props | won-lost | hit rate |
|---|---|---|---|
| Points | 246 | 169-77 | 69% |
| Rebounds | 108 | 79-29 | 73% |
| Assists | 515 | 371-144 | 72% |
| PRA | 132 | 89-43 | 67% |
| Pts+Rebs | 59 | 36-23 | 61% |
| Pts+Asts | 37 | 26-11 | 70% |
| Rebs+Asts | 77 | 49-28 | 64% |
| 3PTM | 73 | 56-17 | 77% |
| Steals | 60 | 37-23 | 62% |
| Blocked Shots | 18 | 11-7 | 61% |

### Baselines on the 53575 lines that had a book line

- Books only (take the side the book line points to): 11036-7390 (60%)
- Projection only, no books, any confidence: 28434-25127 (53%)
- Engine tier A+B (projection + books): 923-402 (70%)

### Ladder check (Goblin / Demon style lines around the PrizePicks line)

Same props, lines moved by -6 to +6. Stated over % vs how often the over hit.

| stated over % | lines | over hit |
|---|---|---|
| 0-9% | 73685 | 4% |
| 10-19% | 32828 | 15% |
| 20-29% | 44579 | 23% |
| 30-39% | 60973 | 31% |
| 40-49% | 51989 | 41% |
| 50-59% | 43114 | 54% |
| 60-69% | 63095 | 64% |
| 70-79% | 50056 | 75% |
| 80-89% | 31585 | 84% |
| 90-99% | 17697 | 94% |

### Ladder lines by tier (the engine side, over or under)

| tier | line kind | won-lost | hit rate |
|---|---|---|---|
| A | Demon-style (line above ours) | 133385-17733 | 88% |
| A | Goblin-style (line below ours) | 80739-18573 | 81% |
| B | Demon-style (line above ours) | 20494-8239 | 71% |
| B | Goblin-style (line below ours) | 20693-10179 | 67% |
| C | Demon-style (line above ours) | 21453-10970 | 66% |
| C | Goblin-style (line below ours) | 19589-12451 | 61% |
| D | Demon-style (line above ours) | 32291-23241 | 58% |
| D | Goblin-style (line below ours) | 21594-17977 | 55% |

### Top 3 board test (lines saved before the start only, board stats, tier A then B, best 3 by confidence)

- Days with PrizePicks lines before the start: 51. Boards built: 51. No board: 0.
- Whole board won-lost: **24-27** (47%). Legs 118-35 (77%).

## Second half (unseen)

### All lines, stated confidence vs what happened

| stated confidence | props | actual hit rate |
|---|---|---|
| 50-54% | 37828 | 52% |
| 55-59% | 10516 | 58% |
| 60-64% | 3573 | 64% |
| 65-69% | 1120 | 68% |
| 70-74% | 512 | 71% |
| 75-79% | 232 | 76% |
| 80-99% | 227 | 85% |

### By tier

| tier | props | won-lost | hit rate |
|---|---|---|---|
| A | 971 | 732-239 | 75% |
| B | 1120 | 760-360 | 68% |
| C | 3573 | 2289-1284 | 64% |
| D | 48344 | 25791-22536 | 53% |

### Tier A and B by stat

| stat | A+B props | won-lost | hit rate |
|---|---|---|---|
| Points | 300 | 184-116 | 61% |
| Rebounds | 205 | 145-60 | 71% |
| Assists | 645 | 485-160 | 75% |
| PRA | 113 | 72-41 | 64% |
| Pts+Rebs | 85 | 54-31 | 64% |
| Pts+Asts | 67 | 42-25 | 63% |
| Rebs+Asts | 145 | 100-45 | 69% |
| 3PTM | 261 | 195-66 | 75% |
| Steals | 161 | 137-24 | 85% |
| Blocked Shots | 72 | 53-19 | 74% |
| Blks+Stls | 37 | 25-12 | 68% |

### Baselines on the 54008 lines that had a book line

- Books only (take the side the book line points to): 10730-7023 (60%)
- Projection only, no books, any confidence: 29014-24977 (54%)
- Engine tier A+B (projection + books): 1492-599 (71%)

### Ladder check (Goblin / Demon style lines around the PrizePicks line)

Same props, lines moved by -6 to +6. Stated over % vs how often the over hit.

| stated over % | lines | over hit |
|---|---|---|
| 0-9% | 80188 | 3% |
| 10-19% | 32413 | 15% |
| 20-29% | 43100 | 23% |
| 30-39% | 59072 | 31% |
| 40-49% | 52145 | 41% |
| 50-59% | 44268 | 54% |
| 60-69% | 62155 | 65% |
| 70-79% | 47792 | 75% |
| 80-89% | 29416 | 85% |
| 90-99% | 16849 | 94% |

### Ladder lines by tier (the engine side, over or under)

| tier | line kind | won-lost | hit rate |
|---|---|---|---|
| A | Demon-style (line above ours) | 138360-17215 | 89% |
| A | Goblin-style (line below ours) | 76827-17356 | 82% |
| B | Demon-style (line above ours) | 19579-7945 | 71% |
| B | Goblin-style (line below ours) | 20421-9830 | 68% |
| C | Demon-style (line above ours) | 20992-10582 | 66% |
| C | Goblin-style (line below ours) | 19744-12134 | 62% |
| D | Demon-style (line above ours) | 32273-23036 | 58% |
| D | Goblin-style (line below ours) | 22347-18757 | 54% |

### Top 3 board test (lines saved before the start only, board stats, tier A then B, best 3 by confidence)

- Days with PrizePicks lines before the start: 87. Boards built: 76. No board: 9.
- Whole board won-lost: **40-36** (53%). Legs 183-45 (80%).

## Honest notes

- A result exactly on the line is a push and is not counted.
- "Who is out" in history is read from who did not play that night, which includes late scratches nobody knew about before tip. Live, it comes from the ESPN injury feed only.
- History book lines are the saved pre-start lines or the opening line. Live, the engine sees 6 books from The Odds API, which is better than most of history had.
- Game totals and spreads exist for history (1994 games) but are not collected live yet, so live cards use a neutral pace factor until that feed is added.
- The ESPN box scores that fill the last days have points, rebounds, assists and FG only, so 3PTM / steals / blocks / turnovers / fantasy use history up to the last full download.

Ran in 602 seconds.
# Step 5 replay, 10/31/2026

## Plain answer: the plan's stop rule says stop.
On unseen games, Top 3 on Standard lines won 14 of 108 days, $[amount]; it needs about 1 day in 6 to break even at 6x. Elite 5 won 3 of 105 days, $[amount]. Tennis in its replay: Top 3 6 of 9, Elite 5 5 of 9 (a different pay table and only 9 days).
Lowered lines (estimate, not real Goblins): Top 3 won 44 of 99, $[amount] at 2.2x. Best lead: 5-pick without rebounds and FG made, 9 of 15, $[amount]; it lost on the build half (4 of 27, $[amount]) and is too small to trust.
Recommendation: do not start Step 6. Keep saving real lines, then re-run this on real Goblin labels.

## Method
Picks from Step 3. Build dates before 11/28/2025, check dates on and after. One pick per game. Rank = Win Prob + 5 x book room signal. Book = median of books last updated before the start; closing lines not used.
Settings chosen on the build half (20+ days) and then checked.
Pay, Standard: 3 Power 6x, 5 Flex 10x / 2x / 0.4x, 6 Flex 25x / 2x / 0.4x (from memory of PrizePicks' table; check). Lowered: 3 Power 2.2x, 5 Flex 2.5x / 1x / 0.4x (from his 10/31 slip, which mixed lines). 6-pick has no lowered pay, so no dollars.
Lowered lines: points and PRA -3, Reb+Ast -2, rebounds and FG made -1, MORE only. Win Prob estimated from Step 3's saved projection, not the full model.

## Chosen settings
| Version | Slip | Setting | Build | Check |
|---|---|---|---|---|
| Standard | 3-pick | floor 55 | 19 of 90, $[amount] | 14 of 108, $[amount] |
| Standard | 5-pick | no floor | 7 of 86, $[amount] | 3 of 105, $[amount] |
| Standard | 6-pick | book agrees only | 1 of 30, $[amount] | 1 of 17, $[amount] |
| Lowered | 3-pick | floor 60 | 26 of 67, $[amount] | 44 of 99, $[amount] |
| Lowered | 5-pick | floor 60, no reb/FG made | 4 of 27, $[amount] | 9 of 15, $[amount] |
| Lowered | 6-pick | floor 60 | 5 of 22 | 6 of 28 |

Every setting and months: reports/latest_step5_numbers.md. Code: code/step5_replay.py.

## Limits
Player history gaps from Step 4 still apply (2,520 of 6,505 team games have incomplete boxes). 'Book agrees' can't be timed against when a PP line was actually playable. The bot's 70 floor would rarely post any pick; the check half has 18 picks at 70+.
Waiting: his call. The bot and collector keep running as TEST.

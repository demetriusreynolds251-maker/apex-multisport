# Step 3: NBA Win Probability, 2026-10-31

**Summary:** the guess is honest, but it almost never gets confident. On the check half (11/28/2025 to 10/30/2026) only 18 picks in 179 days reached 70, about 1 every 10 days, and they went 9 won, 9 lost. No prop type passes as a source of 70+ picks. Picks at 60+ went 121 won, 95 lost on the check half and 146 won, 110 lost on the tuning half, a little over the 55 of 100 a 6x Standard needs, at about 1 pick a day. Under the plan's stop rules, that isn't enough on its own.

## How it works
Projected stat = recent per-minute rate (last 5, last 10, season) x recent minutes, adjusted for what the opponent allows, back-to-back and home or away. A spread around that gives the chance of MORE or LESS than the PrizePicks line. Only games on earlier dates are used. No book lines inside.
Tuning used dates before 11/28/2025. The confidence setting went to the top of the range tried on all five props, which says the numbers barely separate MORE from LESS at these lines.

## Check half, the one that counts (4,969 picks, 2,548 won, 2,421 lost)
| Band | Won | Lost |
|---|---|---|
| 50-54 | 1,875 | 1,822 |
| 55-59 | 554 | 508 |
| 60-64 | 96 | 75 |
| 65-69 | 14 | 7 |
| 70-74 | 8 | 4 |
| 75-79 | 0 | 2 |
| 80+ | 1 | 3 |

By prop, all picks: points 339-294, rebounds 315-319, rebounds + assists 348-309, PRA 325-274, field goals made 1,221-1,225.
By prop, 60-64: points 16-9, rebounds 6-6, rebounds + assists 12-10, PRA 20-9, field goals made 42-41.

## Tuning half (5,191 picks, 2,651 won, 2,540 lost)
50-54: 1,904-1,872. 55-59: 601-559. 60-64: 114-83. 65-69: 22-19. 70-74: 6-5. 75-79: 4-2.
70+ picks: 17, 10 won, 7 lost.

## Why it differs from tennis
Tennis picks reach 70+ largely because Goblin lines sit well below the fair line. These NBA lines have no Goblin or Demon label and behave like Standard lines: MORE and LESS split about even. So a coin-flip-range number is what you'd expect here. It does not tell us how NBA Goblins would do, because this data can't separate them.

## Limits
- Testable props only: PrizePicks line before the start, a book line before the start, a result. 1,383 were left out because the player didn't play, 139 for under 10 earlier games.
- No injury or teammate-out data; both are in the plan as facts for Step 4.
- Field goals made is nearly half the check set and shows no edge.
- 60+ results vary a lot by month, and some rows may share a game.

Numbers file: `latest_step3_numbers.md`. Picks: `data/processed/step3_predictions.sqlite`.

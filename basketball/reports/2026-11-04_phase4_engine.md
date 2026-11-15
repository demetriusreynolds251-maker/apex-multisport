# Apex Basketball - Phase 4: simulation engine, first build, walk-forward replay
Date: 2026-11-04. 15631 props. Older half before 2025-11-10 (rules learned here), newer half from 2025-11-10 (judged here).

## Engine
Anchored projection = 0.4 x box-score projection + 0.6 x book median line (ours alone when no book). Normal curve for points, rebounds, assists, FGM and combos (spread = last-10 spread, floor 1, +10% on back-to-back, +15% when spread is 10+). Poisson for threes, steals, blocks, blocks+steals. Raw chance = tail past the line. Gates: room agrees with the side by 0.5+, not threes.

## Raw chance by bucket (engine side)

| Raw chance | Older half | Newer half |
|---|---|---|
| 50-55% | 2019-1889 (52%) | 2240-2115 (51%) |
| 55-60% | 1211-1045 (54%) | 1220-1059 (54%) |
| 60-65% | 505-433 (54%) | 461-348 (57%) |
| 65-70% | 166-132 (56%) | 171-151 (53%) |
| 70-80% | 78-66 (54%) | 102-86 (54%) |
| 80-100% | 41-20 (67%) | 50-23 (68%) |

- older half Brier, raw engine chance: 0.2513
- newer half Brier, raw engine chance: 0.2514

## Honest chance (table learned on the older half) checked on the newer half
- Newer Brier raw: 0.2514 | honest: 0.2497 | flat 52%: 0.2492

| Bucket (room / raw / side) | Older W-L (honest) | Newer W-L (actual) |
|---|---|---|
| against|p<55|less | 49-43 (53%) | 50-39 (56%) |
| against|p<55|more | 49-68 (42%) | 41-64 (39%) |
| room1|p55-60|less | 114-60 (66%) | 112-82 (58%) |
| room1|p55-60|more | 114-92 (55%) | 137-92 (60%) |
| room1|p60-70|less | 95-82 (54%) | 100-78 (56%) |
| room1|p60-70|more | 121-94 (56%) | 151-121 (56%) |
| room1|p70+|less | 47-41 (53%) | 33-24 (58%) |
| room1|p<55|less | 112-78 (59%) | 67-74 (48%) |
| room1|p<55|more | 82-68 (55%) | 83-68 (55%) |
| same|p55-60|less | 504-437 (54%) | 421-355 (54%) |
| same|p55-60|more | 379-387 (49%) | 438-442 (50%) |
| same|p60-70|less | 272-219 (55%) | 169-128 (57%) |
| same|p60-70|more | 111-98 (53%) | 134-112 (54%) |
| same|p<55|less | 832-721 (54%) | 917-839 (52%) |
| same|p<55|more | 826-866 (49%) | 1011-961 (51%) |

Table saved to calibration/honest_table_v1.json.

## Gated picks (room agrees 0.5+, not threes), engine side

| Picks | Older half | Newer half |
|---|---|---|
| All gated | 921-693 (57%) | 1003-769 (57%) |
| Gated, honest 55%+ | 594-398 (60%) | 630-500 (56%) |
| Gated, honest 58%+ | 306-174 (64%) | 274-237 (54%) |
| Gated, LESS | 475-338 (58%) | 428-342 (56%) |
| Gated, MORE | 446-355 (56%) | 575-427 (57%) |
| Gated, room 1+ | 780-572 (58%) | 826-629 (57%) |
| Not gated (for contrast) | 3099-2892 (52%) | 3241-3013 (52%) |

## Boards on the NEWER half only (rules and table fixed on the older half): one slip per day

| Ranking | Top 3 days W-L | Top 5 days W-L (4 of 5) | Top 6 days W-L (5 of 6) | Days with no board (under 3 picks) | $[amount]/day result Top 3 at 6x |
|---|---|---|---|---|---|
| Honest chance order, gated | 28-102 (22%) | 4-89 (20) | 3-82 (11) | 69 | +380 over 130 days |
| Room size order, gated | 35-95 (27%) | 6-87 (25) | 3-82 (18) | 69 | +800 over 130 days |
| Honest order, gated, honest 55%+ only | 17-85 (17%) | 4-71 (15) | 3-61 (6) | 97 | +0 over 102 days |
| Raw engine chance order, ALL props (baseline) | 34-152 (18%) | 12-160 (35) | 10-154 (25) | 13 | +180 over 186 days |

Break-even for Top 3 Power at 6x is 1 win in 6 days (17%).

## Sample: last 5 days of the newer half, Top 3 by honest order (gated)
- 2026-10-26: Tim Hardaway Jr. MIAMI_HEAT_NBA rebounds 0.5 MORE (honest 72%, room 2.0) ✅; Ajay Mitchell OKLAHOMA_CITY_THUNDER_NBA assists 3.5 MORE (honest 55%, room 1.0) ✅; Luke Kennard PHOENIX_SUNS_NBA points 6.5 MORE (honest 53%, room 3.0) ✅
- 2026-10-27: no board (2 gated picks)
- 2026-10-28: Jaylon Tyson CLEVELAND_CAVALIERS_NBA assists 0.5 MORE (honest 72%, room 2.0) ✅; Naz Reid CHARLOTTE_HORNETS_NBA rebounds 7.5 MORE (honest 72%, room 2.0) ❌; De'Aaron Fox SAN_ANTONIO_SPURS_NBA rebounds+assists 10.5 LESS (honest 65%, room 1.0) ✅
- 2026-10-29: no board (2 gated picks)
- 2026-10-30: Jamal Shead TORONTO_RAPTORS_NBA rebounds 0.5 MORE (honest 72%, room 2.5) ✅; Tre Johnson WASHINGTON_WIZARDS_NBA rebounds 0.5 MORE (honest 72%, room 2.0) ✅; Jabari Smith Jr. HOUSTON_ROCKETS_NBA rebounds+assists 8.5 MORE (honest 62%, room 0.5) ❌

## Read-out of this first build
- Anchoring on the books fixed the raw chance: Brier 0.2513 / 0.2514 (was 0.266), and the 80%+ bucket is now 67% / 68% instead of 57% / 55%. The raw chance is still a little optimistic in the 60-80% buckets (53-57%).
- Gated picks (room agrees 0.5+, not threes) hold at 57% in both halves (921-693, 1003-769). Lines of 0.5/1.5 (14-3 newer, 3-0 older) look like PrizePicks promo lines (PP 0.5 vs book 2.5); they will be shown as a separate flag, not counted as room. Gated picks on lines 2.5+: 674-507 older, 677-524 newer.
- The honest table over-fits when it is sliced thin: "honest 58%+" was 64% on the older half and 54% on the newer half. Keep the table to 12-16 buckets and use it as the card number, not as a gate.
- Ranking decision (Phase 5 update): room size first, honest chance second. On the newer half that board won 35 of 130 days (27%) vs 28 of 130 for honest-first and 34 of 186 (18%) for the all-props baseline. 69 of 199 newer-half days had under 3 gated picks: post "no board today" on those.

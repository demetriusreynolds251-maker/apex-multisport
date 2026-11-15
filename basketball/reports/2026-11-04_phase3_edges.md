# Apex Basketball - Phase 3: edge discovery
Date: 2026-11-04. Every clean PrizePicks prop with a result (PP line taken before tip, at least one book line before tip).

## What the projection is
Built from scratch, no tennis code. For each prop, using only games BEFORE that game:
- Minutes = 60% of the last 5 games + 40% of the last 10.
- Per-minute rate = 40% last 5, 35% last 10, 25% last 40 games.
- Opponent factor = what the opponent allowed of that stat in its last 15 games vs league average (capped 0.8-1.2).
- Spread (how often the number lands) = spread of the last 10 games, floor 1.
- Side = MORE if the projection is above the PrizePicks line, else LESS. Chance = normal curve.
- Needs 5+ prior games with minutes.

Props projected: 15631 of 20837 clean props. Skipped: no_box 1991, no_stat_map:freeThrowsAttempted 1587, no_stat_map:freeThrowsMade 1451, push 10, short_history 167.
Older half: before 2025-11-10 (7605 props). Newer half: 2025-11-10 onward (8026 props).

## Baselines (what you get with no model at all)
### Bet every prop one way

| Value | Older half | Newer half | Both |
|---|---|---|---|
| MORE on every prop | 3630-3975 (48%) | 3964-4062 (49%) | 7594-8037 (49%) |
| LESS on every prop | 3975-3630 (52%) | 4062-3964 (51%) | 8037-7594 (51%) |

## The projection by itself
### Projection side, all props

| Value | Older half | Newer half | Both |
|---|---|---|---|
| Follow the projection | 3932-3673 (52%) | 4160-3866 (52%) | 8092-7539 (52%) |

### Projection side by how sure it is
Calibration check: a bucket is honest if the won-lost percent matches the bucket.

| Value | Older half | Newer half | Both |
|---|---|---|---|
| 50-55% | 1054-1038 (50%) | 1129-1137 (50%) | 2183-2175 (50%) |
| 55-60% | 939-873 (52%) | 1030-906 (53%) | 1969-1779 (53%) |
| 60-65% | 692-685 (50%) | 762-706 (52%) | 1454-1391 (51%) |
| 65-70% | 528-461 (53%) | 528-509 (51%) | 1056-970 (52%) |
| 70-80% | 508-456 (53%) | 506-441 (53%) | 1014-897 (53%) |
| 80%+ | 211-160 (57%) | 205-167 (55%) | 416-327 (56%) |

### Projection side by stat

| Value | Older half | Newer half | Both |
|---|---|---|---|
| assists | 388-369 (51%) | 277-239 (54%) | 665-608 (52%) |
| blocks | 68-63 (52%) | 34-32 (52%) | 102-95 (52%) |
| blocks+steals | 132-103 (56%) | 84-75 (53%) | 216-178 (55%) |
| fieldGoalsMade | 183-188 (49%) | 1368-1299 (51%) | 1551-1487 (51%) |
| points | 498-503 (50%) | 429-403 (52%) | 927-906 (51%) |
| points+assists | 329-298 (52%) | 180-176 (51%) | 509-474 (52%) |
| points+rebounds | 497-429 (54%) | 314-324 (49%) | 811-753 (52%) |
| points+rebounds+assists | 577-545 (51%) | 397-336 (54%) | 974-881 (53%) |
| rebounds | 409-392 (51%) | 440-429 (51%) | 849-821 (51%) |
| rebounds+assists | 476-442 (52%) | 489-429 (53%) | 965-871 (53%) |
| steals | 195-178 (52%) | 68-57 (54%) | 263-235 (53%) |
| threePointersMade | 170-151 (53%) | 66-53 (55%) | 236-204 (54%) |
| turnovers | 10-12 (45%) | 14-14 (50%) | 24-26 (48%) |

### Projection side: MORE picks vs LESS picks

| Value | Older half | Newer half | Both |
|---|---|---|---|
| MORE picks | 1979-2022 (49%) | 2240-2142 (51%) | 4219-4164 (50%) |
| LESS picks | 1953-1651 (54%) | 1920-1724 (53%) | 3873-3375 (53%) |

### Brier score (lower is better; 0.25 = coin flip)
- older half: 0.2660 on 7605 props
- newer half: 0.2655 on 8026 props

## Each fact alone (projection side, split by the fact)
### Back-to-back

| Value | Older half | Newer half | Both |
|---|---|---|---|
| Back-to-back game | 653-544 (55%) | 594-631 (48%) | 1247-1175 (51%) |
| Not back-to-back | 3276-3128 (51%) | 3565-3232 (52%) | 6841-6360 (52%) |

### Rest days

| Value | Older half | Newer half | Both |
|---|---|---|---|
| 1 day (b2b) | 2277-2185 (51%) | 2361-2091 (53%) | 4638-4276 (52%) |
| 2 days | 558-514 (52%) | 698-627 (53%) | 1256-1141 (52%) |
| 3+ days | 441-429 (51%) | 506-514 (50%) | 947-943 (50%) |

### Home / away

| Value | Older half | Newer half | Both |
|---|---|---|---|
| Home | 1745-1614 (52%) | 2156-1926 (53%) | 3901-3540 (52%) |
| Away | 2187-2059 (52%) | 2004-1940 (51%) | 4191-3999 (51%) |

### Point spread (team view, opening line)

| Value | Older half | Newer half | Both |
|---|---|---|---|
| Big favorite (-10 or more) | - | 209-176 (54%) | 209-176 (54%) |
| Favorite (-3 to -10) | - | 375-356 (51%) | 375-356 (51%) |
| Close game (within 3) | - | 262-264 (50%) | 262-264 (50%) |
| Underdog (+3 to +10) | - | 351-355 (50%) | 351-355 (50%) |
| Big underdog (+10 or more) | - | 149-139 (52%) | 149-139 (52%) |
| No spread on file | 3932-3673 (52%) | 2814-2576 (52%) | 6746-6249 (52%) |

### Blowout risk x side

| Value | Older half | Newer half | Both |
|---|---|---|---|
| Big favorite/dog (10+) and MORE | - | 183-167 (52%) | 183-167 (52%) |
| Big favorite/dog (10+) and LESS | - | 175-148 (54%) | 175-148 (54%) |
| Close game (under 5) and MORE | - | 300-301 (50%) | 300-301 (50%) |
| Close game (under 5) and LESS | - | 223-218 (51%) | 223-218 (51%) |

### Game total (opening)

| Value | Older half | Newer half | Both |
|---|---|---|---|
| Under 220 | - | 213-216 (50%) | 213-216 (50%) |
| 220-230 | - | 568-546 (51%) | 568-546 (51%) |
| 230+ | - | 565-528 (52%) | 565-528 (52%) |

### Minutes trend (last 5 vs last 10)

| Value | Older half | Newer half | Both |
|---|---|---|---|
| Minutes up 2+ | 841-704 (54%) | 734-660 (53%) | 1575-1364 (54%) |
| Flat | 2420-2334 (51%) | 2869-2693 (52%) | 5289-5027 (51%) |
| Minutes down 2+ | 671-635 (51%) | 557-513 (52%) | 1228-1148 (52%) |

### Form (last 5 vs last 40)

| Value | Older half | Newer half | Both |
|---|---|---|---|
| Hot (+15% or more) | 1213-1105 (52%) | 1333-1239 (52%) | 2546-2344 (52%) |
| Normal | 1738-1677 (51%) | 1909-1785 (52%) | 3647-3462 (51%) |
| Cold (-15% or worse) | 981-891 (52%) | 918-842 (52%) | 1899-1733 (52%) |

### Form x side

| Value | Older half | Newer half | Both |
|---|---|---|---|
| Hot and MORE | 805-826 (49%) | 948-933 (50%) | 1753-1759 (50%) |
| Hot and LESS | 408-279 (59%) | 385-306 (56%) | 793-585 (58%) |
| Cold and MORE | 280-246 (53%) | 282-255 (53%) | 562-501 (53%) |
| Cold and LESS | 701-645 (52%) | 636-587 (52%) | 1337-1232 (52%) |

### PrizePicks line vs book line (room), projection side
Room = PrizePicks line minus the middle book line. A lower PP line means MORE is easier; higher means LESS is easier.

| Value | Older half | Newer half | Both |
|---|---|---|---|
| PP lower than books by 1+, MORE | 282-225 (56%) | 342-263 (57%) | 624-488 (56%) |
| PP lower than books by 0.5, MORE | 61-58 (51%) | 71-53 (57%) | 132-111 (54%) |
| PP same as books, MORE | 1473-1534 (49%) | 1665-1619 (51%) | 3138-3153 (50%) |
| PP same as books, LESS | 1453-1232 (54%) | 1427-1255 (53%) | 2880-2487 (54%) |
| PP higher than books by 0.5, LESS | 57-42 (58%) | 69-51 (58%) | 126-93 (58%) |
| PP higher than books by 1+, LESS | 297-208 (59%) | 240-191 (56%) | 537-399 (57%) |
| Projection goes AGAINST the room | 309-374 (45%) | 346-434 (44%) | 655-808 (45%) |

### Room alone, no projection (take the side the room favors)

| Value | Older half | Newer half | Both |
|---|---|---|---|
| PP lower by 1+ -> MORE | 426-344 (55%) | 521-404 (56%) | 947-748 (56%) |
| PP lower by 0.5 -> MORE | 86-85 (50%) | 119-96 (55%) | 205-181 (53%) |
| PP higher by 0.5 -> LESS | 91-75 (55%) | 107-90 (54%) | 198-165 (55%) |
| PP higher by 1+ -> LESS | 468-338 (58%) | 409-314 (57%) | 877-652 (57%) |

### Pinnacle room alone (when Pinnacle had a line before tip)

| Value | Older half | Newer half | Both |
|---|---|---|---|
| PP lower than Pinnacle -> MORE | 12-16 (43%) | 16-14 (53%) | 28-30 (48%) |
| PP higher than Pinnacle -> LESS | 15-8 (65%) | 20-19 (51%) | 35-27 (56%) |

### Books agree with the projection?

| Value | Older half | Newer half | Both |
|---|---|---|---|
| Books lean same side | 697-533 (57%) | 722-558 (56%) | 1419-1091 (57%) |
| Books same line (no lean) | 2926-2766 (51%) | 3092-2874 (52%) | 6018-5640 (52%) |
| Books lean other side | 309-374 (45%) | 346-434 (44%) | 655-808 (45%) |

### Line move (book open to close) vs projection side
Note: the close line is known only after the fact; this is a CLV check, not a pre-tip rule.

| Value | Older half | Newer half | Both |
|---|---|---|---|
| Move toward our side | - | 154-137 (53%) | 154-137 (53%) |
| No move | - | 986-951 (51%) | 986-951 (51%) |
| Move against our side | - | 206-202 (50%) | 206-202 (50%) |

### Edge size (projection minus line, in spreads)

| Value | Older half | Newer half | Both |
|---|---|---|---|
| Under 0.25 | 1973-1890 (51%) | 2138-2022 (51%) | 4111-3912 (51%) |
| 0.25-0.5 | 1156-1105 (51%) | 1229-1158 (51%) | 2385-2263 (51%) |
| 0.5-1.0 | 692-594 (54%) | 665-582 (53%) | 1357-1176 (54%) |
| 1.0+ | 111-84 (57%) | 128-104 (55%) | 239-188 (56%) |

### How much history the player has

| Value | Older half | Newer half | Both |
|---|---|---|---|
| 5-9 games | 68-47 (59%) | 14-18 (44%) | 82-65 (56%) |
| 10-29 games | 195-186 (51%) | 171-181 (49%) | 366-367 (50%) |
| 30+ games | 3669-3440 (52%) | 3975-3667 (52%) | 7644-7107 (52%) |

## Best single rules (PASS = 55%+ in BOTH halves with 60+ picks in each)

| Rule | Older half | Newer half | Both | Verdict |
|---|---|---|---|---|
| Projection 60%+ sure | 1939-1762 (52%) | 2001-1823 (52%) | 3940-3585 (52%) | fail |
| Projection 65%+ sure | 1247-1077 (54%) | 1239-1117 (53%) | 2486-2194 (53%) | fail |
| Projection 70%+ sure | 719-616 (54%) | 711-608 (54%) | 1430-1224 (54%) | fail |
| Projection 60%+ and room agrees | 409-329 (55%) | 423-318 (57%) | 832-647 (56%) | PASS |
| Projection 60%+ and books lean same side | 409-329 (55%) | 423-318 (57%) | 832-647 (56%) | PASS |
| Projection 60%+ LESS only | 968-823 (54%) | 892-778 (53%) | 1860-1601 (54%) | fail |
| Projection 60%+ MORE only | 971-939 (51%) | 1109-1045 (51%) | 2080-1984 (51%) | fail |
| Projection 60%+ not back-to-back | 1614-1504 (52%) | 1699-1540 (52%) | 3313-3044 (52%) | fail |
| Projection 60%+ close game (spread under 7) | - | 358-359 (50%) | 358-359 (50%) | fail |
| Projection 60%+ 30+ games history | 1797-1639 (52%) | 1898-1723 (52%) | 3695-3362 (52%) | fail |
| Room 1+ in our favor, any projection | 579-433 (57%) | 582-454 (56%) | 1161-887 (57%) | PASS |
| Projection 60%+ and Pinnacle room agrees | 7-5 (58%) | 12-10 (55%) | 19-15 (56%) | fail |

55% is roughly break-even on a PrizePicks 3-pick standard slip; a board needs more than that.

## Not tested yet (data missing)
- freeThrowsMade / freeThrowsAttempted: no free-throw numbers in the box-score history (3038 clean props skipped).
- Injuries, lineups, usage rate, pace, defensive rating: no history on the machine; the injury + schedule saver started 2026-11-04 and is building it.
- Travel distance: venue data starts 2026-11-04.
- Goblin / Demon lines: history is standard lines only; Goblin/Demon saving started 2026-11-04.

Projections saved to data/processed/phase3_projections.sqlite (table projections) for Phase 4.

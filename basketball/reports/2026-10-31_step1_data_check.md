# Step 1: NBA data check, 2026-10-31

**Summary:** the download has PrizePicks lines, book lines and final player stats together on 20,837 props across 1,928 games. No ESPN needed. Below, by season and prop type.

Files: 3789. ALL THREE = PrizePicks line before start, 1+ book line last updated before the start, and a final result.

Season 2023-24: {'finished games': 646, 'player lines': 8242, 'lines with result': 7863, 'with PP': 0, 'PP before start': 0}
Season 2024-25: {'finished games': 1387, 'player lines': 257466, 'lines with result': 246345, 'with PP': 62812, 'PP before start': 13444, 'ALL THREE': 4451}
Season 2025-26: {'finished games': 1312, 'player lines': 394915, 'lines with result': 379694, 'with PP': 214528, 'PP before start': 22069, 'ALL THREE': 16171}
Season 2026-27: {'finished games': 81, 'player lines': 17188, 'lines with result': 16310, 'with PP': 15708, 'PP before start': 1083, 'ALL THREE': 215}

By prop type:
fieldGoalsMade: {'PP + result': 5790, 'lines': 26758, 'ALL THREE': 3441}
points: {'lines': 49883, 'PP + result': 3240, 'ALL THREE': 2142}
points+rebounds+assists: {'PP + result': 3087, 'lines': 43681, 'ALL THREE': 2097}
rebounds+assists: {'lines': 42965, 'PP + result': 2940, 'ALL THREE': 2088}
rebounds: {'lines': 43702, 'PP + result': 2628, 'ALL THREE': 1922}
points+rebounds: {'lines': 43473, 'PP + result': 2884, 'ALL THREE': 1810}
freeThrowsAttempted: {'lines': 13206, 'PP + result': 3847, 'ALL THREE': 1587}
freeThrowsMade: {'lines': 17477, 'PP + result': 3076, 'ALL THREE': 1451}
assists: {'lines': 45950, 'PP + result': 1788, 'ALL THREE': 1443}
points+assists: {'lines': 43082, 'PP + result': 1931, 'ALL THREE': 1157}
steals: {'lines': 42812, 'ALL THREE': 533, 'PP + result': 542}
threePointersMade: {'lines': 40227, 'ALL THREE': 477, 'PP + result': 496}
blocks+steals: {'lines': 42289, 'ALL THREE': 416, 'PP + result': 433}
blocks: {'lines': 42276, 'ALL THREE': 219, 'PP + result': 227}
turnovers: {'lines': 33900, 'ALL THREE': 54, 'PP + result': 196}
fantasyScore: {'lines': 27220}
threePointersAttempted: {'lines': 18187}
twoPointersAttempted: {'lines': 19681}
fieldGoalsAttempted: {'lines': 19993}
twoPointersMade: {'lines': 19728}
fouls: {'lines': 1321}

Books before start: [('bet365', 328057), ('unknown', 33949), ('bovada', 17760), ('prophetexchange', 15514), ('fliff', 15310), ('pinnacle', 15112), ('ballybet', 14026), ('betmgm', 10512), ('betonline', 9316), ('underdog', 8514), ('espnbet', 8358), ('hardrockbet', 6853), ('fanatics', 5433), ('betrivers', 5316), ('betparx', 4112), ('draftkings', 4009), ('sugarhouse', 3318), ('caesars', 2656), ('fanduel', 2452), ('sporttrade', 2291), ('fourwinds', 2267), ('polymarket', 2165), ('bookmakereu', 1393), ('novig', 1225), ('circa', 171)]

Close vs open, avg miss on game total (a low close means it knew the result):
2024-25: 603 games, close 9.0, open 9.0
2025-26: 1310 games, close 9.6, open 9.9
2026-27: 81 games, close 15.0, open 15.7

player_games rows 66916, prop_lines rows 677811, games 3789, dates 2024-01-31 to 2026-10-30

# Step 2: NBA player history, 2026-10-31

**Summary:** built one table of every player-game with props. 66,916 player-games, 677,811 prop lines, 20,837 testable.

Built `data/processed/nba_history.sqlite`, 187 MB, from the saved SportsGameOdds NBA files.
- games: 3,789 (3,426 finished), 2024-01-31 to 2026-10-30.
- player_games: 66,916 across 752 players.
- prop_lines: 677,811. With a PrizePicks line before the start, a book line before the start and a result: 20,837, across 1,928 games and 12,713 player-games.
Gaps: most PrizePicks lines were last updated after the start. Spread and total close on 1,994 of 3,426 finished games; open on 785. Threes, blocks and turnovers are thin. No Goblin or Demon labels. The 2026-27 close on 81 games misses the total by about 15 points against about 9 to 10 earlier; not yet looked into.

# NBA data dictionary
File: `data/processed/nba_history.sqlite`

## games: one row per game
event_id, season, game_date (Central), start_utc, home, away, home_pts, away_pts, close_spread_home, open_spread_home, close_total, open_total, final (1 = finished). Open and close are SportsGameOdds' blended consensus.

## player_games: one row per player per finished game
event_id, player_id, player, team, opponent, home (1/0), game_date, season, minutes, points, rebounds, assists, threes, steals, blocks, turnovers, rest_days (full days off before this game, blank on a player's first game here), back_to_back (rest_days is 0).

## prop_lines: one row per player, game and stat, full-game over/under
event_id, player_id, stat, game_date, season, pp_line (PrizePicks), pp_before_start (1 if last updated before the listed start), open_line, close_line, close_fair, close_fair_over_odds, books_before_start, books_later, pinnacle_before_start, book_lines_json ({book: [line, odds]}, only books last updated before the earliest listed start), result, more_won, less_won.

Alternate lines stay in the raw files.

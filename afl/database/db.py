#!/usr/bin/env python3
"""history.db for this sport only. Every fetch is appended (snapshots + line rows); nothing is overwritten.
Tables: snapshots, pp_lines (one row per line change = movement), book_lines, injuries, games, player_games, prop_lines (history),
picks (every pick with projection / probability / tier / edge / result), runs, boards, bans, fits."""
import os, sqlite3, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as CM

SCHEMA = """
create table if not exists snapshots(id integer primary key, fetched_at text, kind text, league text, n integer, file text);
create table if not exists pp_lines(projection_id text, league text, player text, player_norm text, team text, opponent text, home_abbr text, away_abbr text, game_id text,
  stat_raw text, stat text, line real, kind text, start text, status text, promo integer, first_seen text, last_seen text, seen_count integer default 1,
  primary key(projection_id, line, kind, status));
create index if not exists ix_pp_start on pp_lines(start);
create table if not exists book_lines(fetched_at text, book text, market text, stat text, player text, player_norm text, line real, over integer, under integer, event_id text, start text);
create index if not exists ix_book on book_lines(player_norm, stat, fetched_at);
create table if not exists injuries(fetched_at text, team text, player text, player_norm text, status text, detail text, primary key(fetched_at, team, player_norm));
create table if not exists games(event_id text primary key, game_date text, start_utc text, home text, away text, home_score real, away_score real, final integer default 0, box_saved integer default 0, source text, total real, spread_home real);
create index if not exists ix_games_date on games(game_date);
create table if not exists player_games(event_id text, player_norm text, player text, team text, opponent text, home integer, game_date text, stats_json text, source text, primary key(event_id, player_norm, source));
create index if not exists ix_pg_player on player_games(player_norm, game_date);
create table if not exists prop_lines(event_id text, game_date text, player text, player_norm text, team text, opponent text, home integer, stat text, pp_line real, pp_before_start integer,
  book_lines_json text, open_line real, result real, source text, primary key(event_id, player_norm, stat, pp_line));
create index if not exists ix_prop_date on prop_lines(game_date);
create table if not exists picks(pick_key text primary key, run_id integer, created text, league text, player text, player_norm text, team text, opponent text, game_date text, start text,
  stat text, stat_raw text, line real, kind text, side text, projection real, sd real, over_p real, under_p real, confidence real, tier text, edge_score real,
  reasons_json text, market_json text, injury_json text, on_board text, status text default 'open', result_value real, graded_at text, hit integer);
create index if not exists ix_picks_date on picks(game_date);
create table if not exists runs(id integer primary key, created text, lines_saved_at text, n_lines integer, n_scored integer, n_floor integer, trigger text);
create table if not exists boards(run_id integer, board text, role text, slot integer, pick_key text, confidence real);
create table if not exists bans(player_norm text primary key, player text, why text, added text);
create table if not exists fits(stat text primary key, sd_k real, anchor real, market_weight real, fitted text, mode text, props integer);
create table if not exists kv(k text primary key, v text);
"""

def connect(path=None):
    p = path or CM.DB_FILE; os.makedirs(os.path.dirname(p), exist_ok=True)
    db = sqlite3.connect(p, timeout=30); db.row_factory = sqlite3.Row; db.executescript(SCHEMA); return db

def kv_get(db, k, default=None):
    r = db.execute('select v from kv where k=?', (k,)).fetchone(); return r[0] if r else default
def kv_set(db, k, v):
    db.execute('insert into kv(k,v) values(?,?) on conflict(k) do update set v=excluded.v', (k, str(v))); db.commit()

if __name__ == '__main__':
    db = connect()
    for t in ('pp_lines', 'book_lines', 'injuries', 'games', 'player_games', 'prop_lines', 'picks', 'runs'):
        print(t, db.execute('select count(*) from %s' % t).fetchone()[0])

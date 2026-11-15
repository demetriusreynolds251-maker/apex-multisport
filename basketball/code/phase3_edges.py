#!/usr/bin/env python3
"""APEX BASKETBALL - Phase 3 edge discovery.
From-scratch projection on every clean historical PrizePicks prop, then each
fact tested alone, older half vs newer half, won-lost per value.
Stdlib only. Reads data/processed/nba_history.sqlite (+ nba_fgm.sqlite).
Writes reports/<date>_phase3_edges.md and data/processed/phase3_projections.sqlite
"""
import sqlite3, json, math, os, sys, statistics as st, datetime as dt
from collections import defaultdict

BASE = os.path.expanduser('~/ApexSports/basketball')
DB = os.path.join(BASE, 'data/processed/nba_history.sqlite')
FGM = os.path.join(BASE, 'data/processed/nba_fgm.sqlite')
TODAY = dt.date.today().isoformat()
OUT = os.path.join(BASE, 'reports', '%s_phase3_edges.md' % TODAY)
OUTDB = os.path.join(BASE, 'data/processed/phase3_projections.sqlite')

STATS = {
 'points': ['points'], 'rebounds': ['rebounds'], 'assists': ['assists'],
 'threePointersMade': ['threes'], 'steals': ['steals'], 'blocks': ['blocks'],
 'turnovers': ['turnovers'], 'fieldGoalsMade': ['fgm'],
 'points+rebounds': ['points','rebounds'], 'points+assists': ['points','assists'],
 'rebounds+assists': ['rebounds','assists'], 'points+rebounds+assists': ['points','rebounds','assists'],
 'blocks+steals': ['blocks','steals'],
}
BOX = ['points','rebounds','assists','threes','steals','blocks','turnovers','fgm']

def ncdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def mean(a):
    return sum(a) / len(a) if a else None

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
con.execute("attach database ? as f", (FGM,))

pg = defaultdict(list)
team_tot = defaultdict(lambda: defaultdict(float))
team_games = defaultdict(set)
rows = con.execute("""select p.*, f.fgm from player_games p left join f.fgm f
   on f.event_id=p.event_id and f.player_id=p.player_id where p.minutes is not null
   order by p.game_date""").fetchall()
for r in rows:
    d = dict(r)
    pg[d['player_id']].append(d)
    for s in BOX:
        v = d.get(s)
        if v is not None:
            team_tot[(d['event_id'], d['team'])][s] += v
    team_games[d['team']].add((d['game_date'], d['event_id'], d['opponent']))
for t in team_games:
    team_games[t] = sorted(team_games[t])
print('players', len(pg), 'player-games', len(rows), flush=True)

league_avg = {}
for s in BOX:
    vals = [tt[s] for tt in team_tot.values() if s in tt]
    league_avg[s] = mean(vals)

def opp_factor(opp, date, stat_cols):
    gl = team_games.get(opp, [])
    prior = [g for g in gl if g[0] < date][-15:]
    if len(prior) < 5:
        return 1.0
    f = []
    for s in stat_cols:
        allowed = [team_tot[(eid, o)].get(s) for (d, eid, o) in prior if (eid, o) in team_tot]
        allowed = [a for a in allowed if a is not None]
        if allowed and league_avg[s]:
            f.append(mean(allowed) / league_avg[s])
    if not f:
        return 1.0
    return max(0.8, min(1.2, mean(f)))

def project(player_id, date, stat_cols):
    hist = [g for g in pg.get(player_id, []) if g['game_date'] < date and g['minutes'] and g['minutes'] > 0]
    if len(hist) < 5:
        return None
    l5, l10, seas = hist[-5:], hist[-10:], hist[-40:]
    mins = 0.6 * mean([g['minutes'] for g in l5]) + 0.4 * mean([g['minutes'] for g in l10])
    def val(g):
        v = 0.0
        for s in stat_cols:
            if g.get(s) is None:
                return None
            v += g[s]
        return v
    def rate(gs):
        xs = [(val(g), g['minutes']) for g in gs]
        xs = [(v, m) for v, m in xs if v is not None]
        if not xs:
            return None
        return sum(v for v, m in xs) / sum(m for v, m in xs)
    r5, r10, rs = rate(l5), rate(l10), rate(seas)
    if r5 is None or r10 is None or rs is None:
        return None
    rate_w = 0.4 * r5 + 0.35 * r10 + 0.25 * rs
    vals10 = [val(g) for g in l10 if val(g) is not None]
    sd = st.pstdev(vals10) if len(vals10) >= 3 else None
    if sd is None or sd < 1.0:
        sd = 1.0
    seas_vals = [val(g) for g in seas if val(g) is not None]
    return dict(mins=mins, rate=rate_w, sd=sd,
                min_l5=mean([g['minutes'] for g in l5]), min_l10=mean([g['minutes'] for g in l10]),
                form_l5=mean([val(g) for g in l5 if val(g) is not None]), form_seas=mean(seas_vals),
                n=len(hist))

props = con.execute("""select p.*, g.open_spread_home, g.close_spread_home, g.open_total, g.home as home_team, g.away as away_team
  from prop_lines p join games g on g.event_id=p.event_id
  where p.pp_before_start=1 and p.result is not null and p.books_before_start>0""").fetchall()
print('clean props', len(props), flush=True)

pg_idx = {}
for pid, gl in pg.items():
    for g in gl:
        pg_idx[(g['event_id'], pid)] = g

out = []
skipped = defaultdict(int)
for p in props:
    p = dict(p)
    cols = STATS.get(p['stat'])
    if not cols:
        skipped['no_stat_map:' + p['stat']] += 1
        continue
    g = pg_idx.get((p['event_id'], p['player_id']))
    if not g:
        skipped['no_box'] += 1
        continue
    pr = project(p['player_id'], p['game_date'], cols)
    if not pr:
        skipped['short_history'] += 1
        continue
    fac = opp_factor(g['opponent'], p['game_date'], cols)
    proj = pr['mins'] * pr['rate'] * fac
    line = p['pp_line']
    z = (line - proj) / pr['sd']
    p_more = 1 - ncdf(z)
    side = 'more' if proj > line else 'less'
    conf = max(p_more, 1 - p_more)
    won = p['more_won'] if side == 'more' else p['less_won']
    if won is None:
        skipped['no_grade'] += 1
        continue
    if p['result'] == line:
        skipped['push'] += 1
        continue
    try:
        bl = json.loads(p['book_lines_json'] or '{}')
        book_lines = [v[0] for v in bl.values() if v and v[0] is not None]
    except Exception:
        book_lines = []
    book_med = st.median(book_lines) if book_lines else None
    room_book = (line - book_med) if book_med is not None else None
    room_pinn = (line - p['pinnacle_before_start']) if p['pinnacle_before_start'] is not None else None
    home = g['home']
    sp = p['open_spread_home']
    team_spread = None
    if sp is not None:
        team_spread = sp if home == 1 else -sp
    if book_med is None:
        book_side = None
    elif book_med > line:
        book_side = 'more'
    elif book_med < line:
        book_side = 'less'
    else:
        book_side = 'same'
    out.append(dict(
        event_id=p['event_id'], player_id=p['player_id'], player=g['player'], team=g['team'], opp=g['opponent'],
        stat=p['stat'], date=p['game_date'], season=p['season'], line=line, proj=round(proj, 2), sd=round(pr['sd'], 2),
        p_side=round(conf, 4), side=side, won=int(won), result=p['result'],
        b2b=g['back_to_back'], rest=g['rest_days'], home=home,
        team_spread=team_spread, open_total=p['open_total'],
        min_trend=pr['min_l5'] - pr['min_l10'],
        form=(pr['form_l5'] / pr['form_seas'] - 1) if pr['form_seas'] else None,
        room_book=room_book, room_pinn=room_pinn, n_books=len(book_lines),
        book_side=book_side,
        close_move=(p['close_line'] - p['open_line']) if (p['close_line'] is not None and p['open_line'] is not None) else None,
        edge=(proj - line) / pr['sd'],
        n_hist=pr['n'],
    ))
print('projected', len(out), 'skipped', dict(skipped), flush=True)

if os.path.exists(OUTDB):
    os.remove(OUTDB)
o = sqlite3.connect(OUTDB)
keys = ['event_id','player_id','player','team','opp','stat','date','season','line','proj','sd','p_side','side','won','result',
        'b2b','rest','home','team_spread','open_total','min_trend','form','room_book','room_pinn','n_books','book_side','close_move','edge','n_hist']
o.execute("create table projections(%s)" % ','.join(keys))
o.executemany("insert into projections values (%s)" % ','.join('?' * len(keys)), [[r[k] for k in keys] for r in out])
o.commit(); o.close()

dates = sorted(r['date'] for r in out)
mid = dates[len(dates) // 2]
for r in out:
    r['half'] = 'older' if r['date'] < mid else 'newer'
H = ['older', 'newer']

def rec(rs):
    w = sum(r['won'] for r in rs); return w, len(rs) - w

def pct(w, l):
    return (100.0 * w / (w + l)) if (w + l) else 0

L = []
def P(s=''):
    L.append(s)

def table(title, groups, note=None):
    P('### %s' % title)
    if note: P(note)
    P()
    P('| Value | Older half | Newer half | Both |')
    P('|---|---|---|---|')
    for lab, fn in groups:
        cells = []
        allw = alll = 0
        for h in H:
            rs = [r for r in out if r['half'] == h and fn(r)]
            w, l = rec(rs); allw += w; alll += l
            cells.append('%d-%d (%.0f%%)' % (w, l, pct(w, l)) if rs else '-')
        cells.append('%d-%d (%.0f%%)' % (allw, alll, pct(allw, alll)) if allw + alll else '-')
        P('| %s | %s |' % (lab, ' | '.join(cells)))
    P()

def fixed_side_table(title, groups):
    """groups: (label, filter, side to bet)"""
    P('### %s' % title)
    P()
    P('| Value | Older half | Newer half | Both |')
    P('|---|---|---|---|')
    for lab, fn, sidew in groups:
        cells = []; aw = al = 0
        for h in H:
            rs = [r for r in out if r['half'] == h and fn(r)]
            w = sum(1 for r in rs if (r['won'] == 1) == (r['side'] == sidew)); l = len(rs) - w; aw += w; al += l
            cells.append('%d-%d (%.0f%%)' % (w, l, pct(w, l)) if rs else '-')
        cells.append('%d-%d (%.0f%%)' % (aw, al, pct(aw, al)) if aw + al else '-')
        P('| %s | %s |' % (lab, ' | '.join(cells)))
    P()

P('# Apex Basketball - Phase 3: edge discovery')
P('Date: %s. Every clean PrizePicks prop with a result (PP line taken before tip, at least one book line before tip).' % TODAY)
P()
P('## What the projection is')
P('Built from scratch, no tennis code. For each prop, using only games BEFORE that game:')
P('- Minutes = 60% of the last 5 games + 40% of the last 10.')
P('- Per-minute rate = 40% last 5, 35% last 10, 25% last 40 games.')
P('- Opponent factor = what the opponent allowed of that stat in its last 15 games vs league average (capped 0.8-1.2).')
P('- Spread (how often the number lands) = spread of the last 10 games, floor 1.')
P('- Side = MORE if the projection is above the PrizePicks line, else LESS. Chance = normal curve.')
P('- Needs 5+ prior games with minutes.')
P()
P('Props projected: %d of %d clean props. Skipped: %s.' % (len(out), len(props), ', '.join('%s %d' % kv for kv in sorted(skipped.items()))))
P('Older half: before %s (%d props). Newer half: %s onward (%d props).' % (mid, sum(r['half']=='older' for r in out), mid, sum(r['half']=='newer' for r in out)))
P()
P('## Baselines (what you get with no model at all)')
fixed_side_table('Bet every prop one way', [('MORE on every prop', lambda r: True, 'more'), ('LESS on every prop', lambda r: True, 'less')])

P('## The projection by itself')
table('Projection side, all props', [('Follow the projection', lambda r: True)])
table('Projection side by how sure it is', [
    ('50-55%', lambda r: r['p_side'] < 0.55),
    ('55-60%', lambda r: 0.55 <= r['p_side'] < 0.60),
    ('60-65%', lambda r: 0.60 <= r['p_side'] < 0.65),
    ('65-70%', lambda r: 0.65 <= r['p_side'] < 0.70),
    ('70-80%', lambda r: 0.70 <= r['p_side'] < 0.80),
    ('80%+', lambda r: r['p_side'] >= 0.80),
], 'Calibration check: a bucket is honest if the won-lost percent matches the bucket.')
table('Projection side by stat', [(s, (lambda s: lambda r: r['stat'] == s)(s)) for s in sorted(set(r['stat'] for r in out))])
table('Projection side: MORE picks vs LESS picks', [
    ('MORE picks', lambda r: r['side'] == 'more'), ('LESS picks', lambda r: r['side'] == 'less')])
P('### Brier score (lower is better; 0.25 = coin flip)')
for h in H:
    rs = [r for r in out if r['half'] == h]
    b = mean([(r['p_side'] - r['won']) ** 2 for r in rs])
    P('- %s half: %.4f on %d props' % (h, b, len(rs)))
P()

P('## Each fact alone (projection side, split by the fact)')
table('Back-to-back', [('Back-to-back game', lambda r: r['b2b'] == 1), ('Not back-to-back', lambda r: r['b2b'] == 0)])
table('Rest days', [('1 day (b2b)', lambda r: r['rest'] == 1), ('2 days', lambda r: r['rest'] == 2), ('3+ days', lambda r: r['rest'] is not None and r['rest'] >= 3)])
table('Home / away', [('Home', lambda r: r['home'] == 1), ('Away', lambda r: r['home'] == 0)])
table('Point spread (team view, opening line)', [
    ('Big favorite (-10 or more)', lambda r: r['team_spread'] is not None and r['team_spread'] <= -10),
    ('Favorite (-3 to -10)', lambda r: r['team_spread'] is not None and -10 < r['team_spread'] <= -3),
    ('Close game (within 3)', lambda r: r['team_spread'] is not None and -3 < r['team_spread'] < 3),
    ('Underdog (+3 to +10)', lambda r: r['team_spread'] is not None and 3 <= r['team_spread'] < 10),
    ('Big underdog (+10 or more)', lambda r: r['team_spread'] is not None and r['team_spread'] >= 10),
    ('No spread on file', lambda r: r['team_spread'] is None),
])
table('Blowout risk x side', [
    ('Big favorite/dog (10+) and MORE', lambda r: r['team_spread'] is not None and abs(r['team_spread']) >= 10 and r['side'] == 'more'),
    ('Big favorite/dog (10+) and LESS', lambda r: r['team_spread'] is not None and abs(r['team_spread']) >= 10 and r['side'] == 'less'),
    ('Close game (under 5) and MORE', lambda r: r['team_spread'] is not None and abs(r['team_spread']) < 5 and r['side'] == 'more'),
    ('Close game (under 5) and LESS', lambda r: r['team_spread'] is not None and abs(r['team_spread']) < 5 and r['side'] == 'less'),
])
table('Game total (opening)', [
    ('Under 220', lambda r: r['open_total'] is not None and r['open_total'] < 220),
    ('220-230', lambda r: r['open_total'] is not None and 220 <= r['open_total'] < 230),
    ('230+', lambda r: r['open_total'] is not None and r['open_total'] >= 230),
])
table('Minutes trend (last 5 vs last 10)', [
    ('Minutes up 2+', lambda r: r['min_trend'] >= 2), ('Flat', lambda r: -2 < r['min_trend'] < 2), ('Minutes down 2+', lambda r: r['min_trend'] <= -2)])
table('Form (last 5 vs last 40)', [
    ('Hot (+15% or more)', lambda r: r['form'] is not None and r['form'] >= 0.15),
    ('Normal', lambda r: r['form'] is not None and -0.15 < r['form'] < 0.15),
    ('Cold (-15% or worse)', lambda r: r['form'] is not None and r['form'] <= -0.15),
])
table('Form x side', [
    ('Hot and MORE', lambda r: r['form'] is not None and r['form'] >= 0.15 and r['side'] == 'more'),
    ('Hot and LESS', lambda r: r['form'] is not None and r['form'] >= 0.15 and r['side'] == 'less'),
    ('Cold and MORE', lambda r: r['form'] is not None and r['form'] <= -0.15 and r['side'] == 'more'),
    ('Cold and LESS', lambda r: r['form'] is not None and r['form'] <= -0.15 and r['side'] == 'less'),
])
def room_agrees(r):
    return r['room_book'] is not None and r['room_book'] != 0 and ((r['room_book'] < 0) == (r['side'] == 'more'))
table('PrizePicks line vs book line (room), projection side', [
    ('PP lower than books by 1+, MORE', lambda r: r['room_book'] is not None and r['room_book'] <= -1 and r['side'] == 'more'),
    ('PP lower than books by 0.5, MORE', lambda r: r['room_book'] is not None and -1 < r['room_book'] < 0 and r['side'] == 'more'),
    ('PP same as books, MORE', lambda r: r['room_book'] == 0 and r['side'] == 'more'),
    ('PP same as books, LESS', lambda r: r['room_book'] == 0 and r['side'] == 'less'),
    ('PP higher than books by 0.5, LESS', lambda r: r['room_book'] is not None and 0 < r['room_book'] < 1 and r['side'] == 'less'),
    ('PP higher than books by 1+, LESS', lambda r: r['room_book'] is not None and r['room_book'] >= 1 and r['side'] == 'less'),
    ('Projection goes AGAINST the room', lambda r: r['room_book'] is not None and r['room_book'] != 0 and not room_agrees(r)),
], 'Room = PrizePicks line minus the middle book line. A lower PP line means MORE is easier; higher means LESS is easier.')
fixed_side_table('Room alone, no projection (take the side the room favors)', [
    ('PP lower by 1+ -> MORE', lambda r: r['room_book'] is not None and r['room_book'] <= -1, 'more'),
    ('PP lower by 0.5 -> MORE', lambda r: r['room_book'] is not None and -1 < r['room_book'] < 0, 'more'),
    ('PP higher by 0.5 -> LESS', lambda r: r['room_book'] is not None and 0 < r['room_book'] < 1, 'less'),
    ('PP higher by 1+ -> LESS', lambda r: r['room_book'] is not None and r['room_book'] >= 1, 'less'),
])
fixed_side_table('Pinnacle room alone (when Pinnacle had a line before tip)', [
    ('PP lower than Pinnacle -> MORE', lambda r: r['room_pinn'] is not None and r['room_pinn'] < 0, 'more'),
    ('PP higher than Pinnacle -> LESS', lambda r: r['room_pinn'] is not None and r['room_pinn'] > 0, 'less'),
])
table('Books agree with the projection?', [
    ('Books lean same side', lambda r: r['book_side'] is not None and r['book_side'] == r['side']),
    ('Books same line (no lean)', lambda r: r['book_side'] == 'same'),
    ('Books lean other side', lambda r: r['book_side'] is not None and r['book_side'] not in ('same', r['side'])),
])
table('Line move (book open to close) vs projection side', [
    ('Move toward our side', lambda r: r['close_move'] is not None and r['close_move'] != 0 and ((r['close_move'] > 0) == (r['side'] == 'more'))),
    ('No move', lambda r: r['close_move'] == 0),
    ('Move against our side', lambda r: r['close_move'] is not None and r['close_move'] != 0 and ((r['close_move'] > 0) != (r['side'] == 'more'))),
], 'Note: the close line is known only after the fact; this is a CLV check, not a pre-tip rule.')
table('Edge size (projection minus line, in spreads)', [
    ('Under 0.25', lambda r: abs(r['edge']) < 0.25), ('0.25-0.5', lambda r: 0.25 <= abs(r['edge']) < 0.5),
    ('0.5-1.0', lambda r: 0.5 <= abs(r['edge']) < 1.0), ('1.0+', lambda r: abs(r['edge']) >= 1.0)])
table('How much history the player has', [
    ('5-9 games', lambda r: r['n_hist'] < 10), ('10-29 games', lambda r: 10 <= r['n_hist'] < 30), ('30+ games', lambda r: r['n_hist'] >= 30)])

P('## Best single rules (PASS = 55%+ in BOTH halves with 60+ picks in each)')
cands = [
 ('Projection 60%+ sure', lambda r: r['p_side'] >= 0.60),
 ('Projection 65%+ sure', lambda r: r['p_side'] >= 0.65),
 ('Projection 70%+ sure', lambda r: r['p_side'] >= 0.70),
 ('Projection 60%+ and room agrees', lambda r: r['p_side'] >= 0.60 and room_agrees(r)),
 ('Projection 60%+ and books lean same side', lambda r: r['p_side'] >= 0.60 and r['book_side'] == r['side']),
 ('Projection 60%+ LESS only', lambda r: r['p_side'] >= 0.60 and r['side'] == 'less'),
 ('Projection 60%+ MORE only', lambda r: r['p_side'] >= 0.60 and r['side'] == 'more'),
 ('Projection 60%+ not back-to-back', lambda r: r['p_side'] >= 0.60 and r['b2b'] == 0),
 ('Projection 60%+ close game (spread under 7)', lambda r: r['p_side'] >= 0.60 and r['team_spread'] is not None and abs(r['team_spread']) < 7),
 ('Projection 60%+ 30+ games history', lambda r: r['p_side'] >= 0.60 and r['n_hist'] >= 30),
 ('Room 1+ in our favor, any projection', lambda r: r['room_book'] is not None and abs(r['room_book']) >= 1 and room_agrees(r)),
 ('Projection 60%+ and Pinnacle room agrees', lambda r: r['p_side'] >= 0.60 and r['room_pinn'] is not None and r['room_pinn'] != 0 and ((r['room_pinn'] < 0) == (r['side'] == 'more'))),
]
P()
P('| Rule | Older half | Newer half | Both | Verdict |')
P('|---|---|---|---|---|')
for lab, fn in cands:
    cells = []; ok = True; aw = al = 0
    for h in H:
        rs = [r for r in out if r['half'] == h and fn(r)]
        w, l = rec(rs); aw += w; al += l
        cells.append('%d-%d (%.0f%%)' % (w, l, pct(w, l)) if rs else '-')
        if (w + l) < 60 or pct(w, l) < 55: ok = False
    cells.append('%d-%d (%.0f%%)' % (aw, al, pct(aw, al)))
    P('| %s | %s | %s |' % (lab, ' | '.join(cells), 'PASS' if ok else 'fail'))
P()
P('55% is roughly break-even on a PrizePicks 3-pick standard slip; a board needs more than that.')
P()
P('## Not tested yet (data missing)')
P('- freeThrowsMade / freeThrowsAttempted: no free-throw numbers in the box-score history (%d clean props skipped).' % sum(v for k, v in skipped.items() if k.startswith('no_stat_map')))
P('- Injuries, lineups, usage rate, pace, defensive rating: no history on the machine; the injury + schedule saver started 2026-11-04 and is building it.')
P('- Travel distance: venue data starts 2026-11-04.')
P('- Goblin / Demon lines: history is standard lines only; Goblin/Demon saving started 2026-11-04.')
P()
P('Projections saved to data/processed/phase3_projections.sqlite (table projections) for Phase 4.')

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w').write('\n'.join(L) + '\n')
print('wrote', OUT, flush=True)

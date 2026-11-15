#!/usr/bin/env python3
"""Apex Basketball - Room check (report only, no board). Joins today's saved PrizePicks standard lines with today's saved book lines
and gives every candidate a Room Edge 0/1/2 (code/room_edge.py). Usage: room_check.py [YYYY-MM-DD] [--post]
"""
import datetime as dt, json, os, statistics as st, sys, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import room_edge as RE
try:
    from zoneinfo import ZoneInfo; CT = ZoneInfo('America/Chicago')
except Exception: CT = dt.timezone(dt.timedelta(hours=-6))
PP2MARKET = {'Points': 'player_points', 'Rebounds': 'player_rebounds', 'Assists': 'player_assists', 'PRA': 'player_points_rebounds_assists', 'Pts+Rebs': 'player_points_rebounds',
             'Pts+Asts': 'player_points_assists', 'Rebs+Asts': 'player_rebounds_assists', 'FG Made': 'player_field_goals', 'Fantasy Score': 'player_fantasy_points'}
PP2HIST = {'Points': 'points', 'Rebounds': 'rebounds', 'Assists': 'assists', 'PRA': 'points+rebounds+assists', 'Pts+Rebs': 'points+rebounds', 'Pts+Asts': 'points+assists', 'Rebs+Asts': 'rebounds+assists', 'FG Made': 'fieldGoalsMade', 'Fantasy Score': 'fantasy'}
def norm(s): return ''.join(c for c in unicodedata.normalize('NFKD', s or '') if not unicodedata.combining(c)).lower().replace('.', '').replace('-', ' ').replace("'", '').strip()
def latest(rows, keyf):
    out = {}
    for r in rows: out[keyf(r)] = r
    return out
def run(day, post=False):
    pp_file = os.path.join(ROOT, 'data', 'collected', day + '.jsonl'); bk_file = os.path.join(ROOT, 'data', 'collected', 'books', day + '.jsonl')
    pp = [json.loads(l) for l in open(pp_file)] if os.path.exists(pp_file) else []
    bk = [json.loads(l) for l in open(bk_file)] if os.path.exists(bk_file) else []
    pp = [r for r in pp if r.get('league') == 'NBA' and r.get('odds_type') == 'standard' and r.get('stat') in PP2MARKET and not r.get('is_promo')]
    pp = latest(pp, lambda r: (r['projection_id'],)).values()
    if not bk: return 'Room check %s: %d PrizePicks standard lines on the 9 stats, but NO book lines saved yet (data/collected/books/%s.jsonl missing).' % (day, len(pp), day)
    last = latest(bk, lambda r: (r['book'], r['market'], norm(r['player'])))
    books = {}
    for (b, m, p), r in last.items(): books.setdefault((m, p), []).append(r['line'])
    out = []; counts = {0: 0, 1: 0, 2: 0}; nobook = 0
    for r in pp:
        bl = books.get((PP2MARKET[r['stat']], norm(r['player'])))
        if not bl: nobook += 1; continue
        e = RE.room_edge(r['line'], bl); counts[e['edge']] += 1
        if e['edge']: out.append((e['edge'], abs(e['room']), r['player'], r['team'], r['opponent'], r['stat'], r['line'], st.median(bl), len(bl), e['side'], e['text']))
    out.sort(key=lambda t: (-t[0], -t[1]))
    L = ['Room check %s (report only, no board): %d PrizePicks lines, %d matched to a book line, %d with no book line.' % (day, len(pp), sum(counts.values()), nobook),
         'Room Edge 2: %d   Room Edge 1: %d   Room Edge 0: %d   (books seen: %s)' % (counts[2], counts[1], counts[0], ', '.join(sorted({r['book'] for r in bk})))]
    for e, _, pl, tm, op, stt, line, med, nb, side, txt in out[:15]:
        L.append('%s %s (%s v %s) %s PP %g / books %g (%d books) -> %s. %s' % ('🟩' if e == 2 else '🟨', pl, tm, op, stt, line, med, nb, side, txt))
    text = '\n'.join(L)
    if post:
        sys.path.insert(0, HERE); import book_line_collector as BL; BL.post('bball-system', text[:1800])
    return text
if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; day = args[0] if args else dt.datetime.now(CT).strftime('%Y-%m-%d')
    print(run(day, post='--post' in sys.argv))

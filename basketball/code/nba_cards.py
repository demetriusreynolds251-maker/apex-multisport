#!/usr/bin/env python3
"""Apex Basketball - NBA prop cards (his 11/5 ask: every prop shown with the reasoning and data points, like the tennis cards).
One card per PrizePicks standard line on the 8 board stats for tonight's games: Room Edge (book lines when saved), Apex side + chance,
last 5 / last 10 / last 40 averages, projection, hot/cold, rest, teammates out. Order: Room Edge 2 first, then Room Edge 1, then Apex chance.
Usage: nba_cards.py [YYYY-MM-DD] [--post] [--top N]   (report only, no board, no slip)
"""
import datetime as dt, json, os, statistics as ST, sys, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import score_board as SB, shadow_runner as SR, room_edge as RE, room_check as RC
CT = SR.CT
FOOT = ''   # APEX-REMOVETEST-2026-11-10 (owner, "go remove test"): the TEST label is gone from every card
def norm(s): return RC.norm(s)
def book_lines(day):
    f = os.path.join(ROOT, 'data', 'collected', 'books', day + '.jsonl')
    if not os.path.exists(f): return {}
    last = {}
    for l in open(f):
        r = json.loads(l); last[(r['book'], r['market'], norm(r['player']))] = r['line']
    out = {}
    for (b, m, p), v in last.items(): out.setdefault((m, p), []).append(v)
    return out
MARKET = {'points': 'player_points', 'rebounds': 'player_rebounds', 'assists': 'player_assists', 'points+rebounds+assists': 'player_points_rebounds_assists', 'points+rebounds': 'player_points_rebounds', 'points+assists': 'player_points_assists', 'rebounds+assists': 'player_rebounds_assists', 'fieldGoalsMade': 'player_field_goals'}
def injuries(day):
    f = os.path.join(ROOT, 'data', 'collected', 'injuries', day + '.jsonl'); out = {}
    if not os.path.exists(f): return out
    for l in open(f):
        r = json.loads(l)
        if r.get('status') in ('Out', 'Doubtful'): out.setdefault(r.get('team_abbr'), {})[r['player']] = r['status']
    return out
def build(day, hist=None, now=None):
    hist = hist or SB.History(); now = now or dt.datetime.now(dt.timezone.utc); lines, saved, bad = SB.load_saved_lines(); books = book_lines(day); inj = injuries(day); out = []
    for r in lines:
        try: st = dt.datetime.fromisoformat(str(r.get('start')).replace('Z', '+00:00')).astimezone(dt.timezone.utc)
        except (ValueError, TypeError): continue
        if st.astimezone(CT).date().isoformat() != day or str(r.get('league') or '') != 'NBA' or st <= now: continue
        if str(r.get('odds_type') or 'standard').lower() != 'standard' or r.get('is_promo') or r.get('flash_sale_line') is not None: continue
        stat = SR.PP.get(str(r.get('stat') or '').strip().lower())
        if not stat: continue
        name = str(r.get('player') or '?'); team = SB.abbr(r.get('team')); opp, home = SB.parse_opponent(r.get('opponent')); sch = SB._schedule_lookup(team, day)
        if sch: opp = opp or sch[0]
        if not team or not opp or opp not in SB.TEAMS: continue
        pid, why = hist.resolve(name, team)
        try: line = float(r.get('line'))
        except (ValueError, TypeError): continue
        c = dict(player=name, team=team, opp=opp, stat=stat, label=SR.STATS[stat][0], line=line, start=st, pid=pid, side=None, chance=None, proj=None, l5=None, l10=None, l40=None, form=None, rest=None, games=0)
        bl = books.get((MARKET[stat], norm(name))); e = RE.room_edge(line, bl or [])
        c.update(edge=e['edge'], rside=e['side'], room=e['room'], rtext=e['text'] if bl else 'Room Edge: no book line saved yet', nbooks=len(bl or []))
        if pid:
            pr, why = SR.project(hist, pid, stat, day, SB.TEAMS[opp][0]); fn = SR.STATS[stat][1]
            H = [h for h in hist.H.get(pid, []) if h['game_date'] < day and h['minutes'] and h['minutes'] > 0]
            if pr:
                p_more = 1 - SR.ncdf((line - pr['proj']) / pr['sd']); side = 'MORE' if p_more >= .5 else 'LESS'
                c.update(proj=pr['proj'], form=pr['form'], games=pr['games'], side=side, chance=round(100 * max(p_more, 1 - p_more)))
            if H:
                vals = [fn(h) for h in H]; c.update(l5=ST.mean(vals[-5:]), l10=ST.mean(vals[-10:]), l40=ST.mean(vals[-40:]), last=H[-1]['game_date'])
                c['rest'] = (dt.date.fromisoformat(day) - dt.date.fromisoformat(H[-1]['game_date'])).days
        c['out'] = [p for p in inj.get(team, {}) if norm(p) != norm(name)]
        if c['edge'] and c['rside']: c['pick'] = c['rside']
        else: c['pick'] = c['side']
        out.append(c)
    out.sort(key=lambda c: (-c['edge'], -(c['chance'] or 0), c['player']))
    return out, saved
def card(c, i):
    hdr = '%d. **%s** %s v %s · %s %g · %s' % (i, c['player'], c['team'], c['opp'], c['label'], c['line'], c['start'].astimezone(CT).strftime('%-I:%M %p CT'))
    L = [hdr]
    L.append('   🎯 Apex: **%s%s**' % (c['pick'] or 'no call', (' %d' % c['chance']) if c['chance'] else '') + ('  (Room Edge decides the side; the number is the projection order)' if c['edge'] else ''))
    L.append('   📏 ' + c['rtext'] + ('  (%d books)' % c['nbooks'] if c['nbooks'] else ''))
    if c['proj'] is not None: L.append('   📈 last 5 avg %.1f · last 10 %.1f · last 40 %.1f · projection %.1f (%d games on file)' % (c['l5'], c['l10'], c['l40'], c['proj'], c['games']))
    else: L.append('   📈 under 5 games on file for this stat, no projection')
    if c['form'] is not None:
        if c['form'] >= .15: L.append('   🔥 hot: last 5 games %.0f%% above his average (hot players miss LESS lines more often)' % (100 * c['form']))
        elif c['form'] <= -.15: L.append('   ❄ cold: last 5 games %.0f%% below his average' % (-100 * c['form']))
    if c['rest'] is not None: L.append('   📅 ' + ('back-to-back (played yesterday)' if c['rest'] == 1 else 'rest %d days' % c['rest']))
    if c['out']: L.append('   🏥 teammates out/doubtful: ' + ', '.join(c['out'][:4]))
    return '\n'.join(L)
def text(day, cards, saved, top=20):
    d = dt.date.fromisoformat(day).strftime('%a %-m/%-d'); n2 = sum(1 for c in cards if c['edge'] == 2); n1 = sum(1 for c in cards if c['edge'] == 1)
    L = ['🏀 **NBA PROPS %s** · %d lines not started · Room Edge 2: %d · Room Edge 1: %d · ordered Room Edge first, then Apex chance. Report, not a board.' % (d, len(cards), n2, n1)]
    if not any(c['nbooks'] for c in cards): L.append('📏 No book lines saved yet, so every Room Edge line reads "no book line". The Odds API key is not in (/bball-setkey).')
    for i, c in enumerate(cards[:top], 1): L.append(card(c, i))
    if len(cards) > top: L.append('… %d more lines not shown. Full list: python3 code/nba_cards.py %s --top 999' % (len(cards) - top, day))
    L.append('📥 Lines saved %s. ' % (dt.datetime.fromisoformat(saved.replace('Z', '+00:00')).astimezone(CT).strftime('%-I:%M %p CT') if saved else 'never') + FOOT)
    return '\n'.join(L)
if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a.count('-') == 2 and len(a) == 10]; day = args[0] if args else dt.datetime.now(CT).strftime('%Y-%m-%d')
    top = int(sys.argv[sys.argv.index('--top') + 1]) if '--top' in sys.argv else 20
    cards, saved = build(day); t = text(day, cards, saved, top); print(t)
    if '--post' in sys.argv: SR.post('bball-picks', t)

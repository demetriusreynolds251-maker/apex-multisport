#!/usr/bin/env python3
"""Results for this sport from ESPN's public scoreboard + box scores (free, no key). One scoreboard call per date, one summary call per finished
game not yet saved. Box-score values are mapped to this sport's stat keys by config['espn']['keys'] (ESPN label -> our key).
  python3 grading/results.py [YYYY-MM-DD ...]   default: yesterday and today"""
import datetime as dt, json, os, re, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as CM
from database import db as DBM

HDR = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=30) as r: return json.load(r)
def _num(x):
    s = str(x if x is not None else '').strip()
    if s in ('', '--', '-'): return None
    m = re.match(r'^(-?\d+(?:\.\d+)?)', s)
    return float(m.group(1)) if m else None
def _pair(x):
    """'22/30' -> (22, 30); '3-45' -> (3, 45)."""
    m = re.match(r'^(\d+)\s*[/-]\s*(\d+)', str(x or ''))
    return (float(m.group(1)), float(m.group(2))) if m else (None, None)
def _minutes(x):
    s = str(x or '').strip()
    if ':' in s:
        a, b = s.split(':')[:2]; return (_num(a) or 0) + (_num(b) or 0) / 60
    return _num(s)

def parse_players(j, game):
    """Rows (player, team, opponent, home, stats dict) from an ESPN summary. Soccer uses rosters; others use boxscore.players."""
    c = CM.cfg()['espn']; keys = c['keys']; out = {}
    def put(name, team, k, v):
        if name is None or v is None: return
        home = int(team == game['home']); opp = game['away'] if home else game['home']
        d = out.setdefault((CM.norm(name), team), dict(player=name, team=team, opp=opp, home=home, stats={})); d['stats'][k] = v
    bs = j.get('boxscore') or {}
    for tb in bs.get('players') or []:
        team = (tb.get('team') or {}).get('abbreviation')
        for sec in tb.get('statistics') or []:
            labels = [str(k) for k in (sec.get('keys') or sec.get('labels') or [])]; cat = sec.get('name') or sec.get('type') or ''
            for a in sec.get('athletes') or []:
                at = a.get('athlete') or {}; name = at.get('displayName'); vals = a.get('stats') or []
                if not name or not vals: continue
                put(name, team, '_played', 1)
                for lab, v in zip(labels, vals):
                    for key, spec in keys.items():
                        if spec[0] == cat or spec[0] == '*':
                            if spec[1] == lab: put(name, team, key, _minutes(v) if spec[2:] == ['minutes'] else _num(v))
                            elif spec[1] == lab + '#1': put(name, team, key, _pair(v)[0])
                            elif spec[1] == lab + '#2': put(name, team, key, _pair(v)[1])
    for tr in (j.get('rosters') or []):                     # soccer
        team = (tr.get('team') or {}).get('abbreviation')
        for p in tr.get('roster') or []:
            at = p.get('athlete') or {}; name = at.get('displayName')
            if not name: continue
            st = {s.get('name'): s.get('value') for s in p.get('stats') or []}
            if not st and not p.get('starter') and not p.get('subbedIn'): continue
            if 'appearances' in st and not (_num(st.get('appearances')) or 0) and not any(_num(v) for k, v in st.items() if k != 'appearances'):
                # APEX-APPEARED-2026-11-12: on the team sheet but never came on = did not play (was saved as a game of zeros and graded as a loss)
                put(name, team, '_played', 0); put(name, team, 'appearances', 0.0); continue
            put(name, team, '_played', 1)
            for key, spec in keys.items():
                if spec[0] == 'roster' and spec[1] in st: put(name, team, key, _num(st[spec[1]]))
    return list(out.values())

def update(db=None, dates=None, pause=1.0):
    db = db or DBM.connect(); c = CM.cfg()['espn']; dates = dates or [(CM.now_ct().date() - dt.timedelta(days=1)).isoformat(), CM.now_ct().date().isoformat()]
    got = dict(dates=0, final=0, new_box=0, failed=0)
    for path in c['paths']:
        for d in dates:
            try: j = fetch('https://site.api.espn.com/apis/site/v2/sports/%s/scoreboard?dates=%s&limit=300' % (path, d.replace('-', '')))
            except Exception as e: got['failed'] += 1; CM.log('grading', 'scoreboard %s %s: %s' % (path, d, type(e).__name__)); continue
            got['dates'] += 1; time.sleep(pause)
            for e in j.get('events') or []:
                comp = ((e.get('competitions') or [None])[0]) or {}; tm = {t.get('homeAway'): t for t in comp.get('competitors') or [] if t}
                if 'home' not in tm or 'away' not in tm or not tm['home'].get('team') or not tm['away'].get('team'): continue
                status = ((comp.get('status') or e.get('status') or {}).get('type') or {}); st = CM.parse_iso(e.get('date'))
                g = dict(event_id=str(e['id']), game_date=st.astimezone(CM.CT).date().isoformat() if st else d, start=CM.iso(st) if st else None, home=tm['home']['team'].get('abbreviation'), away=tm['away']['team'].get('abbreviation'),
                         hs=_num(tm['home'].get('score')), as_=_num(tm['away'].get('score')), final=int(bool(status.get('completed'))))
                db.execute('insert into games(event_id,game_date,start_utc,home,away,home_score,away_score,final,source) values(?,?,?,?,?,?,?,?,?) on conflict(event_id) do update set home_score=excluded.home_score,away_score=excluded.away_score,final=excluded.final',
                           (g['event_id'], g['game_date'], g['start'], g['home'], g['away'], g['hs'], g['as_'], g['final'], 'espn'))
                if not g['final']: continue
                got['final'] += 1
                if db.execute('select box_saved from games where event_id=?', (g['event_id'],)).fetchone()[0]: continue
                try: rows = parse_players(fetch('https://site.api.espn.com/apis/site/v2/sports/%s/summary?event=%s' % (path, g['event_id'])), g); time.sleep(pause)
                except Exception as ex: got['failed'] += 1; CM.log('grading', 'summary %s: %s' % (g['event_id'], type(ex).__name__)); continue
                if rows:
                    for r in rows: db.execute('insert or replace into player_games values(?,?,?,?,?,?,?,?,?)', (g['event_id'], CM.norm(r['player']), r['player'], r['team'], r['opp'], r['home'], g['game_date'], json.dumps(r['stats']), 'espn'))
                    db.execute('update games set box_saved=1 where event_id=?', (g['event_id'],)); got['new_box'] += 1
                else: got['failed'] += 1
            db.commit()
    CM.log('grading', 'results: %s' % got); return got

if __name__ == '__main__': print(update(dates=sys.argv[1:] or None))

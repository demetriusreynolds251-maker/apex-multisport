"""APEX-MATCHUP-NAMES-2026-11-07: full team name -> stored team code, from the SGO event index (names) joined to our games
table (codes). Writes cache/team_codes.json. Run again after new history is built."""
import os, sys, csv, glob, json, sqlite3, unicodedata, re, collections as C
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDX = '/Volumes/2TB Drive/SportsData/sportsgameodds/index'
def norm(s): return ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().upper()).split())
def build():
    names = {}
    for f in glob.glob(os.path.join(IDX, '*_events.csv')):
        for r in csv.DictReader(open(f, encoding='utf-8', errors='ignore')):
            names[r['eventID']] = (r['home'], r['away'])
    db = sqlite3.connect(os.path.join(ROOT, 'database', 'history.db'))
    vote = C.defaultdict(C.Counter)
    for e, h, a in db.execute('select event_id, home, away from games'):
        if e in names and h and a:
            vote[norm(names[e][0])][h] += 1; vote[norm(names[e][1])][a] += 1
    out = {n: c.most_common(1)[0][0] for n, c in vote.items() if c.most_common(1)[0][1] >= 2}
    json.dump(out, open(os.path.join(ROOT, 'cache', 'team_codes.json'), 'w'), indent=0, sort_keys=True)
    return out
def lookup(name, table):
    n = norm(name)
    if n in table: return table[n]
    hits = {v for k, v in table.items() if n and (re.search(r'\b%s\b' % re.escape(n), k))}
    return hits.pop() if len(hits) == 1 else None
if __name__ == '__main__':
    t = build(); print(len(t), 'team names')
    for q in sys.argv[1:]: print(q, '->', lookup(q, t))

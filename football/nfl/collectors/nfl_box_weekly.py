#!/usr/bin/env python3
"""APEX-NFLWEEKLY-2026-11-08 (owner, "Do #5": re-pull the official NFL box scores every Tuesday).
Our own downloader for the free nflverse CSV files (plain downloads, no nflverse code). Then the same steps that loaded the
box scores on 11/8 (history/nflbox/): fill/fix player games (stored PrizePicks-graded numbers win), join name spellings,
set aside did-not-play / preseason fake zeros, fold leftover duplicates, check graded props vs the official box score
(fix only stored-0-but-really-played, move out wrong-player lines), add Rush+Rec TD history, rebuild honest numbers.
Backs up history.db first (last 3 kept). Returns one plain line for #system. Never raises."""
import datetime as dt, glob, os, shutil, subprocess, sys, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
import common as CM
H = os.path.expanduser('~')
RAW = H + '/openclaw/_backups/_sports_staging/nfl_td/raw'            # where history/nflbox scripts read the box scores
ROLE = H + '/openclaw/_backups/_sports_staging/freedata/role'         # games.csv + snap counts
BOX = os.path.join(ROOT, 'history', 'nflbox')
GET = [('https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_%d.csv', RAW + '/stats_player_week_%d.csv', 40),
       ('https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_%d.csv', ROLE + '/snap_counts_%d.csv', 50),
       ('https://github.com/nflverse/nfldata/raw/master/data/games.csv', ROLE + '/games.csv', 20)]
def _season():
    n = dt.date.today(); return n.year if n.month >= 8 else n.year - 1
def _get(url, dest, mb):
    req = urllib.request.Request(url, headers={'User-Agent': 'ApexSports-NFL-collector'})
    with urllib.request.urlopen(req, timeout=90) as r: data = r.read(mb * 1024 * 1024 + 1)
    if len(data) > mb * 1024 * 1024 or len(data) < 1000: raise ValueError('bad size %d' % len(data))
    txt = data.decode('utf-8', errors='replace')
    if txt.count('\n') < 50: raise ValueError('too few rows')
    tmp = dest + '.tmp'; open(tmp, 'w').write(txt); os.replace(tmp, dest)
def _step(args):
    r = subprocess.run(['/usr/bin/python3'] + args, cwd=BOX, capture_output=True, text=True, timeout=1800)
    if r.returncode: raise RuntimeError('%s: %s' % (args[0], (r.stderr or r.stdout)[-300:]))
    return r.stdout
def run():
    try:
        yr = _season()
        for url, dest, mb in GET: _get(url % yr if '%d' in url else url, dest % yr if '%d' in dest else dest, mb)
        db = os.path.join(ROOT, 'database', 'history.db'); bk = os.path.join(ROOT, 'database', 'backup'); os.makedirs(bk, exist_ok=True)
        shutil.copy2(db, os.path.join(bk, 'history.db.before-box-%s' % dt.date.today().isoformat()))
        for old in sorted(glob.glob(os.path.join(bk, 'history.db.before-box-*')))[:-3]: os.remove(old)
        a = _step(['nflbox.py', 'apply']); _step(['names.py', 'apply', 'remove']); _step(['dup2.py', 'apply']); g = _step(['grade.py', 'apply', 'grades', 'td', 'flagged'])
        upd = [l for l in a.splitlines() if l.startswith('rows updated')]; td = [l for l in g.splitlines() if l.startswith('added')]
        try:
            from tracking import honest as HN; HN.build()
        except Exception as e: CM.log('nflbox', 'honest rebuild failed: %s' % e)
        CM.log('nflbox', a[-600:] + '\n' + g[-600:])
        return '🏈 Official NFL box scores re-pulled: %s; Rush+Rec TD history %s. Honest numbers rebuilt.' % (
            (upd[0].replace(', mode apply', '') if upd else 'no change'), (td[0].replace('added', '+') + ' games') if td else 'no new games')
    except Exception as e:
        CM.log('nflbox', 'failed: %s' % e)
        return '⚠️ Weekly NFL box-score pull failed: %s. History unchanged where it stopped; tell Claude.' % str(e)[:200]
if __name__ == '__main__':
    print(run())

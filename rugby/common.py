#!/usr/bin/env python3
"""Shared helpers for THIS sport only (paths, config, time, logging, name matching). Every sport folder has its own copy.
Nothing here imports from another sport, from Apex Tennis or from Apex Basketball."""
import datetime as dt, json, os, re, sys, unicodedata
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.abspath(__file__))
CT = ZoneInfo('America/Chicago')
CFG_FILE = os.path.join(ROOT, 'config', 'sport.json')
DB_FILE = os.path.join(ROOT, 'database', 'history.db')
SNAP = os.path.join(ROOT, 'database', 'snapshots')
LOGS = os.path.join(ROOT, 'logs'); CACHE = os.path.join(ROOT, 'cache'); EXPORTS = os.path.join(ROOT, 'exports'); REPORTS = os.path.join(ROOT, 'reports')
SECRETS = os.path.join(ROOT, 'secrets')
SHARED_COOLDOWN = os.path.expanduser('~/ApexSports/_shared/pp_cooldown.json')          # every sport reads + writes this one flag so PrizePicks is never hammered
TENNIS_COOLDOWN = os.path.expanduser('~/openclaw/data/logs/pp_cooldown.json')         # read only

_cfg = None
def cfg():
    global _cfg
    if _cfg is None: _cfg = json.load(open(CFG_FILE))
    return _cfg

def now_utc(): return dt.datetime.now(dt.timezone.utc)
def now_ct(): return dt.datetime.now(CT)
def iso(t=None): return (t or now_utc()).isoformat(timespec='seconds')
def ct_date(t=None): return (t or now_ct()).astimezone(CT).date().isoformat()
def parse_iso(s):
    try: return dt.datetime.fromisoformat(str(s).replace('Z', '+00:00')).astimezone(dt.timezone.utc)
    except (ValueError, TypeError): return None
def fmt_ct(s, f='%-m/%-d %-I:%M %p CT'):
    t = parse_iso(s) if isinstance(s, str) else s
    return t.astimezone(CT).strftime(f) if t else '?'

def log(name, msg):
    os.makedirs(LOGS, exist_ok=True)
    with open(os.path.join(LOGS, name + '.log'), 'a') as f: f.write('%s %s\n' % (now_ct().strftime('%m/%d %H:%M:%S'), msg))

def norm(s):
    """Name key: lower case, no accents, no punctuation, no suffixes (Jr., III)."""
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode()
    s = re.sub(r"[^a-z0-9 ]", ' ', s.lower()); s = re.sub(r'\b(jr|sr|ii|iii|iv)\b', ' ', s)
    return ' '.join(s.split())

def read_json(path, default=None):
    try: return json.load(open(path))
    except Exception: return default
def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + '.tmp', 'w') as f: json.dump(data, f, indent=1, default=str)
    os.replace(path + '.tmp', path)

def secret(name):
    """Reads an env var (e.g. discord_bot_token.txt -> DISCORD_BOT_TOKEN) or secrets/<name> at call time. Never logged."""
    _env = os.environ.get(os.path.splitext(name)[0].upper())
    if _env: return _env.strip()
    try: return open(os.path.join(SECRETS, name)).read().strip() or None
    except OSError: return None

def jsonl_append(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'a') as f:
        for r in rows: f.write(json.dumps(r, default=str) + '\n')
def jsonl_read(path):
    out = []
    try:
        for l in open(path):
            try: out.append(json.loads(l))
            except ValueError: pass
    except OSError: pass
    return out

def season_of(d):
    """Season label from a date string. Config says which month the season starts."""
    y, m = int(d[:4]), int(d[5:7]); start = cfg().get('season_start_month', 1)
    return '%d' % y if start == 1 else ('%d-%02d' % (y, (y + 1) % 100) if m >= start else '%d-%02d' % (y - 1, y % 100))

def dmod(name):
    """Loads discord/<name>.py from THIS sport folder. The folder is called discord/ (the layout asks for it) so it is loaded by path to leave the
    discord.py library alone."""
    import importlib.util
    key = 'apex_%s_discord_%s' % (cfg()['prefix'], name)
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, os.path.join(ROOT, 'discord', name + '.py')); m = importlib.util.module_from_spec(spec); sys.modules[key] = m; spec.loader.exec_module(m)
    return sys.modules[key]

#!/usr/bin/env python3
"""Outbox for this sport's Discord bot. Any process (scheduler, pipeline, grading) drops a message here; discord/bot.py posts it within seconds.
A copy of every message is kept in exports/discord/YYYY-MM-DD.md, so nothing is lost while the bot has no token yet."""
import hashlib, json, os, re, sys, time, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as CM

OUTBOX = os.path.join(CM.CACHE, 'outbox')
DEDUPE = os.path.join(CM.CACHE, 'post_dedupe.json')
COOL_MIN = {'system': 60, 'alerts': 120, 'general': 60, 'learning': 60}   # same message inside this many minutes is held back

def _hold(channel, text):
    """Cooldown for repeated notices. system/alerts compare the message with its numbers blanked, so the same notice with new counts
    is one notice. Returns (skip, text): skip=True when held back; otherwise text carries a count of what was held back."""
    if channel not in COOL_MIN: return False, text
    shape = re.sub(r'\d+', '#', text) if channel in ('system', 'alerts') else text
    key = hashlib.md5((channel + '|' + shape).encode()).hexdigest(); now = time.time()
    st = CM.read_json(DEDUPE, {}) or {}; st = {k: v for k, v in st.items() if now - v.get('t', 0) < 86400}
    e = st.get(key)
    if e and now - e['t'] < COOL_MIN[channel] * 60:
        e['n'] = e.get('n', 0) + 1; st[key] = e; CM.write_json(DEDUPE, st)
        CM.log('post_held', 'held back #%s (%d since %s): %s' % (channel, e['n'], CM.fmt_ct(CM.iso(CM.dt.datetime.fromtimestamp(e['t'], CM.dt.timezone.utc))), text[:140].replace('\n', ' ')))
        return True, text
    if e and e.get('n'): text += '\n_(same notice %d more time%s in the last %d min, held back)_' % (e['n'], '' if e['n'] == 1 else 's', COOL_MIN[channel])
    st[key] = dict(t=now, n=0); CM.write_json(DEDUPE, st); return False, text

def post(channel, text, force=False):
    """channel = short key: picks, alerts, general, learning, system, pnl, slips."""
    if not force:
        skip, text = _hold(channel, text)
        if skip: return None
    os.makedirs(OUTBOX, exist_ok=True); name = '%d_%s.json' % (int(time.time() * 1000), uuid.uuid4().hex[:6])
    CM.write_json(os.path.join(OUTBOX, name), dict(channel=channel, text=text, created=CM.iso()))
    os.makedirs(os.path.join(CM.EXPORTS, 'discord'), exist_ok=True)
    with open(os.path.join(CM.EXPORTS, 'discord', CM.ct_date() + '.md'), 'a') as f: f.write('\n\n## #%s-%s · %s\n\n%s\n' % (CM.cfg()['prefix'], channel, CM.now_ct().strftime('%-I:%M %p CT'), text))
    return name

def post_boards(s, last_mains=None):
    """Posts every board whose main picks changed since last_mains ({board: [pick keys]}). Returns the new mains."""
    K = CM.dmod("cards")
    last_mains = last_mains or {}; shown = {}
    for b, d in s['boards'].items():
        shown[b] = s['mains'][b] if len(s['mains'][b]) >= d['size'] else ['SHORT']     # a short board posts once, as 'not enough'
        if last_mains.get(b) != shown[b]: post('picks', K.board_text(b, d, s))
    return shown

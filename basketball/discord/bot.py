#!/usr/bin/env python3
"""Apex Basketball Discord bot. Everything is 🧪 TEST and separate from Apex: no imports from ~/openclaw, never calls PrizePicks.
Token is read at runtime only from secrets/discord_bot_token.txt. Start with discord/start_bot.sh."""
import asyncio, datetime as dt, fcntl, io, json, os, sys, traceback
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'code'))
import score_board as SB, bball_tracker as T, bball_pipeline as P
sys.path.insert(0, HERE)
import cards as K
GUILD_ID = int(__import__("os").environ.get("DISCORD_GUILD_ID", "0"))
CLIENT_ID = int(__import__("os").environ.get("DISCORD_CLIENT_ID", "0"))
ROOT = SB.ROOT
TOKEN_FILE = os.path.join(ROOT, 'secrets', 'discord_bot_token.txt')
CHANNEL_FILE = os.path.join(ROOT, 'data', 'discord_channels.json')
STATE_FILE = os.path.join(ROOT, 'data', 'bot_state.json')
LOCK_FILE = os.path.join(ROOT, 'logs', 'bball_bot.lock')
CATEGORY = 'Apex Basketball 🧪'
# Same job as the tennis channel of the same name. Tennis 'moneyline' and ParlayPlay channels have no basketball job yet.
CHANNELS = {'bball-picks': '🧪 TEST boards', 'bball-alerts': '🧪 TEST problems only', 'bball-general': '🧪 TEST one status line a day', 'bball-learning-channel': '🧪 TEST is the number honest', 'bball-system': '🧪 TEST every run',
            'bball-slips': '🧪 TEST slip recommendations', 'bball-slips-pnl': '🧪 TEST slip results', 'bball-pnl': '🧪 TEST paper dollars, not the tennis ledger'}
GRADE_HOUR, STATUS_HOUR, SETTLE_MINUTES, COLLECTOR_SILENT_HOURS = 4, 9, 5, 26
# Collectors the bot keeps alive (checked every 5 minutes): name -> (pid file, command). Restarts are posted to #bball-system.
COLLECTORS = {'line collector (PrizePicks)': ('line_collector.pid', ['code/line_collector.py']), 'injury collector (ESPN)': ('injury_collector.pid', ['code/injury_collector.py']),
              'book line collector (The Odds API)': ('book_line_collector.pid', ['code/book_line_collector.py', '--loop'])}
EXIT_NO_TOKEN, EXIT_BAD_TOKEN, EXIT_LOCKED = 3, 4, 5
def log(m): print('%s %s' % (dt.datetime.now(SB.CT).strftime('%m/%d %H:%M:%S'), m), flush=True)
WATCHDOG_STATE = os.path.join(ROOT, 'logs', 'watchdog.json'); WATCHDOG_LOG = os.path.join(ROOT, 'logs', 'watchdog.log')
COLLECTOR_LOGS = {'line collector (PrizePicks)': ['line_collector.log', 'line_collector.out'], 'injury collector (ESPN)': ['injury_collector.log', 'injury_collector.out'],
                  'book line collector (The Odds API)': ['book_lines.log', 'book_line_collector.out']}
def wd_log(m):
    with open(WATCHDOG_LOG, 'a') as f: f.write('%s %s\n' % (dt.datetime.now(SB.CT).strftime('%m/%d %H:%M:%S'), m))
def collector_pid(pidfile):
    try: return int(open(os.path.join(ROOT, 'logs', pidfile)).read().strip())
    except (OSError, ValueError): return None
def collector_alive(pidfile, script=None):
    """True when the pid in the pid file is running AND is that collector (a reused pid does not count)."""
    pid = collector_pid(pidfile)
    if not pid: return False
    try: os.kill(pid, 0)
    except OSError: return False
    if not script: return True
    import subprocess
    try: cmd = subprocess.run(['ps', '-p', str(pid), '-o', 'command='], capture_output=True, text=True, timeout=5).stdout
    except Exception: return True
    return os.path.basename(script) in cmd
def last_activity(name):
    ts = [os.path.getmtime(os.path.join(ROOT, 'logs', f)) for f in COLLECTOR_LOGS.get(name, []) if os.path.exists(os.path.join(ROOT, 'logs', f))]
    return dt.datetime.fromtimestamp(max(ts), dt.timezone.utc).isoformat(timespec='seconds') if ts else None
def start_collector(name):
    """Starts one collector detached, output to logs/<script>.out. Returns the pid."""
    import subprocess
    pidfile, args = COLLECTORS[name]; out = open(os.path.join(ROOT, 'logs', os.path.basename(args[0]).replace('.py', '.out')), 'a')
    pid = subprocess.Popen([sys.executable] + args, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, start_new_session=True).pid
    try: open(os.path.join(ROOT, 'logs', pidfile), 'w').write(str(pid))
    except OSError: pass
    return pid
def load_token(path=None):
    try:
        with open(path or TOKEN_FILE) as f: return f.read().strip() or None
    except OSError: return None
def load_state():
    try:
        with open(STATE_FILE) as f: return json.load(f)
    except (OSError, ValueError): return {}
def save_state(s):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE + '.tmp', 'w') as f: json.dump(s, f)
    os.replace(STATE_FILE + '.tmp', STATE_FILE)
async def ensure_channels(guild, path=None):
    """Creates any missing bball- channel. Safe to run every start: an existing channel, by saved id or by name, is never made twice. Returns (name->id, failures)."""
    path = path or CHANNEL_FILE; saved = {}
    try:
        with open(path) as f: saved = json.load(f)
    except (OSError, ValueError): pass
    have = {c.name: c for c in guild.text_channels}; byid = {c.id: c for c in guild.text_channels}; out, failed, cat = {}, [], None
    for name, topic in CHANNELS.items():
        ch = byid.get(saved.get(name)) or have.get(name)
        if ch is None:
            try:
                if cat is None: cat = next((c for c in guild.categories if c.name == CATEGORY), None) or await guild.create_category(CATEGORY)
                ch = await guild.create_text_channel(name, category=cat, topic=topic, reason='Apex Basketball test channels')
            except Exception as e: failed.append('%s (%s)' % (name, type(e).__name__)); continue
        out[name] = ch.id
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + '.tmp', 'w') as f: json.dump(out, f, indent=1)
    os.replace(path + '.tmp', path)
    return out, failed
BACKUP_CMDS = {'bball-top3backups': ('top3', 'Top 3'), 'bball-elite5backups': ('elite5', 'Elite 5'), 'bball-elite6backups': ('elite6', 'Elite 6'), 'bball-top10backups': ('top10', 'Top 10'),
               'bball-goblinbackups': ('bestgoblin', 'Best Goblin'), 'bball-lessbackups': ('bestless', 'Best Goblin Less'), 'bball-standardbackups': ('beststandard', 'Best Standard'), 'bball-demonbackups': ('bestdemon', 'Best Demon')}
SIMPLE = {'bball-board': ('Saved lines: counts and when they were saved. No PrizePicks call', K.board_diag_text), 'bball-allprops': ('Every saved prop not yet started, with Win Prob or the reason it has none', K.allprops_text),
          'bball-slips': ('Slips: Top 3 Power, Elite 5 and Elite 6 Flex', K.slips_text), 'bball-counters': ('Whole-slip record per board', K.counters_text), 'bball-besttime': ('Boards by the hour lines were saved, real graded days only', K.besttime_text),
          'bball-soon': ('Board picks by start time, soonest first', K.soon_text), 'bball-soon3': ('Top 3 starting in the next 6 hours', lambda: K.soon_card('top3')), 'bball-soon6': ('Elite 6 starting in the next 6 hours', lambda: K.soon_card('elite6')),
          'bball-banned': ('Show the banned list', K.banned_text)}
for _c, _b in K.BOARD_CMD.items(): SIMPLE[_c] = ('%s from the last scoring, no new call' % P.BOARDS[_b]['title'].title(), (lambda b=_b: K.board_text(b)))
for _c, (_b, _t) in BACKUP_CMDS.items(): SIMPLE[_c] = ('%s backups: next above the floor, in rank order' % _t, (lambda b=_b: K.backups_text(b)))
COMMANDS = sorted(list(SIMPLE) + ['bball-fetch', 'bball-pnl', 'bball-h2h', 'bball-ban', 'bball-unban', 'bball-cancel'])
def is_owner(interaction): return interaction.guild is not None and interaction.guild_id == GUILD_ID and interaction.user.id == interaction.guild.owner_id
async def send_long(send, text):
    """Up to 8 messages, and the full text as a file when longer."""
    import discord
    parts = K.chunks(text)
    for p in parts[:8]: await send(content=p)
    if len(parts) > 8: await send(content='Full list attached. ' + K.FOOT, file=discord.File(io.BytesIO(text.encode()), filename='bball.txt'))

ODDS_KEY_FILE = os.path.join(ROOT, 'secrets', 'odds_api_key.txt')
def save_odds_api_key(k):
    """Test the key with one free call, then save it (mode 600). Never logs or returns the key."""
    import urllib.request, urllib.error, urllib.parse
    k = k.strip()
    if not k or ' ' in k or len(k) < 10: return 'That does not look like a key. Nothing saved.'
    req = urllib.request.Request('https://api.the-odds-api.com/v4/sports?' + urllib.parse.urlencode({'apiKey': k}), headers={'User-Agent': 'ApexBasketball/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r: left = r.headers.get('x-requests-remaining')
    except urllib.error.HTTPError as e: return 'The Odds API refused the key (HTTP %s). Nothing saved.' % e.code
    except Exception as e: return 'Could not reach The Odds API (%s). Nothing saved.' % type(e).__name__
    os.makedirs(os.path.dirname(ODDS_KEY_FILE), exist_ok=True)
    if os.path.exists(ODDS_KEY_FILE): os.replace(ODDS_KEY_FILE, ODDS_KEY_FILE + '.bak_' + dt.datetime.now(SB.CT).strftime('%Y%m%d_%H%M%S'))
    with open(ODDS_KEY_FILE, 'w') as f: f.write(k + '\n')
    os.chmod(ODDS_KEY_FILE, 0o600); log('[SetKey] The Odds API key saved via /bball-setkey (tested 200)')
    return '🔑 The Odds API key saved and tested. Credits left: %s. The book-line collector picks it up within a minute.' % left

class Bot:
    def __init__(self):
        import discord
        from discord import app_commands
        self.discord = discord; self.client = discord.Client(intents=discord.Intents.default()); self.tree = app_commands.CommandTree(self.client)
        self.guild_obj = discord.Object(id=GUILD_ID); self.channels = {}; self.state = load_state(); self.ready_once = False; self.job = asyncio.Lock(); self.pending_sig = None; self.pending_since = None
        self.client.event(self.on_ready); self._register(app_commands)
    def _register(self, app_commands):
        tree, g = self.tree, self.guild_obj
        def simple(name, desc, fn):
            async def cb(interaction):
                await interaction.response.defer(thinking=True)
                try: txt = await asyncio.to_thread(fn)
                except Exception as e: txt = '⚠️ %s failed: %s. %s' % (name, type(e).__name__, K.FOOT); log('%s %s' % (name, traceback.format_exc()))
                await send_long(interaction.followup.send, txt)
            tree.add_command(app_commands.Command(name=name, description=desc[:100], callback=cb), guild=g)
        for n, (d, f) in SIMPLE.items(): simple(n, d, f)
        @tree.command(name='bball-fetch', description='Owner: re-score the saved lines. Never calls PrizePicks', guild=g)
        async def fetch(interaction):
            await interaction.response.defer(thinking=True)
            if not is_owner(interaction): return await interaction.followup.send('Owner only.')
            if self.job.locked(): return await interaction.followup.send('A run is already going. Use /bball-cancel to stop it.')
            s = await self.run_rescore('fetch'); await send_long(interaction.followup.send, K.fetch_result_text(s))
        @tree.command(name='bball-cancel', description='Owner: stop the running re-score. Nothing from it is saved', guild=g)
        async def cancel(interaction):
            if not is_owner(interaction): return await interaction.response.send_message('Owner only.')
            if not self.job.locked(): return await interaction.response.send_message('Nothing is running.')
            P.cancel_event.set(); await interaction.response.send_message('🛑 Stopping before the next step.')
        @tree.command(name='bball-ban', description='Owner: take a player off every basketball board and slip not yet started', guild=g)
        async def ban(interaction, player: str, why: str = ''):
            await interaction.response.defer(thinking=True)
            if not is_owner(interaction): return await interaction.followup.send('Owner only.')
            await send_long(interaction.followup.send, await asyncio.to_thread(K.ban_text, player, why)); await self.run_rescore('ban')
        @tree.command(name='bball-unban', description='Owner: take a player off the banned list', guild=g)
        async def unban(interaction, player: str):
            await interaction.response.defer(thinking=True)
            if not is_owner(interaction): return await interaction.followup.send('Owner only.')
            await send_long(interaction.followup.send, await asyncio.to_thread(K.unban_text, player)); await self.run_rescore('unban')
        @tree.command(name='bball-h2h', description="Past meetings: a player v today's opponent, or 'Player A vs Player B'", guild=g)
        async def h2h(interaction, players: str):
            await interaction.response.defer(thinking=True)
            await send_long(interaction.followup.send, await asyncio.to_thread(K.h2h_text, players))
        @tree.command(name='bball-pnl', description='Paper P&L for the basketball test. Not the tennis ledger', guild=g)
        @app_commands.choices(view=[app_commands.Choice(name=n, value=n) for n in ('daily', 'week', 'month')])
        async def pnl(interaction, view: str = 'daily'):
            await interaction.response.defer(thinking=True)
            await send_long(interaction.followup.send, await asyncio.to_thread(K.pnl_text, view))
        @tree.command(name='bball-setkey', description='Owner: enter The Odds API key in a private box. Saved to secrets/, never shown', guild=g)
        async def setkey(interaction):
            if not is_owner(interaction): return await interaction.response.send_message('Owner only.', ephemeral=True)
            discord = self.discord
            class KeyBox(discord.ui.Modal, title='The Odds API key'):
                key = discord.ui.TextInput(label='Paste the key', style=discord.TextStyle.short, min_length=10, max_length=120)
                async def on_submit(box, inter):
                    await inter.response.defer(thinking=True, ephemeral=True)
                    res = await asyncio.to_thread(save_odds_api_key, str(box.key.value))
                    await inter.followup.send(res, ephemeral=True)
            await interaction.response.send_modal(KeyBox())

        discord = self.discord
        SPORTS = {'nfl': 'football/nfl', 'ncaaf': 'football/ncaaf', 'nhl': 'hockey/nhl', 'ncaab': 'basketball/ncaab', 'wnba': 'basketball/wnba', 'mlb': 'baseball/mlb', 'soccer': 'soccer', 'afl': 'afl', 'rugby': 'rugby'}
        @tree.command(name='bball-sportkey', description='Owner: paste another Apex sport bot token or Odds API key (private box)', guild=g)
        @discord.app_commands.describe(sport='Which Apex sport', what='bot token or odds api key')
        @discord.app_commands.choices(sport=[discord.app_commands.Choice(name=s.upper(), value=s) for s in SPORTS], what=[discord.app_commands.Choice(name='Discord bot token', value='discord_bot_token.txt'), discord.app_commands.Choice(name='The Odds API key', value='odds_api_key.txt'), discord.app_commands.Choice(name='TheOddsGap data key', value='theoddsgap_key.txt')])
        async def sportkey(interaction, sport: discord.app_commands.Choice[str], what: discord.app_commands.Choice[str]):
            if not is_owner(interaction): return await interaction.response.send_message('Owner only.', ephemeral=True)
            folder = os.path.join(os.path.expanduser('~/ApexSports'), SPORTS[sport.value], 'secrets'); fname = what.value
            class SportKeyBox(discord.ui.Modal, title='%s %s' % (sport.name, 'bot token' if 'discord' in fname else 'TheOddsGap key' if 'oddsgap' in fname else 'Odds API key')):
                key = discord.ui.TextInput(label='Paste it', style=discord.TextStyle.short, min_length=10, max_length=120)
                async def on_submit(box, inter):
                    await inter.response.defer(thinking=True, ephemeral=True); k = str(box.key.value).strip()
                    if not k or ' ' in k: return await inter.followup.send('That does not look like a key. Nothing saved.', ephemeral=True)
                    def save():
                        os.makedirs(folder, exist_ok=True); fp = os.path.join(folder, fname)
                        if os.path.exists(fp): os.replace(fp, fp + '.bak_' + dt.datetime.now(SB.CT).strftime('%Y%m%d_%H%M%S'))
                        with open(fp, 'w') as f: f.write(k + '\n')
                        os.chmod(fp, 0o600)
                    await asyncio.to_thread(save); log('[SportKey] %s saved for %s' % (fname, sport.value))
                    link = ''
                    if 'discord' in fname:
                        try:
                            import base64; seg = k.split('.')[0]; app_id = base64.b64decode(seg + '=' * (-len(seg) % 4)).decode()
                            if app_id.isdigit(): link = '\n\nNow add it to this server, tap: https://discord.com/oauth2/authorize?client_id=%s&scope=bot%%20applications.commands&permissions=117776' % app_id
                        except Exception: link = ''
                    await inter.followup.send('🔑 Saved to Apex %s. %s%s' % (sport.name, 'Its bot starts within a minute and makes its own channels once it is in the server.' if 'discord' in fname else ('Saved for the room test. Nothing live uses it.' if 'oddsgap' in fname else 'Its book-line pulls use it from the next scheduled pull.'), link), ephemeral=True)
            await interaction.response.send_modal(SportKeyBox())
    async def post(self, name, text):
        ch = self.client.get_channel(self.channels.get(name) or 0)
        if ch is None: log('NOT POSTED no channel #%s: %s' % (name, text[:200])); return False
        if name == 'bball-alerts' and getattr(ch, 'guild', None): text = '<@%d> ' % ch.guild.owner_id + text   # his 'Go alert pings' 11/5
        try:
            for p in K.chunks(text)[:8]: await ch.send(p)
            return True
        except Exception as e: log('NOT POSTED #%s %s: %s' % (name, type(e).__name__, text[:200])); return False
    async def alert(self, text):
        log('ALERT ' + text); await self.post('bball-alerts', '⚠️ ' + text + '\n' + K.FOOT)
    async def run_rescore(self, trigger):
        async with self.job:
            t0 = dt.datetime.now().timestamp()   # APEX-FETCHDETAIL-2026-11-13
            try: s = await asyncio.to_thread(P.rescore, trigger)
            except P.Cancelled: s = dict(cancelled=True, no_lines=True)
            except Exception as e:
                log(traceback.format_exc()); await self.alert('Scoring failed: %s: %s' % (type(e).__name__, e)); return dict(no_lines=True, cancelled=True)
            self.state['last_sig'] = await asyncio.to_thread(SB.collector_signature); save_state(self.state)
            if s.get('cancelled'): await self.post('bball-system', '🛑 Re-score stopped by /bball-cancel. Nothing saved.'); return s
            if s['no_lines']: await self.post('bball-system', '🧪 Re-score: no saved lines yet.'); return s
            s['report'] = await asyncio.to_thread(K.fetch_report, s, trigger, t0)   # APEX-FETCHDETAIL-2026-11-13: NEW PROPS SCORED card, old line is the fallback
            if s['report']: await self.post('bball-system', s['report'])
            else: await self.post('bball-system', '🧪 Scored %d lines not started: %d with a number, %d at %d+. Lines saved %s. (%s)' % (s['n_lines'], s['n_scored'], s['n_70'], P.FLOOR, K._ct(s['lines_saved_at'], '%-m/%-d %-I:%M %p CT'), trigger))
            if s['bad_rows']: await self.alert('%d saved line rows could not be read.' % s['bad_rows'])
            if self.state.get('last_mains') != s['mains']:
                cur = await asyncio.to_thread(P.current)
                for b in ('top3', 'elite5', 'elite6', 'top10', 'bestgoblin', 'bestless', 'beststandard', 'bestdemon'):
                    if (self.state.get('last_mains') or {}).get(b) != s['mains'].get(b): await self.post('bball-picks', K.board_text(b, cur))
                self.state['last_mains'] = s['mains']; save_state(self.state)
            await self.post_new_slips(); return s
    async def post_new_slips(self):
        db = T.connect()
        try:
            for x in db.execute("select * from slips where status='pending'").fetchall():
                if x['posted_sig'] != x['legs_json'] and await self.post('bball-slips', K.slip_card(db, x)):
                    db.execute('update slips set posted_sig=? where id=?', (x['legs_json'], x['id'])); db.commit()
        finally: db.close()
    async def run_grade(self):
        async with self.job:
            try: g = await asyncio.to_thread(P.grade)
            except Exception as e:
                log(traceback.format_exc()); await self.alert('Grading failed: %s: %s. Will try again tomorrow.' % (type(e).__name__, e)); return
            x = g['graded']; await self.post('bball-system', '🧪 Graded: %d won, %d lost, %d push, %d void, %d waiting on a final, %d other league with no grader. ESPN: %d new box scores, %d failed.' % (x['win'], x['loss'], x['push'], x['void'], x['open'], x['other_league'], g['espn']['new_box'], g['espn']['failed']))
            if g['stuck']: await self.alert('%d NBA picks are still open more than 3 days after their game.' % g['stuck'])
            db = T.connect()
            try:
                for s in db.execute("select * from slips where status!='pending' and settled_posted=0").fetchall():
                    if await self.post('bball-slips-pnl', K.slip_card(db, s)): db.execute('update slips set settled_posted=1 where id=?', (s['id'],)); db.commit()
            finally: db.close()
            await self.post('bball-pnl', K.pnl_text('daily')); await self.post('bball-learning-channel', K.learning_text())
    async def keep_collectors(self, now):
        """Kept for old callers. The watchdog now runs on its own 60 s loop (watchdog_loop)."""
        return
    async def watchdog_once(self):
        """One check of every collector: heartbeat, last activity, failure counter, restart when dead. Writes logs/watchdog.json."""
        try: st = json.load(open(WATCHDOG_STATE))
        except (OSError, ValueError): st = {}
        now = dt.datetime.now(dt.timezone.utc); nowi = now.isoformat(timespec='seconds')
        prev = st.get('_last_check')
        if prev:
            gap = (now - dt.datetime.fromisoformat(prev)).total_seconds()
            if gap > 150: wd_log('check was late: %d s since the last one' % gap)
        st['_last_check'] = nowi
        for name, (pidfile, args) in COLLECTORS.items():
            e = st.setdefault(name, dict(failures=0, restarts=0))
            alive = await asyncio.to_thread(collector_alive, pidfile, args[0])
            e.update(heartbeat=nowi, alive=alive, pid=collector_pid(pidfile), last_activity=last_activity(name))
            if alive:
                if e.get('failures'): wd_log('%s healthy again after %d failed check(s)' % (name, e['failures']))
                e['failures'] = 0; e['last_ok'] = nowi; continue
            e['failures'] = e.get('failures', 0) + 1
            lr = e.get('last_restart')
            if lr and (now - dt.datetime.fromisoformat(lr)).total_seconds() < 90:
                wd_log('%s still down %d s after a restart, waiting (failure %d)' % (name, (now - dt.datetime.fromisoformat(lr)).total_seconds(), e['failures'])); continue
            try:
                pid = await asyncio.to_thread(start_collector, name); e['restarts'] = e.get('restarts', 0) + 1; e['last_restart'] = nowi; e['pid'] = pid
                wd_log('%s was not running (failure %d), restarted pid %d' % (name, e['failures'], pid)); log('restarted %s pid %d' % (name, pid))
                await self.post('bball-system', '🔁 %s was not running, started it again (pid %d). %s' % (name, pid, K.FOOT))
            except Exception as ex:
                wd_log('%s restart FAILED: %s: %s' % (name, type(ex).__name__, ex)); await self.alert('Could not start the %s: %s' % (name, type(ex).__name__))
            if e['failures'] == 3: await self.alert('The %s failed 3 checks in a row. Check logs/watchdog.log.' % name)
        tmp = WATCHDOG_STATE + '.tmp'; json.dump(st, open(tmp, 'w'), indent=1); os.replace(tmp, WATCHDOG_STATE)
    async def watchdog_loop(self):
        wd_log('watchdog started (every 60 s)')
        while True:
            try: await self.watchdog_once()
            except Exception as ex: wd_log('watchdog check failed: %s: %s' % (type(ex).__name__, ex))
            await asyncio.sleep(60)
    async def tick(self):
        """Once a minute: new collector file, 4 AM grade, 9 AM status, collector silence, collectors alive. Missed times run on the next start the same day."""
        ann = os.path.join(ROOT, 'logs', 'announce.txt')          # one-off notices from the autostart (sleep / wake), posted once
        if os.path.exists(ann):
            txt = open(ann).read().strip(); os.remove(ann)
            if txt: await self.post('bball-system', txt)
        now = dt.datetime.now(SB.CT); today = now.date().isoformat(); sig = await asyncio.to_thread(SB.collector_signature); await self.keep_collectors(now)
        if sig != self.state.get('last_sig'):
            if sig != self.pending_sig: self.pending_sig, self.pending_since = sig, now   # the collector waits 90 s between leagues, so wait until the file stops growing
            elif (now - self.pending_since).total_seconds() >= SETTLE_MINUTES * 60 and not self.job.locked(): await self.run_rescore('new lines')
        if now.hour >= GRADE_HOUR and self.state.get('graded') != today:
            self.state['graded'] = today; save_state(self.state); await self.run_grade()
        if now.hour >= STATUS_HOUR and self.state.get('status') != today:
            line = await asyncio.to_thread(K.status_line)
            if await self.post('bball-general', line): self.state['status'] = today; save_state(self.state)
        pull = await asyncio.to_thread(P.last_collector_pull); silent = pull is None or (dt.datetime.now(dt.timezone.utc) - pull).total_seconds() > COLLECTOR_SILENT_HOURS * 3600
        if silent and not self.state.get('silence_alerted'):
            self.state['silence_alerted'] = True; save_state(self.state); await self.alert(('Line collector has not finished a pull yet.' if pull is None else 'Line collector has not finished a pull in %d hours.' % COLLECTOR_SILENT_HOURS) + ' Boards are getting old. Check logs/line_collector.log.')
        elif not silent and self.state.get('silence_alerted'):
            self.state['silence_alerted'] = False; save_state(self.state); await self.post('bball-alerts', '✅ Line collector is pulling again.\n' + K.FOOT)
    async def loop(self):
        while True:
            try: await self.tick()
            except Exception as e:
                log(traceback.format_exc())
                try: await self.alert('Bot job failed: %s: %s' % (type(e).__name__, e))
                except Exception: pass
            await asyncio.sleep(60)
    async def on_ready(self):
        if self.ready_once: return
        self.ready_once = True; log('logged in as %s' % self.client.user); guild = self.client.get_guild(GUILD_ID)
        if guild is None: log('NOT IN THE SERVER. Invite the bot to guild %s (client id %s).' % (GUILD_ID, CLIENT_ID)); return
        self.channels, failed = await ensure_channels(guild)
        if failed: log('could not create channels: %s. The bot needs Manage Channels.' % failed)
        try: log('synced %d commands' % len(await self.tree.sync(guild=self.guild_obj)))
        except Exception as e: log('command sync failed %s: %s' % (type(e).__name__, e))
        await self.post('bball-system', '🧪 Apex Basketball bot started. %s' % K.FOOT)
        if failed: await self.alert('Could not create: %s' % ', '.join(failed))
        self.client.loop.create_task(self.loop()); self.client.loop.create_task(self.watchdog_loop())
def main():
    os.makedirs(os.path.dirname(LOCK_FILE), exist_ok=True); lock = open(LOCK_FILE, 'w')
    try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError: print('Apex Basketball bot is already running.'); return EXIT_LOCKED
    token = load_token()
    if not token: print('No Discord token at secrets/discord_bot_token.txt. Bot not started. Add it with /setkey Basketball bot, then run discord/start_bot.sh.'); return EXIT_NO_TOKEN
    import discord
    async def runner():   # the Lock and Client must be made inside the running loop on Python 3.9
        b = Bot()
        async with b.client: await b.client.start(token)
    try: asyncio.run(runner())
    except discord.LoginFailure: print('Discord refused the token in secrets/discord_bot_token.txt. Bot not started.'); return EXIT_BAD_TOKEN
    return 0
if __name__ == '__main__': sys.exit(main())

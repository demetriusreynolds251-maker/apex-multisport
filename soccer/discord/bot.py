#!/usr/bin/env python3
"""Discord bot for this sport only. 🧪 TEST. Own token (secrets/discord_bot_token.txt), own channels (<prefix>-picks, -alerts, -general,
-learning-channel, -system, -pnl, -slips), own commands (/<prefix>-fetch, -top3, -elite5, -elite6, -top10, -bestgoblin, -beststandard, -bestdemon,
-backups, -picks, -allprops, -pnl, -ban, -unban, -status, -setkey). Posts whatever the scheduler drops in cache/outbox within 10 seconds and keeps the
scheduler alive. Never imports from another sport, Apex Tennis or Apex Basketball. Start with discord/start.sh."""
import asyncio, datetime as dt, fcntl, json, os, subprocess, sys, traceback
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, ROOT)
import common as CM
from database import db as DBM
K = CM.dmod("cards"); PO = CM.dmod("post")
from picks import pipeline as P
from tracking import boards as TB

C = CM.cfg(); PREFIX = C['prefix']; GUILD_ID = C['discord']['guild_id']; CATEGORY = C['discord'].get('category') or 'Apex %s 🧪' % C['name']
TOKEN_FILE = os.path.join(CM.SECRETS, 'discord_bot_token.txt'); CHANNEL_FILE = os.path.join(CM.CACHE, 'discord_channels.json'); LOCK_FILE = os.path.join(CM.LOGS, 'bot.lock')
CHANNELS = {'picks': '🧪 TEST boards and picks', 'alerts': '🧪 TEST problems only', 'general': '🧪 TEST one status line a day', 'learning-channel': '🧪 TEST is the number honest', 'system': '🧪 TEST every run', 'pnl': '🧪 TEST results, paper only', 'slips': '🧪 TEST slip ideas'}
EXIT_NO_TOKEN, EXIT_BAD_TOKEN, EXIT_LOCKED = 3, 4, 5
def log(m): print('%s %s' % (CM.now_ct().strftime('%m/%d %H:%M:%S'), m), flush=True)
def chunks(text, n=1900):
    out, cur = [], ''
    for line in text.split('\n'):
        if len(cur) + len(line) + 1 > n: out.append(cur); cur = ''
        cur += line + '\n'
    if cur.strip(): out.append(cur)
    return out or ['(empty)']
def scheduler_alive():
    try: os.kill(int(open(os.path.join(CM.LOGS, 'scheduler.pid')).read().strip()), 0); return True
    except (OSError, ValueError): return False
def start_scheduler():
    out = open(os.path.join(CM.LOGS, 'scheduler.out'), 'a')
    return subprocess.Popen([sys.executable, os.path.join(ROOT, 'scheduler', 'scheduler.py'), '--loop'], cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, start_new_session=True).pid
def is_owner(i): return i.guild is not None and i.guild_id == GUILD_ID and i.user.id == i.guild.owner_id

def save_odds_key(k):
    import urllib.request, urllib.error, urllib.parse
    k = k.strip()
    if not k or ' ' in k or len(k) < 10: return 'That does not look like a key. Nothing saved.'
    try:
        with urllib.request.urlopen(urllib.request.Request('https://api.the-odds-api.com/v4/sports?' + urllib.parse.urlencode({'apiKey': k}), headers={'User-Agent': 'Apex/1.0'}), timeout=30) as r: left = r.headers.get('x-requests-remaining')
    except urllib.error.HTTPError as e: return 'The Odds API refused the key (HTTP %s). Nothing saved.' % e.code
    except Exception as e: return 'Could not reach The Odds API (%s). Nothing saved.' % type(e).__name__
    p = os.path.join(CM.SECRETS, 'odds_api_key.txt'); os.makedirs(CM.SECRETS, exist_ok=True)
    with open(p, 'w') as f: f.write(k + '\n')
    os.chmod(p, 0o600); return '🔑 Odds API key saved and tested. Credits left: %s.' % left

def latest():
    s = CM.read_json(os.path.join(CM.CACHE, 'latest_scored.json'), {}) or {}
    if not s.get('rows'): return None
    from rules import rules as RU
    db = DBM.connect(); inj = P.latest_injuries(db); banned = {r[0] for r in db.execute('select player_norm from bans')}
    rows = s['rows']
    for r in rows: r['game_key'] = (frozenset([r.get('team') or '?', r.get('opponent') or '?']), r['game_date'])
    s['boards'] = RU.build_boards(rows, inj, banned); s['mains'] = {b: [r['pick_key'] for r in d['main']] for b, d in s['boards'].items()}; return s

class Bot:
    def __init__(self, discord):
        self.discord = discord; intents = discord.Intents.default(); self.client = discord.Client(intents=intents); self.tree = discord.app_commands.CommandTree(self.client)
        self.channels = {}; self.ready = False; self.commands()
        @self.client.event
        async def on_ready():
            if self.ready: return
            self.ready = True; guild = self.client.get_guild(GUILD_ID); log('logged in as %s' % self.client.user)
            if guild is None: log('bot is not in guild %s' % GUILD_ID); return
            await self.ensure_channels(guild)
            try: await self.tree.sync(guild=discord.Object(id=GUILD_ID)); log('synced commands')
            except Exception as e: log('command sync failed: %s' % e)
            await self.post('system', '🟢 %s bot started. Commands: /%s-fetch, /%s-top3, /%s-elite6, /%s-picks, /%s-pnl, /%s-boards. %s' % (C['name'], PREFIX, PREFIX, PREFIX, PREFIX, PREFIX, PREFIX, K.foot()))
            self.client.loop.create_task(self.outbox_loop()); self.client.loop.create_task(self.keepalive_loop())
    async def ensure_channels(self, guild):
        saved = CM.read_json(CHANNEL_FILE, {}) or {}; have = {c.name: c for c in guild.text_channels}; byid = {c.id: c for c in guild.text_channels}; cat = None
        for key, topic in CHANNELS.items():
            name = '%s-%s' % (PREFIX, key); ch = byid.get(saved.get(key)) or have.get(name)
            if ch is None:
                try:
                    if cat is None: cat = next((c for c in guild.categories if c.name == CATEGORY), None) or await guild.create_category(CATEGORY)
                    ch = await guild.create_text_channel(name, category=cat, topic=topic, reason='Apex %s test channels' % C['name'])
                except Exception as e: log('could not create #%s: %s' % (name, type(e).__name__)); continue
            self.channels[key] = ch.id
        CM.write_json(CHANNEL_FILE, self.channels)
    async def post(self, key, text):
        if key == 'learning': key = 'learning-channel'   # APEX-LEARNKEY-2026-11-08: posts said 'learning', the channel is 'learning-channel' (retried every 10 s forever)
        ch = self.client.get_channel(self.channels.get(key) or 0)
        if ch is None: log('NOT POSTED no channel %s: %s' % (key, text[:120])); return False
        if key == 'alerts' and getattr(ch, 'guild', None): text = '<@%d> ' % ch.guild.owner_id + text   # his 'Go alert pings' 11/5: alerts always buzz the phone, nothing else does
        try:
            for p in chunks(text)[:10]: await ch.send(p)
            return True
        except Exception as e: log('NOT POSTED %s %s' % (key, type(e).__name__)); return False
    async def outbox_loop(self):
        while True:
            try:
                for fn in sorted(os.listdir(PO.OUTBOX)) if os.path.isdir(PO.OUTBOX) else []:
                    p = os.path.join(PO.OUTBOX, fn); m = CM.read_json(p, None)
                    if m and await self.post(m['channel'], m['text']): os.remove(p)
                    elif m is None: os.remove(p)
                    else: break
            except Exception: log(traceback.format_exc())
            await asyncio.sleep(10)
    async def keepalive_loop(self):
        while True:
            try:
                if not scheduler_alive(): pid = await asyncio.to_thread(start_scheduler); await self.post('system', '🔁 scheduler was not running, started it again (pid %d).' % pid)
            except Exception as e: log('keepalive: %s' % e)
            await asyncio.sleep(300)
    def commands(self):
        discord = self.discord; tree = self.tree; g = discord.Object(id=GUILD_ID)
        async def send(inter, text):
            for p in chunks(text)[:10]: await inter.followup.send(p)
        async def _fresh(inter):
            # APEX-BOARDREFRESH-2026-11-12 (owner: "Whenever I run a board I want everything refresh"): old lines are read again before any board shows
            try:
                from scheduler import refresh as RF
                if not RF.needed(): return
                await inter.followup.send('🔄 Lines were last read %s ago. Reading PrizePicks again first so nothing pulled or moved shows up. Usually under a minute.' % RF._ago(RF.age_min()))
                r = await asyncio.to_thread(RF.run)
                if r.get('note'): await inter.followup.send('⚠️ ' + r['note'])
            except Exception: log('refresh: %s' % traceback.format_exc())
        def board_cmd(name, board):
            @tree.command(name='%s-%s' % (PREFIX, name), description='%s %s board' % (C['name'], C['boards'][board]['title'].title()), guild=g)
            async def _cmd(interaction):
                await interaction.response.defer(thinking=True); await _fresh(interaction); s = await asyncio.to_thread(latest)
                await send(interaction, K.board_text(board, s['boards'][board], s) if s else 'Nothing scored yet. /%s-fetch first.' % PREFIX)
        for name, board in (('top3', 'top3'), ('elite5', 'elite5'), ('elite6', 'elite6'), ('top10', 'top10'), ('bestgoblin', 'bestgoblin'), ('beststandard', 'beststandard'), ('bestdemon', 'bestdemon')):
            if board in C['boards']: board_cmd(name, board)
        @tree.command(name='%s-fetch' % PREFIX, description='Pull PrizePicks + ESPN now, score, post changed boards', guild=g)
        async def fetch(interaction):
            # APEX-FETCHSUMMARY-2026-11-09 (owner, "go fetch summary"): Cancel button while it runs + the full breakdown after, like tennis /fetch
            await interaction.response.defer(thinking=True)
            from collectors import collector as CO
            import threading
            stop = threading.Event(); state = {'step': 'starting'}
            class CancelView(discord.ui.View):
                def __init__(s_): super().__init__(timeout=900)
                @discord.ui.button(label='🛑 Cancel fetch', style=discord.ButtonStyle.danger)
                async def cancel(s_, inter2, button):
                    stop.set(); button.disabled = True; button.label = 'Cancelling after: %s' % state['step']
                    await inter2.response.edit_message(view=s_)
            view = CancelView()
            try: msg = await interaction.followup.send('📡 **/%s-fetch** — pulling PrizePicks and ESPN, scoring every line, posting changed boards. This can take a few minutes. The full breakdown posts here and in #%s-system when it finishes.\nPress **Cancel fetch** to stop after the current step.' % (PREFIX, PREFIX), view=view, wait=True)
            except Exception: msg = None
            def run():
                t0 = __import__('time').time(); db = DBM.connect()   # APEX-FETCHDETAIL-2026-11-13
                state['step'] = 'PrizePicks pull'; CO.pull_pp(db)
                if stop.is_set(): return None
                state['step'] = 'ESPN pull'; CO.pull_espn(db)
                if stop.is_set(): return None
                state['step'] = 'scoring'; s = P.score(db, trigger='fetch'); st = CM.read_json(os.path.join(CM.CACHE, 'scheduler_state.json'), {}) or {}
                state['step'] = 'posting boards'
                state['report'] = K.fetch_report(s, 'fetch', t0=t0) + '\n\n' + K.fetch_summary(s, 'fetch')   # APEX-FETCHDETAIL-2026-11-13: NEW PROPS SCORED card, then the full breakdown
                PO.post('system', state['report'], force=True); st['last_mains'] = PO.post_boards(s, st.get('last_mains')); st['last_pp'] = st['last_pp_ok'] = CM.iso(); CM.write_json(os.path.join(CM.CACHE, 'scheduler_state.json'), st); return s
            try: s = await asyncio.to_thread(run)
            except Exception as e: s = None; log('fetch: %s' % traceback.format_exc()); await send(interaction, '⚠️ Fetch failed during %s: %s. Boards unchanged.' % (state['step'], type(e).__name__)); return
            view.stop()
            for ch in view.children: ch.disabled = True
            if msg is not None:
                try: await msg.edit(view=view)
                except Exception: pass
            if s is None: return await send(interaction, '🛑 Fetch cancelled after %s. Boards unchanged.' % state['step'])
            await send(interaction, state.get('report') or K.fetch_summary(s, 'fetch'))   # APEX-FETCHDETAIL-2026-11-13
        @tree.command(name='%s-lesswatch' % PREFIX, description='Shots LESS watch: every regular-line Shots LESS, who starts or sits, true number', guild=g)   # APEX-LESSWATCH-2026-11-12
        async def lesswatch(interaction):
            await interaction.response.defer(thinking=True); await _fresh(interaction); s = await asyncio.to_thread(latest)
            await send(interaction, K.less_watch(s) if s else 'Nothing scored yet. /%s-fetch first.' % PREFIX)
        @tree.command(name='%s-picks' % PREFIX, description='Tier A / B / C picks with the full breakdown', guild=g)
        async def picks(interaction):
            await interaction.response.defer(thinking=True); await _fresh(interaction); s = await asyncio.to_thread(latest)
            await send(interaction, K.tier_report(s) if s else 'Nothing scored yet.')
        @tree.command(name='%s-backups' % PREFIX, description='Backups: everything else above the floor, in rank order', guild=g)
        async def backups(interaction):
            await interaction.response.defer(thinking=True); await _fresh(interaction); s = await asyncio.to_thread(latest)
            if not s: return await send(interaction, 'Nothing scored yet.')
            d = s['boards']['top3']; await send(interaction, '\n'.join(['%s **BACKUPS** %d+' % (C['emoji'], d['floor'])] + [K.RULE + '\n' + K.pick_card(r, i, rows=s.get('rows')) for i, r in enumerate(d['backups'], 1)] + [K.foot()]) if d['backups'] else 'No backups above %d right now.' % d['floor'])
        @tree.command(name='%s-allprops' % PREFIX, description='Every scored line, one per row, by confidence', guild=g)
        async def allprops(interaction):
            await interaction.response.defer(thinking=True); await _fresh(interaction); s = await asyncio.to_thread(latest)
            if not s: return await send(interaction, 'Nothing scored yet.')
            rows = sorted(s['rows'], key=lambda r: -r['confidence'])[:60]
            await send(interaction, '\n'.join('%s %s %s %g %s %s · %.0f%% %s%s' % (r['tier'], r['player'], r['label'], r['line'], r['side'], K.KIND.get(r['kind'], r['kind']), r['confidence'], '⚡%+d' % r['edge_score'], ' ⚠ ' + r['no_play'] if r.get('no_play') else '') for r in rows))
        @tree.command(name='%s-pnl' % PREFIX, description='Results: daily, weekly, monthly or season', guild=g)
        @discord.app_commands.describe(period='daily, weekly, monthly or season')
        async def pnl(interaction, period: str = 'daily'):
            await interaction.response.defer(thinking=True)
            from reports import report as RP
            await send(interaction, await asyncio.to_thread(RP.build, period if period in ('daily', 'weekly', 'monthly', 'season') else 'daily'))
        @tree.command(name='%s-boards' % PREFIX, description='Whole-board record: days won and lost per board, last 7 days by name', guild=g)
        async def boards_cmd(interaction):
            await interaction.response.defer(thinking=True)
            await send(interaction, await asyncio.to_thread(TB.boards_text, 7))
        @tree.command(name='%s-pphealth' % PREFIX, description='PrizePicks calls and slow-downs, today and yesterday, all Apex sports', guild=g)
        async def pphealth(interaction):
            await interaction.response.defer(thinking=True)
            from collectors import collector as CO
            def run(): return CO.pp_health_line(CM.ct_date()) + '\n' + CO.pp_health_line() + '\n' + ('⏸ Shared pause on until %s.' % CM.fmt_ct(dt.datetime.fromtimestamp(float(CM.read_json(CM.SHARED_COOLDOWN, {}).get('until') or 0), dt.timezone.utc)) if CO.pp_paused() else '🟢 No pause on right now.')
            await send(interaction, await asyncio.to_thread(run))
        @tree.command(name='%s-status' % PREFIX, description='Collector, scheduler and line counts', guild=g)
        async def status(interaction):
            await interaction.response.defer(thinking=True)
            def st():
                db = DBM.connect(); n = db.execute('select count(*) from pp_lines where start > ?', (CM.iso(),)).fetchone()[0]; pg = db.execute('select count(*) from player_games').fetchone()[0]; pk = db.execute("select count(*) from picks where status!='open'").fetchone()[0]
                return '%s %s: scheduler %s · PrizePicks last pull %s · %d lines not started · %d player games of history · %d graded picks · Odds API credits %s' % (C['emoji'], C['name'], 'running' if scheduler_alive() else 'DOWN', CM.fmt_ct(DBM.kv_get(db, 'pp_last_pull')) if DBM.kv_get(db, 'pp_last_pull') else 'never', n, pg, pk, DBM.kv_get(db, 'odds_api_credits_left', '?'))
            await send(interaction, await asyncio.to_thread(st))
        @tree.command(name='%s-ban' % PREFIX, description='Owner: keep a player off every board', guild=g)
        async def ban(interaction, player: str, why: str = ''):
            await interaction.response.defer(thinking=True)
            if not is_owner(interaction): return await interaction.followup.send('Owner only.')
            db = DBM.connect(); db.execute('insert or replace into bans values(?,?,?,?)', (CM.norm(player), player, why, CM.iso())); db.commit(); await interaction.followup.send('🚫 %s banned from every %s board. %s' % (player, C['name'], why))
        @tree.command(name='%s-unban' % PREFIX, description='Owner: allow a banned player again', guild=g)
        async def unban(interaction, player: str):
            await interaction.response.defer(thinking=True)
            if not is_owner(interaction): return await interaction.followup.send('Owner only.')
            db = DBM.connect(); db.execute('delete from bans where player_norm=?', (CM.norm(player),)); db.commit(); await interaction.followup.send('✅ %s allowed again.' % player)
        @tree.command(name='%s-setkey' % PREFIX, description='Owner: The Odds API key for this sport, private box', guild=g)
        async def setkey(interaction):
            if not is_owner(interaction): return await interaction.response.send_message('Owner only.', ephemeral=True)
            class KeyBox(discord.ui.Modal, title='The Odds API key (%s)' % C['name']):
                key = discord.ui.TextInput(label='Paste the key', style=discord.TextStyle.short, min_length=10, max_length=120)
                async def on_submit(box, inter):
                    await inter.response.defer(thinking=True, ephemeral=True); await inter.followup.send(await asyncio.to_thread(save_odds_key, str(box.key.value)), ephemeral=True)
            await interaction.response.send_modal(KeyBox())

def main():
    token = CM.secret('discord_bot_token.txt')
    if not token: print('No token at secrets/discord_bot_token.txt.'); return EXIT_NO_TOKEN
    os.makedirs(CM.LOGS, exist_ok=True); lock = open(LOCK_FILE, 'w')
    try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError: print('another copy is running'); return EXIT_LOCKED
    import discord
    bot = Bot(discord)
    try: bot.client.run(token, log_handler=None)
    except discord.LoginFailure: log('Discord refused the token'); return EXIT_BAD_TOKEN
    return 0

if __name__ == '__main__': sys.exit(main() or 0)

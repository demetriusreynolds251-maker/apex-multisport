#!/usr/bin/env python3
"""APEX LINE VAULT (owner, 11/9/2026: "I want all PrizePicks lines saved and stored
properly and neat professional with out messing up the call to PrizePicks").

One clean store of every PrizePicks line every Apex bot has saved, same columns for every sport.
Makes ZERO PrizePicks calls: it only READS what the bots already saved (read-only connections)
  tennis      ~/openclaw/data/props_db.sqlite
  team sports ~/ApexSports/<sport>/database/history.db  (pp_lines + box scores)
  NBA         ~/ApexSports/basketball/data/collected/*.jsonl + processed/bball_tracker.sqlite
and writes  ~/ApexSports/_shared/line_vault/line_vault.sqlite  (+ exports/*.csv.gz, + copy on the 2TB drive).

  python3 vault.py            build / update, export, copy
  python3 vault.py --status   one line for the morning #system card
Nothing here changes a board, a pick, or any bot. Undo: unload the com.apex.linevault LaunchAgent.
"""
import sqlite3, json, os, sys, glob, gzip, csv, shutil, datetime as dt, collections, traceback
from zoneinfo import ZoneInfo
HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser("~")
SPORTS_ROOT = os.path.join(HOME, "ApexSports")
TENNIS_DB = os.path.join(HOME, "openclaw", "data", "props_db.sqlite")
NBA_DIR = os.path.join(SPORTS_ROOT, "basketball", "data")
VAULT = os.path.join(HERE, "line_vault.sqlite")
EXPORTS = os.path.join(HERE, "exports")
STATE = os.path.join(HERE, "last_run.json")
DRIVE = "/Volumes/2TB Drive"
DRIVE_DIR = os.path.join(DRIVE, "Apex Line Vault")
KEEP_DRIVE_COPIES = 14
CT = ZoneInfo("America/Chicago")

SCHEMA = """
create table if not exists lines(
  line_key text primary key, sport text, league text, projection_id text,
  player text, team text, opponent text, home_team text, away_team text, game_id text,
  stat text, stat_code text, kind text, less_offered integer,
  line_first real, line_last real, line_at_start real, line_moves integer,
  start_utc text, game_date text, first_seen text, last_seen text, status_last text, promo integer,
  actual real, result text, more_won integer, less_won integer, graded_at text, graded_from text,
  source_store text, vault_updated text);
create index if not exists ix_lines_sport_date on lines(sport, game_date);
create index if not exists ix_lines_player on lines(player);
create table if not exists line_moves(
  line_key text, seen_at text, line real, kind text, status text,
  primary key(line_key, seen_at, line, kind));
create table if not exists vault_runs(run_at text, sport text, lines integer, graded integer, pending integer, new_lines integer, note text);
"""
COLS = ["line_key","sport","league","projection_id","player","team","opponent","home_team","away_team","game_id","stat","stat_code","kind","less_offered",
        "line_first","line_last","line_at_start","line_moves","start_utc","game_date","first_seen","last_seen","status_last","promo",
        "actual","result","more_won","less_won","graded_at","graded_from","source_store","vault_updated"]

def now(): return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
def ro(path): 
    c = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=30); c.row_factory = sqlite3.Row; return c
def to_utc(s):
    if not s: return None
    try:
        d = dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        if d.tzinfo is None: d = d.replace(tzinfo=dt.timezone.utc)
        return d.astimezone(dt.timezone.utc)
    except Exception: return None
def iso(d): return d.isoformat(timespec="seconds") if d else None
def ct_date(d): return d.astimezone(CT).date().isoformat() if d else None
def outcome(actual, line):
    if actual is None or line is None: return None
    return "push" if actual == line else ("more" if actual > line else "less")

def put(v, rows, moves):
    ts = now()
    for r in rows:
        r["vault_updated"] = ts
        r["less_offered"] = 1 if (r.get("kind") or "standard") == "standard" else 0
        res = r.get("result")
        r["more_won"] = 1 if res == "more" else 0 if res == "less" else None
        r["less_won"] = 1 if res == "less" else 0 if res == "more" else None
        v.execute("insert or replace into lines(%s) values(%s)" % (",".join(COLS), ",".join("?" * len(COLS))), [r.get(k) for k in COLS])
    v.executemany("insert or ignore into line_moves values(?,?,?,?,?)", moves)

# ------------------------------------------------------------------ tennis
def load_tennis(v):
    c = ro(TENNIS_DB); rows = []; moves = []
    for p in c.execute("select * from projections"):
        k = "tennis:%s" % p["projection_id"]; st = to_utc(p["start_utc"])
        res = p["result"] if p["result"] in ("more", "less", "push", "void") else ("pending" if p["result"] is None else str(p["result"]))
        rows.append(dict(line_key=k, sport="tennis", league="TENNIS", projection_id=str(p["projection_id"]), player=p["player"], team=None, opponent=p["opponent"],
                         home_team=None, away_team=None, game_id=p["game_id"] or p["pp_game_id"], stat=p["stat_type"], stat_code=p["category"], kind=p["odds_type"] or "standard",
                         line_first=p["line_first"], line_last=p["line_last"], line_at_start=p["line_at_start"], line_moves=p["line_changes"] or 0,
                         start_utc=iso(st), game_date=p["match_date"], first_seen=p["first_seen"], last_seen=p["last_seen"], status_last=p["status_last"], promo=p["is_promo"],
                         actual=p["actual"], result=res, graded_at=p["settled_ts"], graded_from="tennis settle (props_db)" if p["result"] else None,
                         source_store="openclaw/data/props_db.sqlite"))
        if p["line_first"] is not None: moves.append((k, p["first_seen"], p["line_first"], p["odds_type"] or "standard", "first seen"))
    kinds = {r["line_key"]: r["kind"] for r in rows}
    for ch in c.execute("select projection_id, ts, new from changes where field='line'"):
        k = "tennis:%s" % ch["projection_id"]
        try: moves.append((k, ch["ts"], float(ch["new"]), kinds.get(k, "standard"), "moved"))
        except Exception: pass
    put(v, rows, moves); return len(rows)

# ------------------------------------------------------------------ team sports (shared template)
def stat_value(cfg_stats, stats, stat):
    sc = cfg_stats.get(stat)
    if not sc: return None
    tot = 0.0
    for k in sc["formula"]:
        w = 1.0
        if isinstance(k, list): k, w = k
        x = stats.get(k)
        if x is None:
            a = sc.get("alt"); return float(stats[a]) if a and stats.get(a) is not None else None
        tot += w * float(x)
    return tot

# APEX-GRADEMORE-2026-11-09 (his "Go grade more stats"): PrizePicks stats the bots do not score yet but the saved
# box scores can answer. Vault only: no bot, board or pick reads this. Keyed by sport, then PrizePicks stat name (lower case).
# ("sum", keys) adds box-score numbers (a missing one counts 0 when the player has at least one of them);
# ("ratio", top, bottom, times) divides; ("dd",) is a double-double (1 = yes, 0 = no).
_FB = {"pass+rush+rec tds": ("sum", ["passing_tds", "rushing_tds", "receiving_tds"]),
       "completion percentage": ("ratio", "completions", "pass_attempts", 100.0),
       "rush yards per carry": ("ratio", "rushing_yards", "rushing_attempts", 1.0)}
EXTRA = {"nhl": {"sog": ("sum", ["shots"]), "goals allowed": ("sum", ["goals_against"]), "minutes": ("sum", ["toi"])},
         "ncaab": {"pra": ("sum", ["points", "rebounds", "assists"]), "3ptm": ("sum", ["threes"]), "blks+stls": ("sum", ["blocks", "steals"]), "double-double": ("dd",)},
         "wnba": {"pra": ("sum", ["points", "rebounds", "assists"]), "3ptm": ("sum", ["threes"]), "blks+stls": ("sum", ["blocks", "steals"]), "double-double": ("dd",)},
         "nfl": _FB, "ncaaf": _FB}

def extra_value(sport, stat_raw, stats):
    rule = (EXTRA.get(sport) or {}).get((stat_raw or "").strip().lower())
    if not rule: return None, False
    try:
        if rule[0] == "sum":
            have = [stats.get(k) for k in rule[1]]
            if all(x is None for x in have): return None, True
            return sum(float(x) for x in have if x is not None), True
        if rule[0] == "ratio":
            top, bot = stats.get(rule[1]), stats.get(rule[2])
            if top is None or not bot: return None, True
            return round(float(top) / float(bot) * rule[3], 2), True
        if rule[0] == "dd":
            vals = [stats.get(k) for k in ("points", "rebounds", "assists", "steals", "blocks")]
            if vals[0] is None: return None, True
            return 1.0 if sum(1 for x in vals if x is not None and float(x) >= 10) >= 2 else 0.0, True
    except Exception: pass
    return None, True

def sport_dirs():
    out = []
    for cfgp in glob.glob(os.path.join(SPORTS_ROOT, "*", "config", "sport.json")) + glob.glob(os.path.join(SPORTS_ROOT, "*", "*", "config", "sport.json")):
        d = os.path.dirname(os.path.dirname(cfgp))
        if "_shared" in d or not os.path.exists(os.path.join(d, "database", "history.db")): continue
        out.append(d)
    return sorted(out)

def load_sport(v, d):
    cfg = json.load(open(os.path.join(d, "config", "sport.json"))); sport = cfg.get("sport") or os.path.basename(d); cs = cfg.get("stats") or {}
    c = ro(os.path.join(d, "database", "history.db")); rel = os.path.relpath(os.path.join(d, "database", "history.db"), HOME)
    by = collections.defaultdict(list)
    for r in c.execute("select * from pp_lines order by first_seen"): by[r["projection_id"]].append(r)
    if not by: return 0
    dates = set()
    for rs in by.values():
        st = to_utc(rs[-1]["start"])
        if st:
            for off in (-1, 0, 1): dates.add((st.astimezone(CT).date() + dt.timedelta(days=off)).isoformat())
    games = collections.defaultdict(list); box = {}
    if dates:
        lo, hi = min(dates), max(dates)
        for g in c.execute("select * from games where game_date between ? and ? and source='espn'", (lo, hi)): games[g["game_date"]].append(g)
        # espn first (what the grader uses); other sources only fill keys espn lacks
        for pg in c.execute("select event_id, player_norm, stats_json, source from player_games where game_date between ? and ? order by case source when 'espn' then 0 else 1 end", (lo, hi)):
            try: st = json.loads(pg["stats_json"] or "{}")
            except Exception: st = {}
            cur = box.setdefault((str(pg["event_id"]), pg["player_norm"]), {})
            for kk, vv in st.items(): cur.setdefault(kk, vv)
    pidx = collections.defaultdict(list)
    for (ev, pn) in box: pidx[pn].append(ev)
    gby = {str(g["event_id"]): g for gs in games.values() for g in gs}
    rows = []; moves = []
    for pid, rs in by.items():
        last = max(rs, key=lambda r: r["last_seen"]); first = rs[0]; st = to_utc(last["start"]); k = "%s:%s" % (sport, pid)
        pre = [r for r in rs if st is None or (to_utc(r["first_seen"]) or st) < st]
        gd = ct_date(st)
        actual = None; res = "pending"; gfrom = None
        g = None
        if gd:
            cand = [gd] + [(dt.date.fromisoformat(gd) + dt.timedelta(days=o)).isoformat() for o in (-1, 1)]
            for day in cand:
                for x in games.get(day, []):
                    if last["team"] and last["team"] in (x["home"], x["away"]): g = x; break
                if g: break
            if not g:
                for ev in pidx.get(last["player_norm"], []):
                    x = gby.get(ev)
                    if x and x["game_date"] in cand: g = x; break
        if g and g["final"] and g["box_saved"]:
            stt = box.get((str(g["event_id"]), last["player_norm"]))
            gfrom = "box score %s" % g["event_id"]
            if stt is None or (not stt.get("_played") and not any(vv for kk, vv in stt.items() if kk != "_played")): res = "void"
            elif not last["stat"] or last["stat"] not in cs:
                actual, known = extra_value(sport, last["stat_raw"], stt)
                if not known: res = "not graded (stat not in Apex yet)"
                else:
                    res = outcome(actual, last["line"] if not pre else pre[-1]["line"]) or "void"; gfrom += " (vault formula)"
            else:
                actual = stat_value(cs, stt, last["stat"])
                res = outcome(actual, last["line"] if not pre else pre[-1]["line"]) or "void"
        elif st and (dt.datetime.now(dt.timezone.utc) - st).days >= 3:
            res = "not graded (no box score found)"
        rows.append(dict(line_key=k, sport=sport, league=last["league"], projection_id=str(pid), player=last["player"], team=last["team"], opponent=last["opponent"],
                         home_team=last["home_abbr"], away_team=last["away_abbr"], game_id=last["game_id"], stat=last["stat_raw"], stat_code=last["stat"], kind=last["kind"] or "standard",
                         line_first=first["line"], line_last=last["line"], line_at_start=(pre[-1]["line"] if pre else None), line_moves=len({r["line"] for r in rs}) - 1,
                         start_utc=iso(st), game_date=gd, first_seen=first["first_seen"], last_seen=last["last_seen"], status_last=last["status"], promo=last["promo"],
                         actual=actual, result=res, graded_at=now() if res in ("more", "less", "push", "void") else None, graded_from=gfrom, source_store=rel))
        for r in rs: moves.append((k, r["first_seen"], r["line"], r["kind"] or "standard", r["status"]))
    put(v, rows, moves); return len(rows)

# ------------------------------------------------------------------ NBA (own layout)
# APEX-NBABOX-2026-11-09 (his "go save nba box scores"): full NBA box scores saved by basketball/code/espn_box_full.py
NBA_BOX = os.path.join(NBA_DIR, "processed", "nba_box_full.sqlite")
NBA_STATS = {"points": [("points", 1)], "rebounds": [("rebounds", 1)], "assists": [("assists", 1)],
             "pra": [("points", 1), ("rebounds", 1), ("assists", 1)], "pts+rebs+asts": [("points", 1), ("rebounds", 1), ("assists", 1)],
             "pts+rebs": [("points", 1), ("rebounds", 1)], "pts+asts": [("points", 1), ("assists", 1)], "rebs+asts": [("rebounds", 1), ("assists", 1)],
             "3ptm": [("threes", 1)], "3-pt made": [("threes", 1)], "steals": [("steals", 1)], "blocked shots": [("blocks", 1)],
             "blks+stls": [("blocks", 1), ("steals", 1)], "turnovers": [("turnovers", 1)], "fg made": [("fgm", 1)], "fg attempted": [("fga", 1)],
             "free throws made": [("ftm", 1)], "free throws attempted": [("fta", 1)],
             "fantasy score": [("points", 1), ("rebounds", 1.2), ("assists", 1.5), ("steals", 3), ("blocks", 3), ("turnovers", -1)]}
def _norm(s):
    import unicodedata, re
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[.'`]", "", s); s = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", s)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z ]", " ", s)).strip()
def nba_box():
    out = collections.defaultdict(list)
    if os.path.exists(NBA_BOX):
        for r in ro(NBA_BOX).execute("select * from player_box"): out[(r["game_date"], r["player_norm"])].append(r)
    return out
def nba_from_box(box, player, team, gd, stat):
    """(actual, result_or_None, found). result 'void' when the player did not play."""
    rows = box.get((gd, _norm(player))) or []
    if not rows: return None, None, False
    r = next((x for x in rows if x["team"] == team), rows[0])
    if not r["played"]: return None, "void", True
    key = (stat or "").strip().lower()
    f = NBA_STATS.get(key)
    if not f:
        try:
            j = json.loads(r["stats_json"] or "{}")
            pair = lambda k: [float(x) for x in str(j.get(k) or "").split("-")] if "-" in str(j.get(k) or "") else None
            num = lambda k: float(j[k]) if j.get(k) not in (None, "") else None
            three = pair("threePointFieldGoalsMade-threePointFieldGoalsAttempted")
            val = None
            if key == "2-pt made" and three and r["fgm"] is not None: val = r["fgm"] - three[0]
            elif key == "2-pt att" and three and r["fga"] is not None: val = r["fga"] - three[1]
            elif key == "3pta" and three: val = three[1]
            elif key == "ftm": val = r["ftm"]
            elif key == "fta": val = r["fta"]
            elif key == "personal fouls": val = num("fouls")
            elif key == "offensive rebounds": val = num("offensiveRebounds")
            elif key == "defensive rebounds": val = num("defensiveRebounds")
            elif key in ("double-double", "triple-double"):
                n = sum(1 for k in ("points", "rebounds", "assists", "steals", "blocks") if r[k] is not None and r[k] >= 10)
                val = 1.0 if n >= (2 if key == "double-double" else 3) else 0.0
            if val is not None: return round(float(val), 2), None, True
        except Exception: pass
        return None, "not graded (stat not in Apex yet)", True
    tot = 0.0
    for k, w in f:
        if r[k] is None: return None, None, True
        tot += w * float(r[k])
    return round(tot, 2), None, True

def load_nba(v, full):
    files = sorted(glob.glob(os.path.join(NBA_DIR, "collected", "*.jsonl")))
    if not full: files = files[-4:]
    agg = {}
    for f in files:
        with open(f) as fh:
            for ln in fh:
                try: r = json.loads(ln)
                except Exception: continue
                pid = str(r.get("projection_id") or "")
                if not pid: continue
                a = agg.get(pid)
                if a is None: a = agg[pid] = dict(first=r, last=r, seq=[])
                if not a["seq"] or a["seq"][-1][1] != r.get("line") or a["seq"][-1][2] != r.get("odds_type"):
                    a["seq"].append((r.get("seen"), r.get("line"), r.get("odds_type"), r.get("status")))
                a["last"] = r
    results = {}; same = {}
    tp = os.path.join(NBA_DIR, "processed", "bball_tracker.sqlite")
    if os.path.exists(tp):
        t = ro(tp)
        for r in t.execute("select pick_key, status, value, graded_at from results"):
            results.setdefault(r["pick_key"].split("|")[0], r)
        # a line the tracker never scored still has a result when another line on the same player + stat + game was graded
        for r in t.execute("select p.player, p.stat_raw, p.game_date, r.value, r.graded_at from picks p join results r on r.pick_key=p.pick_key where r.value is not null"):
            same.setdefault((r["player"], r["stat_raw"], r["game_date"]), (r["value"], r["graded_at"]))
    rows = []; moves = []; box = nba_box()
    for pid, a in agg.items():
        f, l = a["first"], a["last"]; st = to_utc(l.get("start")); k = "nba:%s" % pid
        old = v.execute("select line_first, first_seen from lines where line_key=?", (k,)).fetchone()
        pre = [s for s in a["seq"] if st is None or (to_utc(s[0]) or st) < st]
        line_ref = pre[-1][1] if pre else l.get("line")
        rr = results.get(pid); actual = None; res = "pending"; gat = None
        if rr is not None:
            gat = rr["graded_at"]
            if rr["value"] is not None: actual = float(rr["value"]); res = outcome(actual, line_ref)
            elif rr["status"] in ("void", "dnp"): res = "void"
            elif rr["status"] == "nostat": res = "not graded (stat not in Apex yet)"
            else: res = str(rr["status"])
        elif (l.get("player"), l.get("stat"), ct_date(st)) in same:
            val, gat = same[(l.get("player"), l.get("stat"), ct_date(st))]; actual = float(val); res = outcome(actual, line_ref)
        elif st and (dt.datetime.now(dt.timezone.utc) - st).days >= 3: res = "not graded (no box score found)"
        gsrc = "NBA tracker results" if actual is not None or rr is not None else None
        if actual is None and res != "void":
            bv, bres, found = nba_from_box(box, l.get("player"), l.get("team"), ct_date(st), l.get("stat"))
            if found:
                gsrc = "NBA full box score (vault formula)"; gat = gat or now()
                if bv is not None: actual = bv; res = outcome(actual, line_ref)
                elif bres: res = bres
        nm = v.execute("select count(distinct line) from line_moves where line_key=?", (k,)).fetchone()[0] if old else 0
        rows.append(dict(line_key=k, sport="nba", league=l.get("league") or "NBA", projection_id=pid, player=l.get("player"), team=l.get("team"), opponent=l.get("opponent"),
                         home_team=l.get("home"), away_team=l.get("away"), game_id=l.get("game_id"), stat=l.get("stat"), stat_code=l.get("stat"), kind=l.get("odds_type") or "standard",
                         line_first=(old[0] if old else f.get("line")), line_last=l.get("line"), line_at_start=(pre[-1][1] if pre else None), line_moves=0,
                         start_utc=iso(st), game_date=ct_date(st), first_seen=(old[1] if old else f.get("seen")), last_seen=l.get("seen"), status_last=l.get("status"), promo=1 if l.get("is_promo") else 0,
                         actual=actual, result=res, graded_at=gat, graded_from=gsrc, source_store="ApexSports/basketball/data/collected/*.jsonl"))
        for s in a["seq"]: moves.append((k, s[0], s[1], s[2] or "standard", s[3]))
    put(v, rows, moves)
    v.execute("update lines set line_moves=(select count(distinct line)-1 from line_moves m where m.line_key=lines.line_key) where sport='nba'")
    return len(rows)

# ------------------------------------------------------------------ export + copy
def export(v):
    os.makedirs(EXPORTS, exist_ok=True)
    for (sport,) in v.execute("select distinct sport from lines").fetchall():
        tmp = os.path.join(EXPORTS, "lines_%s.csv.gz.tmp" % sport)
        with gzip.open(tmp, "wt", newline="") as fh:
            w = csv.writer(fh); w.writerow(COLS)
            for r in v.execute("select %s from lines where sport=? order by game_date, start_utc, player, stat, line_last" % ",".join(COLS), (sport,)): w.writerow(r)
        os.replace(tmp, os.path.join(EXPORTS, "lines_%s.csv.gz" % sport))

def copy_to_drive():
    if not os.path.isdir(DRIVE): return "2TB drive not plugged in, copy skipped"
    try:
        os.makedirs(DRIVE_DIR, exist_ok=True)
        day = dt.datetime.now(CT).date().isoformat(); dst = os.path.join(DRIVE_DIR, "line_vault_%s.sqlite" % day)
        src = sqlite3.connect(VAULT); out = sqlite3.connect(dst + ".tmp"); src.backup(out); out.close(); src.close(); os.replace(dst + ".tmp", dst)
        shutil.copy2(os.path.join(HERE, "DATA_DICTIONARY.md"), os.path.join(DRIVE_DIR, "DATA_DICTIONARY.md"))
        old = sorted(glob.glob(os.path.join(DRIVE_DIR, "line_vault_*.sqlite")))[:-KEEP_DRIVE_COPIES]
        for f in old: os.remove(f)
        return "copied to 2TB drive"
    except Exception as e:
        return "2TB copy FAILED: %s" % type(e).__name__

# APEX-ONELINE-2026-11-12 (his go: "Proper fix all until it's no data poison"): PrizePicks lists some lines under two projection ids
# (twins, or a line re-issued under a new id). The vault keeps every id (it is the raw record), and marks the extra copies in
# copy_of so nothing counts one line twice. Readers add "copy_of is null". Re-marked on every build.
def mark_copies(v):
    if "copy_of" not in [r[1] for r in v.execute("pragma table_info(lines)")]: v.execute("alter table lines add column copy_of text")
    v.execute("update lines set copy_of=null where copy_of is not null"); n = 0; grp = collections.defaultdict(list)
    for k, sport, player, stat, kind, line, gd, opp, seen in v.execute("select line_key, sport, player, stat, kind, line_last, game_date, opponent, last_seen from lines where line_last is not null and game_date is not null"):
        grp[(sport, player, stat, kind, line, gd, opp if sport == "tennis" else None)].append((seen or "", k))
    for rows in grp.values():
        if len(rows) < 2: continue
        rows.sort(reverse=True)
        for _, k in rows[1:]: v.execute("update lines set copy_of=? where line_key=?", (rows[0][1], k)); n += 1
    v.commit(); return n

def build():
    first = not os.path.exists(VAULT)
    v = sqlite3.connect(VAULT, timeout=60); v.executescript(SCHEMA)
    before = dict(v.execute("select sport, count(*) from lines group by 1").fetchall()); errors = []
    def run(name, fn):
        try: fn(); v.commit()
        except Exception as e:
            v.rollback(); errors.append("%s: %s" % (name, type(e).__name__)); traceback.print_exc()
    run("tennis", lambda: load_tennis(v))
    for d in sport_dirs(): run(os.path.basename(d), lambda d=d: load_sport(v, d))
    run("nba", lambda: load_nba(v, first or "--full" in sys.argv))
    run("copies", lambda: mark_copies(v))
    ts = now(); per = {}
    for sport, n, g, p in v.execute("select sport, count(*), sum(result in ('more','less','push','void')), sum(result='pending') from lines group by 1").fetchall():
        per[sport] = dict(lines=n, graded=g or 0, pending=p or 0, new=n - before.get(sport, 0))
        v.execute("insert into vault_runs values(?,?,?,?,?,?,?)", (ts, sport, n, g or 0, p or 0, n - before.get(sport, 0), ""))
    v.commit()
    try: export(v)
    except Exception as e: errors.append("export: %s" % type(e).__name__)
    v.close()
    drive = copy_to_drive()
    state = dict(run_at=ts, sports=per, total=sum(x["lines"] for x in per.values()), new=sum(x["new"] for x in per.values()),
                 graded=sum(x["graded"] for x in per.values()), errors=errors, drive=drive, first_build=first)
    json.dump(state, open(STATE + ".tmp", "w"), indent=1); os.replace(STATE + ".tmp", STATE)
    return state

def status_line():
    """One line for the 9 AM #system card. Never raises. Silence is a bug: says so when the vault did not run."""
    try:
        s = json.load(open(STATE)); age = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(s["run_at"])).total_seconds() / 3600
        if age > 30: return "\U0001F5C4 Line vault: ⚠️ has not run in %d hours (last %s)" % (age, s["run_at"][:10])
        line = "\U0001F5C4 Line vault: %s PrizePicks lines saved across %d sports (+%s new), %s with a result. %s." % (
            format(s["total"], ","), len(s["sports"]), format(s["new"], ","), format(s["graded"], ","), s["drive"][0].upper() + s["drive"][1:])
        if s.get("errors"): line += " ⚠️ problems: " + "; ".join(s["errors"])
        try:   # APEX-NBARECHECK-2026-11-09: nightly NBA box-score recheck result
            r = json.load(open(os.path.join(NBA_DIR, "processed", "nba_recheck_last.json")))
            rage = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(r["run_at"])).total_seconds() / 3600
            if rage > 30: line += "\n🏀 NBA recheck: ⚠️ has not run in %d hours" % rage
            elif r["box_fixed"]: line += "\n🏀 NBA recheck: ESPN corrected %d box-score lines, %d grades fixed, %d flipped win/loss, %d slips changed." % (r["box_fixed"], r["picks_fixed"], r["flipped"], r["slips_changed"])
            else: line += "\n🏀 NBA recheck: %d games re-read, no corrections." % r["games"]
            if r.get("failed"): line += " ⚠️ %d games could not be read." % r["failed"]
        except Exception as e:
            line += "\n🏀 NBA recheck: ⚠️ no run on record (%s)" % type(e).__name__
        return line
    except Exception as e:
        return "\U0001F5C4 Line vault: ⚠️ no run on record (%s)" % type(e).__name__

if __name__ == "__main__":
    if "--status" in sys.argv: print(status_line())
    else:
        s = build(); print(json.dumps(s, indent=1)); print(status_line())

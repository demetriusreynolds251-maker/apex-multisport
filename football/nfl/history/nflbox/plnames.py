"""Step 4: prop_lines (graded PrizePicks history) used the old spellings; point them at the joined name so each line finds its player's games."""
import sqlite3, os
A = """a j dillon>aj dillon|andres borregales>andy borregales|bj hill>b j hill|c j allen>cj allen|cameron skattebo>cam skattebo|cameron ward>cam ward|camryn bynum>cam bynum|chauncey gardner johnson>c j gardner johnson|chigoziem okonkwo>chig okonkwo|chigoziem okonokwo>chig okonkwo|cor dale flott>cordale flott|d j moore>dj moore|d j reader>dj reader|d k metcalf>dk metcalf|dax hill>daxton hill|deaundre alford>dee alford|devon achane>de von achane|folorunso fatukasi>foley fatukasi|foye oluokun>foyesade oluokun|gabriel davis>gabe davis|gregory rousseau>greg rousseau|henry to o to o>henry to oto o|jeffery wilson>jeff wilson|john franklin meyers>john franklin myers|josh metellus>joshua metellus|josh palmer>joshua palmer|josh paschal>joshua paschal|joshua uche>josh uche|julius brents>juju brents|kamren curl>kam curl|keandre lambertsmith>keandre lambert smith|kenneth gainwell>kenny gainwell|kevin concepcion>kc concepcion|matt judon>matthew judon|matthew hibner>matt hibner|michael badgley>mike badgley|michael green>mike green|ogbonnia okoronkwo>ogbo okoronkwo|patrick surtain>pat surtain|prince umanmielen>princely umanmielen|rj mickens>r j mickens|scotty miller>scott miller|starling thomas>starling thomas v|t j parker>tj parker|trevon moehrig>tre von moehrig|ugochukwu amadi>ugo amadi"""
c = sqlite3.connect(os.path.expanduser('~/ApexSports/football/nfl/database/history.db')); c.execute('pragma busy_timeout=60000')
mv = dup = 0
for p in A.split('|'):
    o, n = p.split('>')
    cur = c.execute('update or ignore prop_lines set player_norm=? where player_norm=?', (n, o)); mv += cur.rowcount
    cur = c.execute('delete from prop_lines where player_norm=?', (o,)); dup += cur.rowcount     # same line already stored under the new name
c.commit()
print('prop lines renamed %d, exact duplicates dropped %d' % (mv, dup))
left = c.execute('select count(distinct player_norm), count(*) from prop_lines p where not exists (select 1 from player_games g where g.player_norm=p.player_norm)').fetchone()
print('prop lines whose player has no games in history: %d players, %d lines' % left)
print(c.execute('select group_concat(n) from (select p.player_norm||" "||count(*) n from prop_lines p where not exists (select 1 from player_games g where g.player_norm=p.player_norm) group by p.player_norm order by count(*) desc limit 20)').fetchone()[0])

#!/bin/bash
# Apex Sports + Apex Basketball autostart. launchd runs this at login and every 5 minutes (com.apex.sports.boot).
# Starts any sport loop (scheduler + Discord bot) or the basketball bot loop that is not running; the basketball bot's watchdog
# then starts its collectors. After a reboot (or any start) it writes and posts a startup health report. Tennis is never touched.
R="$HOME/ApexSports"; B="$R/_shared/boot"; LOG="$B/boot.log"; mkdir -p "$B"
ts() { date '+%m/%d %H:%M:%S'; }
alive() { [ -f "$[amount]" ] && kill -0 "$(cat "$[amount]")" 2>/dev/null; }
started=""
/usr/bin/python3 "$B/auto_sleep.py" >> "$B/launchd.log" 2>&1     # a sport with 7 empty PrizePicks days goes to sleep
for s in football/nfl football/ncaaf hockey/nhl basketball/ncaab basketball/wnba baseball/mlb soccer afl rugby; do
  if [ -f "$R/$s/INACTIVE" ]; then              # sport turned off on purpose (reason inside the file)
    WAKE=$(grep -o 'WAKE: [0-9-]*' "$R/$s/INACTIVE" | cut -d' ' -f2)
    if [ -n "$WAKE" ] && [ ! "$(date '+%Y-%m-%d')" \< "$WAKE" ]; then   # wake date reached: turn the sport back on
      mv "$R/$s/INACTIVE" "$R/$s/INACTIVE.woke_$(date '+%Y-%m-%d')"; echo "$(ts) $s wake date $WAKE reached, turning it back on" >> "$LOG"
      (cd "$R/$s" && /usr/bin/python3 -c "import sys; sys.path.insert(0,'.'); import common as CM; CM.dmod('post').post('system', '🌅 Season is near: this sport turned itself back on today. Collectors, grading and boards are running again.', force=True)") >/dev/null 2>&1
    else continue; fi
  fi
  if ! alive "$R/$s/logs/start.pid"; then
    (cd "$R/$s" && nohup /bin/bash discord/start.sh >/dev/null 2>&1 &); started="$started $s"; echo "$(ts) $s was not running, started it" >> "$LOG"
  fi
done
BW=""
if [ -f "$R/basketball/INACTIVE" ]; then
  WAKE=$(grep -o 'WAKE: [0-9-]*' "$R/basketball/INACTIVE" | cut -d' ' -f2)
  if [ -n "$WAKE" ] && [ ! "$(date '+%Y-%m-%d')" \< "$WAKE" ]; then
    mv "$R/basketball/INACTIVE" "$R/basketball/INACTIVE.woke_$(date '+%Y-%m-%d')"; echo "$(ts) basketball wake date $WAKE reached, turning it back on" >> "$LOG"
    echo "🌅 Season is near: Apex Basketball turned itself back on today. Collectors, grading and boards are running again." > "$R/basketball/logs/announce.txt"
  else BW=asleep; fi
fi
if [ -z "$BW" ] && ! alive "$R/basketball/logs/bball_bot.pid"; then
  (cd "$R/basketball" && nohup /bin/bash discord/start_bot.sh >/dev/null 2>&1 &); started="$started basketball"; echo "$(ts) basketball bot was not running, started it" >> "$LOG"
fi
BOOT=$(sysctl -n kern.boottime | sed -E 's/^\{ sec = ([0-9]+).*/\1/')
if [ "$(cat "$B/last_boot" 2>/dev/null)" != "$BOOT" ]; then
  echo "$BOOT" > "$B/last_boot"; echo "$(ts) first run since Mac start $(date -r "$BOOT" '+%m/%d %H:%M'), started:${started:- nothing (all running)}" >> "$LOG"
  (sleep 150; /usr/bin/python3 "$R/_shared/health/health.py" --post startup > "$B/startup_health.txt" 2>&1; echo "$(ts) startup health report posted" >> "$LOG") >/dev/null 2>&1 &
elif [ -n "$started" ]; then
  (sleep 150; /usr/bin/python3 "$R/_shared/health/health.py" --post restart > "$B/startup_health.txt" 2>&1; echo "$(ts) restart health report posted" >> "$LOG") >/dev/null 2>&1 &
fi
TODAY=$(date '+%Y-%m-%d')
if [ "$(date '+%H')" -ge 9 ] && [ "$(cat "$B/daily_health" 2>/dev/null)" != "$TODAY" ]; then
  echo "$TODAY" > "$B/daily_health"; /usr/bin/python3 "$R/_shared/health/health.py" --post daily > "$B/daily_health.txt" 2>&1; echo "$(ts) daily health report posted" >> "$LOG"
fi
# APEX-DATAALERTS-2026-11-08 (his go): nightly data check to #alerts at 9 PM, info only
if [ "$(date '+%H')" -ge 21 ] && [ "$(cat "$B/data_alerts" 2>/dev/null)" != "$TODAY" ]; then
  echo "$TODAY" > "$B/data_alerts"; /usr/bin/python3 "$R/_shared/health/data_alerts.py" > "$B/data_alerts.txt" 2>&1; echo "$(ts) data alerts posted" >> "$LOG"
fi
/usr/bin/python3 "$R/_shared/health/health.py" > /dev/null 2>&1   # refresh latest.md every 5 minutes
exit 0

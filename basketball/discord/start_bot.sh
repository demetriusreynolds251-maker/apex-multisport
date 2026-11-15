#!/bin/bash
# Keeps the Apex Basketball bot running. Waits for the token file, restarts after a crash.
# Start:  nohup basketball/discord/start_bot.sh >/dev/null 2>&1 &
# Stop:   kill "$(cat basketball/logs/bball_bot.pid)"   (the loop and the bot both stop)
# Log:    basketball/logs/bball_bot.log
# A Mac reboot stops this. Run the start line again after a reboot, until a LaunchAgent is pasted in.
ROOT="$(cd "$(dirname "$[amount]")/.." && pwd)"
LOG="$ROOT/logs/bball_bot.log"
PIDFILE="$ROOT/logs/bball_bot.pid"
TOKEN="$ROOT/secrets/discord_bot_token.txt"
mkdir -p "$ROOT/logs"
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "$(date '+%m/%d %H:%M:%S') already running, pid $(cat "$PIDFILE")" >> "$LOG"
  exit 0
fi
echo $$ > "$PIDFILE"
CHILD=""
trap '[ -n "$CHILD" ] && kill "$CHILD" 2>/dev/null; rm -f "$PIDFILE"; exit 0' TERM INT
said=0
while true; do
  if [ ! -s "$TOKEN" ]; then
    if [ "$said" = 0 ]; then echo "$(date '+%m/%d %H:%M:%S') waiting for secrets/discord_bot_token.txt" >> "$LOG"; said=1; fi
    sleep 60 & CHILD=$!; wait "$CHILD"; CHILD=""
    continue
  fi
  said=0
  echo "$(date '+%m/%d %H:%M:%S') starting bot" >> "$LOG"
  /usr/bin/python3 "$ROOT/discord/bot.py" >> "$LOG" 2>&1 &
  CHILD=$!
  wait "$CHILD"; code=$?; CHILD=""
  echo "$(date '+%m/%d %H:%M:%S') bot stopped, exit $code" >> "$LOG"
  case "$code" in
    4) pause=600 ;;  # Discord refused the token: do not hammer the login
    5) rm -f "$PIDFILE"; exit 0 ;;  # another copy holds the lock
    *) pause=60 ;;
  esac
  sleep "$pause" & CHILD=$!; wait "$CHILD"; CHILD=""
done

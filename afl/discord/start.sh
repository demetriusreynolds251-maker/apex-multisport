#!/bin/bash
# Keeps this sport's scheduler and Discord bot running. The scheduler runs even without a Discord token (posts wait in cache/outbox).
# Start:  nohup <sport>/discord/start.sh >/dev/null 2>&1 &      Stop: kill "$(cat <sport>/logs/start.pid)"      Log: <sport>/logs/bot.log
ROOT="$(cd "$(dirname "$[amount]")/.." && pwd)"; LOG="$ROOT/logs/bot.log"; PIDFILE="$ROOT/logs/start.pid"; TOKEN="$ROOT/secrets/discord_bot_token.txt"
mkdir -p "$ROOT/logs" "$ROOT/cache" "$ROOT/secrets"
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then echo "$(date '+%m/%d %H:%M:%S') already running" >> "$LOG"; exit 0; fi
echo $$ > "$PIDFILE"; CHILD=""; SCHED=""
trap '[ -n "$CHILD" ] && kill "$CHILD" 2>/dev/null; [ -n "$SCHED" ] && kill "$SCHED" 2>/dev/null; rm -f "$PIDFILE"; exit 0' TERM INT
said=0
while true; do
  if [ -z "$SCHED" ] || ! kill -0 "$SCHED" 2>/dev/null; then
    /usr/bin/python3 "$ROOT/scheduler/scheduler.py" --loop >> "$ROOT/logs/scheduler.out" 2>&1 & SCHED=$!; echo "$(date '+%m/%d %H:%M:%S') scheduler started pid $SCHED" >> "$LOG"
  fi
  if [ ! -s "$TOKEN" ]; then
    if [ "$said" = 0 ]; then echo "$(date '+%m/%d %H:%M:%S') waiting for secrets/discord_bot_token.txt" >> "$LOG"; said=1; fi
    sleep 60 & CHILD=$!; wait "$CHILD"; CHILD=""; continue
  fi
  said=0; echo "$(date '+%m/%d %H:%M:%S') starting bot" >> "$LOG"
  /usr/bin/python3 "$ROOT/discord/bot.py" >> "$LOG" 2>&1 & CHILD=$!; wait "$CHILD"; code=$?; CHILD=""
  echo "$(date '+%m/%d %H:%M:%S') bot stopped, exit $code" >> "$LOG"
  case "$code" in 4) pause=600 ;; 5) pause=300 ;; *) pause=60 ;; esac
  sleep "$pause" & CHILD=$!; wait "$CHILD"; CHILD=""
done

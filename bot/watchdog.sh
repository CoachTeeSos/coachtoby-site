#!/bin/bash
# Coach Toby Bot — Watchdog / Auto-restart script
# Keeps bot.py running indefinitely, restarting on crash

WORKDIR="/data/home/workspace/coachtoby-site/bot"
LOG="/tmp/bot.log"
PIDFILE="/tmp/coachtoby-bot.pid"

cd "$WORKDIR"
rm -rf __pycache__

echo "[$(date)] Watchdog started" >> "$LOG"

while true; do
    # Kill any existing bot process
    if [ -f "$PIDFILE" ]; then
        OLD_PID=$(cat "$PIDFILE")
        kill "$OLD_PID" 2>/dev/null
        sleep 1
    fi

    echo "[$(date)] Starting bot..." >> "$LOG"

    # Export env vars and start bot
    eval $(python3 -c "
import os
with open('.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            print(f'export {k}=\"{v}\"')
")

    python3 bot.py >> "$LOG" 2>&1 &
    BOT_PID=$!
    echo "$BOT_PID" > "$PIDFILE"

    echo "[$(date)] Bot started with PID $BOT_PID" >> "$LOG"

    # Wait for the bot to exit
    wait "$BOT_PID"
    EXIT_CODE=$?

    echo "[$(date)] Bot exited with code $EXIT_CODE. Restarting in 5s..." >> "$LOG"
    sleep 5
done

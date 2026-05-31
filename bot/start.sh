#!/bin/bash
# Start the Coach Toby Telegram Bot
cd /data/home/workspace/coachtoby-site/bot
source /data/home/workspace/coachtoby-site/bot/.env 2>/dev/null
python3 bot.py

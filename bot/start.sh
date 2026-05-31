#!/bin/bash
# Coach Toby Bot — Startup Script
# Reads .env via Python (avoids bash glob/splitting issues with special chars)
cd /data/home/workspace/coachtoby-site/bot

# Clear Python cache
rm -rf __pycache__

# Export env vars via Python
eval $(python3 -c "
import os
with open('.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            print(f'export {k}=\"{v}\"')
")

echo "BOT_TOKEN length: ${#BOT_TOKEN}"
python3 bot.py

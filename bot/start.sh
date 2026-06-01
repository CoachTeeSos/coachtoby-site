#!/bin/bash
# Coach Toby — Startup Script
# Reads .env via Python (avoids bash glob/splitting issues with special chars)
cd "$(dirname "$0")"

# Clear Python cache
rm -rf __pycache__

# Run the modular bot
exec python3 bot.py

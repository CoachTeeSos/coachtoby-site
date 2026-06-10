"""
Coach Toby Bot — Hugging Face Space Entry Point
Runs the Telegram bot as a persistent background process.
HF Spaces keep this alive 24/7 on free tier.
"""
import os
import sys
import threading
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger("hf-bot")

# Set environment variables from HF secrets
# HF sets these as env vars automatically when you add them as secrets
required_env = ["BOT2_TOKEN", "AIRTABLE_PAT"]
missing = [k for k in required_env if not os.environ.get(k)]
if missing:
    log.error(f"Missing env vars: {missing}")
    log.error("Set these as secrets in your HF Space settings")
    # Don't exit — let the Space start so you can see logs
    # The bot will handle missing token gracefully

# Override config for HF environment
os.environ["BOT2_DATA_DIR"] = "/data/bot2"
os.environ.setdefault("AIRTABLE_BASE_ID", "app3N2MFPvfDSuYxk")
os.environ.setdefault("AIRTABLE_TABLE", "Students")
os.environ.setdefault("ADMIN_TG_ID", "1688731002")
os.environ.setdefault("BOT_USERNAME", "Retpipebot")
os.environ.setdefault("SITE_URL", "https://coachteesos.github.io/coachtoby-site/")
os.environ.setdefault("STALE_SECS", "300")

# Create data directory
os.makedirs("/data/bot2", exist_ok=True)

# Import the bot module
sys.path.insert(0, os.path.dirname(__file__))

# The bot's main() function handles everything
try:
    from retpipebot import main as bot_main
    import asyncio
    
    log.info("Starting Coach Toby bot on Hugging Face...")
    log.info(f"Bot token present: {'BOT2_TOKEN' in os.environ}")
    log.info(f"Airtable PAT present: {'AIRTABLE_PAT' in os.environ}")
    
    # Run the bot
    asyncio.run(bot_main())
    
except KeyboardInterrupt:
    log.info("Bot stopped by user")
except Exception as e:
    log.error(f"Bot crashed: {e}")
    import traceback
    traceback.print_exc()
    # Keep the Space alive so logs are visible
    import time
    while True:
        time.sleep(3600)

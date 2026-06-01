"""
webhook_server.py — Run Flask webhook server alongside Bot 2.
Usage: python webhook_server.py
"""
import os
import threading
import logging

from services.flutterwave_webhook import app as webhook_app
from bot import main as bot_main

logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s: %(message)s",
    level=logging.INFO,
)

# ── Run bot in a background thread ──
bot_thread = threading.Thread(target=bot_main, daemon=True)
bot_thread.start()
logger = logging.getLogger(__name__)
logger.info("Bot 2 started in background thread")

# ── Run Flask webhook server in main thread ──
port = int(os.getenv("PORT", 8080))
logger.info(f"Webhook server starting on port {port}")
webhook_app.run(host="0.0.0.0", port=port)

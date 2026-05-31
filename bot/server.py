"""
Coach Toby — Airtable Proxy Server
====================================
Lightweight Flask server that sits between the website and Airtable.
The frontend calls this server (no Airtable token in client-side code).
This server holds the token and writes to Airtable.

Also handles Flutterwave payment webhooks for auto-verification.
"""

import os
import logging
import json
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load .env file (tokens loaded from file, never hardcoded)
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))
AIRTABLE_BASE = "app3N2MFPvfDSuYxk"
AIRTABLE_TABLE = "Students"
AIRTABLE_TOKEN = os.environ.get("AIRTABLE_TOKEN", "")
AIRTABLE_API = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{AIRTABLE_TABLE}"

# Secret key to authenticate webhook calls from this server to the bot
BOT_NOTIFY_URL = None  # Set to bot's webhook URL if needed

# ═══════════════════════════════════════
# APP
# ═══════════════════════════════════════
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def airtable_headers():
    return {
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type": "application/json"
    }

# ═══════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════

@app.route("/api/register", methods=["POST"])
def register_student():
    """
    Register a new student from the website form.
    Expected JSON: { name, email, phone, telegram, plan, amount?, currency?, budget?, needs? }
    Writes to Airtable Students table.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    telegram = data.get("telegram", "").strip()
    plan = data.get("plan", "").strip()

    if not all([name, email, phone, telegram, plan]):
        return jsonify({"error": "Missing required fields"}), 400

    # Normalize telegram handle
    if not telegram.startswith("@"):
        telegram = "@" + telegram

    # Determine status
    amount = data.get("amount", 0)
    status = "pending_payment" if amount and amount > 0 else "active"

    fields = {
        "Name": name,
        "Email": email,
        "Phone": phone,
        "Telegram": telegram,
        "Plan": plan,
        "Status": status,
        "Source": "Website"
    }
    if amount:
        fields["Amount"] = amount
        fields["Currency"] = data.get("currency", "USD")
    if data.get("budget"):
        fields["Budget"] = data["budget"]
    if data.get("needs"):
        fields["Needs"] = data["needs"]

    try:
        resp = requests.post(
            AIRTABLE_API,
            headers=airtable_headers(),
            json={"fields": fields},
            timeout=10
        )
        resp.raise_for_status()
        record = resp.json()
        logger.info(f"Registered: {name} ({telegram}) — {plan} — {status}")
        return jsonify({
            "success": True,
            "id": record["id"],
            "status": status
        }), 201
    except Exception as e:
        logger.error(f"Airtable write failed: {e}")
        return jsonify({"error": "Registration failed"}), 500


@app.route("/api/flutterwave/webhook", methods=["POST"])
def flutterwave_webhook():
    """
    Handle Flutterwave payment webhook.
    When payment is confirmed, update student status to 'active'.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400

    # Flutterwave sends event data
    event = data.get("event")
    tx_data = data.get("data", {})

    if event == "charge.completed" and tx_data.get("status") == "successful":
        # Find student by email or tx_ref
        email = tx_data.get("customer", {}).get("email", "")
        tx_ref = tx_data.get("tx_ref", "")

        # Try to find student by email
        if email:
            formula = f"{{Email}}='{email}'"
            params = {"filterByFormula": formula}
            try:
                resp = requests.get(AIRTABLE_API, headers=airtable_headers(), params=params, timeout=10)
                resp.raise_for_status()
                records = resp.json().get("records", [])
                for record in records:
                    if record["fields"].get("Status") == "pending_payment":
                        update_resp = requests.patch(
                            f"{AIRTABLE_API}/{record['id']}",
                            headers=airtable_headers(),
                            json={"fields": {"Status": "active"}},
                            timeout=10
                        )
                        update_resp.raise_for_status()
                        logger.info(f"Payment verified: {email} → active")
            except Exception as e:
                logger.error(f"Webhook processing failed: {e}")

    return jsonify({"status": "ok"}), 200


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

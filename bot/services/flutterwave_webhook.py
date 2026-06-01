"""
services/flutterwave_webhook.py — Receive Flutterwave payment webhooks.
Updates Airtable status to 'Active' when payment is confirmed.
"""
import os
import hmac
import hashlib
import json
import logging
from flask import Flask, request, abort

import requests

app = Flask(__name__)

# ── CONFIG ──
FLUTTERWAVE_SECRET_HASH = os.getenv("FLUTTERWAVE_SECRET_HASH", "")  # From Flutterwave dashboard
AIRTABLE_PAT = os.getenv("AIRTABLE_PAT", "")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "app3N2MFPvfDSuYxk")
AIRTABLE_TABLE = "Students"

logger = logging.getLogger(__name__)


def verify_flutterwave_signature(payload: bytes, signature: str) -> bool:
    """Verify the Flutterwave webhook signature."""
    if not FLUTTERWAVE_SECRET_HASH:
        logger.warning("FLUTTERWAVE_SECRET_HASH not set — skipping verification")
        return True  # Allow in dev; enforce in production
    
    computed = hmac.new(
        key=FLUTTERWAVE_SECRET_HASH.encode(),
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(computed, signature)


def find_student_by_email(email: str) -> dict:
    """Find a student in Airtable by email."""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE}"
    headers = {"Authorization": f"Bearer {AIRTABLE_PAT}"}
    params = {"filterByFormula": f"{{Email}}='{email}'"}
    
    r = requests.get(url, headers=headers, params=params, timeout=10)
    if r.status_code != 200:
        logger.error(f"Airtable lookup failed: {r.status_code}")
        return None
    
    records = r.json().get("records", [])
    return records[0] if records else None


def update_student_status(record_id: str, status: str = "Active") -> bool:
    """Update student status in Airtable."""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE}/{record_id}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_PAT}",
        "Content-Type": "application/json",
    }
    payload = {"fields": {"Status": status}}
    
    r = requests.patch(url, headers=headers, json=payload, timeout=10)
    if r.status_code == 200:
        logger.info(f"Updated {record_id} → {status}")
        return True
    logger.error(f"Airtable update failed: {r.status_code} {r.text}")
    return False


@app.route("/webhook/flutterwave", methods=["POST"])
def flutterwave_webhook():
    # 1️⃣ Verify signature
    signature = request.headers.get("verif-hash", "")
    if not verify_flutterwave_signature(request.data, signature):
        logger.warning("❌ Invalid Flutterwave signature")
        abort(400, "Invalid signature")

    # 2️⃣ Parse payload
    try:
        data = request.get_json()
    except Exception:
        abort(400, "Invalid JSON")

    if not data:
        abort(400, "Empty payload")

    # 3️⃣ Check event type
    event = data.get("event", "")
    logger.info(f"Flutterwave webhook: {event}")

    # Only process successful charge events
    if event not in ("charge.completed", "charge.success"):
        return json.dumps({"status": "ignored", "event": event}), 200

    tx_data = data.get("data", {})
    status = tx_data.get("status", "")
    if status not in ("successful", "success"):
        return json.dumps({"status": "not_successful"}), 200

    # 4️⃣ Find the student by email
    # Flutterwave includes customer email in the payload
    customer_email = tx_data.get("customer", {}).get("email", "")
    tx_ref = tx_data.get("tx_ref", "")
    
    logger.info(f"Payment confirmed: {customer_email} | ref: {tx_ref}")

    # Try to find by email first, then by tx_ref pattern
    student = None
    if customer_email:
        student = find_student_by_email(customer_email)
    
    if not student:
        logger.warning(f"No student found for {customer_email}")
        # Could also search by tx_ref if you stored it
        return json.dumps({"status": "student_not_found"}), 200

    # 5️⃣ Update Airtable
    record_id = student.get("id", "")
    success = update_student_status(record_id, "Active")

    if success:
        # 6️⃣ Notify via Bot 2 (if bot is running)
        tg_id = student.get("fields", {}).get("Telegram Chat ID", "")
        name = student.get("fields", {}).get("Name", "Student")
        if tg_id:
            try:
                bot_token = os.getenv("BOT2_TOKEN", "")
                if bot_token:
                    msg = (
                        f"✅ **Payment Confirmed!**\n\n"
                        f"Welcome aboard, **{name}**!\n"
                        f"Your payment has been received and your account is now active.\n\n"
                        f"Type /start to see your menu."
                    )
                    requests.post(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        json={"chat_id": int(tg_id), "text": msg, "parse_mode": "Markdown"},
                        timeout=10,
                    )
                    logger.info(f"Notified student {tg_id}")
            except Exception as e:
                logger.error(f"Failed to notify student: {e}")

    return json.dumps({"status": "updated" if success else "failed"}), 200


@app.route("/webhook/flutterwave", methods=["GET"])
def health_check():
    return json.dumps({"status": "ok"}), 200

"""
Coach Toby — Airtable Proxy Server
====================================
Lightweight Flask server: website → this → Airtable.
Token stays server-side. Frontend never sees it.

Endpoints:
  POST /api/register    — Student registers from website
  POST /api/flutterwave/webhook — Flutterwave payment confirmation
  GET  /api/health     — Health check
"""

import os
import logging
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load .env from this directory
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

AIRTABLE_BASE = os.environ.get("AIRTABLE_BASE_ID", "app3N2MFPvfDSuYxk")
AIRTABLE_TABLE = os.environ.get("AIRTABLE_TABLE", "Students")
AIRTABLE_TOKEN = os.environ.get("AIRTABLE_TOKEN", "")
AIRTABLE_API = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{AIRTABLE_TABLE}"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


def airtable_headers():
    return {
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type": "application/json",
    }


@app.route("/api/register", methods=["POST"])
def register_student():
    """
    Register a new student from the website form.
    Writes to Airtable Students table.

    Expected JSON fields from scripts.js:
      Name, Plan, Service Key, Status, Source, Total Sessions, Sessions Used
      Optional: Budget, Needs
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Build Airtable record — only include non-empty fields
    fields = {}
    for key in ["Name", "Plan", "Service Key", "Status", "Source",
                "Total Sessions", "Sessions Used", "Budget", "Needs"]:
        val = data.get(key)
        if val is not None and val != "":
            fields[key] = val

    if not fields.get("Name") or not fields.get("Plan"):
        return jsonify({"error": "Name and Plan are required"}), 400

    try:
        resp = requests.post(
            AIRTABLE_API,
            headers=airtable_headers(),
            json={"fields": fields},
            timeout=15,
        )
        resp.raise_for_status()
        record = resp.json()
        logger.info(f"Registered: {fields.get('Name')} — {fields.get('Plan')} — {fields.get('Status')}")
        return jsonify({
            "success": True,
            "id": record["id"],
            "status": fields.get("Status", ""),
        }), 201
    except requests.exceptions.HTTPError as e:
        logger.error(f"Airtable HTTP error: {e.response.text if e.response else str(e)}")
        return jsonify({"error": "Registration failed", "detail": str(e)}), 500
    except Exception as e:
        logger.error(f"Airtable write failed: {e}")
        return jsonify({"error": "Registration failed"}), 500


@app.route("/api/flutterwave/webhook", methods=["POST"])
def flutterwave_webhook():
    """
    Handle Flutterwave payment webhook.
    When payment confirmed, update student status from 'Awaiting Receipt' → 'Active'.
    Matches student by tx_ref or email.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400

    event = data.get("event")
    tx_data = data.get("data", {})

    if event == "charge.completed" and tx_data.get("status") == "successful":
        email = tx_data.get("customer", {}).get("email", "")
        tx_ref = tx_data.get("tx_ref", "")

        # Try to find student by email
        if email:
            formula = f"{{Email}}='{email}'"
            params = {"filterByFormula": formula}
            try:
                resp = requests.get(
                    AIRTABLE_API, headers=airtable_headers(),
                    params=params, timeout=10,
                )
                resp.raise_for_status()
                records = resp.json().get("records", [])
                for record in records:
                    if record["fields"].get("Status") == "Awaiting Receipt":
                        update_resp = requests.patch(
                            f"{AIRTABLE_API}/{record['id']}",
                            headers=airtable_headers(),
                            json={"fields": {"Status": "Active"}},
                            timeout=10,
                        )
                        update_resp.raise_for_status()
                        logger.info(f"Payment verified via webhook: {email} → Active")
            except Exception as e:
                logger.error(f"Webhook processing failed: {e}")

    return jsonify({"status": "ok"}), 200


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "time": datetime.utcnow().isoformat(),
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

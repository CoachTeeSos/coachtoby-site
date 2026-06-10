#!/usr/bin/env python3
"""
Airtable → Brevo email trigger.
Run via cron every 2-5 minutes.
Checks for new Students records and sends welcome emails via Brevo.
"""
import os
import json
import logging
import requests
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# ── Load .env ──────────────────────────────────────────────────────────────
def load_env():
    """Load environment variables from .hermes/.env"""
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env()

# ── Config ──────────────────────────────────────────────────────────────────
AIRTABLE_PAT = os.environ.get("AIRTABLE_PAT", "")
AIRTABLE_BASE = os.environ.get("AIRTABLE_BASE_ID", "app3N2MFPvfDSuYxk")
AIRTABLE_TABLE = os.environ.get("AIRTABLE_TABLE", "Students")
BREVO_API_KEY=os.environ.get("BREVO_API_KEY", "")
BREVO_API_URL = "https://api.brevo.com/v3"
SENDER_NAME = os.environ.get("SENDER_NAME", "Coach Toby")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "prosperolumotobi@gmail.com")
STATE_FILE = os.environ.get("STATE_FILE", "/tmp/airtable_brevo_last_run.json")

# ── Payment links ──────────────────────────────────────────────────────────
PAYMENT_LINKS = {
    "single": "https://flutterwave.com/pay/ictjiqq30sz7",
    "monthly": "https://flutterwave.com/pay/b0hjfvjhv8x4",
    "ngn-single": "https://flutterwave.com/pay/xnddgkfjeheq",
    "ngn-monthly": "https://flutterwave.com/pay/wdod0tyeqedw",
    "group3-5": "https://flutterwave.com/pay/lrzz2vk3xez3",
}

PLAN_DETAILS = {
    "single": {"name": "Single Session", "price": "$50", "price_ngn": "₦70,000", "sessions": "1 session"},
    "monthly": {"name": "Monthly Plan", "price": "$200", "price_ngn": "₦300,000", "sessions": "4 sessions (1x/week)"},
    "ngn-single": {"name": "Single Session (NGN)", "price": "₦70,000", "price_ngn": "₦70,000", "sessions": "1 session"},
    "ngn-monthly": {"name": "Monthly Plan (NGN)", "price": "₦300,000", "price_ngn": "₦300,000", "sessions": "4 sessions (1x/week)"},
    "group3-5": {"name": "Group Coaching (3-5)", "price": "Custom", "price_ngn": "Custom", "sessions": "Group sessions"},
    "free-community": {"name": "Free Singers' Community", "price": "FREE", "price_ngn": "FREE", "sessions": "Unlimited"},
    "paid-community": {"name": "Paid Community", "price": "Varies", "price_ngn": "Varies", "sessions": "Community + resources"},
    "abuja-collective": {"name": "Abuja Music Collective", "price": "FREE", "price_ngn": "FREE", "sessions": "Collective sessions"},
    "speaking": {"name": "Speaking & Performance", "price": "Custom", "price_ngn": "Custom", "sessions": "Custom"},
    "custom-plan": {"name": "Custom Plan", "price": "Custom", "price_ngn": "Custom", "sessions": "Custom"},
    "free-call": {"name": "Free Clarity Call", "price": "FREE", "price_ngn": "FREE", "sessions": "1 call"},
    "quiz": {"name": "Which Singer Are You? Quiz", "price": "FREE", "price_ngn": "FREE", "sessions": "Self-paced"},
    "lead-magnet": {"name": "5 Vocal Exercises Guide", "price": "FREE", "price_ngn": "FREE", "sessions": "Self-paced"},
}


def load_state():
    """Load last run state."""
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Default: check last 5 minutes on first run
        return {"last_check": (datetime.utcnow() - timedelta(minutes=5)).isoformat()}


def save_state(state):
    """Save last run state."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def get_new_students(last_check: str) -> list:
    """Fetch students created since last check. Uses minimal API calls."""
    if not AIRTABLE_PAT:
        logger.error("AIRTABLE_PAT not set")
        return []

    # Use filterByFormula to only get records created since last check
    # This minimizes data transfer and API usage
    formula = f"IS_AFTER({{Created time}}, DATETIME_PARSE('{last_check}'))"
    params = {
        "filterByFormula": formula,
        "pageSize": 100,
        "sort": [{"field": "Created time", "direction": "asc"}],
    }
    try:
        r = requests.get(
            f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{AIRTABLE_TABLE}",
            headers={"Authorization": f"Bearer {AIRTABLE_PAT}"},
            params=params,
            timeout=15,
        )
        r.raise_for_status()
        return r.json().get("records", [])
    except Exception as e:
        logger.error(f"Airtable fetch failed: {e}")
        return []


def build_email(name: str, email: str, service_key: str, plan_label: str) -> dict:
    """Build Brevo welcome email."""
    plan = PLAN_DETAILS.get(service_key, {"name": service_key, "price": "Contact us", "price_ngn": "Contact us", "sessions": "Custom"})
    payment_link = PAYMENT_LINKS.get(service_key, "")
    first_name = name.split()[0] if name else "there"
    is_free = plan.get("price") == "FREE" or service_key in ("free-community", "free-call", "quiz", "lead-magnet", "abuja-collective")
    is_custom = not payment_link and not is_free

    if is_free:
        payment_html = f'''<div style="background:#F0FDF4;border:2px solid #22C55E;border-radius:12px;padding:20px;margin:16px 0;">
<h3 style="margin-top:0;color:#166534;">🎉 You're All Set!</h3>
<p style="color:#166534;">Your registration is confirmed. Check your email for next steps!</p></div>'''
        cta = ""
    elif is_custom:
        payment_html = f'''<div style="background:#FEF3C7;border:2px solid #F59E0B;border-radius:12px;padding:20px;margin:16px 0;">
<h3 style="margin-top:0;color:#92400E;">📋 Custom Plan</h3>
<p style="color:#92400E;">Coach Toby will reach out within 24 hours to finalize your plan.</p></div>'''
        cta = ""
    else:
        payment_html = f'''<div style="background:#FEF3C7;border:2px solid #F59E0B;border-radius:12px;padding:20px;margin:16px 0;">
<h3 style="margin-top:0;color:#92400E;">💳 Complete Your Payment</h3>
<p style="color:#92400E;">Activate your plan by completing payment:</p>
<p style="font-size:1.5rem;font-weight:800;color:#92400E;margin:8px 0;">{plan['price']}</p>
<p style="color:#92400E;font-size:0.85rem;">or {plan['price_ngn']} via bank transfer</p></div>'''
        cta = f'''<a href="{payment_link}" style="display:inline-block;padding:16px 32px;background:#004B49;color:#fff;font-weight:700;text-decoration:none;border-radius:12px;border:3px solid #003836;margin:16px 0;font-size:1.1rem;">💳 Pay Now — {plan['price']}</a>'''

    html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px;color:#1a1a1a;background:#f8f9fa;">
<div style="background:#fff;border-radius:16px;padding:32px;border:1px solid #e2e8f0;">
<h1 style="color:#004B49;margin-top:0;">Hey {first_name}! 🎤</h1>
<p>Welcome to <strong>Sessions with Toby</strong>! Coach Toby is excited to start this journey with you.</p>
<div style="background:#F0F9FF;border:2px solid #0EA5E9;border-radius:12px;padding:20px;margin:16px 0;">
<h3 style="margin-top:0;color:#0C4A6E;">📋 YOUR PLAN</h3>
<p style="font-size:1.1rem;margin:4px 0;"><strong>{plan['name']}</strong></p>
<p style="color:#475569;margin:4px 0;">🎯 {plan['sessions']}</p>
</div>
{payment_html}
{cta}
<div style="background:#F8F7FF;border:2px solid #8B5CF6;border-radius:12px;padding:20px;margin:16px 0;">
<h3 style="margin-top:0;color:#5B21B6;">📧 What Happens Next</h3>
<ol style="color:#5B21B6;padding-left:20px;">
<li><strong>Complete your payment</strong> (if applicable)</li>
<li><strong>Coach Toby reviews your registration</strong> within 24 hours</li>
<li><strong>You'll receive a confirmation email</strong> with your session schedule</li>
<li><strong>First session booking link</strong> sent via email</li>
</ol>
</div>
<p>Questions? Reply to this email or WhatsApp: <strong>+234 814 152 9507</strong></p>
<p>Let's transform your voice! 🎤</p>
<p>— Coach Toby<br><em>Sessions with Toby</em><br>
<a href="https://coachteesos.github.io/coachtoby-site/">coachteesos.github.io/coachtoby-site</a></p>
</div></body></html>'''

    return {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": email, "name": name}],
        "subject": f"Welcome to Sessions with Toby 🎤 — Your {plan['name']} is Ready",
        "htmlContent": html,
    }


def send_brevo_email(name: str, email: str, service_key: str, plan_label: str) -> bool:
    """Send email via Brevo API."""
    if not BREVO_API_KEY:
        logger.error("BREVO_API_KEY not set")
        return False
    if not email:
        logger.warning(f"No email for {name}, skipping")
        return False

    payload = build_email(name, email, service_key, plan_label)
    try:
        r = requests.post(
            f"{BREVO_API_URL}/smtp/email",
            headers={"api-key": BREVO_API_KEY, "Content-Type": "application/json", "Accept": "application/json"},
            json=payload,
            timeout=15,
        )
        r.raise_for_status()
        msg_id = r.json().get("messageId", "")
        logger.info(f"✅ Email sent to {email} (msg: {msg_id[:20]}...)")
        return True
    except Exception as e:
        logger.error(f"❌ Brevo send failed for {email}: {e}")
        return False


def main():
    """Main: check for new students and send welcome emails."""
    # Only run between 6am and 6pm WAT (UTC+1) = 5am-17pm UTC
    current_hour = datetime.utcnow().hour
    if current_hour < 5 or current_hour >= 17:
        logger.info(f"Outside operating hours (6am-6pm WAT). Current UTC hour: {current_hour}. Skipping.")
        return

    state = load_state()
    last_check = state.get("last_check", "")
    now = datetime.utcnow().isoformat()

    logger.info(f"Checking for new students since {last_check}")
    new_students = get_new_students(last_check)
    logger.info(f"Found {len(new_students)} new student(s)")

    sent = 0
    skipped = 0
    for record in new_students:
        fields = record.get("fields", {})
        name = fields.get("Name", "")
        email = fields.get("Email", "")
        service_key = fields.get("Service Key", "")
        plan_label = fields.get("Plan", "")
        status = fields.get("Status", "")

        # Skip if already Active (email already sent manually)
        if status == "Active":
            logger.info(f"Skipping {name} — already Active")
            skipped += 1
            continue

        if send_brevo_email(name, email, service_key, plan_label):
            sent += 1

    # Update state
    save_state({"last_check": now})
    logger.info(f"Done: {sent} sent, {skipped} skipped, {len(new_students)} total")


if __name__ == "__main__":
    main()

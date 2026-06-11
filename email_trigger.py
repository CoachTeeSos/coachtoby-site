#!/usr/bin/env python3
"""
Cron job: Check local DB for new registrations and send Brevo welcome emails.
Runs hourly between 6am-6pm WAT.
Uses smart API tracking to prevent rate limit exhaustion.
"""
import sys, os, logging
from datetime import datetime

sys.path.insert(0, "/home/user/workspace")
from local_db import init_db, get_unsent_emails, mark_email_sent, get_stats, load_env
from smart_api import check_limit, log_call

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)
load_env()

BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
BREVO_API_URL = "https://api.brevo.com/v3"
SENDER_NAME = "Coach Toby"
SENDER_EMAIL = "prosperolumotobi@gmail.com"

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
    "quiz": {"name": "Quiz", "price": "FREE", "price_ngn": "FREE", "sessions": "Self-paced"},
    "lead-magnet": {"name": "Vocal Exercises Guide", "price": "FREE", "price_ngn": "FREE", "sessions": "Self-paced"},
}


def build_email_html(name, first_name, plan, payment_link, is_free, is_custom):
    """Build the HTML email body."""

    if is_free:
        payment_block = '<div style="background:#F0FDF4;border:2px solid #22C55E;border-radius:12px;padding:20px;margin:16px 0;"><h3 style="margin-top:0;color:#166534;">&#127881; You are All Set!</h3><p>Your registration is confirmed.</p></div>'
        cta_block = ""
    elif is_custom:
        payment_block = '<div style="background:#FEF3C7;border:2px solid #F59E0B;border-radius:12px;padding:20px;margin:16px 0;"><h3 style="margin-top:0;color:#92400E;">&#128203; Custom Plan</h3><p>Coach Toby will reach out within 24 hours to finalize your plan.</p></div>'
        cta_block = ""
    else:
        price = plan["price"]
        price_ngn = plan["price_ngn"]
        payment_block = (
            '<div style="background:#FEF3C7;border:2px solid #F59E0B;border-radius:12px;padding:20px;margin:16px 0;">'
            '<h3 style="margin-top:0;color:#92400E;">&#128179; Complete Your Payment</h3>'
            '<p>Activate your plan:</p>'
            '<p style="font-size:1.5rem;font-weight:800;color:#92400E;">' + price + '</p>'
            '<p style="font-size:0.85rem;">or ' + price_ngn + ' via bank transfer</p>'
            '</div>'
        )
        cta_block = (
            '<a href="' + payment_link + '" style="display:inline-block;padding:16px 32px;background:#004B49;'
            'color:#fff;font-weight:700;text-decoration:none;border-radius:12px;margin:16px 0;font-size:1.1rem;">'
            '&#128179; Pay Now &mdash; ' + price + '</a>'
        )

    plan_name = plan["name"]
    plan_sessions = plan["sessions"]

    html = (
        '<!DOCTYPE html><html><head><meta charset="UTF-8"></head>'
        '<body style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px;color:#1a1a1a;background:#f8f9fa;">'
        '<div style="background:#fff;border-radius:16px;padding:32px;border:1px solid #e2e8f0;">'
        '<h1 style="color:#004B49;">Hey ' + first_name + '! &#127908;</h1>'
        '<p>Welcome to <strong>Sessions with Toby</strong>!</p>'
        '<div style="background:#F0F9FF;border:2px solid #0EA5E9;border-radius:12px;padding:20px;margin:16px 0;">'
        '<h3 style="margin-top:0;color:#0C4A6E;">&#128203; YOUR PLAN</h3>'
        '<p><strong>' + plan_name + '</strong></p><p>&#127919; ' + plan_sessions + '</p>'
        '</div>'
        + payment_block +
        cta_block +
        '<div style="background:#F8F7FF;border:2px solid #8B5CF6;border-radius:12px;padding:20px;margin:16px 0;">'
        '<h3 style="margin-top:0;color:#5B21B6;">&#128233; What Happens Next</h3>'
        '<ol style="color:#5B21B6;padding-left:20px;">'
        '<li><strong>Complete your payment</strong> (if applicable)</li>'
        '<li><strong>Coach Toby reviews your registration</strong> within 24 hours</li>'
        '<li><strong>Confirmation email</strong> with session schedule</li>'
        '<li><strong>First session booking link</strong> sent via email</li>'
        '</ol></div>'
        '<p>Questions? Reply to this email or WhatsApp: <strong>+234 814 152 9507</strong></p>'
        '<p>Let us transform your voice! &#127908;</p>'
        '<p>&mdash; Coach Toby<br><a href="https://coachteesos.github.io/coachtoby-site/">Sessions with Toby</a></p>'
        '</div></body></html>'
    )
    return html


def send_welcome_email(name, email, service_key, plan_label):
    """Send welcome email via Brevo."""
    if not BREVO_API_KEY or not email:
        return False

    plan = PLAN_DETAILS.get(service_key, {"name": service_key, "price": "Contact us", "price_ngn": "Contact us", "sessions": "Custom"})
    payment_link = PAYMENT_LINKS.get(service_key, "")
    first_name = name.split()[0] if name else "there"
    is_free = plan.get("price") == "FREE" or service_key in ("free-community", "free-call", "quiz", "lead-magnet", "abuja-collective")
    is_custom = not payment_link and not is_free

    html = build_email_html(name, first_name, plan, payment_link, is_free, is_custom)
    plan_name = plan["name"]

    try:
        r = requests.post(
            BREVO_API_URL + "/smtp/email",
            headers={"api-key": BREVO_API_KEY, "Content-Type": "application/json"},
            json={
                "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
                "to": [{"email": email, "name": name}],
                "subject": "Welcome to Sessions with Toby \U0001f3a4 \u2014 Your " + plan_name + " is Ready",
                "htmlContent": html,
            },
            timeout=15,
        )
        r.raise_for_status()
        logger.info("Email sent to " + email)
        return True
    except Exception as e:
        logger.error("Email failed for " + email + ": " + str(e))
        return False


def main():
    # Only run 6am-6pm WAT (5am-17pm UTC)
    current_hour = datetime.utcnow().hour
    if current_hour < 5 or current_hour >= 17:
        logger.info("Outside hours (6am-6pm WAT). UTC hour: " + str(current_hour) + ". Skipping.")
        return

    init_db()
    stats = get_stats()
    logger.info("DB stats: " + str(stats))

    unsent = get_unsent_emails()
    if not unsent:
        logger.info("No unsent emails")
        return

    logger.info("Processing " + str(len(unsent)) + " unsent registration(s)")
    sent = 0
    for rec in unsent:
        # Check rate limit before each email
        ok, msg = check_limit('brevo')
        if not ok:
            logger.warning("Brevo rate limit: " + msg)
            break
        
        if send_welcome_email(rec["name"], rec["email"], rec["service_key"], rec["plan"]):
            mark_email_sent(rec["id"])
            sent += 1
            # Log the API call
            log_call('brevo', endpoint='/v3/smtp/email', model='brevo', status='ok')
        else:
            log_call('brevo', endpoint='/v3/smtp/email', model='brevo', status='error')

    logger.info("Done: " + str(sent) + "/" + str(len(unsent)) + " emails sent")


if __name__ == "__main__":
    main()

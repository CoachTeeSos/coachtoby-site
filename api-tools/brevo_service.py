"""
Brevo email service for Coach Toby student onboarding.
Sends welcome emails with payment links when students register via the website.
"""
import os
import logging
import requests

logger = logging.getLogger(__name__)

BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
BREVO_API_URL = "https://api.brevo.com/v3"
SENDER_NAME = os.environ.get("SENDER_NAME", "Coach Toby")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "prosperolumotobi@gmail.com")

# Flutterwave payment links by service key
PAYMENT_LINKS = {
    "single": "https://flutterwave.com/pay/ictjiqq30sz7",
    "monthly": "https://flutterwave.com/pay/b0hjfvjhv8x4",
    "ngn-single": "https://flutterwave.com/pay/xnddgkfjeheq",
    "ngn-monthly": "https://flutterwave.com/pay/wdod0tyeqedw",
    "group3-5": "https://flutterwave.com/pay/lrzz2vk3xez3",
}

# Plan details for email templates
PLAN_DETAILS = {
    "single": {
        "name": "Single Session",
        "price": "$50",
        "price_ngn": "₦70,000",
        "sessions": "1 session",
        "description": "One focused coaching session to get you started.",
    },
    "monthly": {
        "name": "Monthly Plan",
        "price": "$200",
        "price_ngn": "₦300,000",
        "sessions": "4 sessions (1x/week)",
        "description": "Full month of coaching with weekly sessions.",
    },
    "ngn-single": {
        "name": "Single Session (NGN)",
        "price": "₦70,000",
        "price_ngn": "₦70,000",
        "sessions": "1 session",
        "description": "One focused coaching session to get you started.",
    },
    "ngn-monthly": {
        "name": "Monthly Plan (NGN)",
        "price": "₦300,000",
        "price_ngn": "₦300,000",
        "sessions": "4 sessions (1x/week)",
        "description": "Full month of coaching with weekly sessions.",
    },
    "group3-5": {
        "name": "Group Coaching (3-5 people)",
        "price": "Custom pricing",
        "price_ngn": "Custom pricing",
        "sessions": "Group sessions",
        "description": "Coaching for small groups of 3-5 people.",
    },
    "free-community": {
        "name": "Free Community",
        "price": "FREE",
        "price_ngn": "FREE",
        "sessions": "Unlimited community access",
        "description": "Join our free singing community.",
    },
    "paid-community": {
        "name": "Paid Community",
        "price": "Varies",
        "price_ngn": "Varies",
        "sessions": "Community + resources",
        "description": "Premium community with exclusive resources.",
    },
    "speaking": {
        "name": "Speaking & Performance",
        "price": "Custom pricing",
        "price_ngn": "Custom pricing",
        "sessions": "Custom",
        "description": "Performance coaching and speaking engagements.",
    },
    "custom-plan": {
        "name": "Custom Plan",
        "price": "Custom",
        "price_ngn": "Custom",
        "sessions": "Custom",
        "description": "A personalized coaching plan tailored to your needs.",
    },
}


def get_payment_link(service_key: str) -> str:
    """Get the Flutterwave payment link for a service key."""
    return PAYMENT_LINKS.get(service_key, "")


def get_plan_details(service_key: str) -> dict:
    """Get plan details for email template."""
    return PLAN_DETAILS.get(service_key, {
        "name": service_key,
        "price": "Contact us",
        "price_ngn": "Contact us",
        "sessions": "Custom",
        "description": "A coaching plan tailored to your needs.",
    })


def build_welcome_email(name: str, email: str, service_key: str, plan_label: str = "") -> dict:
    """Build a Brevo welcome email payload."""
    plan = get_plan_details(service_key)
    payment_link = get_payment_link(service_key)
    display_name = name.split()[0] if name else "there"

    # Determine if this is a free/paid plan
    is_free = service_key in ("free-community",) or plan.get("price") == "FREE"
    is_custom = service_key in ("custom-plan", "speaking", "group3-5") or not payment_link

    # Build payment section
    if is_free:
        payment_section = """
        <div style="background:#F0FDF4;border:2px solid #22C55E;border-radius:12px;padding:20px;margin:16px 0;">
        <h3 style="margin-top:0;color:#166534;">🎉 You're All Set!</h3>
        <p style="color:#166534;">Your free community access is active. Check the link below to join!</p>
        </div>"""
        cta_button = ""
    elif is_custom:
        payment_section = f"""
        <div style="background:#FEF3C7;border:2px solid #F59E0B;border-radius:12px;padding:20px;margin:16px 0;">
        <h3 style="margin-top:0;color:#92400E;">📋 Custom Plan</h3>
        <p style="color:#92400E;">Coach Toby will reach out to you within 24 hours to finalize your custom plan and payment details.</p>
        </div>"""
        cta_button = ""
    else:
        payment_section = f"""
        <div style="background:#FEF3C7;border:2px solid #F59E0B;border-radius:12px;padding:20px;margin:16px 0;">
        <h3 style="margin-top:0;color:#92400E;">💳 Complete Your Payment</h3>
        <p style="color:#92400E;">To activate your plan, complete your payment below:</p>
        <p style="font-size:1.5rem;font-weight:800;color:#92400E;margin:8px 0;">{plan['price']}</p>
        <p style="color:#92400E;font-size:0.85rem;">or {plan['price_ngn']} via bank transfer</p>
        </div>"""
        cta_button = f"""
        <a href="{payment_link}" style="display:inline-block;padding:16px 32px;background:#004B49;color:#fff;font-weight:700;text-decoration:none;border-radius:12px;border:3px solid #003836;margin:16px 0;font-size:1.1rem;">💳 Pay Now — {plan['price']}</a>"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px;color:#1a1a1a;background:#f8f9fa;">
<div style="background:#fff;border-radius:16px;padding:32px;border:1px solid #e2e8f0;">

<h1 style="color:#004B49;margin-top:0;">Hey {display_name}! 🎤</h1>

<p>Welcome to <strong>Sessions with Toby</strong>! Coach Toby is excited to start this journey with you.</p>

<div style="background:#F0F9FF;border:2px solid #0EA5E9;border-radius:12px;padding:20px;margin:16px 0;">
<h3 style="margin-top:0;color:#0C4A6E;">📋 YOUR PLAN</h3>
<p style="font-size:1.1rem;margin:4px 0;"><strong>{plan['name']}</strong></p>
<p style="color:#475569;margin:4px 0;">{plan['description']}</p>
<p style="color:#475569;margin:4px 0;">🎯 {plan['sessions']}</p>
</div>

{payment_section}

{cta_button}

<div style="background:#F8F7FF;border:2px solid #8B5CF6;border-radius:12px;padding:20px;margin:16px 0;">
<h3 style="margin-top:0;color:#5B21B6;">📧 What Happens Next</h3>
<ol style="color:#5B21B6;padding-left:20px;">
<li><strong>Complete your payment</strong> (if applicable)</li>
<li><strong>Coach Toby reviews your registration</strong> within 24 hours</li>
<li><strong>You'll receive a confirmation email</strong> with your session schedule</li>
<li><strong>First session booking link</strong> sent via email</li>
</ol>
</div>

<p>Questions? Just reply to this email or reach out on WhatsApp: <strong>+234 916 010 6084</strong></p>

<p>Let's transform your voice! 🎤</p>

<p>— Coach Toby<br>
<em>Sessions with Toby</em><br>
<a href="https://coachteesos.github.io/coachtoby-site/">coachteesos.github.io/coachtoby-site</a></p>

</div>
</body>
</html>"""

    return {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": email, "name": name}],
        "subject": f"Welcome to Sessions with Toby 🎤 — Your {plan['name']} is Ready",
        "htmlContent": html,
    }


def send_welcome_email(name: str, email: str, service_key: str, plan_label: str = "") -> dict:
    """Send a welcome email to a new student via Brevo."""
    if not BREVO_API_KEY:
        logger.error("BREVO_API_KEY not set")
        return {"success": False, "error": "Brevo API key not configured"}

    if not email:
        logger.error("No email provided for welcome email")
        return {"success": False, "error": "No email provided"}

    payload = build_welcome_email(name, email, service_key, plan_label)

    try:
        resp = requests.post(
            f"{BREVO_API_URL}/smtp/email",
            headers={
                "api-key": BREVO_API_KEY,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        result = resp.json()
        logger.info(f"Welcome email sent to {email} (service: {service_key})")
        return {"success": True, "message_id": result.get("messageId", "")}
    except requests.exceptions.HTTPError as e:
        logger.error(f"Brevo API error: {e.response.text if e.response else str(e)}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Failed to send welcome email: {e}")
        return {"success": False, "error": str(e)}

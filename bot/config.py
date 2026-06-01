"""
config.py — Bot 2 Configuration.
Priority: .env file > environment variables > hardcoded fallback.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / ".env")

# ── Telegram ──
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_IDS: list[int] = [int(x) for x in os.getenv("ADMIN_IDS", "1688731002").split(",")]

# ── Airtable ──
AIRTABLE_PAT: str = os.getenv("AIRTABLE_PAT", "")
AIRTABLE_BASE_ID: str = os.getenv("AIRTABLE_BASE_ID", "app3N2MFPvfDSuYxk")
AIRTABLE_STUDENTS_TABLE: str = os.getenv("AIRTABLE_STUDENTS_TABLE", "Students")

# Airtable field names (must exactly match your base schema)
FIELD_NAME        = "Name"
FIELD_STATUS      = "Status"
FIELD_PLAN        = "Plan"
FIELD_SERVICE_KEY = "Service Key"
FIELD_TG_ID       = "Telegram Chat ID"       # existing text column
FIELD_TG_USERNAME  = "Telegram Username"     # ADD THIS column in Airtable (single line text)
FIELD_EMAIL       = "Email"                  # ADD IF NOT PRESENT
FIELD_PHONE       = "Phone"                  # ADD IF NOT PRESENT

# Status values (must match Airtable singleSelect choices exactly)
STATUS_ACTIVE       = "Active"
STATUS_PENDING      = "Pending Review"
STATUS_AWAITING     = "Awaiting Receipt"
STATUS_EXPIRED      = "Expired"
STATUS_REJECTED     = "Rejected"

# ── Links ──
REGISTRATION_URL: str = "https://coachteesos.github.io/coachtoby-site/"

# ── Rate Limits ──
RATE_LIMIT_DM: int = 5
RATE_LIMIT_MENU: int = 3
RATE_LIMIT_ESCALATION: int = 1
RATE_LIMIT_START: int = 1
COOLDOWN_ESCALATION_SEC: int = 300

# ── Service Map (mirrors website) ──
SERVICES = {
    "single":         {"label": "Single Session",          "price": 50,     "currency": "USD", "type": "coaching"},
    "monthly":        {"label": "Monthly Package",          "price": 200,    "currency": "USD", "type": "coaching"},
    "ngn-single":     {"label": "Single Session (NGN)",     "price": 70000,  "currency": "NGN", "type": "coaching"},
    "ngn-monthly":    {"label": "Monthly Package (NGN)",    "price": 300000, "currency": "NGN", "type": "coaching"},
    "group3-5":       {"label": "Group of 3-5",             "price": 20000,  "currency": "NGN", "type": "group"},
    "free-community": {"label": "Free Singers' Community",  "price": 0,      "currency": "",    "type": "community"},
    "paid-community": {"label": "Paid Singers' Community", "price": 20000,  "currency": "NGN", "type": "community"},
    "speaking":       {"label": "Speaking Engagement",     "price": 200000, "currency": "NGN", "type": "speaking"},
    "custom-plan":    {"label": "Custom Plan",              "price": 0,      "currency": "",    "type": "custom"},
    "abuja-collective": {"label": "Abuja Music Collective","price": 0,      "currency": "",    "type": "community"},
}

FLUTTERWAVE = {
    "single":           "https://flutterwave.com/pay/ictjiqq30sz7",
    "monthly":          "https://flutterwave.com/pay/b0hjfvjhv8x4",
    "ngn-single":       "https://flutterwave.com/pay/xnddgkfjeheq",
    "ngn-monthly":      "https://flutterwave.com/pay/wdod0tyeqedw",
    "group3-5":         "https://flutterwave.com/pay/lrgz2vk3xez3",
    "paid-community":   "https://flutterwave.com/pay/lrgz2vk3xez3",
    "speaking":         "https://flutterwave.com/pay/wdod0tyeqedw",
}

"""
templates/messages.py — ALL pre-written responses.
Zero AI. Zero tokens. Every string is final.
"""

# ── Main Menu ──
WELCOME_NEW = (
    "👋 **Welcome!**\n\n"
    "I'm here to help with:\n"
    "• 📅 Schedule info\n"
    "• 📝 Assignments & submissions\n"
    "• 💳 Payment status\n"
    "• ❓ Report a bottleneck\n"
    "• 📞 Contact your coach\n\n"
    "_Pick a topic below or type your question._"
)

# ── Registration Flow ──
REG_NAME_PROMPT = (
    "👋 **Welcome to Sessions with Toby!**\n\n"
    "I'll help you get started. First, what's your **full name**?\n\n"
    "_Just type your name and send it._"
)

REG_EMAIL_PROMPT = (
    "Nice to meet you, **{name}**! 👋\n\n"
    "What's your **email address**?\n\n"
    "_This is where you'll receive session confirmations._"
)

REG_PHONE_PROMPT = (
    "Great! Last one — what's your **phone number**?\n\n"
    "Include your country code (e.g., +234 for Nigeria)\n\n"
    "_This helps your coach reach you for scheduling._"
)

REG_CONFIRM = (
    "✅ **Please confirm your details:**\n\n"
    "👤 Name: {name}\n"
    "📧 Email: {email}\n"
    "📱 Phone: {phone}\n"
    "📋 Plan: {plan}\n\n"
    "Tap **✅ Confirm** to proceed to payment."
)

REG_CANCELLED = (
    "❌ Registration cancelled.\n\n"
    "No worries! Send /register anytime to start again."
)

NOT_REGISTERED = (
    "I don't have your record yet.\n\n"
    "📝 Register here first:\n{registration_url}\n\n"
    "After registering, come back and tap /start."
)

PENDING_PAYMENT = (
    "💳 **Complete Your Payment**\n\n"
    "Plan: {plan}\n"
    "Amount: {amount}\n\n"
    "Pay here: {payment_link}\n\n"
    "After payment, send me the word **PAID** ✅\n"
    "Your coach will confirm within 24 hours."
)

# ── Custom Plan Flow ──
CUSTOM_AMOUNT_PROMPT = (
    "💰 **Custom Plan**\n\n"
    "How much would you like to pay?\n\n"
    "Enter any amount (e.g., 50000 for ₦50,000 or 100 for $100).\n\n"
    "_Your coach will review and confirm._"
)

CUSTOM_NEEDS_PROMPT = (
    "Got it! **{amount}** noted.\n\n"
    "What do you need help with?\n\n"
    "_Describe your goals — vocal coaching, life coaching, or both._"
)

CUSTOM_SUBMITTED = (
    "✅ **Custom Plan Request Submitted!**\n\n"
    "Amount: {amount}\n"
    "Needs: {needs}\n\n"
    "Your coach will review and get back to you within 24 hours.\n"
    "You'll receive a payment link once approved."
)

CUSTOM_APPROVED = (
    "✅ **Custom Plan Approved!**\n\n"
    "Plan: {plan}\n"
    "Amount: {amount}\n"
    "Sessions: {sessions}\n\n"
    "Pay here: {payment_link}\n\n"
    "After payment, send **PAID** ✅"
)

WELCOME_BACK = (
    "👋 Welcome back, **{name}**!\n\n"
    "📋 Plan: {plan}\n"
    "🎯 Sessions left: {sessions_left}\n\n"
    "Your Telegram: **@{username}** (ID: `{tg_id}`)\n\n"
    "_How can I help?_"
)

WELCOME_NEW_ACTIVE = (
    "✅ **Welcome, {name}!**\n\n"
    "Your Telegram: **@{username}** (ID: `{tg_id}`)\n"
    "📋 Plan: {plan}\n"
    "🎯 Sessions: {sessions_left}\n\n"
    "_How can I help?_"
)

# ── Menu Responses ──
SCHEDULE_RESPONSE = (
    "📅 **Your Schedule**\n\n"
    "No upcoming sessions booked.\n\n"
    "To book a session, contact your coach:\n"
    "📞 Tap 'Contact Admin' below."
)

ASSIGNMENT_RESPONSE = (
    "📝 **Assignments**\n\n"
    "No active assignments right now.\n\n"
    "Your coach will send assignments after each session.\n"
    "To submit work, reply here with a voice note or text."
)

PAYMENT_STATUS_ACTIVE = (
    "💳 **Payment Status**\n\n"
    "✅ Active\n"
    "Plan: {plan}\n"
    "Sessions used: {sessions_used}/{sessions_total}\n"
    "Remaining: {sessions_left}"
)

PAYMENT_STATUS_PENDING = (
    "💳 **Payment Status**\n\n"
    "⏳ Pending\n"
    "Plan: {plan}\n"
    "Amount: {amount}\n\n"
    "Complete payment: {payment_link}"
)

PAYMENT_STATUS_OVERDUE = (
    "💳 **Payment Status**\n\n"
    "⚠️ Payment overdue\n\n"
    "Please contact your coach to reactivate:\n"
    "📞 Tap 'Contact Admin' below."
)

PAYMENT_STATUS_CUSTOM_PENDING = (
    "💳 **Custom Plan Status**\n\n"
    "⏳ Awaiting coach review\n"
    "Amount offered: {amount}\n"
    "Needs: {needs}\n\n"
    "Your coach will respond within 24 hours."
)

BOTTLENECK_RESPONSE = (
    "❓ **What's blocking you?**\n\n"
    "Describe your specific problem below.\n"
    "Your message goes **directly to your coach**.\n\n"
    "_Examples:_\n"
    "• \"I can't hit the high notes in chorus\"\n"
    "• \"I don't understand breath control\"\n"
    "• \"I need to reschedule my session\""
)

CONTACT_RESPONSE = (
    "📞 **Contact Your Coach**\n\n"
    "Coach Toby will respond directly.\n\n"
    "Type your message below — it goes straight to them.\n\n"
    "_For urgent matters, you can also reach via:_"
)

# ── Escalation ──
ESCALATION_ACK = (
    "⏳ Your message has been forwarded to your coach.\n"
    "They'll respond shortly!"
)

ESCALATION_ADMIN_FWD = (
    "📩 **Student Message**\n\n"
    "From: {student_name} (@{username}) — {plan}\n"
    "ID: #{esc_id}\n\n"
    "_{message}_\n\n"
    "Reply: `/reply {esc_id} <your message>`"
)

REPLY_SENT = "✅ Reply sent to {student_name}."
REPLY_NOT_FOUND = "❌ Escalation #{esc_id} not found or already resolved."

# ── Admin Commands ──
APPROVE_USAGE = "Usage: `/approve <telegram_id>`\n\nOr: `/pending` to see pending payments."

APPROVE_SUCCESS = (
    "✅ **Payment Approved**\n\n"
    "Student: {name} (@{telegram_id})\n"
    "Plan: {plan}\n\n"
    "Student has been notified."
)

APPROVE_NOT_FOUND = "❌ No pending payment found for ID: `{telegram_id}`."
APPROVE_ALREADY = "ℹ️ Payment already approved for `{telegram_id}`."

REJECT_SUCCESS = (
    "❌ **Payment Rejected**\n\n"
    "Student: {name} (@{telegram_id})\n"
    "Plan: {plan}\n\n"
    "Student has been notified to try again."
)

BROADCAST_USAGE = "Usage: `/broadcast <message>`\n\nSends to ALL active students."
BROADCAST_SENT = "✅ Broadcast sent to {count} students."

PENDING_HEADER = "💳 **Pending Payments**\n\n"
PENDING_ITEM = "• {name} — {plan} — {amount}\n  ID: `{telegram_id}` → `/approve {telegram_id}`\n\n"
PENDING_EMPTY = "No pending payments. 👍"

ESCALATIONS_HEADER = "📩 **Pending Escalations**\n\n"
ESCALATION_ITEM = (
    "• **#{esc_id}** — {student_name}\n"
    "  _{message}_\n"
    "  `/reply {esc_id} <message>`\n\n"
)
ESCALATIONS_EMPTY = "No pending escalations. 👍"

# ── Custom Plan Admin ──
CUSTOM_APPROVE_USAGE = (
    "Usage: `/setprice <telegram_id> <amount> <sessions>`\n\n"
    "Example: `/setprice 12345 50000 4`\n"
    "This sets the custom plan price and sends payment link to student."
)

CUSTOM_SET_SUCCESS = (
    "✅ **Custom Plan Priced**\n\n"
    "Student: {name} (@{telegram_id})\n"
    "Amount: {amount}\n"
    "Sessions: {sessions}\n\n"
    "Student has been sent the payment link."
)

# ── Rate Limit ──
RATE_LIMITED = "⏳ Please wait a moment before sending another message."

# ── Invalid Input ──
INVALID_INPUT = "I only accept text and document messages.\n\nTry again or tap /help."
NO_DOC_FILE = "Please send a **document** (PDF, JPG, PNG) — not a photo or voice note."

# ── Group Auto-Leave ──
GROUP_LEAVE_MSG = "I only work in private DMs. Bye! 👋"

# ── Help ──
HELP_TEXT = (
    "**Available Commands:**\n\n"
    "📅 — Schedule & bookings\n"
    "📝 — Assignments & submissions\n"
    "💳 — Payment status\n"
    "❓ — Report a bottleneck\n"
    "📞 — Contact your coach\n\n"
    "/help — Show this menu\n"
    "/menu — Main menu\n\n"
    "_Type a message or tap a button below._"
)

ADMIN_HELP = (
    "**Admin Commands:**\n\n"
    "/approve `<telegram_id>` — Approve payment\n"
    "/reject `<telegram_id>` — Reject payment\n"
    "/pending — List pending payments\n"
    "/reply `<esc_id> <message>` — Reply to escalated msg\n"
    "/escalations — List pending escalations\n"
    "/broadcast `<message>` — Message all active students\n"
    "/stats — Student statistics\n"
    "/setprice `<telegram_id> <amount> <sessions>` — Set custom plan price\n\n"
    "All commands work in this DM."
)

STATS_TEMPLATE = (
    "📊 **Student Statistics**\n\n"
    "Total active: {active_count}\n"
    "Pending payment: {pending_count}\n"
    "Total sessions booked: {total_sessions}\n"
    "Total revenue: {revenue}\n\n"
    "_Updated: {timestamp}_"
)

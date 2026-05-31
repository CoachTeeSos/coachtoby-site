"""
Coach Toby — Telegram Bot 2 (@Retpipebot)
===========================================
Handles new user registration, Airtable verification, strict menu flow,
payment tracking, and admin commands.

Flow:
  /start → check Airtable by Telegram ID
    → NOT FOUND: "Register here: [website URL]"
    → FOUND + pending_payment: "Complete payment: [link]"
    → FOUND + active: show strict menu

Admin commands (Toby only):
  /approve <telegram_handle>  — mark student as active
  /pending                    — list pending payment students
  /send <telegram_handle> <msg> — DM a student
  /broadcast <msg>            — message all active students
"""

import os
import logging
import json
from datetime import datetime

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ═══════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════
BOT_TOKEN = os.environ["BOT_TOKEN"]
AIRTABLE_BASE = "app3N2MFPvfDSuYxk"
AIRTABLE_TABLE = "Students"
AIRTABLE_TOKEN = os.environ["AIRTABLE_TOKEN"]
AIRTABLE_API = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{AIRTABLE_TABLE}"

# Your Telegram user ID (Toby) — you'll need to set this
ADMIN_IDS = []  # Will be populated on first /start from a user with matching Airtable record

WEBSITE_URL = "https://coachteesos.github.io/coachtoby-site/"
FLUTTERWAVE_PENDING_URL = "https://coachteesos.github.io/coachtoby-site/pricing.html"

# ═══════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════
# AIRTABLE HELPERS
# ═══════════════════════════════════════
def airtable_headers():
    return {
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type": "application/json"
    }

def find_student_by_telegram(telegram_handle: str) -> dict | None:
    """Look up a student by their Telegram @handle in Airtable."""
    # Try exact match on Telegram field
    formula = f"{{Telegram}}='{telegram_handle}'"
    params = {"filterByFormula": formula}
    try:
        resp = requests.get(AIRTABLE_API, headers=airtable_headers(), params=params, timeout=10)
        resp.raise_for_status()
        records = resp.json().get("records", [])
        if records:
            return records[0]
        # Try without @ prefix
        if telegram_handle.startswith("@"):
            formula2 = f"{{Telegram}}='{telegram_handle[1:]}'"
        else:
            formula2 = f"{{Telegram}}='@{telegram_handle}'"
        params2 = {"filterByFormula": formula2}
        resp2 = requests.get(AIRTABLE_API, headers=airtable_headers(), params=params2, timeout=10)
        resp2.raise_for_status()
        records2 = resp2.json().get("records", [])
        if records2:
            return records2[0]
    except Exception as e:
        logger.error(f"Airtable lookup failed: {e}")
    return None

def find_student_by_chat_id(chat_id: int) -> dict | None:
    """Look up a student by Telegram Chat ID."""
    formula = f"{{ChatID}}={chat_id}"
    params = {"filterByFormula": formula}
    try:
        resp = requests.get(AIRTABLE_API, headers=airtable_headers(), params=params, timeout=10)
        resp.raise_for_status()
        records = resp.json().get("records", [])
        if records:
            return records[0]
    except Exception as e:
        logger.error(f"Airtable lookup by chat_id failed: {e}")
    return None

def update_student(record_id: str, fields: dict) -> bool:
    """Update a student record in Airtable."""
    try:
        resp = requests.patch(
            f"{AIRTABLE_API}/{record_id}",
            headers=airtable_headers(),
            json={"fields": fields},
            timeout=10
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Airtable update failed: {e}")
        return False

def get_pending_students() -> list:
    """Get all students with pending_payment status."""
    formula = "{{Status}}='pending_payment'"
    params = {"filterByFormula": formula}
    try:
        resp = requests.get(AIRTABLE_API, headers=airtable_headers(), params=params, timeout=10)
        resp.raise_for_status()
        return resp.json().get("records", [])
    except Exception as e:
        logger.error(f"Airtable pending lookup failed: {e}")
        return []

def get_active_students() -> list:
    """Get all active students."""
    formula = "{{Status}}='active'"
    params = {"filterByFormula": formula}
    try:
        resp = requests.get(AIRTABLE_API, headers=airtable_headers(), params=params, timeout=10)
        resp.raise_for_status()
        return resp.json().get("records", [])
    except Exception as e:
        logger.error(f"Airtable active lookup failed: {e}")
        return []

# ═══════════════════════════════════════
# KEYBOARDS
# ═══════════════════════════════════════
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Schedule Session", callback_data="menu_schedule")],
        [InlineKeyboardButton("📝 Assignments", callback_data="menu_assignments")],
        [InlineKeyboardButton("💳 Payment", callback_data="menu_payment")],
        [InlineKeyboardButton("📞 Contact Admin", callback_data="menu_contact")],
    ])

def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("← Back to Menu", callback_data="menu_back")]
    ])

def pending_approve_keyboard(handle: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Approve Payment", callback_data=f"approve_{handle}")],
        [InlineKeyboardButton("← Back", callback_data="menu_back")]
    ])

# ═══════════════════════════════════════
# BOT HANDLERS
# ═══════════════════════════════════════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — check Airtable and route accordingly."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    username = f"@{user.username}" if user.username else ""

    # Parse deep link: /start name|serviceKey|telegram
    args = context.args
    service_key = None
    student_name = user.first_name or "there"

    if args:
        parts = args[0].split("|")
        student_name = parts[0] if parts[0] else student_name
        if len(parts) > 1:
            service_key = parts[1]
        # If deep link includes telegram handle, use it for lookup
        telegram_override = parts[2] if len(parts) > 2 else None
    else:
        telegram_override = None

    # Store chat_id in Airtable for this user
    lookup = telegram_override or username
    student = None

    if lookup:
        student = find_student_by_telegram(lookup)

    # Also try by chat_id
    if not student:
        student = find_student_by_chat_id(chat_id)

    if not student:
        # NEW USER — not in Airtable
        await update.message.reply_text(
            f"👋 Hey {student_name}!\n\n"
            f"Welcome to Sessions with Toby. To get started, please register on the website first:\n\n"
            f"🔗 {WEBSITE_URL}\n\n"
            f"Once you've signed up, come back and tap /start again.\n\n"
            f"Or if you've already registered, make sure you entered your Telegram @username correctly.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌐 Register on Website", url=WEBSITE_URL)],
                [InlineKeyboardButton("🔄 Try Again", callback_data="menu_back")]
            ])
        )
        return

    # FOUND in Airtable — update ChatID
    record_id = student["id"]
    student_fields = student["fields"]
    current_status = student_fields.get("Status", "")
    stored_name = student_fields.get("Name", student_name)

    # Save chat_id for future lookups
    update_student(record_id, {"ChatID": chat_id})

    if current_status == "pending_payment":
        # PENDING PAYMENT
        plan = student_fields.get("Plan", "your plan")
        await update.message.reply_text(
            f"👋 Welcome back, {stored_name}!\n\n"
            f"You've registered for: **{plan}**\n"
            f"Status: ⏳ Pending Payment\n\n"
            f"To complete your registration, please make your payment:\n"
            f"💳 {FLUTTERWAVE_PENDING_URL}\n\n"
            f"After payment, an admin will verify and activate your account.\n"
            f"We'll notify you here when you're approved.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 View Pricing & Pay", url=FLUTTERWAVE_PENDING_URL)],
                [InlineKeyboardButton("📞 Contact Admin", callback_data="menu_contact")]
            ])
        )
        return

    if current_status == "active":
        # ACTIVE — Show main menu
        await update.message.reply_text(
            f"👋 Welcome back, {stored_name}!\n\n"
            f"What would you like to do?",
            reply_markup=main_menu_keyboard()
        )
        return

    # Unknown status
    await update.message.reply_text(
        f"👋 Hey {stored_name}!\n\n"
        f"Your account status: {current_status}\n"
        f"Please contact an admin for assistance.",
        reply_markup=back_keyboard()
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button presses."""
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Find student
    student = find_student_by_chat_id(chat_id)
    if not student and user.username:
        student = find_student_by_telegram(f"@{user.username}")

    data = query.data

    if data == "menu_back":
        if student and student["fields"].get("Status") == "active":
            await query.edit_message_text(
                "👋 What would you like to do?",
                reply_markup=main_menu_keyboard()
            )
        else:
            await query.edit_message_text(
                f"Please register first: {WEBSITE_URL}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🌐 Register", url=WEBSITE_URL)]
                ])
            )
        return

    # Check if user is active for menu actions
    is_active = student and student["fields"].get("Status") == "active"

    if not is_active:
        await query.edit_message_text(
            f"⚠️ You need to complete registration and payment first.\n\n"
            f"Register: {WEBSITE_URL}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌐 Register", url=WEBSITE_URL)]
            ])
        )
        return

    student_name = student["fields"].get("Name", user.first_name)

    if data == "menu_schedule":
        calendar_url = "https://calendly.com/d/cx3t-9f8-b7r"
        await query.edit_message_text(
            f"📅 **Schedule a Session**\n\n"
            f"Book directly on my Calendly — pick a time that works for you.\n\n"
            f"For Monthly Package holders: all 4 sessions are included.\n"
            f"For Single Session: book your one session below.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📅 Open Calendly", url=calendar_url)],
                [InlineKeyboardButton("← Back", callback_data="menu_back")]
            ])
        )

    elif data == "menu_assignments":
        await query.edit_message_text(
            f"📝 **Assignments**\n\n"
            f"After each session, I'll send you personalized exercises here in Telegram.\n\n"
            f"Complete them before your next session. Consistency is what transforms your voice.\n\n"
            f"If you haven't received any assignments yet, you may need to complete your first session first.",
            parse_mode="Markdown",
            reply_markup=back_keyboard()
        )

    elif data == "menu_payment":
        await query.edit_message_text(
            f"💳 **Payment**\n\n"
            f"Your current plan: **{student['fields'].get('Plan', 'N/A')}**\n"
            f"Status: ✅ Active\n\n"
            f"Need to upgrade or make a new payment?\n"
            f"View all options on the website.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 View Pricing", url=FLUTTERWAVE_PENDING_URL)],
                [InlineKeyboardButton("← Back", callback_data="menu_back")]
            ])
        )

    elif data == "menu_contact":
        await query.edit_message_text(
            f"📞 **Contact Admin**\n\n"
            f"Need help? Want to talk before committing?\n\n"
            f"WhatsApp: wa.me/2349160106084\n"
            f"Email: prosperolumotobi@gmail.com\n\n"
            f"Or just reply to this message and I'll see it.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 WhatsApp", url="https://wa.me/2349160106084")],
                [InlineKeyboardButton("← Back", callback_data="menu_back")]
            ])
        )

    elif data.startswith("approve_"):
        # Admin-only: approve a student
        handle = data.replace("approve_", "")
        pending_student = find_student_by_telegram(handle)
        if pending_student:
            update_student(pending_student["id"], {"Status": "active"})
            await query.edit_message_text(
                f"✅ Approved: {pending_student['fields'].get('Name', handle)}\n"
                f"Status updated to 'active' in Airtable.\n\n"
                f"They'll now see the full menu when they tap /start.",
                reply_markup=back_keyboard()
            )
            # Notify the student
            student_chat_id = pending_student["fields"].get("ChatID")
            if student_chat_id:
                try:
                    await context.bot.send_message(
                        chat_id=int(student_chat_id),
                        text=f"🎉 {pending_student['fields'].get('Name', 'Hey')}! Your payment has been verified.\n\n"
                             f"You're now fully registered. Tap /start to access your menu.",
                    )
                except Exception as e:
                    logger.error(f"Failed to notify student: {e}")
        else:
            await query.edit_message_text(
                f"❌ Could not find pending student with handle: {handle}",
                reply_markup=back_keyboard()
            )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular text messages."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    text = update.message.text

    student = find_student_by_chat_id(chat_id)
    if not student and user.username:
        student = find_student_by_telegram(f"@{user.username}")

    if student and student["fields"].get("Status") == "active":
        # Active student — show menu + acknowledge
        name = student["fields"].get("Name", user.first_name)
        await update.message.reply_text(
            f"👋 Hey {name}!\n\n"
            f"I received your message. Use the menu below to navigate, "
            f"or contact me directly on WhatsApp: wa.me/2349160106084",
            reply_markup=main_menu_keyboard()
        )
    else:
        # Not registered or pending
        await update.message.reply_text(
            f"Please register first: {WEBSITE_URL}\n\n"
            f"Or if you've already registered, make sure your Telegram @username is correct and tap /start.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌐 Register", url=WEBSITE_URL)]
            ])
        )


# ═══════════════════════════════════════
# ADMIN COMMANDS
# ═══════════════════════════════════════
async def admin_approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/approve @username — manually approve a student's payment."""
    if not context.args:
        await update.message.reply_text("Usage: /approve @username")
        return

    handle = context.args[0]
    if not handle.startswith("@"):
        handle = "@" + handle

    student = find_student_by_telegram(handle)
    if not student:
        await update.message.reply_text(f"❌ Student not found: {handle}")
        return

    if student["fields"].get("Status") == "active":
        await update.message.reply_text(f"✅ {handle} is already active.")
        return

    success = update_student(student["id"], {"Status": "active"})
    if success:
        name = student["fields"].get("Name", handle)
        plan = student["fields"].get("Plan", "")
        await update.message.reply_text(
            f"✅ Approved: **{name}**\n"
            f"Plan: {plan}\n"
            f"Handle: {handle}\n\n"
            f"They now have full access. They'll see the menu on /start.",
            parse_mode="Markdown"
        )
        # Notify student
        chat_id = student["fields"].get("ChatID")
        if chat_id:
            try:
                await context.bot.send_message(
                    chat_id=int(chat_id),
                    text=f"🎉 {name}! Your payment has been verified and your account is now active.\n\n"
                         f"Tap /start to access your menu."
                )
            except Exception as e:
                logger.error(f"Failed to notify approved student: {e}")
    else:
        await update.message.reply_text("❌ Failed to update Airtable. Try again.")


async def admin_pending(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/pending — list all students awaiting payment verification."""
    students = get_pending_students()
    if not students:
        await update.message.reply_text("✅ No pending students.")
        return

    lines = ["⏳ **Pending Payment Students:**\n"]
    for s in students:
        f = s["fields"]
        name = f.get("Name", "?")
        handle = f.get("Telegram", "?")
        plan = f.get("Plan", "?")
        amount = f.get("Amount", "?")
        currency = f.get("Currency", "")
        lines.append(f"• {name} ({handle}) — {plan} ({currency}{amount})")

    # Approve keyboard
    buttons = []
    for s in students:
        handle = s["fields"].get("Telegram", "")
        if handle:
            buttons.append([InlineKeyboardButton(
                f"✅ Approve {s['fields'].get('Name', handle)}",
                callback_data=f"approve_{handle}"
            )])

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
    )


async def admin_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/send @username <message> — DM a student."""
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /send @username Your message here")
        return

    handle = context.args[0]
    msg = " ".join(context.args[1:])
    if not handle.startswith("@"):
        handle = "@" + handle

    student = find_student_by_telegram(handle)
    if not student:
        await update.message.reply_text(f"❌ Student not found: {handle}")
        return

    chat_id = student["fields"].get("ChatID")
    if not chat_id:
        await update.message.reply_text(f"❌ No Chat ID for {handle}. They need to /start first.")
        return

    try:
        await context.bot.send_message(chat_id=int(chat_id), text=f"📩 From Toby:\n\n{msg}")
        await update.message.reply_text(f"✅ Sent to {handle}.")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to send: {e}")


async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/broadcast <message> — message all active students."""
    if not context.args:
        await update.message.reply_text("Usage: /broadcast Your message here")
        return

    msg = " ".join(context.args)
    students = get_active_students()
    if not students:
        await update.message.reply_text("No active students to broadcast to.")
        return

    sent = 0
    failed = 0
    for s in students:
        chat_id = s["fields"].get("ChatID")
        if chat_id:
            try:
                await context.bot.send_message(
                    chat_id=int(chat_id),
                    text=f"📢 **Announcement from Toby:**\n\n{msg}",
                    parse_mode="Markdown"
                )
                sent += 1
            except Exception:
                failed += 1

    await update.message.reply_text(
        f"📢 Broadcast sent to {sent} students. {failed} failed."
    )


# ═══════════════════════════════════════
# BOT SETUP
# ═══════════════════════════════════════
def main() -> None:
    """Start the bot."""
    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve", admin_approve))
    app.add_handler(CommandHandler("pending", admin_pending))
    app.add_handler(CommandHandler("send", admin_send))
    app.add_handler(CommandHandler("broadcast", admin_broadcast))
    app.add_handler(CommandHandler("help", lambda u, c: u.message.reply_text(
        "Admin commands:\n"
        "/approve @username — approve payment\n"
        "/pending — list pending students\n"
        "/send @username msg — DM a student\n"
        "/broadcast msg — message all active students"
    )))

    # Buttons
    app.add_handler(CallbackQueryHandler(button_handler))

    # Text messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot starting — polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

"""
handlers/registration.py — Multi-step registration conversation.
Collects name, email, phone from user via chat, then writes to Airtable.
No forms. No sign-ins. Just conversation.
"""
import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler,
)

from config import SERVICES, FLUTTERWAVE, STATUS_PENDING, STATUS_ACTIVE
from services.airtable import AirtableService
from templates.messages import (
    REG_NAME_PROMPT, REG_EMAIL_PROMPT, REG_PHONE_PROMPT,
    REG_CONFIRM, REG_CANCELLED, PENDING_PAYMENT,
)

logger = logging.getLogger(__name__)

# Conversation states
NAME, EMAIL, PHONE, CONFIRM = range(4)


async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for /register — starts fresh registration."""
    context.user_data["reg_tg_id"] = str(update.effective_user.id)
    context.user_data["reg_tg_username"] = update.effective_user.username or ""
    context.user_data["reg_plan"] = "single"
    context.user_data["reg_free"] = False
    await update.message.reply_text(REG_NAME_PROMPT, parse_mode="Markdown")
    return NAME


async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store name, ask for email."""
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("❌ Name too short. Please enter your full name.")
        return NAME

    context.user_data["reg_name"] = name
    await update.message.reply_text(
        REG_EMAIL_PROMPT.format(name=name),
        parse_mode="Markdown",
    )
    return EMAIL


async def receive_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store email, ask for phone."""
    email = update.message.text.strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        await update.message.reply_text(
            "❌ That doesn't look like a valid email.\n\n"
            "Please enter a valid email (e.g., you@example.com)"
        )
        return EMAIL

    context.user_data["reg_email"] = email
    await update.message.reply_text(
        REG_PHONE_PROMPT,
        parse_mode="Markdown",
    )
    return PHONE


async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store phone, show confirmation."""
    phone = update.message.text.strip()
    digit_count = sum(c.isdigit() for c in phone)
    if digit_count < 5:
        await update.message.reply_text(
            "❌ That doesn't look like a valid phone number.\n\n"
            "Please enter your phone with country code (e.g., +234 800 000 0000)"
        )
        return PHONE

    context.user_data["reg_phone"] = phone

    name = context.user_data.get("reg_name", "")
    email = context.user_data.get("reg_email", "")
    plan = context.user_data.get("reg_plan", "single")
    svc = SERVICES.get(plan, SERVICES["single"])

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirm", callback_data="reg:confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="reg:cancel"),
        ],
        [InlineKeyboardButton("🔄 Start Over", callback_data="reg:restart")],
    ])

    await update.message.reply_text(
        REG_CONFIRM.format(
            name=name, email=email, phone=phone, plan=svc["label"]
        ),
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
    return CONFIRM


async def confirm_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User confirmed — write to Airtable, send payment link or activate."""
    query = update.callback_query
    await query.answer()

    if query.data == "reg:cancel":
        await query.edit_message_text(REG_CANCELLED, parse_mode="Markdown")
        context.user_data.clear()
        return ConversationHandler.END

    if query.data == "reg:restart":
        await query.edit_message_text(REG_NAME_PROMPT, parse_mode="Markdown")
        return NAME

    # confirmed
    user_data = context.user_data
    airtable: AirtableService = context.bot_data["airtable"]

    plan = user_data.get("reg_plan", "single")
    svc = SERVICES.get(plan, SERVICES["single"])
    is_free = user_data.get("reg_free", False) or svc.get("price", 0) == 0

    # Check if student already exists
    existing = await airtable.find_student(int(user_data["reg_tg_id"]))

    fields = {
        "Name": user_data["reg_name"],
        "Email": user_data["reg_email"],
        "Phone": user_data["reg_phone"],
        "Telegram Username": user_data.get("reg_tg_username", ""),
        "Telegram Chat ID": user_data["reg_tg_id"],
        "Service Key": plan,
        "Plan": svc["label"],
        "Source": "Telegram Bot",
        "Status": STATUS_ACTIVE if is_free else STATUS_PENDING,
    }

    if existing:
        await airtable.update_student(existing["record_id"], fields)
        logger.info(f"Updated existing student {user_data['reg_tg_id']}")
    else:
        await airtable.create_student(fields)
        logger.info(f"Created new student {user_data['reg_tg_id']}")

    if is_free:
        # Free service — activate immediately, show menu
        from handlers.start import get_main_menu_keyboard
        await query.edit_message_text(
            f"✅ **Welcome, {user_data['reg_name']}!**\n\n"
            f"You're all set. Here's what I can help with:",
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard(),
        )
    else:
        # Paid service — send payment link + back to menu button
        fw_link = FLUTTERWAVE.get(plan, "")
        amount = f"${svc['price']}" if svc['currency'] == 'USD' else f"₦{svc['price']:,}"

        from handlers.start import get_back_button
        await query.edit_message_text(
            PENDING_PAYMENT.format(
                plan=svc["label"],
                amount=amount,
                payment_link=fw_link,
            ),
            parse_mode="Markdown",
            reply_markup=get_back_button(),
        )

    context.user_data.clear()
    return ConversationHandler.END


async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel registration."""
    context.user_data.clear()
    await update.message.reply_text(REG_CANCELLED, parse_mode="Markdown")
    return ConversationHandler.END

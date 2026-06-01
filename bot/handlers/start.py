"""
handlers/start.py — /start handler + student routing logic.
"""
import logging
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import REGISTRATION_URL, ADMIN_IDS
from services.airtable import AirtableService
from templates.messages import (
    WELCOME_NEW, NOT_REGISTERED, PENDING_PAYMENT, WELCOME_BACK, HELP_TEXT,
    SCHEDULE_RESPONSE, ASSIGNMENT_RESPONSE, PAYMENT_STATUS_ACTIVE,
    PAYMENT_STATUS_PENDING, PAYMENT_STATUS_OVERDUE, BOTTLENECK_RESPONSE,
    CONTACT_RESPONSE,
)

logger = logging.getLogger(__name__)

# Inline keyboard for main menu
MAIN_MENU_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("📅 Schedule", callback_data="menu:schedule"),
        InlineKeyboardButton("📝 Assignments", callback_data="menu:assignment"),
    ],
    [
        InlineKeyboardButton("💳 Payment Status", callback_data="menu:payment"),
        InlineKeyboardButton("❓ Bottleneck", callback_data="menu:bottleneck"),
    ],
    [
        InlineKeyboardButton("📞 Contact Admin", callback_data="menu:contact"),
    ],
    [
        InlineKeyboardButton("👋 Main Menu", callback_data="menu:home"),
    ],
])


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start — route based on Airtable record."""
    user = update.effective_user
    bot_data = context.bot_data
    airtable: AirtableService = bot_data["airtable"]

    logger.info(f"/start from {user.id} (@{user.username}) — checking Airtable")

    student = await airtable.find_student(user.id)

    if not student:
        # Not registered — send registration link
        await update.message.reply_text(
            NOT_REGISTERED.format(registration_url=REGISTRATION_URL),
            parse_mode="Markdown",
        )
        return

    status = (student.get("status", "") or "").strip().lower()
    name = student.get("name", "there")
    plan = student.get("plan", "No plan")
    sessions_used = student.get("sessions_used", 0)
    total_sessions = student.get("total_sessions", 0)
    sessions_left = max(0, total_sessions - sessions_used)

    # Normalize status (Airtable uses "Active", "Pending Review", etc.)
    status = (student.get("status") or "").strip().lower()

    if status in ("pending review", "awaiting receipt", "pending_payment"):
        from config import SERVICES, FLUTTERWAVE
        svc_key = student.get("service_key", "single")
        svc = SERVICES.get(svc_key, SERVICES["single"])
        fw_link = FLUTTERWAVE.get(svc_key, "")
        amount_display = f"${svc['price']}" if svc['currency'] == 'USD' else f"₦{svc['price']:,}"

        await update.message.reply_text(
            PENDING_PAYMENT.format(
                plan=svc["label"],
                amount=amount_display,
                payment_link=fw_link,
            ),
            parse_mode="Markdown",
        )
        return

    if status in ("expired", "rejected"):
        await update.message.reply_text(
            PAYMENT_STATUS_OVERDUE,
            parse_mode="Markdown",
            reply_markup=MAIN_MENU_KEYBOARD,
        )
        return

    # Active student (status == "active") — welcome back + menu
    await update.message.reply_text(
        WELCOME_BACK.format(
            name=name,
            plan=plan,
            sessions_left=sessions_left,
        ),
        parse_mode="Markdown",
        reply_markup=MAIN_MENU_KEYBOARD,
    )


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    return MAIN_MENU_KEYBOARD


def get_back_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("👈 Back to Menu", callback_data="menu:home"),
    ]])

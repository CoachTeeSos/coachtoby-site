"""
handlers/menu.py — Main menu callbacks + message routing.
All responses are pre-written. 0 AI tokens.
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.start import get_main_menu_keyboard
from services.airtable import AirtableService
from services.router import categorize
from templates.messages import (
    SCHEDULE_RESPONSE, ASSIGNMENT_RESPONSE,
    PAYMENT_STATUS_ACTIVE, PAYMENT_STATUS_PENDING,
    BOTTLENECK_RESPONSE, CONTACT_RESPONSE,
    ESCALATION_ACK, ESCALATION_ADMIN_FWD,
    WELCOME_NEW, HELP_TEXT,
)

logger = logging.getLogger(__name__)


async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button presses."""
    query = update.callback_query
    await query.answer()

    data = query.data
    user = query.from_user
    airtable: AirtableService = context.bot_data["airtable"]

    if data == "menu:home":
        student = await airtable.find_student(user.id)
        name = student.get("name", "there") if student else "there"
        plan = student.get("plan", "") if student else ""
        sessions_left = max(0, (student.get("total_sessions", 0) if student else 0)
                            - (student.get("sessions_used", 0) if student else 0))

        await query.edit_message_text(
            WELCOME_NEW if not student else (
                f"👋 Welcome back, **{name}**!\n\n"
                f"📋 Plan: {plan}\n"
                f"🎯 Sessions left: {sessions_left}\n\n"
                "_How can I help?_"
            ),
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    if data == "menu:schedule":
        await query.edit_message_text(
            SCHEDULE_RESPONSE,
            parse_mode="Markdown",
            reply_markup=_back_keyboard(),
        )
        return

    if data == "menu:assignment":
        await query.edit_message_text(
            ASSIGNMENT_RESPONSE,
            parse_mode="Markdown",
            reply_markup=_back_keyboard(),
        )
        return

    if data == "menu:payment":
        student = await airtable.find_student(user.id)
        if student and student.get("status") == "Active":
            sessions_used = student.get("sessions_used", 0)
            total = student.get("total_sessions", 0)
            await query.edit_message_text(
                PAYMENT_STATUS_ACTIVE.format(
                    plan=student.get("plan", ""),
                    sessions_used=sessions_used,
                    sessions_total=total,
                    sessions_left=max(0, total - sessions_used),
                ),
                parse_mode="Markdown",
                reply_markup=_back_keyboard(),
            )
        elif student and student.get("status") in ("Pending Review", "Awaiting Receipt"):
            from config import SERVICES, FLUTTERWAVE
            svc_key = student.get("service_key", "single")
            svc = SERVICES.get(svc_key, SERVICES["single"])
            fw_link = FLUTTERWAVE.get(svc_key, "")
            amount = f"${svc['price']}" if svc['currency'] == 'USD' else f"₦{svc['price']:,}"
            await query.edit_message_text(
                PAYMENT_STATUS_PENDING.format(
                    plan=svc["label"], amount=amount, payment_link=fw_link,
                ),
                parse_mode="Markdown",
                reply_markup=_back_keyboard(),
            )
        else:
            await query.edit_message_text(
                "💳 No payment record found.\n\nRegister here: https://coachteesos.github.io/coachtoby-site/",
                reply_markup=_back_keyboard(),
            )
        return

    if data == "menu:bottleneck":
        await query.edit_message_text(
            BOTTLENECK_RESPONSE,
            parse_mode="Markdown",
            reply_markup=_back_keyboard(),
        )
        return

    if data == "menu:contact":
        await query.edit_message_text(
            CONTACT_RESPONSE,
            parse_mode="Markdown",
            reply_markup=_back_keyboard(),
        )
        return

    # Unknown callback
    logger.warning(f"Unknown callback: {data}")
    await query.edit_message_text("Something went wrong. Try /start.")


async def dm_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all DM text messages — categorize and route."""
    user = update.effective_user
    text = update.message.text or ""
    airtable: AirtableService = context.bot_data["airtable"]

    # Ignore non-text (voices, stickers, etc.)
    if not update.message.text:
        from templates.messages import INVALID_INPUT
        await update.message.reply_text(INVALID_INPUT)
        return

    # Check if user is admin (admins use commands, not this handler)
    from config import ADMIN_IDS
    if user.id in ADMIN_IDS:
        return  # Admin commands handled separately

    # Check Airtable
    student = await airtable.find_student(user.id)
    if not student:
        from templates.messages import NOT_REGISTERED
        from config import REGISTRATION_URL
        await update.message.reply_text(
            NOT_REGISTERED.format(registration_url=REGISTRATION_URL),
            parse_mode="Markdown",
        )
        return

    if student.get("status") in ("Pending Review", "Awaiting Receipt"):
        from templates.messages import PENDING_PAYMENT
        from config import SERVICES, FLUTTERWAVE
        svc_key = student.get("service_key", "single")
        svc = SERVICES.get(svc_key, SERVICES["single"])
        fw_link = FLUTTERWAVE.get(svc_key, "")
        amount = f"${svc['price']}" if svc['currency'] == 'USD' else f"₦{svc['price']:,}"

        # Check if they said "PAID" or similar
        if text.strip().upper() in ("PAID", "✅", "DONE", "I PAID", "PAYMENT DONE"):
            from handlers.payment import handle_paid_claim
            await handle_paid_claim(update, context, student)
            return

        await update.message.reply_text(
            PENDING_PAYMENT.format(
                plan=svc["label"], amount=amount, payment_link=fw_link,
            ),
            parse_mode="Markdown",
        )
        return

    if student.get("status") in ("Expired", "Rejected"):
        from templates.messages import PAYMENT_STATUS_OVERDUE
        await update.message.reply_text(
            PAYMENT_STATUS_OVERDUE,
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    # Active student — categorize the message
    category = categorize(text)

    if category == "schedule":
        await update.message.reply_text(
            SCHEDULE_RESPONSE, parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard(),
        )
    elif category == "assignment":
        await update.message.reply_text(
            ASSIGNMENT_RESPONSE, parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard(),
        )
    elif category == "payment":
        sessions_used = student.get("sessions_used", 0)
        total = student.get("total_sessions", 0)
        await update.message.reply_text(
            PAYMENT_STATUS_ACTIVE.format(
                plan=student.get("plan", ""),
                sessions_used=sessions_used,
                sessions_total=total,
                sessions_left=max(0, total - sessions_used),
            ),
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard(),
        )
    elif category == "bottleneck":
        await update.message.reply_text(
            BOTTLENECK_RESPONSE, parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard(),
        )
    elif category == "contact":
        await update.message.reply_text(
            CONTACT_RESPONSE, parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard(),
        )
    elif category == "menu":
        await update.message.reply_text(
            HELP_TEXT, parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard(),
        )
    else:
        # OFF-TOPIC → escalate to admin
        await _escalate_to_admin(update, context, student, airtable)


async def _escalate_to_admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    student: dict,
    airtable: AirtableService,
):
    """Forward off-topic message to admin. Student gets ack. 0 AI tokens."""
    from config import ADMIN_IDS

    user = update.effective_user
    text = update.message.text or ""

    # Log escalation locally
    esc_id = await airtable.log_escalation(
        telegram_id=user.id,
        message_text=text,
        forwarded_to=ADMIN_IDS[0],
    )

    # Forward to each admin
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=ESCALATION_ADMIN_FWD.format(
                    student_name=student.get("name", "Unknown"),
                    username=user.username or "no_username",
                    plan=student.get("plan", ""),
                    esc_id=esc_id,
                    message=text[:500],  # Cap length
                ),
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Failed to forward escalation to admin {admin_id}: {e}")

    # Ack student
    await update.message.reply_text(
        ESCALATION_ACK,
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(),
    )
    logger.info(f"Escalation #{esc_id} from {user.id}: {text[:50]}")


def _back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("👈 Back to Menu", callback_data="menu:home"),
    ]])

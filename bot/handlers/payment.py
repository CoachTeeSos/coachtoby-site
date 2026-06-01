"""
handlers/payment.py — Payment claim and approval flow.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS, SERVICES, FLUTTERWAVE
from services.airtable import AirtableService
from templates.messages import (
    ESCALATION_ACK, APPROVE_SUCCESS, APPROVE_NOT_FOUND,
    APPROVE_ALREADY, REJECT_SUCCESS, ESCALATION_ADMIN_FWD,
)

logger = logging.getLogger(__name__)


async def handle_paid_claim(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    student: dict,
):
    """Student claims they've paid. Notify admin for verification."""
    user = update.effective_user
    airtable: AirtableService = context.bot_data["airtable"]

    # Log the pending payment
    svc_key = student.get("service_key", "single")
    svc = SERVICES.get(svc_key, SERVICES["single"])
    await airtable.log_pending_payment(
        telegram_id=user.id,
        service_key=svc_key,
        amount=svc["price"],
    )

    # Notify admins
    amount = f"${svc['price']}" if svc['currency'] == 'USD' else f"₦{svc['price']:,}"
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    "💳 **Payment Claim**\n\n"
                    f"Student: {student.get('name', 'Unknown')} (`{user.id}`)\n"
                    f"Plan: {svc['label']}\n"
                    f"Amount: {amount}\n\n"
                    f"Approve: `/approve {user.id}`\n"
                    f"Reject: `/reject {user.id}`"
                ),
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")

    await update.message.reply_text(
        ESCALATION_ACK,
        parse_mode="Markdown",
    )


async def approve_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /approve <telegram_id> — confirm payment + activate student."""
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return

    if not context.args:
        await update.message.reply_text("Usage: `/approve <telegram_id>`", parse_mode="Markdown")
        return

    target_id = context.args[0].strip()
    # Strip @ if present
    target_id = target_id.lstrip("@")

    airtable: AirtableService = context.bot_data["airtable"]

    # Find student
    student = await airtable.find_student(target_id)
    if not student:
        await update.message.reply_text(
            APPROVE_NOT_FOUND.format(telegram_id=target_id),
            parse_mode="Markdown",
        )
        return

    if student.get("status") == "Active":
        await update.message.reply_text(
            APPROVE_ALREADY.format(telegram_id=target_id),
            parse_mode="Markdown",
        )
        return

    # Update Airtable
    record_id = student.get("record_id", "")
    svc_key = student.get("service_key", "single")
    svc = SERVICES.get(svc_key, SERVICES["single"])

    # Set total sessions based on plan
    total_sessions = 4 if "monthly" in svc_key.lower() or svc.get("type") == "coaching" else 1

    success = await airtable.update_student(record_id, {
        "Status": "Active",
        "Total Sessions": total_sessions,
        "Sessions Used": 0,
    })

    if not success:
        await update.message.reply_text("❌ Failed to update Airtable. Try again.")
        return

    # Update local cache
    await airtable.mark_payment_approved(int(target_id))

    # Notify student
    try:
        from handlers.start import get_main_menu_keyboard
        await context.bot.send_message(
            chat_id=int(target_id),
            text=(
                "✅ **Payment Confirmed!**\n\n"
                f"Plan: {svc['label']}\n"
                f"Sessions: {total_sessions}\n\n"
                "Welcome aboard! Here's what I can help you with:"
            ),
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard(),
        )
    except Exception as e:
        logger.error(f"Failed to notify student {target_id}: {e}")

    await update.message.reply_text(
        APPROVE_SUCCESS.format(
            name=student.get("name", ""),
            username=target_id,
            plan=svc["label"],
            telegram_id=target_id,
        ),
        parse_mode="Markdown",
    )


async def reject_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /reject <telegram_id>."""
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return

    if not context.args:
        await update.message.reply_text("Usage: `/reject <telegram_id>`", parse_mode="Markdown")
        return

    target_id = context.args[0].strip().lstrip("@")
    airtable: AirtableService = context.bot_data["airtable"]

    student = await airtable.find_student(target_id)
    if not student:
        await update.message.reply_text(
            APPROVE_NOT_FOUND.format(telegram_id=target_id),
            parse_mode="Markdown",
        )
        return

    record_id = student.get("record_id", "")
    await airtable.update_student(record_id, {"Status": "rejected"})

    # Notify student
    try:
        await context.bot.send_message(
            chat_id=int(target_id),
            text=(
                "❌ **Payment Could Not Be Verified**\n\n"
                "Please double-check your payment and try again.\n"
                "Contact your coach if you believe this is an error."
            ),
        )
    except Exception as e:
        logger.error(f"Failed to notify student {target_id}: {e}")

    await update.message.reply_text(
        REJECT_SUCCESS.format(
            name=student.get("name", ""),
            username=target_id,
            plan=student.get("plan", ""),
            telegram_id=target_id,
        ),
        parse_mode="Markdown",
    )


async def pending_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /pending — list all pending payments."""
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return

    airtable: AirtableService = context.bot_data["airtable"]
    pending = await airtable.get_all_pending_payments()

    if not pending:
        await update.message.reply_text("No pending payments. 👍")
        return

    from templates.messages import PENDING_HEADER, PENDING_ITEM
    lines = [PENDING_HEADER]
    for i, p in enumerate(pending, 1):
        svc = SERVICES.get(p["service_key"], {})
        amount = f"${svc.get('price', '?')}" if svc.get('currency') == 'USD' else f"₦{svc.get('price', '?'):,}"
        lines.append(PENDING_ITEM.format(
            name=f"Student #{p['telegram_id']}",
            plan=svc.get('label', p['service_key']),
            amount=amount,
            telegram_id=p['telegram_id'],
        ))

    await update.message.reply_text("".join(lines), parse_mode="Markdown")

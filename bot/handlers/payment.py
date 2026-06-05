"""
handlers/payment.py — Payment claim, approval, and custom plan pricing.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS, SERVICES, FLUTTERWAVE
from services.airtable import AirtableService
from templates.messages import (
    ESCALATION_ACK, APPROVE_SUCCESS, APPROVE_NOT_FOUND,
    APPROVE_ALREADY, REJECT_SUCCESS,
    CUSTOM_APPROVE_USAGE, CUSTOM_SET_SUCCESS,
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

    svc_key = student.get("service_key", "single")
    svc = SERVICES.get(svc_key, SERVICES["single"])
    await airtable.log_pending_payment(
        telegram_id=user.id,
        service_key=svc_key,
        amount=svc["price"],
    )

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

    # Check if student sent a photo/document (payment slip)
    if update.message.photo or update.message.document:
        # Forward the slip to admin
        for admin_id in ADMIN_IDS:
            try:
                if update.message.photo:
                    await context.bot.send_photo(
                        chat_id=admin_id,
                        photo=update.message.photo[-1].file_id,
                        caption=f"📸 Payment slip from {student.get('name', 'Unknown')} (`{user.id}`)",
                    )
                elif update.message.document:
                    await context.bot.send_document(
                        chat_id=admin_id,
                        document=update.message.document.file_id,
                        caption=f"📄 Payment slip from {student.get('name', 'Unknown')} (`{user.id}`)",
                    )
            except Exception as e:
                logger.error(f"Failed to forward slip to admin {admin_id}: {e}")

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

    target_id = context.args[0].strip().lstrip("@")
    airtable: AirtableService = context.bot_data["airtable"]

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

    record_id = student.get("record_id", "")
    svc_key = student.get("service_key", "single")
    svc = SERVICES.get(svc_key, SERVICES["single"])

    # Set total sessions based on plan
    if svc.get("type") == "coaching":
        total_sessions = 4 if "monthly" in svc_key.lower() else 1
    elif svc.get("type") == "group":
        total_sessions = 8
    else:
        total_sessions = 1

    success = await airtable.update_student(record_id, {
        "Status": "Active",
        "Total Sessions": total_sessions,
        "Sessions Used": 0,
    })

    if not success:
        await update.message.reply_text("❌ Failed to update Airtable. Try again.")
        return

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
    await airtable.update_student(record_id, {"Status": "Rejected"})

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

    # Also get pending from Airtable (students with Pending Review status)
    from templates.messages import PENDING_HEADER, PENDING_ITEM
    from config import SERVICES

    pending_students = await airtable.get_pending_payments()

    if not pending_students:
        await update.message.reply_text("No pending payments. 👍")
        return

    lines = [PENDING_HEADER]
    for i, s in enumerate(pending_students, 1):
        svc_key = s.get("service_key", "single")
        svc = SERVICES.get(svc_key, {})
        amount = f"${svc.get('price', '?')}" if svc.get('currency') == 'USD' else f"₦{svc.get('price', '?'):,}"
        plan_label = svc.get('label', svc_key) if svc else svc_key
        lines.append(PENDING_ITEM.format(
            name=f"{s.get('name', 'Unknown')} ({s.get('telegram_id', '?')})",
            plan=plan_label,
            amount=amount,
            telegram_id=s.get('telegram_id', '?'),
        ))

    await update.message.reply_text("".join(lines), parse_mode="Markdown")


async def setprice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /setprice <telegram_id> <amount> <sessions> — set custom plan price."""
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return

    if not context.args or len(context.args) < 3:
        await update.message.reply_text(
            CUSTOM_APPROVE_USAGE,
            parse_mode="Markdown",
        )
        return

    target_id = context.args[0].strip().lstrip("@")
    try:
        amount = int(context.args[1].strip())
        sessions = int(context.args[2].strip())
    except ValueError:
        await update.message.reply_text("❌ Amount and sessions must be numbers.")
        return

    airtable: AirtableService = context.bot_data["airtable"]
    student = await airtable.find_student(target_id)

    if not student:
        await update.message.reply_text(
            APPROVE_NOT_FOUND.format(telegram_id=target_id),
            parse_mode="Markdown",
        )
        return

    record_id = student.get("record_id", "")

    # Update Airtable with priced custom plan
    await airtable.update_student(record_id, {
        "Status": "Pending Review",
        "Plan": f"Custom Plan — ₦{amount:,}",
        "Budget": str(amount),
        "Total Sessions": sessions,
        "Service Key": "custom-plan",
        "Amount Paid": amount,
    })

    # Notify student — direct them to contact coach for payment link
    try:
        await context.bot.send_message(
            chat_id=int(target_id),
            text=(
                f"✅ **Custom Plan Approved!**\n\n"
                f"Plan: Custom Plan\n"
                f"Amount: ₦{amount:,}\n"
                f"Sessions: {sessions}\n\n"
                f"Your coach has set up your custom plan.\n"
                f"Contact your coach to complete payment:\n"
                f"📞 https://t.me/{student.get('Telegram_Username', 'coachteeos')}"
            ),
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Failed to notify student {target_id}: {e}")

    # Notify admin with payment instructions
    await update.message.reply_text(
        f"✅ **Custom Plan Priced**\n\n"
        f"Student: {student.get('name', '')} (`{target_id}`)\n"
        f"Amount: ₦{amount:,}\n"
        f"Sessions: {sessions}\n\n"
        f"Student has been notified to contact you for payment.\n"
        f"Send them a Flutterwave payment link or bank details.\n"
        f"Once paid, use `/approve {target_id}` to activate.",
        parse_mode="Markdown",
    )

"""
handlers/admin.py — Admin-only commands: /reply, /broadcast, /stats, /escalations, /setprice.
Also handles command polling from Hermes via Airtable.
"""
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS
from services.airtable import AirtableService
from templates.messages import (
    REPLY_SENT, REPLY_NOT_FOUND, BROADCAST_USAGE, BROADCAST_SENT,
    ADMIN_HELP, STATS_TEMPLATE,
    ESCALATIONS_HEADER, ESCALATION_ITEM, ESCALATIONS_EMPTY,
)

logger = logging.getLogger(__name__)


async def admin_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return
    await update.message.reply_text(ADMIN_HELP, parse_mode="Markdown")


async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /reply <esc_id> <message> — reply to escalated student message."""
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Usage: `/reply <message_id> <your message>`\n\n"
            "Example: `/reply 42 Thanks for reaching out! Let's schedule a call.`",
            parse_mode="Markdown",
        )
        return

    esc_id = context.args[0]
    reply_text = " ".join(context.args[1:])
    airtable: AirtableService = context.bot_data["airtable"]

    esc = await airtable.get_escalation(int(esc_id))
    if not esc:
        await update.message.reply_text(
            REPLY_NOT_FOUND.format(esc_id=esc_id),
            parse_mode="Markdown",
        )
        return

    student_id = esc["telegram_id"]
    try:
        await context.bot.send_message(
            chat_id=student_id,
            text=f"**From your coach:**\n\n{reply_text}",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Failed to send reply to {student_id}: {e}")
        await update.message.reply_text(f"❌ Could not reach student {student_id}.")
        return

    await airtable.reply_escalation(int(esc_id), reply_text)
    await update.message.reply_text(
        REPLY_SENT.format(student_name=f"Student #{student_id}"),
    )


async def escalations_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /escalations — list pending escalations."""
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return

    airtable: AirtableService = context.bot_data["airtable"]
    pending = await airtable.get_pending_escalations()

    if not pending:
        await update.message.reply_text(ESCALATIONS_EMPTY)
        return

    lines = [ESCALATIONS_HEADER]
    for esc in pending:
        lines.append(ESCALATION_ITEM.format(
            esc_id=esc["id"],
            student_name=f"Student #{esc['telegram_id']}",
            message=(esc["message_text"] or "")[:100],
        ))

    await update.message.reply_text("".join(lines), parse_mode="Markdown")


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /broadcast <message> — send to all active students."""
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return

    if not context.args:
        await update.message.reply_text(BROADCAST_USAGE, parse_mode="Markdown")
        return

    broadcast_text = " ".join(context.args)
    airtable: AirtableService = context.bot_data["airtable"]

    active_students = await airtable.get_all_active_students()

    if not active_students:
        await update.message.reply_text("No active students to broadcast to.")
        return

    sent = 0
    failed = 0
    for student in active_students:
        sid = student.get("telegram_id", "")
        if not sid:
            continue
        try:
            await context.bot.send_message(
                chat_id=int(sid),
                text=f"📢 **Announcement**\n\n{broadcast_text}",
                parse_mode="Markdown",
            )
            sent += 1
        except Exception as e:
            logger.warning(f"Broadcast failed for {sid}: {e}")
            failed += 1

    await update.message.reply_text(
        BROADCAST_SENT.format(count=f"{sent} sent, {failed} failed"),
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /stats — student statistics."""
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return

    airtable: AirtableService = context.bot_data["airtable"]

    active = await airtable.get_all_active_students()
    pending = await airtable.get_pending_payments()

    total_sessions = sum(s.get("sessions_used", 0) for s in active)

    from config import SERVICES
    revenue = 0
    for s in active:
        svc = SERVICES.get(s.get("service_key", ""), {})
        revenue += svc.get("price", 0)

    await update.message.reply_text(
        STATS_TEMPLATE.format(
            active_count=len(active),
            pending_count=len(pending),
            total_sessions=total_sessions,
            revenue=f"${revenue:,}" if revenue < 10000 else f"₦{revenue:,}",
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        ),
        parse_mode="Markdown",
    )


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /menu — show main menu to any user."""
    from handlers.start import get_main_menu_keyboard, WELCOME_NEW
    await update.message.reply_text(
        WELCOME_NEW,
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(),
    )


# ── Hermes Command Polling ──

async def poll_commands_job(context: ContextTypes.DEFAULT_TYPE):
    """Poll SQLite commands table for pending commands from Hermes."""
    airtable: AirtableService = context.bot_data["airtable"]
    bot = context.bot

    try:
        commands = await airtable.poll_pending_commands()
        for cmd in commands:
            cmd_id = cmd["id"]
            command = cmd["command"]
            target_id = cmd["target_id"]
            params = cmd["params"] or ""

            result = ""

            if command == "approve":
                # Approve a student's payment
                student = await airtable.find_student(int(target_id))
                if student and student.get("status") != "Active":
                    svc_key = student.get("service_key", "single")
                    svc = __import__("config", fromlist=["SERVICES"]).SERVICES.get(svc_key, {})
                    total_sessions = 4 if "monthly" in svc_key.lower() else 1
                    await airtable.update_student(student["record_id"], {
                        "Status": "Active",
                        "Total Sessions": total_sessions,
                        "Sessions Used": 0,
                    })
                    # Notify student
                    try:
                        from handlers.start import get_main_menu_keyboard
                        await bot.send_message(
                            chat_id=int(target_id),
                            text=f"✅ **Payment Confirmed!**\n\nWelcome aboard!",
                            parse_mode="Markdown",
                            reply_markup=get_main_menu_keyboard(),
                        )
                    except Exception:
                        pass
                    result = f"Approved {target_id}"
                else:
                    result = f"Already active or not found: {target_id}"

            elif command == "reject":
                student = await airtable.find_student(int(target_id))
                if student:
                    await airtable.update_student(student["record_id"], {"Status": "Rejected"})
                    result = f"Rejected {target_id}"
                else:
                    result = f"Not found: {target_id}"

            elif command == "setprice":
                # params = "amount,sessions"
                parts = params.split(",")
                if len(parts) >= 2:
                    amount = int(parts[0])
                    sessions = int(parts[1])
                    student = await airtable.find_student(int(target_id))
                    if student:
                        await airtable.update_student(student["record_id"], {
                            "Status": "Pending Review",
                            "Budget": str(amount),
                            "Total Sessions": sessions,
                        })
                        result = f"Set price {amount} / {sessions} sessions for {target_id}"
                    else:
                        result = f"Not found: {target_id}"
                else:
                    result = f"Invalid params: {params}"

            else:
                result = f"Unknown command: {command}"

            await airtable.mark_command_executed(cmd_id, result)
            logger.info(f"Command #{cmd_id} executed: {result}")

    except Exception as e:
        logger.error(f"Command poll job failed: {e}")

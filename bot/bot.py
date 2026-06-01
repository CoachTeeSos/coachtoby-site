"""
bot.py — Bot 2 Entry Point: @Retpipebot
Student-facing service bot. Strict menus. 0 AI tokens.
"""
import logging
import sys

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

from config import BOT_TOKEN, ADMIN_IDS
from services.airtable import AirtableService
from services.payment_verifier import verify_payments_job
from handlers.start import start_handler
from handlers.registration import (
    receive_name, receive_email, receive_phone,
    confirm_registration, cancel_registration,
    NAME, EMAIL, PHONE, CONFIRM,
)
from handlers.menu import menu_callback_handler, dm_message_handler
from handlers.group import group_message_handler
from handlers.payment import approve_command, reject_command, pending_command
from handlers.admin import (
    admin_help_command, reply_command, escalations_command,
    broadcast_command, stats_command,
)

logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s: %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def payment_poll_job(context: ContextTypes.DEFAULT_TYPE):
    """Recurring job: check Airtable for newly activated students."""
    airtable: AirtableService = context.bot_data["airtable"]
    bot = context.bot

    try:
        active_students = await airtable.get_all_active_students()
        welcomed_set = context.bot_data.get("_welcomed", set())

        for student in active_students:
            tid = str(student.get("telegram_id", "")).strip()
            if not tid or tid in welcomed_set:
                continue

            record = await airtable.find_student(int(tid))
            if not record or record.get("status", "").lower() != "active":
                continue

            from handlers.start import get_main_menu_keyboard
            name = record.get("name", "there")
            plan = record.get("plan", "")
            sessions_used = record.get("sessions_used", 0)
            total = record.get("total_sessions", 0)
            sessions_left = max(0, total - sessions_used)

            try:
                await bot.send_message(
                    chat_id=int(tid),
                    text=(
                        f"✅ **Payment Confirmed!**\n\n"
                        f"Welcome aboard, **{name}**!\n"
                        f"📋 Plan: {plan}\n"
                        f"🎯 Sessions left: {sessions_left}\n\n"
                        f"Here's what I can help you with:"
                    ),
                    parse_mode="Markdown",
                    reply_markup=get_main_menu_keyboard(),
                )
                welcomed_set.add(tid)
                context.bot_data["_welcomed"] = welcomed_set
                logger.info(f"Auto-welcomed student {tid} ({name})")
            except Exception as e:
                logger.warning(f"Failed to welcome {tid}: {e}")
    except Exception as e:
        logger.error(f"Payment poll job failed: {e}")


def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set. Exiting.")
        sys.exit(1)

    app = Application.builder().token(BOT_TOKEN).build()

    # ── Initialize Services ──
    airtable = AirtableService(db_path="bot_cache.db")
    loop = __import__("asyncio").new_event_loop()
    loop.run_until_complete(airtable.init_db())

    app.bot_data["airtable"] = airtable
    app.bot_data["_welcomed"] = set()

    # ── Job Queue ──
    job_queue = app.job_queue
    job_queue.run_repeating(payment_poll_job, interval=60, first=10, name="payment_poll")
    job_queue.run_repeating(verify_payments_job, interval=120, first=30, name="fw_verify")

    # ── Handlers ──
    # Registration conversation (must be before /start CommandHandler)
    reg_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start_handler)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_email)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone)],
            CONFIRM: [CallbackQueryHandler(confirm_registration, pattern="^reg:")],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_registration),
            CommandHandler("start", start_handler),
        ],
        per_message=False,
    )
    app.add_handler(reg_conv)

    app.add_handler(CommandHandler("approve", approve_command))
    app.add_handler(CommandHandler("reject", reject_command))
    app.add_handler(CommandHandler("pending", pending_command))
    app.add_handler(CommandHandler("reply", reply_command))
    app.add_handler(CommandHandler("escalations", escalations_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("adminhelp", admin_help_command))
    app.add_handler(CallbackQueryHandler(menu_callback_handler))
    app.add_handler(MessageHandler(filters.ChatType.GROUPS, group_message_handler), group=1)
    app.add_handler(
        MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND & filters.TEXT, dm_message_handler),
        group=2,
    )
    app.add_handler(
        MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND & ~filters.TEXT, dm_message_handler),
        group=3,
    )

    logger.info("Bot 2 (@Retpipebot) starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()

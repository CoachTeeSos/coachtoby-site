"""
handlers/start.py — /start handler + student routing logic.
New users get a conversation flow (name → email → phone).
Custom plan users get amount → needs → submitted.
Returning users get routed by Airtable status.
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from config import ADMIN_IDS, SERVICES, FLUTTERWAVE, STATUS_CUSTOM, STATUS_ACTIVE, STATUS_PENDING
from services.airtable import AirtableService
from templates.messages import (
    WELCOME_NEW, NOT_REGISTERED, PENDING_PAYMENT, WELCOME_BACK,
    REG_NAME_PROMPT, REG_EMAIL_PROMPT, REG_PHONE_PROMPT,
    REG_CONFIRM, REG_CANCELLED,
    CUSTOM_AMOUNT_PROMPT, CUSTOM_NEEDS_PROMPT, CUSTOM_SUBMITTED,
    PAYMENT_STATUS_CUSTOM_PENDING,
)
from handlers.registration import (
    receive_name, receive_email, receive_phone,
    confirm_registration, cancel_registration,
    NAME, EMAIL, PHONE, CONFIRM,
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

# Custom plan states (extend registration states)
CUSTOM_AMOUNT, CUSTOM_NEEDS = range(10, 12)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start — route based on Airtable record or start new registration."""
    user = update.effective_user
    bot_data = context.bot_data
    airtable: AirtableService = bot_data["airtable"]

    logger.info(f"/start from {user.id} (@{user.username}) — checking Airtable")

    # Check if returning student
    student = await airtable.find_student(user.id)

    if student:
        # ── RETURNING STUDENT ──
        status = (student.get("status") or "").strip()
        name = student.get("name", "there")
        plan = student.get("plan", "No plan")
        sessions_used = student.get("sessions_used", 0)
        total_sessions = student.get("total_sessions", 0)
        sessions_left = max(0, total_sessions - sessions_used)

        # Active → welcome back + menu
        if status == "Active":
            await update.message.reply_text(
                WELCOME_BACK.format(
                    name=name, plan=plan, sessions_left=sessions_left,
                    username=user.username or "no_username", tg_id=user.id,
                ),
                parse_mode="Markdown",
                reply_markup=MAIN_MENU_KEYBOARD,
            )
            return ConversationHandler.END

        # Pending payment → show payment link
        if status in ("Pending Review", "Awaiting Receipt"):
            svc_key = student.get("service_key", "single")
            svc = SERVICES.get(svc_key, SERVICES["single"])
            fw_link = FLUTTERWAVE.get(svc_key, "")
            amount_display = f"${svc['price']}" if svc['currency'] == 'USD' else f"₦{svc['price']:,}"
            await update.message.reply_text(
                PENDING_PAYMENT.format(plan=svc["label"], amount=amount_display, payment_link=fw_link),
                parse_mode="Markdown",
            )
            return ConversationHandler.END

        # Custom plan pending → show status
        if status == STATUS_CUSTOM:
            await update.message.reply_text(
                PAYMENT_STATUS_CUSTOM_PENDING.format(
                    amount=student.get("budget", ""),
                    needs=student.get("needs", ""),
                ),
                parse_mode="Markdown",
            )
            return ConversationHandler.END

        # Expired/Rejected → show overdue + give menu option to re-register
        if status in ("Expired", "Rejected"):
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Start New Registration", callback_data="reg:restart")],
                [InlineKeyboardButton("📞 Contact Admin", callback_data="menu:contact")],
            ])
            await update.message.reply_text(
                "⚠️ Your previous plan has expired or was rejected.\n\n"
                "Tap below to start a new registration or contact your coach.",
                reply_markup=keyboard,
            )
            return ConversationHandler.END

        # Fallback for any other status → treat as active
        await update.message.reply_text(
            WELCOME_BACK.format(
                name=name, plan=plan, sessions_left=sessions_left,
                username=user.username or "no_username", tg_id=user.id,
            ),
            parse_mode="Markdown",
            reply_markup=MAIN_MENU_KEYBOARD,
        )
        return ConversationHandler.END

    # ── NEW STUDENT ──
    context.user_data["reg_tg_id"] = str(user.id)
    context.user_data["reg_tg_username"] = user.username or ""

    # Parse start payload from website form:
    #   name|email|whatsapp|location|service   (5 parts = full form)
    #   name|serviceKey                          (2 parts = old modal)
    #   name only                                (1 part)
    payload = (update.message.text or "").replace("/start", "").strip()
    parts = payload.split("|") if payload else []

    if len(parts) >= 5:
        # ── FULL FORM SUBMISSION FROM WEBSITE ──
        # All data collected at once — skip step-by-step, write to Airtable directly
        student_name  = parts[0].strip()
        student_email = parts[1].strip()
        student_phone = parts[2].strip()
        student_loc   = parts[3].strip()
        plan_key      = parts[4].strip()

        context.user_data["reg_name"]  = student_name
        context.user_data["reg_email"] = student_email
        context.user_data["reg_phone"] = student_phone
        context.user_data["reg_plan"]  = plan_key
        context.user_data["reg_source"] = "Website Form"

        svc = SERVICES.get(plan_key, SERVICES["single"])
        is_free = svc.get("price", 0) == 0 and svc.get("type") == "community"

        # Build Airtable fields
        fields = {
            "Name": student_name,
            "Email": student_email,
            "Phone": student_phone,
            "Location": student_loc,
            "Telegram Username": user.username or "",
            "Telegram Chat ID": str(user.id),
            "Service Key": plan_key,
            "Plan": svc["label"],
            "Source": "Website Form",
            "Status": STATUS_CUSTOM if svc.get("type") == "custom" else (STATUS_ACTIVE if is_free else STATUS_PENDING),
        }

        # Check if student already exists (by Telegram Chat ID via cache lookup)
        existing = None
        try:
            existing = await airtable.find_student(user.id)
        except Exception:
            pass

        if existing:
            await airtable.update_student(existing["record_id"], fields)
            logger.info(f"Updated existing student from website form: {user.id} ({student_name})")
        else:
            await airtable.create_student(fields)
            logger.info(f"Created new student from website form: {user.id} ({student_name})")

        # Respond based on service type
        if svc.get("type") == "custom":
            # Custom plan — notify admin, show pending
            from handlers.registration import STATUS_CUSTOM as _sc
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=(
                            "🔔 **Custom Plan Request (Website)**\n\n"
                            f"Student: {student_name} (`{user.id}`)\n"
                            f"Email: {student_email}\n"
                            f"WhatsApp: {student_phone}\n"
                            f"Location: {student_loc}\n\n"
                            f"Review in Airtable and use `/setprice {user.id} <amount> <sessions>`"
                        ),
                        parse_mode="Markdown",
                    )
                except Exception:
                    pass
            await update.message.reply_text(
                f"✅ **Thanks, {student_name}!**\n\n"
                f"Your custom plan request has been submitted.\n"
                f"📧 {student_email}\n"
                f"📱 {student_phone}\n"
                f"📍 {student_loc}\n\n"
                f"Your coach will review within 24 hours and send you a payment link.\n"
                f"You'll get a message here when it's ready. 🎤",
                parse_mode="Markdown",
            )
        elif is_free:
            # Free service — activate immediately
            await update.message.reply_text(
                f"✅ **Welcome, {student_name}!**\n\n"
                f"You're all set — your free community access is active.\n\n"
                f"Here's what I can help with:",
                parse_mode="Markdown",
                reply_markup=MAIN_MENU_KEYBOARD,
            )
        else:
            # Paid — show payment link
            fw_link = FLUTTERWAVE.get(plan_key, "")
            amount_display = f"${svc['price']}" if svc['currency'] == 'USD' else f"₦{svc['price']:,}"
            await update.message.reply_text(
                f"✅ **Thanks, {student_name}!**\n\n"
                f"📋 Plan: {svc['label']}\n"
                f"💰 Amount: {amount_display}\n"
                f"📧 {student_email}\n"
                f"📱 {student_phone}\n\n"
                f"Complete your payment to activate:\n"
                f"💳 {fw_link}\n\n"
                f"After payment, your coach will verify and activate your account.\n"
                f"You'll get a message herewhen you're approved. 🎤",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💳 Pay Now", url=fw_link)],
                    [InlineKeyboardButton("📞 Contact Admin", callback_data="menu:contact")],
                ]),
            )

        context.user_data.clear()
        return ConversationHandler.END

    elif len(parts) >= 2:
        # Old modal format: name|serviceKey
        context.user_data["reg_plan"] = parts[1].strip()
    else:
        context.user_data["reg_plan"] = "single"

    plan_key = context.user_data["reg_plan"]
    svc = SERVICES.get(plan_key, SERVICES["single"])

    # Validate required fields for non-website flows
    context.user_data["reg_name"] = parts[0].strip() if parts else user.first_name or "there"

    # Custom plan → ask for amount first
    if svc.get("type") == "custom":
        await update.message.reply_text(
            f"💰 **Custom Plan**\n\n"
            f"Building a plan just for you!\n\n"
            f"First, how much would you like to pay?\n"
            f"Enter any amount (e.g., 50000 for ₦50,000 or 100 for $100).\n\n"
            f"_Your coach will review and confirm._",
            parse_mode="Markdown",
        )
        return CUSTOM_AMOUNT

    # Free service → no payment needed, just register
    if svc.get("price", 0) == 0 and svc.get("type") == "community":
        context.user_data["reg_free"] = True
        await update.message.reply_text(REG_NAME_PROMPT, parse_mode="Markdown")
        return NAME

    # Paid service — start normal registration
    context.user_data["reg_free"] = False
    await update.message.reply_text(REG_NAME_PROMPT, parse_mode="Markdown")
    return NAME


async def custom_amount_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Custom plan: receive amount from user."""
    text = update.message.text.strip()
    # Extract numeric value
    import re
    numbers = re.findall(r'[\d,]+', text.replace(",", ""))
    if not numbers:
        await update.message.reply_text(
            "❌ Please enter a valid number.\n"
            "Example: 50000 for ₦50,000 or 100 for $100."
        )
        return CUSTOM_AMOUNT

    amount = int(numbers[0])
    if amount < 1:
        await update.message.reply_text("❌ Amount must be at least 1. Try again.")
        return CUSTOM_AMOUNT

    context.user_data["reg_custom_amount"] = amount
    context.user_data["reg_name"] = update.message.text.strip()  # temp, will get real name

    await update.message.reply_text(
        f"Got it! **{amount:,}** noted.\n\n"
        f"Now enter your **full name**:",
        parse_mode="Markdown",
    )
    # Next: get name → email → phone → needs → confirm
    return NAME_CUSTOM


async def custom_needs_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Custom plan: receive needs description, then confirm."""
    needs = update.message.text.strip()
    if len(needs) < 5:
        await update.message.reply_text("❌ Please describe your needs in more detail (at least 5 characters).")
        return CUSTOM_NEEDS

    context.user_data["reg_needs"] = needs

    # Show confirmation
    name = context.user_data.get("reg_name", "")
    email = context.user_data.get("reg_email", "")
    phone = context.user_data.get("reg_phone", "")
    amount = context.user_data.get("reg_custom_amount", 0)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Submit", callback_data="custom:confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="custom:cancel"),
        ],
    ])

    await update.message.reply_text(
        f"✅ **Please confirm your custom plan request:**\n\n"
        f"👤 Name: {name}\n"
        f"📧 Email: {email}\n"
        f"📱 Phone: {phone}\n"
        f"💰 Amount: {amount:,}\n"
        f"📝 Needs: {needs}\n\n"
        f"Your coach will review within 24 hours.",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
    return CONFIRM


async def custom_confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Custom plan: user confirmed — write to Airtable, notify admin."""
    query = update.callback_query
    await query.answer()

    if query.data == "custom:cancel":
        await query.edit_message_text(REG_CANCELLED, parse_mode="Markdown")
        context.user_data.clear()
        return ConversationHandler.END

    user_data = context.user_data
    user = query.from_user
    airtable: AirtableService = context.bot_data["airtable"]

    amount = user_data.get("reg_custom_amount", 0)

    fields = {
        "Name": user_data.get("reg_name", ""),
        "Email": user_data.get("reg_email", ""),
        "Phone": user_data.get("reg_phone", ""),
        "Telegram Username": user_data.get("reg_tg_username", ""),
        "Telegram Chat ID": str(user.id),
        "Service Key": "custom-plan",
        "Plan": "Custom Plan",
        "Source": "Telegram Bot",
        "Status": STATUS_CUSTOM,
        "Budget": str(amount),
        "Needs": user_data.get("reg_needs", ""),
    }

    existing = await airtable.find_student(user.id)
    if existing:
        await airtable.update_student(existing["record_id"], fields)
    else:
        await airtable.create_student(fields)

    # Notify admin
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    "🔔 **Custom Plan Request**\n\n"
                    f"Student: {user_data.get('reg_name', 'Unknown')} (`{user.id}`)\n"
                    f"Amount: {amount:,}\n"
                    f"Needs: {user_data.get('reg_needs', '')}\n\n"
                    f"Set price: `/setprice {user.id} <amount> <sessions>`"
                ),
                parse_mode="Markdown",
            )
        except Exception:
            pass

    await query.edit_message_text(
        CUSTOM_SUBMITTED.format(amount=f"{amount:,}", needs=user_data.get("reg_needs", "")),
        parse_mode="Markdown",
    )

    context.user_data.clear()
    return ConversationHandler.END


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    return MAIN_MENU_KEYBOARD


def get_back_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("👈 Back to Menu", callback_data="menu:home"),
    ]])


# Additional state for custom plan flow (after amount, get name)
NAME_CUSTOM = 101

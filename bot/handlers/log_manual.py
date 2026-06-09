"""
handlers/log_manual.py — Manual payment & session logging for admin.
Lets you log payments received outside Flutterwave (bank transfer, cash, interim, etc.)
Directly writes to Airtable and notifies student on Telegram.
"""
import logging
import re
from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS, SERVICES
from services.airtable import AirtableService
from templates.messages import MAIN_MENU_KEYBOARD

logger = logging.getLogger(__name__)


async def log_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /log Name | Amount | Plan | Method | Notes
    
    Logs a manual payment or session update directly to Airtable.
    Works even if student never went through the website or Flutterwave.
    
    Usage:
      /log Sarah Johnson | 30000 | single | Bank Transfer | Interim session 1
      /log Ali Reza | 80000 | custom-plan | Cash | 6-session package
      /log Sarah Johnson | 0 | - | - | Session 2 of 4 completed (increment sessions used)
      /log New Student Name | email | phone | 50 | single | Bank Transfer | Brand new student
    """
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return

    if not context.args:
        await update.message.reply_text(
            "📝 **Manual Payment/Session Log**\n\n"
            "Usage:\n"
            "`/log Name | Amount | Plan | Method | Notes`\n\n"
            "Examples:\n"
            "`/log Sarah | 30000 | single | Bank Transfer | Interim session 1`\n"
            "`/log Ali | 80000 | custom-plan | Cash | 6-session package`\n"
            "`/log Sarah | 0 | - | - | Session 2 of 4 done`\n\n"
            "Plans: single, monthly, ngn-single, ngn-monthly, custom-plan\n"
            "Method: Bank Transfer, Cash, Flutterwave, Other, -\n"
            "Amount 0 = session update only (no payment)\n"
            "Use '-' for fields you want to skip",
            parse_mode="Markdown",
        )
        return

    text = " ".join(context.args)
    parts = [p.strip() for p in text.split("|")]

    if len(parts) < 2:
        await update.message.reply_text(
            "❌ Invalid format. Use: `/log Name | Amount | Plan | Method | Notes`",
            parse_mode="Markdown",
        )
        return

    # Parse fields
    name = parts[0].strip()
    amount_str = parts[1].strip() if len(parts) > 1 else "0"
    plan_key = parts[2].strip() if len(parts) > 2 else "single"
    method = parts[3].strip() if len(parts) > 3 else "Other"
    notes = parts[4].strip() if len(parts) > 4 else ""

    # Parse amount
    try:
        amount = int(amount_str.replace(",", "").replace("₦", "").replace("$", ""))
    except ValueError:
        await update.message.reply_text(f"❌ Invalid amount: {amount_str}")
        return

    # Validate plan
    if plan_key == "-":
        plan_key = None
    svc = SERVICES.get(plan_key) if plan_key else None

    airtable: AirtableService = context.bot_data["airtable"]

    # Search for existing student by name
    existing = await airtable.find_by_name(name)
    matched_student = None

    if existing:
        # Find best match (active or most recent)
        for s in existing:
            if s.get("name", "").lower() == name.lower():
                matched_student = s
                break
        if not matched_student:
            matched_student = existing[0]

    if matched_student:
        # ── UPDATE EXISTING STUDENT ──
        record_id = matched_student.get("record_id", "")
        tg_id = matched_student.get("telegram_id", "")
        current_sessions_used = matched_student.get("sessions_used", 0)
        current_total = matched_student.get("total_sessions", 0)

        if amount == 0 and plan_key == "-":
            # Session-only update (no payment)
            new_sessions_used = current_sessions_used + 1
            update_fields = {
                "Sessions Used": new_sessions_used,
            }
            if notes:
                existing_notes = matched_student.get("notes", "") or ""
                update_fields["Needs"] = f"{existing_notes}\n[Log {new_sessions_used}/{current_total}] {notes}".strip()
            await airtable.update_student(record_id, update_fields)

            # Notify student on Telegram
            try:
                sessions_left = max(0, current_total - new_sessions_used)
                await context.bot.send_message(
                    chat_id=int(tg_id),
                    text=(
                        f"📋 **Session Update**\n\n"
                        f"Session {new_sessions_used} of {current_total} logged.\n"
                        f"Sessions remaining: {sessions_left}\n"
                        f"{'📝 ' + notes if notes else ''}"
                    ),
                    parse_mode="Markdown",
                    reply_markup=MAIN_MENU_KEYBOARD,
                )
            except Exception as e:
                logger.warning(f"Could not notify student {tg_id}: {e}")

            await update.message.reply_text(
                f"✅ **Session Logged**\n\n"
                f"👤 Student: {matched_student.get('name', name)}\n"
                f"📋 Sessions: {new_sessions_used}/{current_total}\n"
                f"🎯 Remaining: {max(0, current_total - new_sessions_used)}\n"
                f"{'📝 ' + notes if notes else ''}\n"
                f"🆔 TG: `{tg_id}`",
                parse_mode="Markdown",
            )
        else:
            # Payment + plan update
            if svc:
                total_sessions = 4 if "monthly" in plan_key.lower() else (8 if "group" in svc.get("type", "") else 1)
                plan_label = svc["label"]
            else:
                total_sessions = 1
                plan_label = plan_key

            update_fields = {
                "Status": "Active",
                "Amount Paid": amount,
                "Source": f"Manual Log ({method})",
            }
            if plan_key and plan_key != "-":
                update_fields["Service Key"] = plan_key
                update_fields["Plan"] = plan_label
                update_fields["Total Sessions"] = total_sessions
                update_fields["Sessions Used"] = 0
            if notes:
                update_fields["Needs"] = notes

            await airtable.update_student(record_id, update_fields)

            # Notify student
            try:
                await context.bot.send_message(
                    chat_id=int(tg_id),
                    text=(
                        f"✅ **Payment Confirmed!**\n\n"
                        f"Plan: {plan_label}\n"
                        f"Paid via: {method}\n"
                        f"Sessions: {total_sessions}\n\n"
                        f"Welcome aboard! Here's what I can help with:"
                    ),
                    parse_mode="Markdown",
                    reply_markup=MAIN_MENU_KEYBOARD,
                )
            except Exception as e:
                logger.warning(f"Could not notify student {tg_id}: {e}")

            currency = "₦" if svc and svc.get("currency") == "NGN" else "$"
            await update.message.reply_text(
                f"✅ **Payment Logged**\n\n"
                f"👤 Student: {matched_student.get('name', name)}\n"
                f"💰 Amount: {currency}{amount:,}\n"
                f"📋 Plan: {plan_label}\n"
                f"🎯 Sessions: {total_sessions}\n"
                f"💳 Method: {method}\n"
                f"{'📝 ' + notes if notes else ''}\n"
                f"🆔 TG: `{tg_id}` | Status: ✅ Active",
                parse_mode="Markdown",
            )
    else:
        # ── CREATE NEW STUDENT ──
        if not plan_key or plan_key == "-":
            plan_key = "single"
        if not svc:
            svc = SERVICES.get("single")

        total_sessions = 4 if "monthly" in plan_key.lower() else (8 if svc.get("type") == "group" else 1)
        plan_label = svc["label"]

        fields = {
            "Name": name,
            "Status": "Active",
            "Amount Paid": amount,
            "Service Key": plan_key,
            "Plan": plan_label,
            "Total Sessions": total_sessions,
            "Sessions Used": 0,
            "Source": f"Manual Log ({method})",
            "Telegram Chat ID": "PENDING",
            "Telegram Username": "",
            "Email": "",
            "Phone": "",
        }
        if notes:
            fields["Needs"] = notes

        record_id = await airtable.create_student(fields)

        if record_id:
            await update.message.reply_text(
                f"✅ **New Student Created & Activated**\n\n"
                f"👤 Student: {name}\n"
                f"💰 Amount: ₦{amount:,}\n"
                f"📋 Plan: {plan_label}\n"
                f"🎯 Sessions: {total_sessions}\n"
                f"💳 Method: {method}\n"
                f"{'📝 ' + notes if notes else ''}\n"
                f"🆔 Record: `{record_id}`\n\n"
                f"⚠️ Student has no Telegram link. Share their details so they can connect.",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text("❌ Failed to create student in Airtable. Try again.")


async def sessions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /sessions <name> — quick view of a student's session status."""
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: `/sessions <student_name>`\n\nExample: `/sessions Sarah`",
            parse_mode="Markdown",
        )
        return

    name = " ".join(context.args).strip()
    airtable: AirtableService = context.bot_data["airtable"]

    results = await airtable.find_by_name(name)

    if not results:
        await update.message.reply_text(f"❌ No student found matching '{name}'.")
        return

    lines = [f"📋 **Student Search: {name}**\n"]
    for s in results:
        status = s.get("status", "?")
        plan = s.get("plan", "?")
        used = s.get("sessions_used", 0)
        total = s.get("total_sessions", 0)
        remaining = max(0, total - used)
        source = s.get("source", "?")
        lines.append(
            f"👤 **{s.get('name', '?')}** (`{s.get('telegram_id', 'N/A')}`)\n"
            f"📋 Plan: {plan}\n"
            f"🎯 Sessions: {used}/{total} (remaining: {remaining})\n"
            f"📍 Status: {source}\n"
            f"🔗 Source: {status}\n"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

"""
services/payment_verifier.py — Poll Flutterwave for successful payments.
Runs as a scheduled job inside Bot 2. No separate server needed.
Matches recent Flutterwave transactions against pending Airtable records.
"""
import os
import logging
import requests

logger = logging.getLogger(__name__)


async def verify_payments_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Every 60s: fetch recent successful transactions from Flutterwave.
    Match against Airtable pending records. Update status → Active.
    """
    airtable = context.bot_data["airtable"]
    bot = context.bot

    # Get Flutterwave API key
    fw_key = os.getenv("FLUTTERWAVE_SECRET_KEY", "")
    if not fw_key:
        return

    # Track which tx_refs we already processed
    processed = context.bot_data.get("_processed_txs", set())

    try:
        # 1️⃣ Fetch recent successful transactions from Flutterwave
        url = "https://api.flutterwave.com/v3/transactions"
        headers = {"Authorization": f"Bearer {fw_key}"}
        params = {"status": "successful", "page": 1, "limit": 50}

        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code != 200:
            logger.warning(f"Flutterwave API error: {r.status_code}")
            return

        transactions = r.json().get("data", [])
        if not transactions:
            return

        # 2️⃣ Get pending students from Airtable
        pending = await airtable.get_pending_students()
        if not pending:
            return

        # Build lookup: email → student record
        pending_by_email = {}
        for s in pending:
            fields = s.get("fields", {})
            email = (fields.get("Email") or "").strip().lower()
            if email:
                pending_by_email[email] = s

        # 3️⃣ Match transactions to pending students
        for tx in transactions:
            tx_ref = tx.get("tx_ref", "")
            if tx_ref in processed:
                continue

            tx_email = (tx.get("customer", {}).get("email", "") or "").strip().lower()
            tx_status = tx.get("status", "")

            if tx_status not in ("successful", "success"):
                continue

            if not tx_email:
                continue

            # Find matching student
            student = pending_by_email.get(tx_email)
            if not student:
                continue

            # 4️⃣ Update Airtable
            record_id = student["id"]
            airtable_obj = context.bot_data["airtable"]
            await airtable_obj.update_student(record_id, {"Status": "Active"})
            logger.info(f"✅ Auto-approved: {tx_email} (tx: {tx_ref[:12]}...)")

            # 5️⃣ Notify student via Telegram
            fields = student.get("fields", {})
            tg_id = fields.get("Telegram Chat ID", "")
            name = fields.get("Name", "Student")

            if tg_id:
                try:
                    await bot.send_message(
                        chat_id=int(tg_id),
                        text=(
                            f"✅ **Payment Confirmed!**\n\n"
                            f"Welcome aboard, **{name}**!\n"
                            f"Your Flutterwave payment was received successfully.\n\n"
                            f"Type /start to see your menu."
                        ),
                        parse_mode="Markdown",
                    )
                    processed.add(tx_ref)
                    context.bot_data["_processed_txs"] = processed
                except Exception as e:
                    logger.warning(f"Failed to notify {tg_id}: {e}")

    except Exception as e:
        logger.error(f"Payment verification error: {e}")

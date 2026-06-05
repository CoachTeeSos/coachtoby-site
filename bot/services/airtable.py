"""
services/airtable.py — All Airtable operations with retry, caching, and offline fallback.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

import aiosqlite
from pyairtable import Api as AirtableApi, Table

from config import (
    AIRTABLE_PAT, AIRTABLE_BASE_ID, AIRTABLE_STUDENTS_TABLE,
    FIELD_NAME, FIELD_STATUS, FIELD_PLAN, FIELD_SERVICE_KEY,
    FIELD_TG_ID, FIELD_TG_USERNAME, FIELD_EMAIL, FIELD_PHONE,
    STATUS_ACTIVE, STATUS_PENDING,
)

logger = logging.getLogger(__name__)


class AirtableService:
    """Async-friendly Airtable service with SQLite cache fallback."""

    def __init__(self, db_path: str = "bot_cache.db"):
        self.api = AirtableApi(AIRTABLE_PAT)
        self.base_id = AIRTABLE_BASE_ID
        self.table_name = AIRTABLE_STUDENTS_TABLE
        self.table: Table = self.api.table(self.base_id, self.table_name)
        self.db_path = db_path
        self._cache_ttl = timedelta(minutes=5)

    async def init_db(self):
        """Initialize SQLite cache tables."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS students_cache (
                    telegram_id     TEXT PRIMARY KEY,
                    name            TEXT,
                    plan            TEXT,
                    status          TEXT,
                    sessions_used   INTEGER DEFAULT 0,
                    total_sessions  INTEGER DEFAULT 0,
                    source          TEXT,
                    service_key     TEXT,
                    budget          TEXT,
                    needs           TEXT,
                    amount_paid     INTEGER DEFAULT 0,
                    last_synced     TEXT
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS escalations (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id     INTEGER,
                    message_text    TEXT,
                    forwarded_to    INTEGER,
                    status          TEXT DEFAULT 'pending',
                    reply_text      TEXT,
                    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS pending_payments (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id     INTEGER,
                    service_key     TEXT,
                    amount          INTEGER,
                    status          TEXT DEFAULT 'pending',
                    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS commands (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    command         TEXT,
                    target_id       TEXT,
                    params          TEXT,
                    status          TEXT DEFAULT 'pending',
                    result          TEXT,
                    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    executed_at     TEXT
                )
            """)
            await db.commit()

    def _row_to_dict(self, record: dict) -> dict:
        """Normalize an Airtable record to a flat dict."""
        f = record.get("fields", {})
        return {
            "telegram_id": str(f.get("Telegram Chat ID", "")).strip(),
            "name": f.get("Name", "").strip(),
            "plan": (f.get("Plan", "") or f.get("Service Key", "")).strip(),
            "status": (f.get("Status", "") or "").strip(),
            "sessions_used": f.get("Sessions Used", 0) or 0,
            "total_sessions": f.get("Total Sessions", 0) or 0,
            "source": (f.get("Source", "") or "").strip(),
            "service_key": (f.get("Service Key", "") or "").strip(),
            "budget": (f.get("Budget", "") or "").strip(),
            "needs": (f.get("Needs", "") or "").strip(),
            "amount_paid": f.get("Amount Paid", 0) or 0,
            "record_id": record.get("id", ""),
        }

    async def find_student(self, telegram_id: int) -> Optional[dict]:
        """Look up student by telegram_id. Cache-first, Airtable fallback."""
        tid = str(telegram_id)

        # 1. Check local cache first
        cached = await self._cache_get(tid)
        if cached:
            last_synced = datetime.fromisoformat(cached.get("last_synced", "2000-01-01"))
            if datetime.utcnow() - last_synced < self._cache_ttl:
                logger.debug(f"Cache hit for {tid}")
                return cached

        # 2. Query Airtable
        try:
            formula = f"{{Telegram Chat ID}}='{tid}'"
            records = self.table.all(formula=formula, max_records=1)
            if records:
                student = self._row_to_dict(records[0])
                await self._cache_set(student)
                logger.info(f"Airtable hit for {tid}: {student['name']}")
                return student
            logger.info(f"No Airtable record for {tid}")
            return None
        except Exception as e:
            logger.error(f"Airtable query failed: {e}")
            if cached:
                logger.warning(f"Using stale cache for {tid}")
                return cached
            return None

    async def find_by_name(self, name: str) -> list[dict]:
        """Search students by name (partial match)."""
        try:
            formula = f"FIND(LOWER('{name}'), LOWER({{Name}})) > 0"
            records = self.table.all(formula=formula)
            return [self._row_to_dict(r) for r in records]
        except Exception as e:
            logger.error(f"Airtable name search failed: {e}")
            return []

    async def update_student(self, record_id: str, fields: dict) -> bool:
        """Update a student record in Airtable."""
        try:
            self.table.update(record_id, fields)
            logger.info(f"Updated Airtable record {record_id}: {fields}")
            return True
        except Exception as e:
            logger.error(f"Airtable update failed: {e}")
            return False

    async def create_student(self, fields: dict) -> Optional[str]:
        """Create a new student record in Airtable."""
        try:
            record = self.table.create(fields)
            logger.info(f"Created Airtable record: {record['id']}")
            return record["id"]
        except Exception as e:
            logger.error(f"Airtable create failed: {e}")
            return None

    async def get_all_active_students(self) -> list[dict]:
        """Get all active students (for /broadcast)."""
        try:
            formula = "{Status}='Active'"
            records = self.table.all(formula=formula)
            return [self._row_to_dict(r) for r in records]
        except Exception as e:
            logger.error(f"Airtable fetch all failed: {e}")
            return []

    async def get_pending_payments(self) -> list[dict]:
        """Get all pending payment students."""
        try:
            formula = "OR({Status}='Pending Review',{Status}='Awaiting Receipt')"
            records = self.table.all(formula=formula)
            return [self._row_to_dict(r) for r in records]
        except Exception as e:
            logger.error(f"Airtable pending fetch failed: {e}")
            return []

    # ── Commands table (Hermes → Retpipebot) ──

    async def poll_pending_commands(self) -> list[dict]:
        """Poll for pending commands from Hermes. Returns list of command dicts."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT * FROM commands WHERE status='pending' ORDER BY created_at"
            )
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def mark_command_executed(self, cmd_id: int, result: str):
        """Mark a command as executed with result."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE commands SET status='done', result=?, executed_at=? WHERE id=?",
                (result, datetime.utcnow().isoformat(), cmd_id)
            )
            await db.commit()

    # ── SQLite Cache ──

    async def _cache_get(self, telegram_id: str) -> Optional[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT * FROM students_cache WHERE telegram_id = ?", (telegram_id,)
            )
            row = await cur.fetchone()
            if row:
                return dict(row)
        return None

    async def _cache_set(self, student: dict):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO students_cache
                (telegram_id, name, plan, status, sessions_used, total_sessions,
                 source, service_key, budget, needs, amount_paid, last_synced)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                student["telegram_id"], student["name"], student["plan"],
                student["status"], student["sessions_used"], student["total_sessions"],
                student["source"], student["service_key"],
                student.get("budget", ""), student.get("needs", ""),
                student.get("amount_paid", 0),
                datetime.utcnow().isoformat()
            ))
            await db.commit()

    # ── Escalations ──

    async def log_escalation(self, telegram_id: int, message_text: str, forwarded_to: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                "INSERT INTO escalations (telegram_id, message_text, forwarded_to) VALUES (?, ?, ?)",
                (telegram_id, message_text, forwarded_to)
            )
            await db.commit()
            return cur.lastrowid

    async def get_escalation(self, esc_id: int) -> Optional[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM escalations WHERE id = ?", (esc_id,))
            row = await cur.fetchone()
            return dict(row) if row else None

    async def reply_escalation(self, esc_id: int, reply_text: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE escalations SET status='replied', reply_text=? WHERE id=?",
                (reply_text, esc_id)
            )
            await db.commit()

    async def get_pending_escalations(self) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT * FROM escalations WHERE status='pending' ORDER BY created_at"
            )
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    # ── Pending Payments ──

    async def log_pending_payment(self, telegram_id: int, service_key: str, amount: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                "INSERT INTO pending_payments (telegram_id, service_key, amount) VALUES (?, ?, ?)",
                (telegram_id, service_key, amount)
            )
            await db.commit()
            return cur.lastrowid

    async def get_pending_payment(self, pay_id: int) -> Optional[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM pending_payments WHERE id = ?", (pay_id,))
            row = await cur.fetchone()
            return dict(row) if row else None

    async def mark_payment_approved(self, telegram_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE pending_payments SET status='approved' WHERE telegram_id=? AND status='pending'",
                (telegram_id,)
            )
            await db.commit()

    async def get_all_pending_payments(self) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT * FROM pending_payments WHERE status='pending' ORDER BY created_at"
            )
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

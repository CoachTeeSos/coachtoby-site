#!/usr/bin/env python3
"""
Coach Toby — Local student registration database.
SQLite-based, with GitHub backup and Airtable sync.
"""
import os
import json
import sqlite3
import logging
import hashlib
import base64
import requests
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# ── Paths ───────────────────────────────────────────────────────────────────
DATA_DIR = Path(os.environ.get("DATA_DIR", "/home/user/data"))
DB_PATH = DATA_DIR / "registrations.db"
BACKUP_DIR = DATA_DIR / "backups"
DATA_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# ── Env ─────────────────────────────────────────────────────────────────────
def load_env():
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env()

AIRTABLE_PAT = os.environ.get("AIRTABLE_PAT", "")
AIRTABLE_BASE = os.environ.get("AIRTABLE_BASE_ID", "app3N2MFPvfDSuYxk")
AIRTABLE_TABLE = os.environ.get("AIRTABLE_TABLE", "Students")
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
BREVO_API_URL = "https://api.brevo.com/v3"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_BACKUP_REPO", "CoachToby/student-data-backup")
ENCRYPTION_KEY = os.environ.get("BACKUP_ENCRYPTION_KEY", "coachtoby-2026-secret")


# ── Database ────────────────────────────────────────────────────────────────
def get_db():
    """Get SQLite connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            telegram TEXT,
            location TEXT,
            plan TEXT NOT NULL,
            service_key TEXT NOT NULL,
            status TEXT DEFAULT 'Awaiting Receipt',
            source TEXT DEFAULT 'Website',
            total_sessions INTEGER DEFAULT 0,
            sessions_used INTEGER DEFAULT 0,
            budget TEXT,
            needs TEXT,
            email_sent INTEGER DEFAULT 0,
            airtable_synced INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_email_sent ON registrations(email_sent);
        CREATE INDEX IF NOT EXISTS idx_airtable_synced ON registrations(airtable_synced);
        CREATE INDEX IF NOT EXISTS idx_created_at ON registrations(created_at);
        CREATE INDEX IF NOT EXISTS idx_status ON registrations(status);

        CREATE TABLE IF NOT EXISTS sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sync_type TEXT NOT NULL,
            records_count INTEGER DEFAULT 0,
            status TEXT NOT NULL,
            details TEXT,
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {DB_PATH}")


# ── CRUD ────────────────────────────────────────────────────────────────────
def add_registration(data: dict) -> int:
    """Add a new registration. Returns the record ID."""
    conn = get_db()
    now = datetime.utcnow().isoformat()
    cursor = conn.execute("""
        INSERT INTO registrations
        (name, email, phone, telegram, location, plan, service_key, status,
         source, total_sessions, sessions_used, budget, needs, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("name", ""),
        data.get("email", ""),
        data.get("phone", ""),
        data.get("telegram", ""),
        data.get("location", ""),
        data.get("plan", ""),
        data.get("service_key", ""),
        data.get("status", "Awaiting Receipt"),
        data.get("source", "Website"),
        data.get("total_sessions", 0),
        data.get("sessions_used", 0),
        data.get("budget", ""),
        data.get("needs", ""),
        now, now,
    ))
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    logger.info(f"New registration: {data.get('name')} ({data.get('email')}) — ID: {record_id}")
    return record_id


def get_unsent_emails() -> list:
    """Get registrations that haven't received welcome emails."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM registrations WHERE email_sent = 0 AND email != '' ORDER BY created_at ASC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def mark_email_sent(record_id: int):
    """Mark a registration as having received welcome email."""
    conn = get_db()
    conn.execute("UPDATE registrations SET email_sent = 1, updated_at = ? WHERE id = ?",
                 (datetime.utcnow().isoformat(), record_id))
    conn.commit()
    conn.close()


def get_unsynced_airtable() -> list:
    """Get registrations not yet synced to Airtable."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM registrations WHERE airtable_synced = 0 ORDER BY created_at ASC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def mark_airtable_synced(record_id: int):
    """Mark a registration as synced to Airtable."""
    conn = get_db()
    conn.execute("UPDATE registrations SET airtable_synced = 1, updated_at = ? WHERE id = ?",
                 (datetime.utcnow().isoformat(), record_id))
    conn.commit()
    conn.close()


def get_all_registrations() -> list:
    """Get all registrations."""
    conn = get_db()
    rows = conn.execute("SELECT * FROM registrations ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_stats() -> dict:
    """Get database stats."""
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM registrations").fetchone()[0]
    unsent = conn.execute("SELECT COUNT(*) FROM registrations WHERE email_sent = 0").fetchone()[0]
    unsynced = conn.execute("SELECT COUNT(*) FROM registrations WHERE airtable_synced = 0").fetchone()[0]
    today = conn.execute(
        "SELECT COUNT(*) FROM registrations WHERE date(created_at) = date('now')"
    ).fetchone()[0]
    conn.close()
    return {"total": total, "unsent_emails": unsent, "unsynced_airtable": unsynced, "today": today}


# ── Encryption for GitHub backup ─────────────────────────────────────────────
def encrypt_data(data: str) -> str:
    """Simple XOR encryption with key. Good enough for backup privacy."""
    key = ENCRYPTION_KEY
    encrypted = []
    for i, char in enumerate(data):
        encrypted.append(chr(ord(char) ^ ord(key[i % len(key)])))
    return base64.b64encode(''.join(encrypted).encode()).decode()


def decrypt_data(encrypted_str: str) -> str:
    """Decrypt XOR-encrypted data."""
    key = ENCRYPTION_KEY
    data = base64.b64decode(encrypted_str).decode()
    decrypted = []
    for i, char in enumerate(data):
        decrypted.append(chr(ord(char) ^ ord(key[i % len(key)])))
    return ''.join(decrypted)


# ── GitHub Backup ────────────────────────────────────────────────────────────
def backup_to_github():
    """Backup database to GitHub private repo (encrypted)."""
    if not GITHUB_TOKEN:
        logger.warning("GITHUB_TOKEN not set, skipping backup")
        return False

    # Export database to JSON
    registrations = get_all_registrations()
    if not registrations:
        logger.info("No data to backup")
        return True

    data_json = json.dumps(registrations, indent=2, default=str)
    encrypted = encrypt_data(data_json)

    # Create backup filename with timestamp
    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = f"backups/registrations_{timestamp}.json.enc"

    # Also create a latest.json.enc that always has the most recent data
    latest_file = "backups/latest.json.enc"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

    success = True

    # Upload timestamped backup
    for filepath, content in [(backup_file, encrypted), (latest_file, encrypted)]:
        # Check if file exists (for latest.json.enc)
        sha = None
        r = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filepath}",
            headers=headers, timeout=15,
        )
        if r.status_code == 200:
            sha = r.json().get("sha")

        data = {
            "message": f"Backup {timestamp}" if "latest" not in filepath else f"Latest backup {timestamp}",
            "content": base64.b64encode(content.encode()).decode(),
        }
        if sha:
            data["sha"] = sha

        r = requests.put(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filepath}",
            headers=headers, json=data, timeout=15,
        )
        if r.status_code in (200, 201):
            logger.info(f"✅ Backed up to GitHub: {filepath}")
        else:
            logger.error(f"❌ GitHub backup failed: {r.status_code} - {r.text[:100]}")
            success = False

    # Log sync
    conn = get_db()
    conn.execute(
        "INSERT INTO sync_log (sync_type, records_count, status, details, created_at) VALUES (?, ?, ?, ?, ?)",
        ("github_backup", len(registrations), "success" if success else "failed", timestamp, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

    return success


# ── Airtable Sync ────────────────────────────────────────────────────────────
def sync_to_airtable():
    """Sync unsynced registrations to Airtable."""
    if not AIRTABLE_PAT:
        logger.warning("AIRTABLE_PAT not set, skipping Airtable sync")
        return 0

    unsynced = get_unsynced_airtable()
    if not unsynced:
        logger.info("No records to sync to Airtable")
        return 0

    synced = 0
    for rec in unsynced:
        fields = {
            "Name": rec["name"],
            "Email": rec["email"],
            "Phone": rec["phone"] or "",
            "Plan": rec["plan"],
            "Service Key": rec["service_key"],
            "Status": rec["status"],
            "Source": rec["source"],
            "Total Sessions": rec["total_sessions"],
            "Sessions Used": rec["sessions_used"],
        }
        if rec.get("budget"):
            fields["Budget"] = rec["budget"]
        if rec.get("needs"):
            fields["Needs"] = rec["needs"]
        if rec.get("telegram"):
            fields["Telegram Chat ID"] = rec["telegram"]

        try:
            r = requests.post(
                f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{AIRTABLE_TABLE}",
                headers={"Authorization": f"Bearer {AIRTABLE_PAT}", "Content-Type": "application/json"},
                json={"fields": fields},
                timeout=15,
            )
            r.raise_for_status()
            mark_airtable_synced(rec["id"])
            synced += 1
            logger.info(f"✅ Synced to Airtable: {rec['name']} ({rec['email']})")
        except Exception as e:
            logger.error(f"❌ Airtable sync failed for {rec['name']}: {e}")

    # Log sync
    conn = get_db()
    conn.execute(
        "INSERT INTO sync_log (sync_type, records_count, status, details, created_at) VALUES (?, ?, ?, ?, ?)",
        ("airtable_sync", synced, "success" if synced == len(unsynced) else "partial",
         f"{synced}/{len(unsynced)} synced", datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

    logger.info(f"Airtable sync complete: {synced}/{len(unsynced)} records")
    return synced


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    stats = get_stats()
    print(f"Database stats: {stats}")

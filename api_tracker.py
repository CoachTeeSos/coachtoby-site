#!/usr/bin/env python3
"""
Smart API usage tracker and rate limiter.
Monitors all API calls and prevents exhaustion.
"""
import os, json, time, sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path('/home/user/data/api_usage.db')

def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT NOT NULL,
            endpoint TEXT,
            model TEXT,
            tokens_in INTEGER DEFAULT 0,
            tokens_out INTEGER DEFAULT 0,
            cost REAL DEFAULT 0,
            status TEXT DEFAULT 'ok',
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rate_limits (
            service TEXT PRIMARY KEY,
            limit_per_minute INTEGER,
            limit_per_day INTEGER,
            current_minute_count INTEGER DEFAULT 0,
            current_day_count INTEGER DEFAULT 0,
            window_start TEXT,
            day_start TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_call(service, endpoint='', model='', tokens_in=0, tokens_out=0, cost=0, status='ok'):
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "INSERT INTO api_calls (service, endpoint, model, tokens_in, tokens_out, cost, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (service, endpoint, model, tokens_in, tokens_out, cost, status, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

def get_usage_summary(hours=24):
    conn = sqlite3.connect(str(DB_PATH))
    since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    
    # By service
    rows = conn.execute("""
        SELECT service, COUNT(*) as calls, SUM(tokens_in) as total_in, SUM(tokens_out) as total_out, SUM(cost) as total_cost
        FROM api_calls WHERE created_at > ? GROUP BY service
    """, (since,)).fetchall()
    
    # Recent calls
    recent = conn.execute("""
        SELECT service, model, tokens_in, tokens_out, cost, created_at
        FROM api_calls WHERE created_at > ? ORDER BY created_at DESC LIMIT 10
    """, (since,)).fetchall()
    
    conn.close()
    return rows, recent

def check_rate_limit(service, max_per_minute=10, max_per_day=100):
    """Check if we're within rate limits. Returns True if OK to proceed."""
    conn = sqlite3.connect(str(DB_PATH))
    now = datetime.utcnow()
    minute_ago = (now - timedelta(minutes=1)).isoformat()
    day_ago = (now - timedelta(days=1)).isoformat()
    
    minute_count = conn.execute(
        "SELECT COUNT(*) FROM api_calls WHERE service = ? AND created_at > ?",
        (service, minute_ago)
    ).fetchone()[0]
    
    day_count = conn.execute(
        "SELECT COUNT(*) FROM api_calls WHERE service = ? AND created_at > ?",
        (service, day_ago)
    ).fetchone()[0]
    
    conn.close()
    
    if minute_count >= max_per_minute:
        return False, f"Rate limit: {minute_count}/{max_per_minute} per minute"
    if day_count >= max_per_day:
        return False, f"Rate limit: {day_count}/{max_per_day} per day"
    
    return True, f"OK: {minute_count}/min, {day_count}/day"

def print_summary():
    rows, recent = get_usage_summary(24)
    print("=== API Usage (Last 24h) ===")
    if not rows:
        print("  No API calls recorded")
    for service, calls, tin, tout, cost in rows:
        print(f"  {service}: {calls} calls, {tin+tout} tokens, ${cost:.4f}")
    print("\n=== Recent Calls ===")
    for service, model, tin, tout, cost, ts in recent[:5]:
        print(f"  {ts[:16]} {service} {model} {tin+tout}t ${cost:.4f}")

if __name__ == '__main__':
    init_db()
    print_summary()

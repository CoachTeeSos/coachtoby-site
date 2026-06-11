#!/usr/bin/env python3
"""
Smart API caller with rate limiting and usage tracking.
Import this in any script that makes API calls.
"""
import os, json, time, sqlite3, requests
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path('/home/user/data/api_usage.db')

# Rate limits per service
LIMITS = {
    'openrouter': {'per_minute': 10, 'per_day': 500},
    'airtable': {'per_second': 5, 'per_day': 1000},
    'brevo': {'per_second': 10, 'per_day': 300},
    'github': {'per_hour': 5000},
    'exa': {'per_minute': 20, 'per_day': 1000},
    'ddgs': {'per_minute': 10, 'per_day': 500},
}

def init_db():
    if not DB_PATH.parent.exists():
        DB_PATH.parent.mkdir(parents=True)
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
    conn.commit()
    conn.close()

def log_call(service, endpoint='', model='', tokens_in=0, tokens_out=0, cost=0, status='ok'):
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "INSERT INTO api_calls (service, endpoint, model, tokens_in, tokens_out, cost, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (service, endpoint, model, tokens_in, tokens_out, cost, status, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

def check_limit(service):
    """Check if we're within rate limits. Returns (ok, message)."""
    init_db()
    limits = LIMITS.get(service, {'per_minute': 60, 'per_day': 10000})
    conn = sqlite3.connect(str(DB_PATH))
    now = datetime.utcnow()
    
    # Check per-minute
    if 'per_minute' in limits:
        minute_ago = (now - timedelta(minutes=1)).isoformat()
        count = conn.execute("SELECT COUNT(*) FROM api_calls WHERE service = ? AND created_at > ?", (service, minute_ago)).fetchone()[0]
        if count >= limits['per_minute']:
            conn.close()
            return False, f"{service}: {count}/{limits['per_minute']} per minute"
    
    # Check per-day
    if 'per_day' in limits:
        day_ago = (now - timedelta(days=1)).isoformat()
        count = conn.execute("SELECT COUNT(*) FROM api_calls WHERE service = ? AND created_at > ?", (service, day_ago)).fetchone()[0]
        if count >= limits['per_day']:
            conn.close()
            return False, f"{service}: {count}/{limits['per_day']} per day"
    
    conn.close()
    return True, "OK"

def smart_call(service, url, method='GET', headers=None, json_data=None, timeout=15, **kwargs):
    """Make an API call with rate limiting and usage tracking."""
    # Check rate limit
    ok, msg = check_limit(service)
    if not ok:
        raise Exception(f"Rate limit exceeded: {msg}")
    
    # Make the call
    try:
        if method == 'GET':
            r = requests.get(url, headers=headers, timeout=timeout, **kwargs)
        elif method == 'POST':
            r = requests.post(url, headers=headers, json=json_data, timeout=timeout, **kwargs)
        elif method == 'PATCH':
            r = requests.patch(url, headers=headers, json=json_data, timeout=timeout, **kwargs)
        elif method == 'DELETE':
            r = requests.delete(url, headers=headers, timeout=timeout, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        # Log the call
        tokens_in = len(json.dumps(json_data)) if json_data else 0
        tokens_out = len(r.text) if r.text else 0
        log_call(service, endpoint=url, status='ok' if r.status_code < 400 else 'error',
                 tokens_in=tokens_in, tokens_out=tokens_out)
        
        return r
    except Exception as e:
        log_call(service, endpoint=url, status='error')
        raise

def get_usage(hours=24):
    """Get usage summary for the last N hours."""
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    
    rows = conn.execute("""
        SELECT service, COUNT(*) as calls, SUM(tokens_in + tokens_out) as tokens, SUM(cost) as cost
        FROM api_calls WHERE created_at > ? GROUP BY service ORDER BY calls DESC
    """, (since,)).fetchall()
    
    total = conn.execute("""
        SELECT COUNT(*), SUM(tokens_in + tokens_out), SUM(cost)
        FROM api_calls WHERE created_at > ?
    """, (since,)).fetchone()
    
    conn.close()
    return rows, total

def print_usage(hours=24):
    rows, total = get_usage(hours)
    print(f"=== API Usage (Last {hours}h) ===")
    if not rows:
        print("  No calls recorded")
    for service, calls, tokens, cost in rows:
        print(f"  {service:15} {calls:5} calls  {tokens:8} tokens  ${cost:.4f}")
    if total and total[0]:
        print(f"  {'TOTAL':15} {total[0]:5} calls  {total[1] or 0:8} tokens  ${total[2] or 0:.4f}")

if __name__ == '__main__':
    print_usage()

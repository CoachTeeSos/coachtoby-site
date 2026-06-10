# Coach Toby — Hugging Face Deployment Package

## Space 1: Bot (Python Space)
- Type: Python (Gradio or direct)
- Main file: app.py (wraps retpipebot.py)
- Requirements: python-telegram-bot, requests, python-dotenv
- Persistent storage: /data for SQLite cache
- Runs 24/7 on HF free tier

## Space 2: Server (Docker Space)
- Type: Docker
- Main file: server.js (Express)
- Exposes: port 7860
- Endpoints:
  - GET / — serves static site
  - POST /webhook/flutterwave — payment confirmation
  - POST /api/create-payment — generate payment link
  - GET /api/health — health check

## Space 3: Cron Jobs (Python Space)
- Type: Python (Gradio with no UI)
- Runs payment_reminder.py and analytics_report.py on schedule
- Uses HF persistent storage for state

## Secrets (set in HF Space settings):
- BOT2_TOKEN
- AIRTABLE_PAT
- AIRTABLE_BASE_ID
- FLW_SECRET_KEY
- FLW_PUBLIC_KEY
- FLW_WEBHOOK_HASH
- SMTP_USER
- SMTP_PASS
- ADMIN_TG_ID

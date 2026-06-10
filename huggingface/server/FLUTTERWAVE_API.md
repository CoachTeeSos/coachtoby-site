var https://api.flutterwave.com/v3/payments
Headers: Authorization: Bearer FLW_SECRET_KEY
Body: {tx_ref, amount, currency, redirect_url, customer: {email, name}, customizations: {title, description}}
Response: data.link → payment URL

## Webhook
POST /webhook/flutterwave
- Verify hash: compare verifihash header with FLW_WEBHOOK_HASH
- On success: update Airtable student status to Active
- Return 200 OK immediately

## Payment Reminders
- Run payment_reminder.py every 12 hours
- Check students with Status = "Awaiting Receipt" or "Pending Review"
- Send Telegram reminder if pending > 48 hours
- Escalate to admin if pending > 72 hours

## Analytics
- Run analytics_report.py every 6 hours
- Generate Markdown report
- Save to /data/reports/

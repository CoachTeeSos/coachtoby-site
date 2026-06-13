# 🔍 QA ANALYSIS — Complete System Map
## Coach Toby: Site → Bot → Airtable → Cron

---

## 1. SITE FLOW (GitHub Pages — Static)

### Entry Points:
1. **index.html** — Quiz funnel (5-step quiz → recommendation → CTA to book.html)
2. **book.html** — Main conversion page (Pay Now / Free Demo / Payment Plan)
3. **pricing.html** — Plan comparison
4. **home.html** — Marketing page
5. **thank-you.html** — Post-payment confirmation

### Conversion Paths:

#### Path A: Paid Plan (Fastest)
```
book.html → select plan → enter name+email → Flutterwave checkout
→ payment success → thank-you.html → redirect to t.me/Retpipebot
→ /start on bot → Airtable check → show payment link (Pending Review)
→ Admin /approve → Airtable Active → bot auto-welcomes (5-min poll)
```

#### Path B: Free Demo
```
book.html → Free Demo tab → form (name, email, WhatsApp, service, level)
→ formsubmit.co → email to Toby
→ Manual: Toby reviews → creates student in Airtable → /approve
```

#### Path C: Payment Plan (Custom)
```
book.html → Payment Plan → form (name, email, amount, currency, date, notes)
→ formsubmit.co → email to Toby
→ Manual: Toby reviews → /setprice <tg_id> <amount> <sessions>
→ Bot sends payment link → student pays → /approve
```

#### Path D: Quiz Funnel
```
index.html → 5 quiz steps → recommendation → CTA to book.html
→ continues as Path A, B, or C
```

#### Path E: Direct Telegram (No Site)
```
t.me/Retpipebot → /start → Airtable check (not found)
→ Registration flow: name → email → phone → confirm
→ Airtable write (Pending Review) → payment link shown
→ Student pays → admin /approve → Active → auto-welcome
```

---

## 2. BOT FLOW (@Retpipebot — python-telegram-bot)

### States:
- `NAME` (0) → waiting for name
- `EMAIL` (1) → waiting for email
- `PHONE` (2) → waiting for phone
- `CONFIRM` (3) → waiting for confirm/cancel
- `CUSTOM_AMOUNT` (10) → custom plan amount
- `CUSTOM_NEEDS` (11) → custom plan needs
- `NAME_CUSTOM` (101) → custom plan name (after amount)

### Commands:
| Command | Access | Action |
|---|---|---|
| `/start` | All | Route by Airtable status (new/returning) |
| `/register` | All | Fresh registration (skips deep link) |
| `/approve <id>` | Admin | Set Active + notify student |
| `/reject <id>` | Admin | Set Rejected + notify |
| `/pending` | Admin | List pending students |
| `/log ...` | Admin | Manual payment log |
| `/logsession <id>` | Admin | Increment session count |
| `/assign <id>\|title\|content` | Admin | Send assignment |
| `/broadcast <msg>` | Admin | Message all active students |
| `/checkin` | Admin | Send check-in poll |
| `/sessions` | Admin | Show all student status |
| `/setprice <id> <amt> <sess>` | Admin | Set custom plan price |
| `/reply <esc_id> <msg>` | Admin | Reply to escalation |
| `/escalations` | Admin | List pending escalations |
| `/adminhelp` | Admin | Show admin commands |
| `/cancel` | All | Cancel current conversation |

### Main Menu (Active students):
- 📅 Schedule → callback `menu:schedule`
- 📝 Assignments → callback `menu:assignment`
- 💳 Payment Status → callback `menu:payment`
- ❓ Bottleneck → callback `menu:bottleneck`
- 📞 Contact Admin → callback `menu:contact`
- 👋 Main Menu → callback `menu:home`

### Auto-Jobs (every 5 min):
- `payment_poll` — checks Airtable for new Active students → sends welcome
- `fw_verify` — verifies Flutterwave payments
- `cmd_poll` (every 30s) — polls for new commands

---

## 3. AIRTABLE SCHEMA

### Students Table:
| Field | Type | Notes |
|---|---|---|
| Name | singleLineText | |
| Email | singleLineText | |
| Phone | singleLineText | |
| Location | singleLineText | |
| Plan | singleLineText | |
| Status | singleSelect | Active, Pending Review, Awaiting Receipt, Rejected, Expired, Custom Plan Pending |
| Service Key | singleLineText | single, monthly, ngn-single, ngn-monthly, group3-5, free-community, paid-community, speaking, custom-plan |
| Sessions Used | number | |
| Total Sessions | number | |
| Source | singleSelect | Telegram Bot, Website Form, Referral, Website Payment Plan |
| Budget | singleLineText | For custom plans |
| Needs | multilineText | Notes, payment plan details |
| Telegram Chat ID | singleLineText | |
| Telegram Username | singleLineText | |
| Amount Paid | singleLineText | |

### Status Flow:
```
New → Pending Review → (payment) → Awaiting Receipt → /approve → Active
                                                         → /reject → Rejected
Custom → Custom Plan Pending → /setprice → Pending Review → (payment) → Active
```

---

## 4. CRON JOBS (Hermes cron on Termux)

| Job | Frequency | Script | Purpose |
|---|---|---|---|
| Payment Reminders | Every 12h | payment_reminder.py | Remind students pending >48h, escalate >72h |
| Analytics Report | Every 6h | analytics_report.py | Business intelligence report |
| Bot Watchdog | Every 5min | watchdog.sh | Keep bot.py alive, restart on crash |

---

## 5. IDENTIFIED GAPS / ISSUES

### Critical:
1. **thank-you.html doesn't write to Airtable** — After payment, the thank-you page only shows a redirect to Telegram. It doesn't create an Airtable record. The student arrives at the bot as "new" even though they just paid.
2. **No webhook receiver running** — server.js (Express/Node) needs to be running to receive Flutterwave webhooks. Currently no server is running on Termux.
3. **formsubmit.co for demo/pay-later** — Relies on email delivery. No Airtable write from the site for demo or payment plan submissions.
4. **Bot token in .env is masked** — Need the full token from the previous agent or generate a new one.

### Medium:
5. **No email automation** — Brevo SMTP credentials exist but server.js needs to be running to send onboarding emails.
6. **Quiz funnel doesn't pass data to bot** — The quiz on index.html recommends a plan but doesn't pre-fill the bot deep link with the recommendation.
7. **Payment plan flow is email-only** — submitPayLater() sends to formsubmit.co, no Airtable integration.

### Low:
8. **No error handling for duplicate registrations** — If a user registers twice via bot, the `find_student` check handles update but doesn't notify about duplicate.
9. **No session expiry automation** — Expired status must be set manually.
10. **GA4 tracking on book.html** — `begin_checkout` event fires but no `purchase` event on thank-you.

---

## 6. LIGHTWEIGHT FAIL-SAFE MAPPING

### Principle: Every path must work even if one component fails.

```
                    ┌─────────────────────────────────┐
                    │         USER ARRIVES             │
                    └──────────┬──────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                 ▼
        ┌──────────┐   ┌──────────┐    ┌──────────────┐
        │   Site   │   │ Telegram │    │  Direct Link  │
        │  (book)  │   │  (bot)   │    │  (deep link)  │
        └────┬─────┘   └────┬─────┘    └──────┬───────┘
             │              │                  │
             ▼              ▼                  ▼
    ┌────────────┐  ┌──────────────┐  ┌────────────────┐
    │ Airtable   │  │ Registration │  │ Deep link      │
    │ write via  │  │ conversation │  │ parsing:       │
    │ bot deep   │  │ (name,email, │  │ name|email|    │
    │ link       │  │ phone)       │  │ phone|loc|plan │
    └─────┬──────┘  └──────┬───────┘  └───────┬────────┘
          │                │                   │
          ▼                ▼                   ▼
    ┌──────────────────────────────────────────────┐
    │              AIRTABLE RECORD                  │
    │  Status: Pending Review / Active (free)      │
    └──────────────────────┬───────────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ /approve │ │ /reject  │ │ /setprice│
        │ → Active │ → Rejected │ → Pending  │
        └────┬─────┘ └──────────┘ └────┬─────┘
             │                         │
             ▼                         ▼
    ┌──────────────────┐    ┌──────────────────┐
    │ Auto-welcome     │    │ Payment link     │
    │ (5-min poll)     │    │ sent to student  │
    │ Main menu shown  │    │ → pay → /approve │
    └──────────────────┘    └──────────────────┘
```

### Fail-Safes:
1. **If bot is down** → Site still collects leads via formsubmit.co (email fallback)
2. **If Airtable is down** → Bot uses SQLite cache (bot_cache.db), syncs when back
3. **If Flutterwave webhook fails** → Admin can manually /approve from Airtable
4. **If student pays but bot doesn't know** → payment_poll job checks every 5 min
5. **If bot crashes** → watchdog.sh restarts within 5 seconds
6. **If site can't reach bot** → Student can always manually message @Retpipebot
7. **If deep link fails** → Bot treats as new student, registration conversation
8. **If formsubmit.co fails** → Data in localStorage, can retry

---

## 7. TERMUX API INTEGRATION MAP

### Available (once Termux:API app installed):
| Feature | Command | Use Case |
|---|---|---|
| Flashlight | `termux-torch on/off` | Quick light |
| Battery | `termux-battery-status` | Monitor phone battery |
| Location | `termux-location` | GPS coordinates |
| Notifications | `termux-notification` | Push notifications |
| Toast | `termux-toast` | Quick popup messages |
| Vibrate | `termux-vibrate` | Haptic feedback |
| SMS | `termux-sms-send` | Send SMS |
| Contacts | `termux-contact-list` | Read contacts |
| Camera | `termux-camera-photo` | Take photos |
| TTS | `termux-tts-speak` | Text to speech |
| WiFi | `termux-wifi-connectioninfo` | Network info |
| Volume | `termux-volume` | Control volume |
| Brightness | `termux-brightness` | Screen brightness |
| Wake Lock | `termux-wake-lock` | Keep Termux alive |

### Integration Points:
1. **Bot monitoring** → `termux-notification` when bot crashes/restarts
2. **Payment alerts** → `termux-notification` + `termux-vibrate` on new payment
3. **Student activity** → `termux-toast` for quick status checks
4. **Location** → Student location for local meetups
5. **TTS** → Voice announcements for important events
6. **SMS** → Fallback notification channel if Telegram fails

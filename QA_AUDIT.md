# 🔍 QA AUDIT REPORT — Sessions with Toby
## Date: 2026-06-13
## Auditor: OWL — Lead Systems Architect

---

## PAGES AUDITED (28 HTML files)

| # | Page | Lines | Size | Status | Issues |
|---|---|---|---|---|---|
| 1 | index.html | 181 | 15KB | ✅ | Page loader may block if JS fails |
| 2 | home.html | 353 | 20KB | ✅ | None critical |
| 3 | book.html | 353 | 24KB | ⚠️ | Formsubmit.co fallback only, no Airtable write on site |
| 4 | pricing.html | 320 | 23KB | ⚠️ | Page loader may cause "blank" appearance |
| 5 | about.html | 308 | 22KB | ✅ | None |
| 6 | thank-you.html | 67 | 4KB | 🔴 | No Airtable write, no bot deep link with data |
| 7 | sessions-with-toby-2026.html | 236 | 14KB | ⚠️ | Static content, needs daily cron |
| 8 | quiz.html | 301 | 23KB | ✅ | None critical |
| 9 | community.html | 226 | 13KB | ✅ | None |
| 10 | blog.html | 117 | 7KB | ⚠️ | Blog listing only, no articles linked |
| 11 | lead-magnet.html | 230 | 15KB | ✅ | None |
| 12 | links.html | 131 | 8KB | ✅ | None |
| 13 | schedule-session.html | 196 | 11KB | ✅ | None |
| 14 | vocal-pain.html | 266 | 15KB | ✅ | None |
| 15 | linkedin.html | 171 | 10KB | ✅ | None |
| 16-21 | geo/* (6 files) | ~150ea | ~10KB | ✅ | SEO content, well structured |
| 22-24 | daily/* (3 files) | ~200ea | ~14KB | ⚠️ | Only 2 days of content, needs cron |
| 25 | abuja-community.html | — | — | ✅ | Community page |

---

## 🔴 CRITICAL ISSUES

### 1. thank-you.html — No Airtable Write (BROKEN FLOW)
**Severity:** CRITICAL
**Impact:** Students who pay via Flutterwave are NOT written to Airtable. They arrive at the bot as complete strangers. Admin has no way to know they paid without manually checking Flutterwave dashboard.

**Current flow:**
```
Payment → thank-you.html → redirect to t.me/Retpipebot → /start → "New student"
```

**Should be:**
```
Payment → thank-you.html → Airtable write (Pending Review) → redirect to bot → /start → "Payment pending, coach will verify"
```

**Fix:** Add JavaScript to thank-you.html that parses URL params (ref, amount, currency, name, email) and writes to Airtable via a lightweight API endpoint or Formsubmit.

---

### 2. Pricing Page "Blank" Issue
**Severity:** HIGH (you reported this)
**Root Cause:** The page loader (`#pageLoader`) has a 1.8s animation + 3.5s fallback. If the CSS file (`main.css?v=5.2`) fails to load or the JS errors, the loader stays visible and covers the entire page content.

**Fix:** Add a hard timeout that forces the loader to hide after 5 seconds regardless. Also add `<noscript>` fallback.

---

### 3. No Daily Content Cron Job
**Severity:** HIGH
**Impact:** The `sessions-with-toby-2026.html` page has static content. You said there should be a cron that researches and writes daily content. Currently only 2 daily pages exist (June 11, June 12). The page shows "Day 2 of 30" but there's no Day 3, 4, etc.

**Fix:** Build a Hermes cron job that:
1. Researches a high-pain-point singing topic daily
2. Writes a full content page (following the existing format)
3. Updates the main sessions-with-toby-2026.html to link to the latest article
4. Commits and pushes to GitHub

---

## ⚠️ MEDIUM ISSUES

### 4. book.html — No Direct Airtable Write
**Severity:** MEDIUM
**Impact:** The "Pay Now" buttons redirect to Flutterwave hosted links (not the Flutterwave API). The site never writes to Airtable. Only the bot handles Airtable writes.

**Flow gap:** Student pays on Flutterwave → Flutterwave redirects to thank-you.html → no Airtable record → student goes to bot → bot treats as new student.

**Fix:** Either:
a) Use Flutterwave API to create payment links dynamically with webhook callback, OR
b) Add Airtable write to thank-you.html (fixes #1 above)

### 5. Demo Form — formsubmit.co Only
**Severity:** MEDIUM
**Impact:** Free demo submissions go to email only. No Airtable record created automatically.

**Fix:** Add Airtable write to the demo form submission.

### 6. Payment Plan Form — formsubmit.co Only
**Severity:** MEDIUM
**Impact:** Same as demo form. Payment plan requests go to email only.

**Fix:** Add Airtable write to the payment plan form.

### 7. Blog Page Has No Articles
**Severity:** LOW
**Impact:** blog.html is a listing page with no linked articles.

**Fix:** Link to daily content pages or GEO articles.

### 8. No 404 Page
**Severity:** LOW
**Impact:** Broken links show GitHub Pages default 404.

**Fix:** Add a custom 404.html.

---

## ✅ WHAT'S WORKING WELL

1. **Design system** — Clean, modern, high-contrast dark theme. Consistent across all pages.
2. **Quiz funnel** — 5-step quiz with personalized recommendations. Works smoothly.
3. **Pricing page** — Complete with 4 coaching plans, 3 community plans, speaking, comparison table, FAQ, guarantee.
4. **Bot code** — Comprehensive, well-structured, zero AI tokens.
5. **Airtable integration** — Full CRUD with SQLite cache fallback.
6. **Flutterwave integration** — Hosted payment links working.
7. **GEO content** — 6 SEO articles ready.
8. **Responsive design** — Mobile-first, works on all screen sizes.
9. **Page loader animation** — Smooth branded loader (when it works correctly).

---

## 📋 FIX PRIORITY ORDER

| Priority | Fix | Effort |
|---|---|---|
| P0 | thank-you.html → Airtable write | 2 hours |
| P0 | Pricing page loader fix | 30 min |
| P0 | Daily content cron job | 3 hours |
| P1 | book.html → Airtable write for all paths | 2 hours |
| P1 | Demo form → Airtable write | 1 hour |
| P1 | Payment plan form → Airtable write | 1 hour |
| P2 | Blog page → link articles | 30 min |
| P2 | Custom 404 page | 30 min |

---

## 🔧 TECHNICAL NOTES

- All pages load `main.css?v=5.2` — cache busting with version parameter ✅
- All pages load `payment.js` for Flutterwave ✅
- Pricing page loads `pricing.js` for geo-IP currency detection ✅
- GA4 tracking on all pages ✅
- Plausible analytics on pricing page ✅
- Formsubmit.co used for demo and payment plan forms ⚠️ (no Airtable)
- No CSP headers (GitHub Pages limitation) ⚠️
- No service worker / PWA ⚠️

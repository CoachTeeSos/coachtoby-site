/* ═══════════════════════════════════════════════════════════════
   COACH TOBY — Express Controller (server.js)
   Serves 20 flat HTML pages + static assets
   POST /webhook/flutterwave → Nodemailer onboarding email
   ═══════════════════════════════════════════════════════════════ */

const express    = require('express');
const path       = require('path');
const nodemailer = require('nodemailer');

const app  = express();
const PORT = process.env.PORT || 3000;

// ── Middleware ──
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// ── Static Assets ──
app.use('/assets', express.static(path.join(__dirname, 'assets')));

// ── 20 HTML Page Routes ──
const pages = [
  'index', 'home', 'about', 'book', 'pricing', 'blog',
  'community', 'abuja-community', 'content', 'lead-magnet',
  'quiz', 'links', 'carousel-30days', 'carousel-generator'
];

pages.forEach(function(page) {
  app.get('/' + page, function(req, res) {
    res.sendFile(path.join(__dirname, page + '.html'));
  });
});

// GEO pages
const geoPages = [
  'index', 'how-to-improve-singing-voice', 'how-to-overcome-stage-fright',
  'life-coaching-vs-therapy', 'online-vocal-coaching-nigeria',
  'voice-coach-vs-singing-teacher'
];

geoPages.forEach(function(page) {
  app.get('/geo/' + page, function(req, res) {
    res.sendFile(path.join(__dirname, 'geo', page + '.html'));
  });
});

// Root → index
app.get('/', function(req, res) {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// Catch-all → index (SPA fallback)
app.get('*', function(req, res) {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// ═══════════════════════════════════════════════════════════════
// FLUTTERWAVE WEBHOOK
// Receives server-to-server payment notifications
// ═══════════════════════════════════════════════════════════════
app.post('/webhook/flutterwave', function(req, res) {
  const event = req.body.event || '';
  const data  = req.body.data  || {};

  // Only process successful charges
  if (event === 'charge.completed' && (data.status === 'successful' || data.status === 'completed')) {
    const email = data.customer && data.customer.email ? data.customer.email : '';
    const name  = data.customer && data.customer.name  ? data.customer.name  : 'Friend';
    const amount = data.amount || 0;
    const currency = data.currency || 'USD';
    const txRef = data.tx_ref || '';

    if (email) {
      sendOnboardingEmail(email, name, amount, currency, txRef)
        .then(function() { console.log('[FW] Onboarding email sent to', email); })
        .catch(function(err) { console.error('[FW] Email failed:', err.message); });
    }
  }

  // Always respond 200 so FW doesn't retry
  res.status(200).json({ received: true });
});

// ═══════════════════════════════════════════════════════════════
// NODEMAILER — Onboarding Email
// ═══════════════════════════════════════════════════════════════
function sendOnboardingEmail(email, name, amount, currency, txRef) {
  const transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST || 'smtp-rely.brevo.com',
    port: parseInt(process.env.SMTP_PORT) || 587,
    auth: {
      user: process.env.SMTP_USER || process.env.BREVO_USER || '',
      pass: process.env.SMTP_PASS || process.env.BREVO_PASS || ''
    }
  });

  const botLink = 'https://t.me/Retpipebot?start=payment_' + txRef;

  const html = [
    '<div style="max-width:600px;margin:0 auto;font-family:Inter,Arial,sans-serif;color:#004B49">',
      '<div style="background:#004B49;padding:32px;text-align:center;border-radius:32px 32px 0 0">',
        '<h1 style="color:#D2E823;margin:0;font-size:1.5rem;font-weight:800">Welcome to Sessions with Toby 🎤</h1>',
      '</div>',
      '<div style="background:#FDFBF7;border:3px solid #004B49;border-top:none;padding:32px;border-radius:0 0 32px 32px">',
        '<p style="font-size:1.1rem">Hey ' + name + ',</p>',
        '<p>Your payment of <strong>' + currency + ' ' + amount.toLocaleString() + '</strong> has been confirmed (Ref: ' + txRef + ').</p>',
        '<p>You\'re officially on the path to transforming your voice.</p>',
        '<div style="text-align:center;margin:2rem 0">',
          '<a href="' + botLink + '" style="display:inline-block;padding:16px 40px;background:#58CC02;color:#004B49;font-weight:700;text-decoration:none;border-radius:16px;border:3px solid #004B49;font-size:1.05rem;box-shadow:0 4px 0 0 #46A302">Start Coaching on Telegram →</a>',
        '</div>',
        '<p style="color:#5A7D7C;font-size:0.9rem;line-height:1.7">This is your fastest way to book sessions, get your practice plan, and connect with Coach Toby directly inside Telegram.</p>',
        '<hr style="border:none;border-top:1px solid rgba(0,75,73,0.12);margin:24px 0">',
        '<p style="color:#5A7D7C;font-size:0.85rem;line-height:1.7">Not on Telegram? No problem — reply to this email and we\'ll send you a manual alternative to access your coaching plan.</p>',
        '<p style="color:#5A7D7C;font-size:0.8rem;margin-top:24px">© 2026 Sessions with Toby · prosperolumotobi@gmail.com</p>',
      '</div>',
    '</div>'
  ].join('\n');

  return transporter.sendMail({
    from: '"Sessions with Toby" <prosperolumotobi@gmail.com>',
    to: email,
    subject: 'Welcome to Sessions with Toby 🎤 Your Payment is Confirmed',
    html: html
  });
}

// ── Start Server ──
app.listen(PORT, function() {
  console.log('CoachToby site running on port ' + PORT);
});

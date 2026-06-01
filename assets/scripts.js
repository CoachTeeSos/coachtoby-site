/* ═════════════════════════════════════════
   COACH TOBY — CORE SCRIPTS v2
   Inline form → Airtable API → Telegram bot
   ════════════════════════════════════════ */

/* ── PROGRESS BAR ──*/
(function() {
  var bar = document.querySelector('.progress-bar');
  if (!bar) return;
  window.addEventListener('scroll', function() {
    var scrollTop = window.scrollY;
    var docHeight = document.documentElement.scrollHeight - window.innerHeight;
    var pct = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
    bar.style.width = pct + '%';
  }, { passive: true });
})();

/* ── SCROLL REVEAL ──*/
(function() {
  var reveals = document.querySelectorAll('.reveal');
  if (!reveals.length) return;
  var observer = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      } else {
        entry.target.classList.remove('visible');
      }
    });
  }, { threshold: 0.05, rootMargin: '0px' });
  reveals.forEach(function(el) { observer.observe(el); });
})();

/* ── NAV SCROLL EFFECT ──*/
(function() {
  var nav = document.querySelector('nav');
  if (!nav) return;
  window.addEventListener('scroll', function() {
    nav.classList.toggle('scrolled', window.scrollY > 60);
  }, { passive: true });
})();

/* ── COUNTER ANIMATION ──*/
(function() {
  var stats = document.querySelectorAll('.stat .num');
  if (!stats.length) return;
  var observer = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        var el = entry.target;
        var raw = el.textContent.trim();
        var numMatch = raw.match(/^([\\d,.]+)/);
        if (!numMatch) return;
        var target = parseFloat(numMatch[1].replace(/,/g, ''));
        var suffix = raw.replace(numMatch[1], '');
        var duration = 2000;
        var start = null;
        function step(timestamp) {
          if (!start) start = timestamp;
          var progress = Math.min((timestamp - start) / duration, 1);
          var eased = 1 - Math.pow(1 - progress, 3);
          var current = Math.round(eased * target);
          el.textContent = current.toLocaleString() + suffix;
          if (progress < 1) requestAnimationFrame(step);
          else el.textContent = raw;
        }
        requestAnimationFrame(step);
        observer.unobserve(el);
      }
    });
  }, { threshold: 0.5 });
  stats.forEach(function(el) { observer.observe(el); });
})();

/* ── STICKY CTA ──*/
(function() {
  var sticky = document.querySelector('.sticky-cta');
  var hero = document.querySelector('.hero');
  if (!sticky || !hero) return;
  window.addEventListener('scroll', function() {
    var heroBottom = hero.getBoundingClientRect().bottom;
    sticky.classList.toggle('visible', heroBottom < 0);
  }, { passive: true });
})();

/* ── SIDE RAIL ──*/
function openRail() {
  var panel = document.querySelector('.rail-panel');
  var overlay = document.querySelector('.rail-overlay');
  if (panel) panel.classList.add('open');
  if (overlay) overlay.classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeRail() {
  var panel = document.querySelector('.rail-panel');
  var overlay = document.querySelector('.rail-overlay');
  if (panel) panel.classList.remove('open');
  if (overlay) overlay.classList.remove('open');
  document.body.style.overflow = '';
}
document.addEventListener('keydown', function(e) { if (e.key === 'Escape') closeRail(); });

/* ── HAMBURGER TOGGLE ──*/
function toggleMobileMenu() {
  var links = document.querySelector('nav .nav-links');
  if (links) links.classList.toggle('mobile-open');
}

/* ═══════════════════════════════════════
   CONFIG
   ═══════════════════════════════════════ */
const BOT_USERNAME = 'Retpipebot';

const SERVICES = {
  single:      { label: 'Single Session — $50',           price: 50,     currency: 'USD', type: 'coaching' },
  monthly:     { label: 'Monthly Package — $200',          price: 200,    currency: 'USD', type: 'coaching' },
  'ngn-single':{ label: 'Single Session — ₦70,000',       price: 70000,  currency: 'NGN', type: 'coaching' },
  'ngn-monthly':{ label: 'Monthly Package — ₦300,000',    price: 300000, currency: 'NGN', type: 'coaching' },
  'free-community': { label: "Free Singers' Community",    price: 0,      currency: '',    type: 'community', link: 'https://t.me/+LGYumO9JZOc1M2M0' },
  'paid-community': { label: "Paid Singers' Community — ₦20,000/mo", price: 20000, currency: 'NGN', type: 'paid-community', link: 'https://t.me/+SMnit5TdCuBlOWE0' },
  'abuja-collective': { label: 'Abuja Music Collective',   price: 0,      currency: '',    type: 'community', link: 'https://t.me/+qv5hIOIBKgtmNjhk' },
  quiz:        { label: 'Which Singer Are You? Quiz',      price: 0,      currency: '',    type: 'content',   link: 'https://coachteesos.github.io/coachtoby-site/quiz.html' },
  'lead-magnet': { label: '5 Vocal Exercises Guide',       price: 0,      currency: '',    type: 'content',   link: 'https://coachteesos.github.io/coachtoby-site/lead-magnet.html' },
  'speaking': { label: 'Speaking Engagement — ₦200,000', price: 200000, currency: 'NGN', type: 'speaking' },
  'custom-plan': { label: 'Design Your Own Plan', price: 0, currency: '', type: 'custom' },
  'group3-5': { label: 'Group of 3-5 — ₦20,000/month', price: 20000, currency: 'NGN', type: 'paid-community' },
  'free-call': { label: 'Free Clarity Call', price: 0, currency: '', type: 'call' }
};

const FLUTTERWAVE = {
  single:         'https://flutterwave.com/pay/ictjiqq30sz7',
  monthly:        'https://flutterwave.com/pay/b0hjfvjhv8x4',
  'ngn-single':   'https://flutterwave.com/pay/xnddgkfjeheq',
  'ngn-monthly':  'https://flutterwave.com/pay/wdod0tyeqedw',
  'group3-5':     'https://flutterwave.com/pay/lrgz2vk3xez3',
  'paid-community': 'https://flutterwave.com/pay/lrgz2vk3xez3',
  'speaking':     'https://flutterwave.com/pay/wdod0tyeqedw'
};

/* ═══════════════════════════════════════
   INLINE FORM MODAL
   ═══════════════════════════════════════ */
var currentServiceKey = null;
var formModal = null;

function ensureModal() {
  if (formModal) return;
  var d = document.createElement('div');
  d.id = 'cta-modal';
  d.innerHTML = [
    '<div class="cta-modal-overlay" onclick="closeModal()"></div>',
    '<div class="cta-modal-box">',
      '<button class="cta-modal-close" onclick="closeModal()">×</button>',
      '<h3 id="cta-modal-title">Let\'s Get Started</h3>',
      '<p class="cta-modal-sub" id="cta-modal-sub">Fill this out and we\'ll take it from here.</p>',
      '<form id="cta-form" onsubmit="return submitForm(event)">',
        '<div class="cta-field"><label>Full Name *</label><input type="text" id="cta-name" required placeholder="Your full name"></div>',
        '<div class="cta-field"><label>Email *</label><input type="email" id="cta-email" required placeholder="you@example.com"></div>',
        '<div class="cta-field"><label>Phone (with country code) *</label><input type="tel" id="cta-phone" required placeholder="+234 800 000 0000"></div>',
        '<div class="cta-field" id="cta-budget-field" style="display:none;"><label>Your Budget</label><input type="text" id="cta-budget" placeholder="₦50,000 – ₦500,000"></div>',
        '<div class="cta-field" id="cta-needs-field" style="display:none;"><label>What do you need help with?</label><input type="text" id="cta-needs" placeholder="Vocal coaching, life coaching, etc."></div>',
        '<div class="cta-field" id="cta-payment-row" style="display:none;">',
          '<button type="button" id="cta-pay-btn" class="btn-primary" style="width:100%;">💳 Pay Now</button>',
          '<p id="cta-pay-status" style="font-size:0.78rem;color:var(--muted);margin-top:8px;text-align:center;"></p>',
        '</div>',
        '<button type="submit" class="btn-primary" style="width:100%;margin-top:8px;">Continue →</button>',
        '<p style="font-size:0.72rem;color:var(--muted);margin-top:10px;text-align:center;">No spam. We respect your privacy.</p>',
      '</form>',
    '</div>'
  ].join('');

  // Inject modal styles
  var s = document.createElement('style');
  s.textContent = [
    '.cta-modal-overlay{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.7);backdrop-filter:blur(8px);z-index:1000;}',
    '.cta-modal-box{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:#0e0e14;border:1px solid #1c1c28;border-radius:20px;padding:32px 28px;width:90%;max-width:440px;z-index:1001;max-height:90vh;overflow-y:auto;}',
    '.cta-modal-close{position:absolute;top:14px;right:14px;background:none;border:none;color:#6e6e8a;font-size:1.4rem;cursor:pointer;padding:4px;line-height:1;}',
    '.cta-modal-box h3{font-size:1.2rem;font-weight:800;margin-bottom:6px;}',
    '.cta-modal-sub{color:#6e6e8a;font-size:0.85rem;margin-bottom:20px;}',
    '.cta-field{margin-bottom:14px;}',
    '.cta-field label{display:block;font-size:0.78rem;font-weight:600;color:#c8c8d8;margin-bottom:4px;}',
    '.cta-field input{width:100%;padding:12px 14px;background:#06060a;border:1px solid #1c1c28;border-radius:10px;color:#ededf4;font-size:0.92rem;font-family:inherit;outline:none;transition:border-color .2s;}',
    '.cta-field input:focus{border-color:#c084fc;}',
    '.cta-field input::placeholder{color:#4a4a6a;}'
  ].join('');

  document.head.appendChild(s);
  document.body.appendChild(d);
  formModal = d;

  // Payment button handler
  document.getElementById('cta-pay-btn').addEventListener('click', function() {
    var fwLink = FLUTTERWAVE[currentServiceKey];
    if (fwLink) {
      window.open(fwLink, '_blank');
      document.getElementById('cta-pay-status').textContent = 'Payment page opened. Come back here after paying.';
      document.getElementById('cta-pay-status').style.color = 'var(--success)';
    }
  });
}

function openModal(serviceKey) {
  currentServiceKey = serviceKey;
  var svc = SERVICES[serviceKey];
  if (!svc) return;

  ensureModal();

  document.getElementById('cta-modal-title').textContent = svc.label;
  document.getElementById('cta-modal-sub').textContent = svc.price > 0
    ? 'Fill this out, then complete payment to secure your spot.'
    : 'Fill this out and we\'ll get you started right away.';

  // Show/hide fields based on service type
  var isCustom = svc.type === 'custom';
  var isPaid = svc.price > 0;
  document.getElementById('cta-budget-field').style.display = isCustom ? '' : 'none';
  document.getElementById('cta-needs-field').style.display = isCustom ? '' : 'none';
  document.getElementById('cta-payment-row').style.display = isPaid ? '' : 'none';
  document.getElementById('cta-pay-status').textContent = '';

  // Reset form
  document.getElementById('cta-form').reset();
  document.getElementById('cta-name').focus();

  document.getElementById('cta-modal').style.display = 'block';
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  if (formModal) formModal.style.display = 'none';
  document.body.style.overflow = '';
  currentServiceKey = null;
}

document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') closeModal();
});

/* ── FORM SUBMIT ──*/
function submitForm(e) {
  e.preventDefault();
  var serviceKey = currentServiceKey;
  var svc = SERVICES[serviceKey];
  if (!svc) return false;

  var name = document.getElementById('cta-name').value.trim();
  var email = document.getElementById('cta-email').value.trim();
  var phone = document.getElementById('cta-phone').value.trim();
  var budget = document.getElementById('cta-budget') ? document.getElementById('cta-budget').value.trim() : '';
  var needs = document.getElementById('cta-needs') ? document.getElementById('cta-needs').value.trim() : '';

  if (!name || !email || !phone) {
    alert('Please fill in all required fields.');
    return false;
  }

  closeModal();

  // Redirect to bot — it will capture @username + ID automatically from Telegram
  var botUrl = 'https://t.me/' + BOT_USERNAME + '?start=' + encodeURIComponent(name + '|' + serviceKey);

  if (svc.price > 0) {
    // Paid: open Flutterwave payment, then redirect to bot after delay
    var fwLink = FLUTTERWAVE[serviceKey];
    if (fwLink) window.open(fwLink, '_blank');
    setTimeout(function() {
      window.open(botUrl, '_blank');
    }, 2000);
    alert('✅ Almost done!\n\n1. Complete your payment\n2. Tap "Start" in Telegram\n\nWelcome, ' + name + ' 🎤');
  } else {
    // Free: go straight to bot
    window.open(botUrl, '_blank');
  }

  return false;
}

/* ═══════════════════════════════════════
   MAIN ROUTER — Every button calls this
   ═══════════════════════════════════════ */
function goToBot(serviceKey) {
  openModal(serviceKey);
}

/* ── LEGACY COMPATIBILITY ──*/
function legacyPay(plan) { goToBot(plan); }
function payWithFlutterwaveNGN(amount, planName) {
  if (planName && planName.includes('300')) goToBot('ngn-monthly');
  else goToBot('ngn-single');
}


/* ── CTA FORM SUBMIT (replaces Airtable iframe) ── */
function handleCTASubmit(e) {
  e.preventDefault();
  var name = document.getElementById('cta-name').value.trim();
  var email = document.getElementById('cta-email').value.trim();
  var phone = document.getElementById('cta-phone').value.trim();
  var service = document.getElementById('cta-service').value;

  if (!name || !email || !phone || !service) {
    alert('Please fill in all required fields.');
    return false;
  }

  closeModal();

  // Redirect to bot — it will capture @username + ID automatically from Telegram
  var botUrl = 'https://t.me/Retpipebot?start=' + encodeURIComponent(name + '|' + service);

  var FLUTTERWAVE = {
    single: 'https://flutterwave.com/pay/ictjiqq30sz7',
    monthly: 'https://flutterwave.com/pay/b0hjfvjhv8x4',
    'ngn-single': 'https://flutterwave.com/pay/xnddgkfjeheq',
    'ngn-monthly': 'https://flutterwave.com/pay/wdod0tyeqedw',
    'group3-5': 'https://flutterwave.com/pay/lrgz2vk3xez3',
    'paid-community': 'https://flutterwave.com/pay/lrgz2vk3xez3',
    speaking: 'https://flutterwave.com/pay/wdod0tyeqedw'
  };

  var isPaid = ['single','monthly','ngn-single','ngn-monthly','group3-5','paid-community','speaking'].indexOf(service) !== -1;

  if (isPaid) {
    var fwLink = FLUTTERWAVE[service];
    if (fwLink) window.open(fwLink, '_blank');
    setTimeout(function() { window.open(botUrl, '_blank'); }, 2000);
    alert('✅ Almost done!\n\n1. Complete your payment\n2. Tap "Start" in Telegram\n\nWelcome, ' + name + ' 🎤');
  } else {
    window.open(botUrl, '_blank');
  }

  return false;
}


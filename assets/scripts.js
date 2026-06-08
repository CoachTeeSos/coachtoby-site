/* ═══════════════════════════════════════════════════════════════
   COACH TOBY — CORE SCRIPTS v3
   Geo-IP currency detection · Budget calculator · Singing-first
   ═══════════════════════════════════════════════════════════════ */

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
      if (entry.isIntersecting) entry.target.classList.add('visible');
      else entry.target.classList.remove('visible');
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
        var numMatch = raw.match(/^([\d,.]+)/);
        if (!numMatch) return;
        var target = parseFloat(numMatch[1].replace(/,/g, ''));
        var suffix = raw.replace(numMatch[1], '');
        var duration = 2000;
        var start = null;
        function step(ts) {
          if (!start) start = ts;
          var p = Math.min((ts - start) / duration, 1);
          var eased = 1 - Math.pow(1 - p, 3);
          el.textContent = Math.round(eased * target).toLocaleString() + suffix;
          if (p < 1) requestAnimationFrame(step);
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
    sticky.classList.toggle('visible', hero.getBoundingClientRect().bottom < 0);
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

/* ═══════════════════════════════════════════════════════════════
   GEO-IP CURRENCY DETECTION
   Uses free ipapi.co — no key needed, 45 req/min free tier
   ═══════════════════════════════════════════════════════════════ */
var USER_COUNTRY = null;
var USER_CURRENCY = 'USD'; // default
var USER_SYMBOL = '$';
var USER_IS_NIGERIA = false;

function detectCurrency() {
  // Check localStorage cache first (valid 24h)
  var cached = localStorage.getItem('ct_geo');
  if (cached) {
    try {
      var d = JSON.parse(cached);
      if (d && d.ts && (Date.now() - d.ts) < 86400000) {
        applyCurrency(d.country, d.currency, d.symbol, d.isNG);
        return;
      }
    } catch(e) {}
  }

  // Fetch from ipapi.co (free, no key)
  fetch('https://ipapi.co/json/')
    .then(function(r) { return r.json(); })
    .then(function(d) {
      var country = d.country_code || '';
      var isNG = country === 'NG';
      var currency = isNG ? 'NGN' : 'USD';
      var symbol = isNG ? '₦' : '$';
      localStorage.setItem('ct_geo', JSON.stringify({ country: country, currency: currency, symbol: symbol, isNG: isNG, ts: Date.now() }));
      applyCurrency(country, currency, symbol, isNG);
    })
    .catch(function() {
      // Fallback: try ip-api.com
      fetch('http://ip-api.com/json/')
        .then(function(r) { return r.json(); })
        .then(function(d) {
          var country = d.countryCode || '';
          var isNG = country === 'NG';
          var currency = isNG ? 'NGN' : 'USD';
          var symbol = isNG ? '₦' : '$';
          applyCurrency(country, currency, symbol, isNG);
        })
        .catch(function() {
          // Silent fallback to USD
          applyCurrency('US', 'USD', '$', false);
        });
    });
}

function applyCurrency(country, currency, symbol, isNG) {
  USER_COUNTRY = country;
  USER_CURRENCY = currency;
  USER_SYMBOL = symbol;
  USER_IS_NIGERIA = isNG;

  // Update all price elements on the page
  document.querySelectorAll('[data-price-usd]').forEach(function(el) {
    var usd = el.getAttribute('data-price-usd');
    var ngn = el.getAttribute('data-price-ngn');
    if (isNG && ngn) {
      el.textContent = '₦' + parseInt(ngn).toLocaleString();
    } else if (usd) {
      el.textContent = '$' + parseInt(usd).toLocaleString();
    }
  });

  // Update currency labels
  document.querySelectorAll('[data-currency-label]').forEach(function(el) {
    el.textContent = isNG ? 'NGN' : 'USD';
  });

  // Update per-session labels
  document.querySelectorAll('[data-per-label]').forEach(function(el) {
    el.textContent = isNG ? '/session' : '/session';
  });

  // Show/hide Nigeria-specific pricing notes
  document.querySelectorAll('[data-ng-only]').forEach(function(el) {
    el.style.display = isNG ? '' : 'none';
  });
  document.querySelectorAll('[data-intl-only]').forEach(function(el) {
    el.style.display = isNG ? 'none' : '';
  });

  // Update budget placeholder
  var budgetInput = document.getElementById('cta-budget');
  if (budgetInput) {
    budgetInput.placeholder = isNG ? '₦10,000 – ₦500,000' : '$20 – $500';
  }

  // Dispatch event so other scripts can react
  document.dispatchEvent(new CustomEvent('currencyDetected', { detail: { country: country, currency: currency, symbol: symbol, isNG: isNG } }));
}

// Run on load
detectCurrency();

/* ═══════════════════════════════════════════════════════════════
   BUDGET CALCULATOR — "What Can I Afford?"
   ═══════════════════════════════════════════════════════════════ */
function initBudgetCalculator() {
  var calc = document.getElementById('budget-calculator');
  if (!calc) return;

  var input = document.getElementById('budget-input');
  var result = document.getElementById('budget-result');
  var currencyToggle = document.getElementById('budget-currency-toggle');

  if (!input || !result) return;

  // Set placeholder based on detected currency
  input.placeholder = USER_IS_NIGERIA ? 'Enter amount in Naira (e.g. 50000)' : 'Enter amount in USD (e.g. 100)';

  input.addEventListener('input', function() {
    var raw = input.value.replace(/[^0-9]/g, '');
    var amount = parseInt(raw);
    if (!amount || amount <= 0) {
      result.innerHTML = '';
      result.style.display = 'none';
      return;
    }

    var isNG = USER_IS_NIGERIA;
    var html = '<div class="budget-result-inner">';
    html += '<h4>Here\'s what <strong>' + (isNG ? '₦' : '$') + amount.toLocaleString() + '</strong> can get you:</h4>';
    html += '<div class="budget-options">';

    if (isNG) {
      // Naira pricing
      if (amount >= 700000) {
        html += budgetOption('🎤 Full Monthly Package', '₦300,000/mo', '4 sessions + priority + WhatsApp check-ins', 'monthly', 'ngn-monthly');
        html += budgetOption('👥 Group Coaching (10 people)', '₦20,000/person/mo', '4 group sessions — perfect for your team or choir', 'group3-5', 'group3-5');
        html += budgetOption('⭐ Paid Community', '₦20,000/mo', 'Weekly tips, Q&As, personalized feedback', 'paid-community', 'paid-community');
      } else if (amount >= 300000) {
        html += budgetOption('🎤 Monthly Package', '₦300,000/mo', '4 sessions + priority + WhatsApp check-ins', 'monthly', 'ngn-monthly');
        html += budgetOption('👥 Group Coaching', '₦20,000/person/mo', '4 group sessions — bring your friends', 'group3-5', 'group3-5');
        html += budgetOption('⭐ Paid Community', '₦20,000/mo', 'Weekly tips, Q&As, personalized feedback', 'paid-community', 'paid-community');
      } else if (amount >= 140000) {
        html += budgetOption('🎤 2 Single Sessions', '₦70,000 each', '2 × 60-min 1-on-1 sessions', 'single', 'ngn-single');
        html += budgetOption('👥 Group Coaching', '₦20,000/person/mo', '4 group sessions — bring your friends', 'group3-5', 'group3-5');
        html += budgetOption('⭐ Paid Community', '₦20,000/mo', 'Weekly tips, Q&As, personalized feedback', 'paid-community', 'paid-community');
      } else if (amount >= 70000) {
        html += budgetOption('🎤 1 Single Session', '₦70,000', '60-min 1-on-1 session + personalized exercises', 'single', 'ngn-single');
        html += budgetOption('👥 Group Coaching', '₦20,000/person/mo', '4 group sessions — bring your friends', 'group3-5', 'group3-5');
        html += budgetOption('⭐ Paid Community', '₦20,000/mo', 'Weekly tips, Q&As, personalized feedback', 'paid-community', 'paid-community');
      } else if (amount >= 20000) {
        html += budgetOption('👥 Group Coaching', '₦20,000/person/mo', '4 group sessions — bring your friends', 'group3-5', 'group3-5');
        html += budgetOption('⭐ Paid Community', '₦20,000/mo', 'Weekly tips, Q&As, personalized feedback', 'paid-community', 'paid-community');
        html += budgetOption('🎤 Save for a Single Session', '₦70,000 needed', 'You\'re ₦' + (70000 - amount).toLocaleString() + ' away — keep saving!', null, null);
      } else if (amount >= 10000) {
        html += budgetOption('⭐ Paid Community', '₦20,000/mo', 'You\'re ₦' + (20000 - amount).toLocaleString() + ' away — almost there!', 'paid-community', 'paid-community');
        html += budgetOption('🎤 Save for a Single Session', '₦70,000 needed', 'You\'re ₦' + (70000 - amount).toLocaleString() + ' away — keep saving!', null, null);
        html += budgetOption('🎵 Free Community', 'FREE', 'Join now — start growing today', 'free-community', 'free-community');
      } else {
        html += budgetOption('🎵 Free Singers\' Community', 'FREE', 'Join 50+ singers — share recordings, get feedback', 'free-community', 'free-community');
        html += budgetOption('🎯 Take the Quiz', 'FREE', 'Find out what\'s holding you back', 'quiz', 'quiz');
        html += budgetOption('📖 Free Vocal Exercises Guide', 'FREE', '5 exercises that instantly improve your tone', 'lead-magnet', 'lead-magnet');
        html += budgetOption('💡 Save toward coaching', '₦20,000+', 'Group coaching starts at ₦20,000/person/month', null, null);
      }
    } else {
      // USD pricing
      if (amount >= 500) {
        html += budgetOption('🎤 Monthly Package', '$200/mo', '4 sessions + priority + WhatsApp check-ins', 'monthly', 'monthly');
        html += budgetOption('🎤 2 Single Sessions', '$50 each', '2 × 60-min 1-on-1 sessions', 'single', 'single');
        html += budgetOption('⭐ Paid Community', '~$30/mo', 'Weekly tips, Q&As, personalized feedback', 'paid-community', 'paid-community');
      } else if (amount >= 200) {
        html += budgetOption('🎤 Monthly Package', '$200/mo', '4 sessions + priority + WhatsApp check-ins', 'monthly', 'monthly');
        html += budgetOption('⭐ Paid Community', '~$30/mo', 'Weekly tips, Q&As, personalized feedback', 'paid-community', 'paid-community');
      } else if (amount >= 100) {
        html += budgetOption('🎤 2 Single Sessions', '$50 each', '2 × 60-min 1-on-1 sessions', 'single', 'single');
        html += budgetOption('⭐ Paid Community', '~$30/mo', 'Weekly tips, Q&As, personalized feedback', 'paid-community', 'paid-community');
      } else if (amount >= 50) {
        html += budgetOption('🎤 1 Single Session', '$50', '60-min 1-on-1 session + personalized exercises', 'single', 'single');
        html += budgetOption('⭐ Paid Community', '~$30/mo', 'Weekly tips, Q&As, personalized feedback', 'paid-community', 'paid-community');
      } else if (amount >= 20) {
        html += budgetOption('⭐ Paid Community', '~$30/mo', 'You\'re $' + (30 - amount) + ' away — almost there!', 'paid-community', 'paid-community');
        html += budgetOption('🎤 Save for a Session', '$50 needed', 'You\'re $' + (50 - amount) + ' away — keep saving!', null, null);
        html += budgetOption('🎵 Free Community', 'FREE', 'Join now — start growing today', 'free-community', 'free-community');
      } else {
        html += budgetOption('🎵 Free Singers\' Community', 'FREE', 'Join 50+ singers — share recordings, get feedback', 'free-community', 'free-community');
        html += budgetOption('🎯 Take the Quiz', 'FREE', 'Find out what\'s holding you back', 'quiz', 'quiz');
        html += budgetOption('📖 Free Vocal Exercises Guide', 'FREE', '5 exercises that instantly improve your tone', 'lead-magnet', 'lead-magnet');
        html += budgetOption('💡 Save toward coaching', '$50+', 'Single sessions start at $50', null, null);
      }
    }

    html += '</div>';
    html += '<p class="budget-disclaimer">Prices shown in ' + (isNG ? 'Naira (₦)' : 'USD ($)') + '. <a href="pricing.html">See full pricing →</a></p>';
    html += '</div>';

    result.innerHTML = html;
    result.style.display = 'block';
  });
}

function budgetOption(title, price, desc, serviceKey, btnKey) {
  var btn = '';
  if (serviceKey) {
    btn = '<button class="btn-primary btn-sm" onclick="goToBot(\'' + serviceKey + '\')">' + (price === 'FREE' ? 'Join Free →' : 'Get Started →') + '</button>';
  } else {
    btn = '<span class="budget-save-note">💡 Save up</span>';
  }
  return '<div class="budget-option">' +
    '<div class="budget-option-info">' +
      '<div class="budget-option-title">' + title + '</div>' +
      '<div class="budget-option-price">' + price + '</div>' +
      '<div class="budget-option-desc">' + desc + '</div>' +
    '</div>' +
    '<div class="budget-option-action">' + btn + '</div>' +
  '</div>';
}

// Run on DOM ready
document.addEventListener('DOMContentLoaded', initBudgetCalculator);

/* ═══════════════════════════════════════════════════════════════
   CONFIG
   ═══════════════════════════════════════════════════════════════ */
const BOT_USERNAME = 'Retpipebot';
const PROXY_URL = '';

function sendToProxy(fields) {
  if (!PROXY_URL) return Promise.resolve(false);
  return fetch(PROXY_URL + '/register', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(fields),
  }).then(function(res) { return res.ok; });
}

/* ── SERVICES ── */
const SERVICES = {
  single:      { label: 'Single Session',           price: 50,     currency: 'USD', type: 'coaching' },
  monthly:     { label: 'Monthly Package',           price: 200,    currency: 'USD', type: 'coaching' },
  'ngn-single':{ label: 'Single Session',            price: 70000,  currency: 'NGN', type: 'coaching' },
  'ngn-monthly':{ label: 'Monthly Package',          price: 300000, currency: 'NGN', type: 'coaching' },
  'free-community': { label: "Free Singers' Community", price: 0,  currency: '',    type: 'community', link: 'https://t.me/+LGYumO9JZOc1M2M0' },
  'paid-community': { label: "Paid Singers' Community", price: 20000, currency: 'NGN', type: 'paid-community', link: 'https://t.me/+SMnit5TdCuBlOWE0' },
  'abuja-collective': { label: 'Abuja Music Collective', price: 0, currency: '',    type: 'community', link: 'https://t.me/+qv5hIOIBKgtmNjhk' },
  quiz:        { label: 'Which Singer Are You? Quiz', price: 0,     currency: '',    type: 'content',   link: 'https://coachteesos.github.io/coachtoby-site/quiz.html' },
  'lead-magnet': { label: '5 Vocal Exercises Guide',  price: 0,      currency: '',    type: 'content',   link: 'https://coachteesos.github.io/coachtoby-site/lead-magnet.html' },
  'group3-5':  { label: 'Group of 3-5',              price: 20000,  currency: 'NGN', type: 'paid-community' },
  'free-call': { label: 'Free Clarity Call',         price: 0,      currency: '',    type: 'call' }
};

const FLUTTERWAVE = {
  single:         'https://flutterwave.com/pay/ictjiqq30sz7',
  monthly:        'https://flutterwave.com/pay/b0hjfvjhv8x4',
  'ngn-single':   'https://flutterwave.com/pay/xnddgkfjeheq',
  'ngn-monthly':  'https://flutterwave.com/pay/wdod0tyeqedw',
  'group3-5':     'https://flutterwave.com/pay/lrgz2vk3xez3',
  'paid-community': 'https://flutterwave.com/pay/lrgz2vk3xez3'
};

/* ═══════════════════════════════════════════════════════════════
   INLINE FORM MODAL
   ═══════════════════════════════════════════════════════════════ */
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
        '<div class="cta-field"><label>First Name *</label><input type="text" id="cta-name" required placeholder="Your first name"></div>',
        '<div class="cta-field"><label>Email *</label><input type="email" id="cta-email" required placeholder="you@example.com"></div>',
        '<div class="cta-field"><label>Phone (with country code) *</label><input type="tel" id="cta-phone" required placeholder="+234 800 000 0000"></div>',
        '<div class="cta-field"><label>Telegram @username *</label><input type="text" id="cta-telegram" required placeholder="@yourusername"></div>',
        '<div class="cta-field"><label>Location (City, Country) *</label><input type="text" id="cta-location" required placeholder="Lagos, Nigeria"></div>',
        '<div class="cta-field" id="cta-budget-field" style="display:none;"><label>Your Budget</label><input type="text" id="cta-budget" placeholder="₦50,000 – ₦500,000"></div>',
        '<div class="cta-field" id="cta-needs-field" style="display:none;"><label>What do you need help with?</label><input type="text" id="cta-needs" placeholder="Riffs and runs, breath control, stage presence..."></div>',
        '<div class="cta-field" id="cta-payment-row" style="display:none;">',
          '<button type="button" id="cta-pay-btn" class="btn-primary" style="width:100%;">💳 Pay Now</button>',
          '<p id="cta-pay-status" style="font-size:0.78rem;color:var(--muted);margin-top:8px;text-align:center;"></p>',
        '</div>',
        '<button type="submit" class="btn-primary" style="width:100%;margin-top:8px;">Continue →</button>',
        '<p style="font-size:0.72rem;color:var(--muted);margin-top:10px;text-align:center;">No spam. We respect your privacy.</p>',
      '</form>',
    '</div>'
  ].join('');

  var s = document.createElement('style');
  s.textContent = [
    '.cta-modal-overlay{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.7);backdrop-filter:blur(8px);z-index:1000;}',
    '.cta-modal-box{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:#fff;border:1px solid #e4e6f0;border-radius:20px;padding:32px 28px;width:90%;max-width:440px;z-index:1001;max-height:90vh;overflow-y:auto;}',
    '.cta-modal-close{position:absolute;top:14px;right:14px;background:none;border:none;color:#6b7094;font-size:1.4rem;cursor:pointer;padding:4px;line-height:1;}',
    '.cta-modal-box h3{font-size:1.2rem;font-weight:800;margin-bottom:6px;color:#0f1120;}',
    '.cta-modal-sub{color:#6b7094;font-size:0.85rem;margin-bottom:20px;}',
    '.cta-field{margin-bottom:14px;}',
    '.cta-field label{display:block;font-size:0.78rem;font-weight:600;color:#2a2d4a;margin-bottom:4px;}',
    '.cta-field input{width:100%;padding:12px 14px;background:#f8f9fc;border:1px solid #e4e6f0;border-radius:10px;color:#0f1120;font-size:0.92rem;font-family:inherit;outline:none;transition:border-color .2s;}',
    '.cta-field input:focus{border-color:#6d28d9;}',
    '.cta-field input::placeholder{color:#9ca3af;}'
  ].join('');

  document.head.appendChild(s);
  document.body.appendChild(d);
  formModal = d;

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

  var isCustom = serviceKey === 'custom-plan';
  var isPaid = svc.price > 0;
  document.getElementById('cta-budget-field').style.display = isCustom ? '' : 'none';
  document.getElementById('cta-needs-field').style.display = isCustom ? '' : 'none';
  document.getElementById('cta-payment-row').style.display = isPaid ? '' : 'none';
  document.getElementById('cta-pay-status').textContent = '';

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

document.addEventListener('keydown', function(e) { if (e.key === 'Escape') closeModal(); });

function submitForm(e) {
  e.preventDefault();
  var serviceKey = currentServiceKey;
  var svc = SERVICES[serviceKey];
  if (!svc) return false;

  var name = document.getElementById('cta-name').value.trim();
  var email = document.getElementById('cta-email').value.trim();
  var phone = document.getElementById('cta-phone').value.trim();
  var telegram = document.getElementById('cta-telegram').value.trim();
  var location = document.getElementById('cta-location') ? document.getElementById('cta-location').value.trim() : '';
  var budget = document.getElementById('cta-budget') ? document.getElementById('cta-budget').value.trim() : '';
  var needs = document.getElementById('cta-needs') ? document.getElementById('cta-needs').value.trim() : '';

  if (!name || !email || !phone || !telegram || !location) {
    alert('Please fill in all required fields.');
    return false;
  }

  if (telegram.indexOf('@') !== 0) telegram = '@' + telegram;

  var fields = {
    'Name': name,
    'Plan': svc.label,
    'Service Key': serviceKey,
    'Status': svc.price > 0 ? 'Awaiting Receipt' : 'Active',
    'Source': 'Website',
    'Total Sessions': svc.price > 0 ? (serviceKey === 'monthly' || serviceKey === 'ngn-monthly' ? 4 : 1) : 0,
    'Sessions Used': 0
  };
  if (budget) fields['Budget'] = budget;
  if (needs) fields['Needs'] = needs;

  var submitBtn = e.target.querySelector('button[type="submit"]');
  submitBtn.textContent = 'Submitting...';
  submitBtn.disabled = true;

  sendToProxy(fields).then(function(written) {
    if (written) console.log('Airtable write OK');
  }).catch(function() {});

  closeModal();

  if (svc.type === 'community') {
    var groupLink = svc.link || '';
    if (groupLink) {
      alert('✅ Welcome, ' + name + '!\n\nYour community link: ' + groupLink + '\n\nJoin now! The bot will also welcome you in Telegram.');
      sendToProxy(fields).catch(function(){});
      window.open(groupLink, '_blank');
      setTimeout(function() {
        var botUrl = 'https://t.me/' + BOT_USERNAME + '?start=' + encodeURIComponent(name + '|' + email + '|' + phone + '|' + location + '|' + serviceKey);
        window.open(botUrl, '_blank');
      }, 1500);
    } else {
      var botUrl = 'https://t.me/' + BOT_USERNAME + '?start=' + encodeURIComponent(name + '|' + email + '|' + phone + '|community|' + serviceKey);
      window.open(botUrl, '_blank');
    }
    return false;
  }

  var botUrl = 'https://t.me/' + BOT_USERNAME + '?start=' + encodeURIComponent(name + '|' + email + '|' + phone + '|' + location + '|' + serviceKey);

  if (svc.price > 0) {
    var fwLink = FLUTTERWAVE[serviceKey];
    if (fwLink) window.open(fwLink, '_blank');
    setTimeout(function() { window.open(botUrl, '_blank'); }, 1500);
    alert('✅ Registered! Complete your payment, then tap "Start" in Telegram.\n\nWelcome, ' + name + ' 🎤');
  } else {
    window.open(botUrl, '_blank');
  }
  return false;
}

/* ═══════════════════════════════════════════════════════════════
   MAIN ROUTER
   ═══════════════════════════════════════════════════════════════ */
function goToBot(serviceKey) { openModal(serviceKey); }

/* ── LEGACY COMPATIBILITY ──*/
function legacyPay(plan) { goToBot(plan); }
function payWithFlutterwaveNGN(amount, planName) {
  if (planName && planName.includes('300')) goToBot('ngn-monthly');
  else goToBot('ngn-single');
}
function payWithFlutterwaveUSD(amount, planName) {
  if (planName && planName.includes('200')) goToBot('monthly');
  else goToBot('single');
}

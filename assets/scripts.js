/* ═══════════════════════════════════════
   COACH TOBY — CORE SCRIPTS
   Every "action" button routes through goToBot(serviceKey)
   so the bot knows EXACTLY what the user picked
   ═══════════════════════════════════════ */

// ── PROGRESS BAR ──
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

// ── SCROLL REVEAL ──
(function() {
  var reveals = document.querySelectorAll('.reveal');
  if (!reveals.length) return;
  var observer = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) entry.target.classList.add('visible');
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
  reveals.forEach(function(el) { observer.observe(el); });
})();

// ── NAV SCROLL EFFECT ──
(function() {
  var nav = document.querySelector('nav');
  if (!nav) return;
  window.addEventListener('scroll', function() {
    nav.classList.toggle('scrolled', window.scrollY > 60);
  }, { passive: true });
})();

// ── COUNTER ANIMATION ──
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

// ── STICKY CTA ──
(function() {
  var sticky = document.querySelector('.sticky-cta');
  var hero = document.querySelector('.hero');
  if (!sticky || !hero) return;
  window.addEventListener('scroll', function() {
    var heroBottom = hero.getBoundingClientRect().bottom;
    sticky.classList.toggle('visible', heroBottom < 0);
  }, { passive: true });
})();

// ── SIDE RAIL ──
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

// ── HAMBURGER TOGGLE ──
function toggleMobileMenu() {
  var links = document.querySelector('nav .nav-links');
  if (links) links.classList.toggle('mobile-open');
}

// ══════════════════════════════════════
// BOT ROUTER — Every button calls this
// ══════════════════════════════════════
const BOT_USERNAME = 'Retpipebot';

const SERVICES = {
  single:      { label: 'Single Session — $50',           price: 50,     currency: 'USD', type: 'coaching' },
  monthly:     { label: 'Monthly Package — $200',          price: 200,    currency: 'USD', type: 'coaching' },
  'ngn-single':{ label: 'Single Session — ₦70,000',       price: 70000,  currency: 'NGN', type: 'coaching' },
  'ngn-monthly':{ label: 'Monthly Package — ₦300,000',    price: 300000, currency: 'NGN', type: 'coaching' },
  'free-community': { label: "Free Singers' Community",    price: 0,      currency: '',    type: 'community', link: 'https://t.me/+LGYumO9JZOc1M2M0' },
  'paid-community': { label: "Paid Singers' Community — ₦2,000/mo", price: 2000, currency: 'NGN', type: 'community', link: 'https://t.me/+SMnit5TdCuBlOWE0' },
  'abuja-collective': { label: 'Abuja Music Collective',   price: 0,      currency: '',    type: 'community', link: 'https://t.me/+qv5hIOIBKgtmNjhk' },
  quiz:        { label: 'Which Singer Are You? Quiz',      price: 0,      currency: '',    type: 'content',   link: 'https://coachteesos.github.io/coachtoby-site/quiz.html' },
  'lead-magnet': { label: '5 Vocal Exercises Guide',       price: 0,      currency: '',    type: 'content',   link: 'https://coachteesos.github.io/coachtoby-site/lead-magnet.html' },
  'free-call': { label: 'Free Consultation Call',          price: 0,      currency: '',    type: 'call',      link: 'https://calendly.com/d/cx3t-9f8-b7r' },
};

// ── MAIN ROUTER FUNCTION ──
function goToBot(serviceKey) {
  var svc = SERVICES[serviceKey];
  if (!svc) { alert('Something went wrong. Please try again.'); return; }

  var name = prompt('Enter your first name:');
  if (!name || !name.trim()) return;
  name = name.trim();

  // For paid coaching: collect email + open payment
  if (svc.type === 'coaching' && svc.price > 0) {
    var email = prompt('Enter your email:');
    if (!email || !email.trim()) return;
    email = email.trim();

    // Log to Airtable via formsubmit
    var data = new URLSearchParams();
    data.append('Name', name);
    data.append('Email', email);
    data.append('Plan', svc.label);
    data.append('Amount', svc.price);
    data.append('Currency', svc.currency);
    data.append('Status', 'Pending Confirmation');
    data.append('Source', 'Website');
    data.append('_subject', 'New Booking: ' + name + ' — ' + svc.label);
    fetch('https://formsubmit.co/prosperolumotobi@gmail.com', {
      method: 'POST', body: data,
      headers: {'Content-Type': 'application/x-www-form-urlencoded'}
    }).catch(function(){});

    // Open payment
    if (svc.currency === 'USD') {
      var raenestLinks = { single: 'RNM3A232T', monthly: 'RNM56B3LH' };
      var key = serviceKey === 'single' ? 'single' : 'monthly';
      window.open('https://app.raenest.com/invoice/payment/' + raenestLinks[key], '_blank');
    } else {
      // Naira — show bank details
      alert('Pay ₦' + svc.price.toLocaleString() + ' to:\n\nBank: First Bank PLC\nAccount: 3110071863\nName: PROSPER TOBI OLUMO\n\nAfter payment, tap OK to continue to Telegram.');
    }

    // Redirect to bot with service key
    setTimeout(function() {
      window.open('https://t.me/' + BOT_USERNAME + '?start=' + encodeURIComponent(name + '|' + serviceKey), '_blank');
    }, 2000);

    alert("Complete your payment, then tap 'Start' in Telegram. Welcome, " + name + "! 🎤");
    return;
  }

  // For free/community/content/call: redirect to bot directly
  window.open('https://t.me/' + BOT_USERNAME + '?start=' + encodeURIComponent(name + '|' + serviceKey), '_blank');
}

// ── LEGACY COMPATIBILITY (for any old onclick still in HTML) ──
function raenestPay(plan) { goToBot(plan); }
function payWithFlutterwaveNGN(amount, planName) {
  // Map old calls to service keys
  if (planName && planName.includes('300')) goToBot('ngn-monthly');
  else goToBot('ngn-single');
}
function payWithFlutterwaveUSD(amount, planName) {
  if (planName && planName.includes('200')) goToBot('monthly');
  else goToBot('single');
}

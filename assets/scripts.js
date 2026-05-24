/* ═══════════════════════════════════════
   COACH TOBY — CORE SCRIPTS
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
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
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

// ── STICKY CTA (appears after hero) ──
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
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') closeRail();
});

// ── HAMBURGER TOGGLE ──
function toggleMobileMenu() {
  var links = document.querySelector('nav .nav-links');
  if (links) links.classList.toggle('mobile-open');
}

// ── FLUTTERWAVE PAYMENT ──
function payWithFlutterwaveNGN(amount, planName) {
  var publicKey = 'FLWPUBK_TEST-xxxxxxxxxxxxx'; // Replace with live key when ready
  getpaidSetup({
    PBFPubKey: publicKey,
    customer_email: '',
    customer_firstname: '',
    amount: amount,
    currency: 'NGN',
    txref: 'Toby-' + Date.now(),
    meta: [{ metaname: 'plan', metavalue: planName }],
    onclose: function() {},
    callback: function(response) {
      if (response.tx.chargeResponseCode === '00') {
        // Redirect to WhatsApp to confirm
        var waMsg = encodeURIComponent('Hi Toby! I just paid for the ' + planName + ' plan. Here\'s my receipt: ' + response.tx.txRef);
        window.open('https://wa.me/2349160106084?text=' + waMsg, '_blank');
      }
    }
  });
}

function payWithFlutterwaveUSD(amount, planName) {
  var publicKey = 'FLWPUBK_TEST-xxxxxxxxxxxxx'; // Replace with live key
  getpaidSetup({
    PBFPubKey: publicKey,
    customer_email: '',
    customer_firstname: '',
    amount: amount,
    currency: 'USD',
    txref: 'Toby-' + Date.now(),
    meta: [{ metaname: 'plan', metavalue: planName }],
    onclose: function() {},
    callback: function(response) {
      if (response.tx.chargeResponseCode === '00') {
        var waMsg = encodeURIComponent('Hi Toby! I just paid for the ' + planName + ' plan. Here\'s my receipt: ' + response.tx.txRef);
        window.open('https://wa.me/2349160106084?text=' + waMsg, '_blank');
      }
    }
  });
}

/* ═══════════════════════════════════════════════════════════════
   GEOLOCATION IP ENGINE — Pricing.js
   Uses ipapi.co (free, no key, 45 req/min)
   NG → ₦ NGN pricing | Other → $ USD pricing
   ═══════════════════════════════════════════════════════════════ */

var USER_COUNTRY = null;
var USER_CURRENCY = 'USD';
var USER_SYMBOL = '$';
var USER_IS_NIGERIA = false;

function detectCurrency() {
  // Check localStorage cache first (valid 24h)
  try {
    var cached = localStorage.getItem('ct_geo');
    if (cached) {
      var d = JSON.parse(cached);
      if (d && d.ts && (Date.now() - d.ts) < 86400000) {
        setCurrency(d.country, d.currency, d.symbol, d.isNG);
        return;
      }
    }
  } catch(e) {}

  // Fetch from ipapi.co
  fetch('https://ipapi.co/json/')
    .then(function(r) { return r.json(); })
    .then(function(d) {
      var country = d.country_code || '';
      var isNG = country === 'NG';
      var currency = isNG ? 'NGN' : 'USD';
      var symbol = isNG ? '₦' : '$';
      try { localStorage.setItem('ct_geo', JSON.stringify({ country: country, currency: currency, symbol: symbol, isNG: isNG, ts: Date.now() })); } catch(e) {}
      setCurrency(country, currency, symbol, isNG);
    })
    .catch(function() {
      // Fallback: ip-api.com
      fetch('https://ip-api.com/json/')
        .then(function(r) { return r.json(); })
        .then(function(d) {
          var country = d.countryCode || '';
          var isNG = country === 'NG';
          setCurrency(country, isNG ? 'NGN' : 'USD', isNG ? '₦' : '$', isNG);
        })
        .catch(function() { setCurrency('US', 'USD', '$', false); });
    });
}

function setCurrency(country, currency, symbol, isNG) {
  USER_COUNTRY = country;
  USER_CURRENCY = currency;
  USER_SYMBOL = symbol;
  USER_IS_NIGERIA = isNG;

  // Update price elements
  document.querySelectorAll('[data-price-usd]').forEach(function(el) {
    var usd = el.getAttribute('data-price-usd');
    var ngn = el.getAttribute('data-price-ngn');
    if (isNG && ngn) el.textContent = '₦' + parseInt(ngn).toLocaleString();
    else if (usd) el.textContent = '$' + parseInt(usd).toLocaleString();
  });

  // Update currency labels
  document.querySelectorAll('[data-currency-label]').forEach(function(el) {
    el.textContent = isNG ? 'NGN' : 'USD';
  });

  // Show/hide region-specific elements
  document.querySelectorAll('[data-ng-only]').forEach(function(el) { el.style.display = isNG ? '' : 'none'; });
  document.querySelectorAll('[data-intl-only]').forEach(function(el) { el.style.display = isNG ? 'none' : ''; });

  // Update budget placeholder
  var budgetInput = document.getElementById('cta-budget');
  if (budgetInput) budgetInput.placeholder = isNG ? '₦10,000 – ₦500,000' : '$20 – $500';

  // Update data-currency on pay buttons
  document.querySelectorAll('[data-currency]').forEach(function(el) {
    el.setAttribute('data-currency', isNG ? 'NGN' : 'USD');
  });

  document.dispatchEvent(new CustomEvent('currencyDetected', { detail: { country: country, currency: currency, symbol: symbol, isNG: isNG } }));
}

// Run on load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', detectCurrency);
} else {
  detectCurrency();
}

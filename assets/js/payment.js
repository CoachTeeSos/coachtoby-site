/* ═══════════════════════════════════════════════════════════════
   FLUTTERWAVE PAYMENT EXTENSION — Payment.js
   Reads data-amount + data-currency from clicked element.
   On success → deep-link to Telegram bot.
   ═══════════════════════════════════════════════════════════════ */

var BOT_USERNAME = 'Retpipebot';

function initFlutterwavePay(btn) {
  if (!btn) return;
  btn.addEventListener('click', function(e) {
    e.preventDefault();
    var amount = btn.getAttribute('data-amount') || '';
    var currency = btn.getAttribute('data-currency') || 'USD';
    var email = btn.getAttribute('data-email') || '';
    var name = btn.getAttribute('data-name') || '';
    var ref = 'CT-' + Date.now() + '-' + Math.random().toString(36).substr(2, 6).toUpperCase();

    if (typeof FlutterwaveCheckout === 'undefined') {
      // Fallback: redirect to Flutterwave payment link if inline FW not loaded
      var fwLinks = {
        'single': 'https://flutterwave.com/pay/ictjiqq30sz7',
        'monthly': 'https://flutterwave.com/pay/b0hjfvjhv8x4',
        'ngn-single': 'https://flutterwave.com/pay/xnddgkfjeheq',
        'ngn-monthly': 'https://flutterwave.com/pay/wdod0tyeqedw',
        'group3-5': 'https://flutterwave.com/pay/lrgz2vk3xez3',
        'paid-community': 'https://flutterwave.com/pay/lrgz2vk3xez3'
      };
      var serviceKey = btn.getAttribute('data-service') || '';
      if (fwLinks[serviceKey]) {
        window.open(fwLinks[serviceKey], '_blank');
      } else {
        alert('Payment system loading. Please try again in a moment.');
      }
      return;
    }

    FlutterwaveCheckout({
      public_key: btn.getAttribute('data-pw-key') || '',
      tx_ref: ref,
      amount: parseFloat(amount),
      currency: currency,
      payment_options: 'card,banktransfer,ussd',
      customer: { email: email, name: name },
      callback: function(data) {
        if (data.status === 'successful' || data.status === 'completed') {
          // Redirect to Telegram bot on success
          window.location.href = 'https://t.me/' + BOT_USERNAME + '?start=payment_' + ref;
        }
      },
      onclose: function() {},
      customizations: {
        title: 'Sessions with Toby',
        description: btn.getAttribute('data-desc') || 'Vocal Coaching Payment',
        logo: ''
      }
    });
  });
}

// Auto-init all pay buttons on page load
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('[data-amount][data-currency]').forEach(function(btn) {
    initFlutterwavePay(btn);
  });
});

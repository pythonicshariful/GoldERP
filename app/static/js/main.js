/* ═══════════════════════════════════════════════════════════════
   Gold Seller Management System — Main JavaScript
   ═══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

  // ── Auto-dismiss flash alerts after 5 seconds ────────────────
  setTimeout(function () {
    document.querySelectorAll('.flash-container .alert').forEach(function (el) {
      el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      el.style.opacity = '0';
      el.style.transform = 'translateX(120%)';
      setTimeout(() => el.remove(), 500);
    });
  }, 5000);

  // ── Set today's date as default for all date inputs ──────────
  const today = new Date().toISOString().split('T')[0];
  document.querySelectorAll('input[type="date"]').forEach(function (el) {
    if (!el.value) el.value = today;
  });

  // ── Format number inputs with commas (display only) ──────────
  document.querySelectorAll('input[data-type="currency"]').forEach(function (el) {
    el.addEventListener('input', function () {
      const raw = this.value.replace(/[^0-9.]/g, '');
      this.value = raw;
    });
  });

  // ── Confirm delete dialogs ────────────────────────────────────
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      const msg = this.getAttribute('data-confirm') || 'Are you sure? This action cannot be undone.';
      if (!confirm(msg)) {
        e.preventDefault();
        return false;
      }
    });
  });

  // ── Auto-calculate totals in sale/purchase forms ─────────────
  function calcTotal() {
    const qty = parseFloat(document.getElementById('quantity')?.value || 0);
    const rate = parseFloat(document.getElementById('rate_per_unit')?.value || 0);
    const making = parseFloat(document.getElementById('making_charge')?.value || 0);
    const total = (qty * rate) + making;
    const totalEl = document.getElementById('total_amount');
    if (totalEl) {
      totalEl.value = total.toFixed(2);
    }
    // Update balance due
    const paid = parseFloat(document.getElementById('paid_amount')?.value || 0);
    const balanceEl = document.getElementById('balance_due');
    if (balanceEl) {
      balanceEl.value = Math.max(0, total - paid).toFixed(2);
    }
  }

  ['quantity', 'rate_per_unit', 'making_charge', 'paid_amount'].forEach(function (id) {
    const el = document.getElementById(id);
    if (el) el.addEventListener('input', calcTotal);
  });

  // ── Mortgage auto-calculate interest ─────────────────────────
  function calcInterest() {
    const loan = parseFloat(document.getElementById('loan_amount')?.value || 0);
    const rate = parseFloat(document.getElementById('interest_rate')?.value || 0);
    const monthly = (loan * rate / 100).toFixed(2);
    const interestEl = document.getElementById('monthly_interest_display');
    if (interestEl) {
      interestEl.textContent = '৳ ' + parseFloat(monthly).toLocaleString('en-IN', { minimumFractionDigits: 2 });
    }
  }

  ['loan_amount', 'interest_rate'].forEach(function (id) {
    const el = document.getElementById(id);
    if (el) el.addEventListener('input', calcInterest);
  });

  // ── Navbar active link highlight ─────────────────────────────
  const path = window.location.pathname.split('/')[1];
  document.querySelectorAll('.navbar-nav .nav-link').forEach(function (link) {
    const href = link.getAttribute('href') || '';
    if (href.startsWith('/' + path) && path !== '') {
      link.classList.add('active');
    }
  });

  // ── Number formatter for display spans ───────────────────────
  document.querySelectorAll('[data-format="number"]').forEach(function (el) {
    const val = parseFloat(el.textContent.replace(/[^0-9.]/g, ''));
    if (!isNaN(val)) {
      el.textContent = '৳ ' + val.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
  });

  // ── Tooltip initialization ────────────────────────────────────
  if (typeof bootstrap !== 'undefined') {
    const tooltipEls = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipEls.forEach(el => new bootstrap.Tooltip(el));
  }

  // ── Form validation styling ───────────────────────────────────
  const forms = document.querySelectorAll('.needs-validation');
  forms.forEach(function (form) {
    form.addEventListener('submit', function (event) {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add('was-validated');
    }, false);
  });

  // ── Smooth number animation for KPI cards ────────────────────
  function animateNumber(el, target, duration) {
    const start = 0;
    const startTime = performance.now();
    const isFloat = target % 1 !== 0;

    function update(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = start + (target - start) * eased;
      el.textContent = isFloat
        ? '৳ ' + current.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
        : current.toLocaleString('en-IN', { maximumFractionDigits: 0 });
      if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
  }

  document.querySelectorAll('.kpi-animate').forEach(function (el) {
    const target = parseFloat(el.getAttribute('data-value') || 0);
    animateNumber(el, target, 1200);
  });

});

// ── Chart.js Dashboard Helper ─────────────────────────────────────────────
function initSalesChart(labels, data) {
  const ctx = document.getElementById('salesChart');
  if (!ctx) return;

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Sales (৳)',
        data: data,
        backgroundColor: function (context) {
          const chart = context.chart;
          const { ctx: c, chartArea } = chart;
          if (!chartArea) return '#B8860B';
          const gradient = c.createLinearGradient(0, chartArea.bottom, 0, chartArea.top);
          gradient.addColorStop(0, 'rgba(184,134,11,0.4)');
          gradient.addColorStop(1, 'rgba(184,134,11,0.9)');
          return gradient;
        },
        borderColor: '#B8860B',
        borderWidth: 2,
        borderRadius: 8,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1F3864',
          titleColor: '#D4A017',
          bodyColor: '#fff',
          borderColor: '#B8860B',
          borderWidth: 1,
          callbacks: {
            label: ctx => '৳ ' + ctx.raw.toLocaleString('en-IN', { minimumFractionDigits: 2 })
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(31,56,100,0.08)' },
          ticks: {
            callback: v => '৳' + (v >= 1000 ? (v/1000).toFixed(0) + 'K' : v),
            color: '#6c757d',
            font: { size: 11 }
          }
        },
        x: {
          grid: { display: false },
          ticks: { color: '#6c757d', font: { size: 11 } }
        }
      }
    }
  });
}

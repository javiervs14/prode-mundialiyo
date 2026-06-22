/* ============================================================
   PRODE MUNDIALIYO 2026 — Animations & Interactions
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {
  // ── Loading Screen ──────────────────────────────────────
  const loadingScreen = document.getElementById('loading-screen');
  const loadingBar = document.getElementById('loading-bar');

  if (loadingScreen && loadingBar) {
    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 30 + 10;
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
        setTimeout(() => {
          loadingScreen.classList.add('hidden');
          document.body.style.overflow = '';
        }, 400);
      }
      loadingBar.style.width = progress + '%';
    }, 200);
    document.body.style.overflow = 'hidden';
  }

  // ── Navbar scroll effect ───────────────────────────────
  const navbar = document.querySelector('.navbar');
  if (navbar) {
    window.addEventListener('scroll', () => {
      navbar.classList.toggle('scrolled', window.scrollY > 20);
    }, { passive: true });
  }

  // ── Mobile menu toggle ─────────────────────────────────
  const mobileToggle = document.querySelector('.mobile-toggle');
  const navLinks = document.querySelector('.nav-links');
  if (mobileToggle && navLinks) {
    mobileToggle.addEventListener('click', () => {
      navLinks.classList.toggle('open');
      const icon = mobileToggle.querySelector('i');
      if (icon) {
        icon.classList.toggle('bi-list');
        icon.classList.toggle('bi-x-lg');
      }
    });

    navLinks.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        navLinks.classList.remove('open');
      });
    });
  }

  // ── Phase tabs ─────────────────────────────────────────
  document.querySelectorAll('.phase-tab').forEach(tab => {
    tab.addEventListener('click', function () {
      const target = this.dataset.phase;
      document.querySelectorAll('.phase-tab').forEach(t => t.classList.remove('active'));
      this.classList.add('active');
      document.querySelectorAll('.match-group').forEach(group => {
        if (target === 'all' || group.dataset.phase === target) {
          group.style.display = '';
          group.style.animation = 'fadeInUp 0.4s ease forwards';
        } else {
          group.style.display = 'none';
        }
      });
    });
  });

  // ── Prediction counter ─────────────────────────────────
  const predictionInputs = document.querySelectorAll('.prediction-input');
  const counterEl = document.querySelector('.predictions-counter span');
  const totalMatches = document.querySelectorAll('.match-card').length;

  function updateCounter() {
    const filled = document.querySelectorAll('.prediction-input.filled').length / 2;
    if (counterEl) {
      counterEl.textContent = Math.round(filled) + ' / ' + totalMatches;
    }
    const saveBtn = document.querySelector('.save-predictions-bar .btn-primary');
    if (saveBtn) {
      const allFilled = Math.round(filled) === totalMatches && totalMatches > 0;
      saveBtn.disabled = !allFilled;
      saveBtn.style.opacity = allFilled ? '1' : '0.5';
    }
  }

  predictionInputs.forEach(input => {
    input.addEventListener('input', function () {
      this.value = this.value.replace(/[^0-9]/g, '').slice(0, 2);
      this.classList.toggle('filled', this.value.length > 0);
      updateCounter();
    });

    input.addEventListener('keydown', function (e) {
      if (e.key >= '0' && e.key <= '9' && this.value.length >= 2) {
        e.preventDefault();
        const next = this.closest('.prediction-row').querySelectorAll('.prediction-input');
        const idx = Array.from(next).indexOf(this);
        if (idx < next.length - 1) next[idx + 1].focus();
      }
    });
  });

  // ── Match card animation on scroll ─────────────────────
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -40px 0px'
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.animationDelay = (entry.target.dataset.delay || '0') + 's';
        entry.target.style.opacity = '1';
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  document.querySelectorAll('.match-group, .match-card').forEach((el, i) => {
    if (!el.dataset.delay) el.dataset.delay = (i * 0.08).toFixed(2);
    observer.observe(el);
  });

  // ── Dismiss flash messages ─────────────────────────────
  document.querySelectorAll('.alert .btn-close').forEach(btn => {
    btn.addEventListener('click', function () {
      this.closest('.alert').style.animation = 'fadeIn 0.3s ease reverse forwards';
      setTimeout(() => this.closest('.alert').remove(), 300);
    });
  });

  // ── Auto-dismiss flash after 5s ────────────────────────
  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      if (alert.parentNode) {
        alert.style.animation = 'fadeIn 0.3s ease reverse forwards';
        setTimeout(() => alert.remove(), 300);
      }
    }, 5000);
  });

  // ── Confetti on exact prediction (bonus) ───────────────
  window.triggerConfetti = function () {
    const canvas = document.createElement('canvas');
    canvas.style.cssText = 'position:fixed;inset:0;z-index:9999;pointer-events:none;';
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    document.body.appendChild(canvas);
    const ctx = canvas.getContext('2d');
    const colors = ['#E4007C', '#7B2FF7', '#A6FF00', '#FFD700', '#0047BB', '#75AADB'];
    const particles = Array.from({ length: 80 }, () => ({
      x: Math.random() * canvas.width,
      y: -20 - Math.random() * 100,
      w: 6 + Math.random() * 6,
      h: 4 + Math.random() * 4,
      color: colors[Math.floor(Math.random() * colors.length)],
      vx: (Math.random() - 0.5) * 3,
      vy: 2 + Math.random() * 4,
      rotation: Math.random() * 360,
      rotationSpeed: (Math.random() - 0.5) * 10
    }));
    let frame = 0;
    function animate() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      let active = false;
      particles.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.08;
        p.rotation += p.rotationSpeed;
        if (p.y < canvas.height + 20) active = true;
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.rotation * Math.PI / 180);
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
        ctx.restore();
      });
      frame++;
      if (active && frame < 180) requestAnimationFrame(animate);
      else canvas.remove();
    }
    animate();
  };

  // ── Service Worker ─────────────────────────────────────
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/service-worker.js').catch(() => {});
  }
});

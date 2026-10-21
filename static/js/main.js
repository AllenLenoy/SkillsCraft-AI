/**
 * CraftConnect - Vanilla JavaScript
 * INT253 CA3 Project — Full Interactivity Module
 */

document.addEventListener('DOMContentLoaded', () => {
  // ═══════════════════════════════════════════════════════════
  // Mobile Navigation Toggle
  // ═══════════════════════════════════════════════════════════
  const mobileMenuBtn = document.getElementById('mobileMenuBtn');
  const mobileMenu = document.getElementById('mobileMenu');
  if (mobileMenuBtn && mobileMenu) {
    mobileMenuBtn.addEventListener('click', () => {
      const isOpen = !mobileMenu.classList.contains('hidden');
      mobileMenu.classList.toggle('hidden');
      const icon = mobileMenuBtn.querySelector('.material-symbols-outlined');
      if (icon) icon.textContent = isOpen ? 'menu' : 'close';
    });
  }

  // ═══════════════════════════════════════════════════════════
  // Auto-dismiss alert notifications after 5 seconds
  // ═══════════════════════════════════════════════════════════
  const alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-8px)';
      setTimeout(() => alert.remove(), 500);
    }, 5000);
  });

  // ═══════════════════════════════════════════════════════════
  // Semantic Chip Quick-Fill (Hero Discovery Bar)
  // ═══════════════════════════════════════════════════════════
  document.querySelectorAll('[data-search-chip]').forEach(chip => {
    chip.addEventListener('click', () => {
      const searchInput = document.querySelector('input[name="q"]');
      if (searchInput) {
        searchInput.value = chip.textContent.trim();
        searchInput.focus();
        // Subtle pulse feedback
        chip.style.transform = 'scale(0.95)';
        setTimeout(() => chip.style.transform = '', 150);
      }
    });
  });

  // ═══════════════════════════════════════════════════════════
  // Wishlist Heart Toggle (AJAX-like visual toggle)
  // ═══════════════════════════════════════════════════════════
  document.querySelectorAll('[data-wishlist-toggle]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const icon = btn.querySelector('.material-symbols-outlined');
      if (icon) {
        const isFilled = icon.style.fontVariationSettings.includes("'FILL' 1");
        icon.style.fontVariationSettings = isFilled
          ? "'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24"
          : "'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24";
        // Add bounce
        btn.style.transform = 'scale(1.2)';
        setTimeout(() => btn.style.transform = '', 200);
      }
    });
  });

  // ═══════════════════════════════════════════════════════════
  // Scroll-based Card Entrance Animation
  // ═══════════════════════════════════════════════════════════
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -40px 0px'
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-fade-in-up');
        entry.target.style.opacity = '1';
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  document.querySelectorAll('[data-animate]').forEach(el => {
    el.style.opacity = '0';
    observer.observe(el);
  });

  // ═══════════════════════════════════════════════════════════
  // Password Visibility Toggle (Auth Pages)
  // ═══════════════════════════════════════════════════════════
  document.querySelectorAll('[data-toggle-password]').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.dataset.togglePassword;
      const input = document.getElementById(targetId);
      const icon = btn.querySelector('.material-symbols-outlined');
      if (input && icon) {
        if (input.type === 'password') {
          input.type = 'text';
          icon.textContent = 'visibility_off';
        } else {
          input.type = 'password';
          icon.textContent = 'visibility';
        }
      }
    });
  });

  // ═══════════════════════════════════════════════════════════
  // Auth Tab Switching
  // ═══════════════════════════════════════════════════════════
  const loginTab = document.getElementById('tab-login');
  const signupTab = document.getElementById('tab-signup');
  const loginPanel = document.getElementById('login-panel');
  const signupPanel = document.getElementById('signup-panel');

  if (loginTab && signupTab && loginPanel && signupPanel) {
    loginTab.addEventListener('click', () => {
      loginTab.classList.add('active');
      signupTab.classList.remove('active');
      loginPanel.classList.remove('hidden');
      signupPanel.classList.add('hidden');
    });

    signupTab.addEventListener('click', () => {
      signupTab.classList.add('active');
      loginTab.classList.remove('active');
      signupPanel.classList.remove('hidden');
      loginPanel.classList.add('hidden');
    });
  }

  // ═══════════════════════════════════════════════════════════
  // Role Selector (Auth Pages)
  // ═══════════════════════════════════════════════════════════
  document.querySelectorAll('[data-role-select]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-role-select]').forEach(b => {
        b.classList.remove('border-primary', 'bg-surface-container-low', 'text-primary');
        b.classList.add('border-outline-variant', 'bg-surface-container-lowest', 'text-on-surface-variant');
      });
      btn.classList.remove('border-outline-variant', 'bg-surface-container-lowest', 'text-on-surface-variant');
      btn.classList.add('border-primary', 'bg-surface-container-low', 'text-primary');

      // Update hidden role field
      const roleInput = document.getElementById('id_role');
      if (roleInput) {
        roleInput.value = btn.dataset.roleSelect;
      }

      // Toggle artisan-only fields
      const artisanFields = document.getElementById('artisan-signup-fields');
      if (artisanFields) {
        artisanFields.style.display = btn.dataset.roleSelect === 'artisan' ? 'block' : 'none';
      }
    });
  });

  // ═══════════════════════════════════════════════════════════
  // Price Range Slider (Category/Catalogue Filter)
  // ═══════════════════════════════════════════════════════════
  const priceRange = document.getElementById('priceRangeSlider');
  const priceDisplay = document.getElementById('priceRangeDisplay');
  if (priceRange && priceDisplay) {
    priceRange.addEventListener('input', () => {
      priceDisplay.textContent = `₹${parseInt(priceRange.value).toLocaleString('en-IN')}`;
    });
  }

  // ═══════════════════════════════════════════════════════════
  // Smooth scroll for anchor links
  // ═══════════════════════════════════════════════════════════
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      const target = document.querySelector(targetId);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // ═══════════════════════════════════════════════════════════
  // Header scroll shadow
  // ═══════════════════════════════════════════════════════════
  const header = document.querySelector('header');
  if (header) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 10) {
        header.classList.add('shadow-md');
      } else {
        header.classList.remove('shadow-md');
      }
    }, { passive: true });
  }
});

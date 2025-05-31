function showSliders(sliderId, valueDisplayId, bulbIconId) {
  const slider = document.getElementById(sliderId);
  const valueDisplay = document.getElementById(valueDisplayId);
  const bulbIcon = document.getElementById(bulbIconId);
  const bulbSvg = bulbIcon?.querySelector('svg');

  if (!slider || !valueDisplay || !bulbIcon || !bulbSvg) {
    console.error(`Slider elements not found: ${sliderId}, ${valueDisplayId}, ${bulbIconId}`);
    return;
  }

  function updateSliderVisuals(value) {
    valueDisplay.textContent = `${value}%`;

    const percentage = value;
    slider.style.background = `linear-gradient(to right, var(--main-color) 0%, var(--main-color) ${percentage}%, #e0e0e0 ${percentage}%, #e0e0e0 100%)`;

    if (value > 0) {
      bulbSvg.style.fill = '#4A90E2';
      bulbSvg.style.opacity = '1';
    } else {
      bulbSvg.style.fill = '#7B7B7B';
      bulbSvg.style.opacity = '0.5';
    }
  }

  // Handle input changes - simplified approach
  slider.addEventListener('input', function() {
    const value = parseInt(this.value, 10);
    updateSliderVisuals(value);
  });

  // Add visual feedback for active state
  slider.addEventListener('mousedown', function() {
    this.classList.add('active');
  });

  slider.addEventListener('mouseup', function() {
    this.classList.remove('active');
  });

  slider.addEventListener('touchstart', function() {
    this.classList.add('active');
  });

  slider.addEventListener('touchend', function() {
    this.classList.remove('active');
  });

  // Initialize slider visuals
  const initialValue = parseInt(slider.value, 10);
  updateSliderVisuals(initialValue);
}

function showDropdown() {
  const hamburger = document.querySelector('.c-hamburger');
  const navPopup = document.querySelector('.c-nav-popup');
  const overlay = document.querySelector('.c-overlay');
  const closeIcon = document.querySelector('.c-nav-popup__close');

  if (!hamburger || !navPopup || !overlay || !closeIcon) {
    console.error('Dropdown elements not found');
    return;
  }

  function toggleMenu() {
    const isActive = navPopup.classList.toggle('c-nav-popup--active');
    overlay.classList.toggle('c-overlay--active');
    hamburger.setAttribute('aria-expanded', isActive);
    navPopup.setAttribute('aria-hidden', !isActive);
    overlay.setAttribute('aria-hidden', !isActive);
  }

  if (window.matchMedia('(max-width: 767px)').matches) {
    hamburger.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleMenu();
    });

    closeIcon.addEventListener('click', (e) => {
      e.stopPropagation();
      navPopup.classList.remove('c-nav-popup--active');
      overlay.classList.remove('c-overlay--active');
      hamburger.setAttribute('aria-expanded', 'false');
      navPopup.setAttribute('aria-hidden', 'true');
      overlay.setAttribute('aria-hidden', 'true');
    });

    overlay.addEventListener('click', () => {
      navPopup.classList.remove('c-nav-popup--active');
      overlay.classList.remove('c-overlay--active');
      hamburger.setAttribute('aria-expanded', 'false');
      navPopup.setAttribute('aria-hidden', 'true');
      overlay.setAttribute('aria-hidden', 'true');
    });

    const navLinks = document.querySelectorAll('.c-nav-popup__link');
    navLinks.forEach((link) => {
      link.addEventListener('click', () => {
        navPopup.classList.remove('c-nav-popup--active');
        overlay.classList.remove('c-overlay--active');
        hamburger.setAttribute('aria-expanded', 'false');
        navPopup.setAttribute('aria-hidden', 'true');
        overlay.setAttribute('aria-hidden', 'true');
      });
    });

    document.addEventListener('click', (e) => {
      if (!navPopup.contains(e.target) && !hamburger.contains(e.target)) {
        navPopup.classList.remove('c-nav-popup--active');
        overlay.classList.remove('c-overlay--active');
        hamburger.setAttribute('aria-expanded', 'false');
        navPopup.setAttribute('aria-hidden', 'true');
        overlay.setAttribute('aria-hidden', 'true');
      }
    });
  }

  window.addEventListener('resize', () => {
    if (window.matchMedia('(min-width: 768px)').matches) {
      navPopup.classList.remove('c-nav-popup--active');
      overlay.classList.remove('c-overlay--active');
      hamburger.setAttribute('aria-expanded', 'false');
      navPopup.setAttribute('aria-hidden', 'true');
      overlay.setAttribute('aria-hidden', 'true');
    }
  });
}

const init = () => {
  console.info('DOM loaded');
  showSliders('lightSliderLower', 'valueDisplayLower', 'bulbIconLower');
  showSliders('lightSliderUpper', 'valueDisplayUpper', 'bulbIconUpper');
  showDropdown();
};

document.addEventListener('DOMContentLoaded', init);
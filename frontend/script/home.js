'use strict';
const lanIP = `http://192.168.168.169:8000`;
const socketio = io(lanIP);
const ENDPOINT = 'http://192.168.168.169:8000/api/v1';

// #region ***  DOM references                           ***********
// #endregion

// #region ***  Callback-Visualisation - showVisuals         ***********

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

function showSliders(sliderId, valueDisplayId, bulbIconId) {
  const slider = document.getElementById(sliderId);
  const valueDisplay = document.getElementById(valueDisplayId);
  const bulbIcon = document.getElementById(bulbIconId);
  const bulbSvg = bulbIcon?.querySelector('svg');

  if (!slider || !valueDisplay || !bulbIcon || !bulbSvg) {
    console.error(`Slider elements not found: ${sliderId}, ${valueDisplayId}, ${bulbIconId}`);
    return;
  }

  slider.removeAttribute('title');
  valueDisplay.removeAttribute('title');
  bulbIcon.removeAttribute('title');

  function updateSliderVisuals(value) {
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

  slider.addEventListener('input', function () {
    const value = parseInt(this.value, 10);
    updateSliderVisuals(value);
  });

  slider.addEventListener('mousedown', function () {
    this.classList.add('active');
  });

  slider.addEventListener('mouseup', function () {
    this.classList.remove('active');
  });

  slider.addEventListener('touchstart', function () {
    this.classList.add('active');
  });

  slider.addEventListener('touchend', function () {
    this.classList.remove('active');
  });

  const initialValue = parseInt(slider.value, 10);
  updateSliderVisuals(initialValue);
}

// #endregion

// #region ***  Callback-Visualisation - showData         ***********
const showBatteryIn = (json) => {
  let batteryInTotal = 0;
  for (const log of json) {
    const batteryIn = parseFloat(log.value);
    batteryInTotal += batteryIn;
  }
  const solarDisplay = document.querySelector('.js-solar_value');
  solarDisplay.innerHTML = batteryInTotal + ' Watt';
};

const showEnergyToday = (json) => {
  let energyTodayTotal = 0;
  for (const log of json) {
    const energyToday = parseFloat(log.value);
    energyTodayTotal += energyToday;
  }
  const energyTodayDisplay = document.querySelector('.js-energy_today_value');
  energyTodayDisplay.innerHTML = energyTodayTotal + ' Watt';
};

const showEnergyWeek = (json) => {
  let energyWeekTotal = 0;
  for (const log of json) {
    const energyWeek = parseFloat(log.value);
    energyWeekTotal += energyWeek;
  }
  const energyWeekDisplay = document.querySelector('.js-energy_week_value');
  energyWeekDisplay.innerHTML = energyWeekTotal + ' Watt';
};

const showTemperature = (json) => {
  const temperatureDisplay = document.querySelector('.js-temperature_value');
  const temperature = parseFloat(json.value);
  if (!isNaN(temperature)) {
    temperatureDisplay.innerHTML = temperature.toFixed(1);
  } else {
    console.error('Invalid temperature value:', json.value);
    temperatureDisplay.innerHTML = 'N/A';
  }
};

const showTemperatureSchedule = (json, json2) => {
  const scheduleEnabled = json.enabled;
  const scheduleEnabled2 = json2.enabled;
  const scheduleDisplay = document.querySelector('.js-temperature_schedule');
  if (scheduleEnabled === scheduleEnabled2) {
    if (scheduleEnabled) {
      scheduleDisplay.innerHTML = `Schedule active`;
      scheduleDisplay.classList.add('c-active');
    } else {
      scheduleDisplay.innerHTML = `Schedule inactive`;
      scheduleDisplay.classList.remove('c-active');
    }
  } else {
    console.error('Schedules enable dont correspond');
  }
};

const showLightingLowerSchedule = (json) => {
  const lightingLowerScheduleDisplay = document.querySelector('.js-schedule_lower');
  const scheduleEnabled = json.enabled;
  if (scheduleEnabled) {
    lightingLowerScheduleDisplay.innerHTML = `Schedule active`;
    lightingLowerScheduleDisplay.classList.add('c-active');
  } else {
    lightingLowerScheduleDisplay.innerHTML = `Schedule inactive`;
    lightingLowerScheduleDisplay.classList.remove('c-active');
  }
};

const showLightingUpperSchedule = (json) => {
  const lightingUpperScheduleDisplay = document.querySelector('.js-schedule_upper');
  const scheduleEnabled = json.enabled;
  if (scheduleEnabled) {
    lightingUpperScheduleDisplay.innerHTML = `Schedule active`;
    lightingUpperScheduleDisplay.classList.add('c-active');
  } else {
    lightingUpperScheduleDisplay.innerHTML = `Schedule inactive`;
    lightingUpperScheduleDisplay.classList.remove('c-active');
  }
};

// #endregion ***  Callback-Visualisation - showData         ***********

// #endregion ***  Callback-Visualisation - showVisuals         ***********

// #region ***  Callback-No Visualisation - callback___  ***********

class TemperatureControl {
  constructor() {
    this.temperature = 22;
    this.minTemp = 16;
    this.maxTemp = 30;
    this.increment = 0.5;
    this.totalSegments = 30;
    this.isEditing = false;

    this.tempDisplay = document.getElementById('tempValue');
    this.tempContainer = document.getElementById('tempDisplay');
    this.progressRing = document.getElementById('progressRing');
    this.decreaseBtn = document.getElementById('decreaseBtn');
    this.increaseBtn = document.getElementById('increaseBtn');

    this.init();
  }

  init() {
    this.createSegments();
    this.updateDisplay();
    this.attachEvents();
  }

  createSegments() {
    for (let i = 0; i < this.totalSegments; i++) {
      const segment = document.createElement('div');
      segment.className = 'c-segment';

      const angle = (i * 180) / (this.totalSegments - 1);
      segment.style.transform = `rotate(${angle}deg)`;
      segment.style.left = '50%';
      segment.style.top = '50%';
      segment.style.marginLeft = '-2px';
      segment.style.marginTop = '-125px';

      this.progressRing.appendChild(segment);
    }
  }

  updateDisplay() {
    if (!this.isEditing) {
      this.tempDisplay.textContent = this.temperature.toFixed(1);
    }

    const progress = (this.temperature - this.minTemp) / (this.maxTemp - this.minTemp);
    const activeSegments = Math.round(progress * this.totalSegments);

    const segments = this.progressRing.querySelectorAll('.c-segment');
    segments.forEach((segment, index) => {
      if (index < activeSegments) {
        segment.className = 'c-segment active';
      } else {
        segment.className = 'c-segment inactive';
      }
    });

    this.decreaseBtn.style.opacity = this.temperature <= this.minTemp ? '0.3' : '1';
    this.increaseBtn.style.opacity = this.temperature >= this.maxTemp ? '0.3' : '1';
  }

  increaseTemp() {
    if (this.temperature < this.maxTemp) {
      this.temperature = Math.round((this.temperature + this.increment) * 10) / 10;
      this.updateDisplay();
    }
  }

  decreaseTemp() {
    if (this.temperature > this.minTemp) {
      this.temperature = Math.round((this.temperature - this.increment) * 10) / 10;
      this.updateDisplay();
    }
  }

  startEditing() {
    if (this.isEditing) return;

    this.isEditing = true;

    const input = document.createElement('input');
    input.type = 'number';
    input.min = this.minTemp;
    input.max = this.maxTemp;
    input.step = this.increment;
    input.value = this.temperature.toFixed(1);
    input.className = 'c-temp-input';

    input.style.cssText = `
      background: transparent;
      border: none;
      color: #333;
      font-size: 2.025rem;
      font-family: inherit;
      text-align: center;
      width: 6rem;
      outline: none;
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    `;

    const originalText = this.tempDisplay.textContent;

    this.tempDisplay.textContent = '';
    this.tempDisplay.appendChild(input);

    input.focus();
    input.select();

    const finishEditing = () => {
      if (!this.isEditing) return;

      let newTemp = parseFloat(input.value);

      if (isNaN(newTemp)) {
        newTemp = this.temperature;
      } else {
        newTemp = Math.max(this.minTemp, Math.min(this.maxTemp, newTemp));
        newTemp = Math.round(newTemp / this.increment) * this.increment;
        newTemp = Math.round(newTemp * 10) / 10;
      }

      this.temperature = newTemp;
      this.isEditing = false;

      input.remove();
      this.updateDisplay();
    };

    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        finishEditing();
      } else if (e.key === 'Escape') {
        this.isEditing = false;
        input.remove();
        this.updateDisplay();
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        const currentValue = parseFloat(input.value) || this.temperature;
        const newValue = Math.min(this.maxTemp, currentValue + this.increment);
        input.value = newValue.toFixed(1);
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        const currentValue = parseFloat(input.value) || this.temperature;
        const newValue = Math.max(this.minTemp, currentValue - this.increment);
        input.value = newValue.toFixed(1);
      }
    });

    input.addEventListener('blur', finishEditing);

    input.addEventListener('input', () => {
      const value = parseFloat(input.value);
      if (!isNaN(value)) {
        if (value < this.minTemp) {
          input.style.borderColor = '#ff4444';
          input.style.border = '1px solid #ff4444';
        } else if (value > this.maxTemp) {
          input.style.borderColor = '#ff4444';
          input.style.border = '1px solid #ff4444';
        } else {
          input.style.borderColor = '#4A90E2';
          input.style.border = '1px solid #4A90E2';
        }
      }
    });
  }

  attachEvents() {
    this.increaseBtn.addEventListener('click', () => this.increaseTemp());
    this.decreaseBtn.addEventListener('click', () => this.decreaseTemp());

    this.tempDisplay.addEventListener('click', () => this.startEditing());

    this.tempDisplay.style.cursor = 'pointer';

    document.addEventListener('keydown', (e) => {
      if (!this.isEditing) {
        if (e.key === 'ArrowUp' || e.key === '+') {
          this.increaseTemp();
        } else if (e.key === 'ArrowDown' || e.key === '-') {
          this.decreaseTemp();
        }
      }
    });
  }
}
// #endregion

// #region ***  Data Access - get___                     ***********
const getBatteryIn = async () => {
  const url = ENDPOINT + `/logs/17/24h/`;
  const response = await fetch(url).catch((err) => console.error('Fetch-error:', err));
  const json = await response.json().catch((err) => console.error('JSON-error:', err));
  showBatteryIn(json);
};

const getEnergyToday = async () => {
  const url = ENDPOINT + `/logs/18/24h/`;
  const response = await fetch(url).catch((err) => console.error('Fetch-error:', err));
  const json = await response.json().catch((err) => console.error('JSON-error:', err));
  showEnergyToday(json);
};

const getEnergyWeek = async () => {
  const url = ENDPOINT + `/logs/18/week/`;
  const response = await fetch(url).catch((err) => console.error('Fetch-error:', err));
  const json = await response.json().catch((err) => console.error('JSON-error:', err));
  showEnergyWeek(json);
};

const getTemperature = async () => {
  const url = ENDPOINT + `/logs/11/last/`;
  const response = await fetch(url).catch((err) => console.error('Fetch-error:', err));
  const json = await response.json().catch((err) => console.error('JSON-error:', err));
  showTemperature(json);
};

const getTemperatureSchedule = async () => {
  let url = ENDPOINT + `/schedules/1/`;
  let response = await fetch(url).catch((err) => console.error('Fetch-error:', err));
  const json = await response.json().catch((err) => console.error('JSON-error:', err));

  url = ENDPOINT + `/schedules/2/`;
  response = await fetch(url).catch((err) => console.error('Fetch-error:', err));
  const json2 = await response.json().catch((err) => console.error('JSON-error:', err));

  showTemperatureSchedule(json, json2);
};

const getLightingLowerSchedule = async () => {
  let url = ENDPOINT + `/schedules/3/`;
  let response = await fetch(url).catch((err) => console.error('Fetch-error:', err));
  const json = await response.json().catch((err) => console.error('JSON-error:', err));
  showLightingLowerSchedule(json);
};

const getLightingUpperSchedule = async () => {
  let url = ENDPOINT + `/schedules/4/`;
  let response = await fetch(url).catch((err) => console.error('Fetch-error:', err));
  const json = await response.json().catch((err) => console.error('JSON-error:', err));
  showLightingUpperSchedule(json);
};

const getLastDoor = async () => {
  const url = ENDPOINT + `/logs/10/last/`;
  const response = await fetch(url).catch((err) => console.error('Fetch-error:', err));
  const json = await response.json().catch((err) => console.error('JSON-error:', err));
  getLastInhabitant(json.value);
};

const getLastInhabitant = (value) => {

// #endregion

// #region ***  Event Listeners - listenTo___            ***********
// #endregion

// #region ***  Init / DOMContentLoaded                  ***********

const init = () => {
  console.info('DOM loaded');
  // showSliders('lightSliderLower', 'valueDisplayLower', 'bulbIconLower');
  // showSliders('lightSliderUpper', 'valueDisplayUpper', 'bulbIconUpper');
  // showDropdown();
  // new TemperatureControl();
  // console.info('All components initialized');

  getBatteryIn();
  getEnergyToday();
  getEnergyWeek();
  getTemperature();
  getTemperatureSchedule();
  getLightingLowerSchedule();
  getLightingUpperSchedule();
  getLastDoor();
};

document.addEventListener('DOMContentLoaded', init);
// #endregion

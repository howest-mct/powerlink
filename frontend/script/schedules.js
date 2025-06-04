'use strict';
const lanIP = `http://192.168.168.169:8000`;
const socketio = io(lanIP);
const ENDPOINT = 'http://192.168.168.169:8000/api/v1';

// #region ***  DOM references                           ***********
// #endregion

// #region ***  Callback-Visualisation - show___         ***********
const showSliders = async (light_slider_id, value_display_id, bulb_icon_id) => {
  const slider = document.getElementById(light_slider_id);
  const valueDisplay = document.getElementById(value_display_id);
  const bulbIcon = document.getElementById(bulb_icon_id);
  const bulbSvg = bulbIcon?.querySelector('svg');

  if (!slider || !valueDisplay || !bulbIcon || !bulbSvg) {
    console.error(`Slider elements not found: ${light_slider_id}, ${value_display_id}, ${bulb_icon_id}`);
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

  slider.addEventListener('input', () => {
    const value = parseInt(slider.value, 10);
    updateSliderVisuals(value);
  });

  const initialValue = parseInt(slider.value, 10);
  updateSliderVisuals(initialValue);
};

const showDropdown = () => {
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
};

const showAllSchedules = (schedules) => {
  let htmlRooms = '';
  const roomsContainer = document.querySelector('.js-main');

  let roomSchedules = {};
  for (const schedule of schedules) {
    const room_id = schedule.room_id;
    if (!roomSchedules[room_id]) {
      roomSchedules[room_id] = [];
    }
    roomSchedules[room_id].push(schedule);
  }

  const chartsToRender = [];

  for (const room_id in roomSchedules) {
    const room_data = roomSchedules[room_id];
    const room_name = room_data[0].room_name;

    let htmlSchedules = '';
    htmlRooms += `
      <div class="c-room__container js-room__container" data-room_id="${room_id}">
        <section class="c-room">
          <h2 class="c-section__title">${room_name}</h2>
          <div class="c-schedules__container">
    `;

    for (const schedule of room_data) {
      const { schedule_id, schedule_name, start_time, end_time, value, value_unit, enabled, type_id, component_id, room_id, room_name, type_name } = schedule;

      if (type_id === 1) {
        htmlSchedules += `
          <div class="c-temperature-control js-schedule__container js-temperature-control c-hover--shadow" data-schedule_id="${schedule_id}" data-component_id="${component_id}" data-room_id="${room_id}">
            <div>
              <h4 class="c-schedule-card__title">${type_name}</h4>
              <input type="checkbox" class="c-lighting-card__checkbox js-schedule__checkbox"
                  id="lightingCheckbox">
            </div>
            <div class="c-circular-progress">
              <div class="c-circular-progress__chart" id="chart_${schedule_id}"></div>
            </div>
            <div class="c-controls">
              <svg class="c-control-btn" id="decrease_btn_${schedule_id}" xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="#000000" viewBox="0 0 256 256">
                <path d="M224,128a8,8,0,0,1-8,8H40a8,8,0,0,1,0-16H216A8,8,0,0,1,224,128Z"></path>
              </svg>
              <svg class="c-control-btn" id="increase_btn_${schedule_id}" xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="#000000" viewBox="0 0 256 256">
                <path d="M224,128a8,8,0,0,1-8,8H136v80a8,8,0,0,1-16,0V136H40a8,8,0,0,1,0-16h80V40a8,8,0,0,1,16,0v80h80A8,8,0,0,1,224,128Z"></path>
              </svg>
            </div>
            <div class="c-temperature-card__meta">
              <div class="c-temperature-card__info">
                <p class="c-temperature-card__status">Turn on climate control</p>
                <div class="c-temperature-card__schedule">
                  <div class="c-temperature-card__schedule-from">
                    <p>from</p>
                    <input type="time" class="js-input_container" value="${start_time}">
                  </div>
                  <div class="c-temperature-card__schedule-to">
                    <p>to</p>
                    <input type="time" class="js-input_container" value="${end_time}">
                  </div>
                  <div>
                    <button type="button">SAVE</button>
                  </div>
                </div>
              </div>
            </div>
          </div>`;

        chartsToRender.push({
          containerId: `chart_${schedule_id}`,
          options: {
            series: [((value - 16) / (30 - 16)) * 100],
            chart: {
              height: 280,
              type: 'radialBar',
              offsetY: -10,
            },
            plotOptions: {
              radialBar: {
                startAngle: -90,
                endAngle: 90,
                dataLabels: {
                  name: {
                    fontSize: '2.025rem',
                    color: undefined,
                    offsetY: 120,
                  },
                  value: {
                    offsetY: -15,
                    fontSize: '2.025rem',
                    color: '#4a90e2',
                    formatter: function (val) {
                      const temp = (val / 100) * (30 - 16) + 16;
                      return temp.toFixed(1) + '°C';
                    },
                  },
                },
              },
            },
            fill: {
              type: 'gradient',
              gradient: {
                shade: 'dark',
                shadeIntensity: 0.15,
                inverseColors: false,
                opacityFrom: 1,
                opacityTo: 1,
                stops: [0, 50, 65, 91],
              },
            },
            stroke: {
              dashArray: 4,
            },
            labels: [''],
          },
        });
      } else if (type_id === 2) {
        htmlSchedules += `
          <div class="c-lighting-card js-schedule__container c-hover--shadow" data-schedule_id="${schedule_id}" data-component_id="${component_id}" data-room_id="${room_id}">
            <div>    
              <h4 class="c-schedule-card__title">${type_name}</h4>
              <input type="checkbox" class="c-schedule__checkbox js-schedule__checkbox"
                id="lightingCheckbox">
            </div>
            <div class="c-lighting-card__content">
              <div class="c-bulb-icon" id="bulb_icon_${schedule_id}">
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="#000000" viewBox="0 0 256 256">
                  <path d="M176,232a8,8,0,0,1-8,8H88a8,8,0,0,1,0-16h80A8,8,0,0,1,176,232Zm40-128a87.55,87.55,0,0,1-33.64,69.21A16.24,16.24,0,0,0,176,186v6a16,16,0,0,1-16,16H96a16,16,0,0,1-16-16v-6a16,16,0,0,0-6.23-12.66A87.59,87.59,0,0,1,40,104.49C39.74,56.83,78.26,17.14,125.88,16A88,88,0,0,1,216,104Zm-16,0a72,72,0,0,0-73.74-72c-39,.92-70.47,33.39-70.26,72.39a71.65,71.65,0,0,0,27.64,56.3A32,32,0,0,1,96,186v6h64v-6a32.15,32.15,0,0,1,12.47-25.35A71.65,71.65,0,0,0,200,104Zm-16.11-9.34a57.6,57.6,0,0,0-46.56-46.55,8,8,0,0,0-2.66,15.78c16.57,2.79,30.63,16.85,33.44,33.45A8,8,0,0,0,176,104a9,9,0,0,0,1.35-.11A8,8,0,0,0,183.89,94.66Z"></path>
                </svg>
              </div>
              <input type="range" min="0" max="100" value="${value}" class="c-slider" id="light_slider_${schedule_id}">
              <div class="c-value-display" id="value_display_${schedule_id}">${value}%</div>
            </div>
            <div class="c-lighting-card__info">
              <p class="c-lighting-card__status">Dim lights automatically</p>
              <div class="c-lighting-card__schedule">
                <div class="c-lighting-card__schedule-from">
                  <p>from</p>
                  <input type="time" class="js-input_container" value="${start_time}">
                </div>
                <div class="c-lighting-card__schedule-to">
                  <p>to</p>
                  <input type="time" class="js-input_container" value="${end_time}">
                </div>
                <div>
                  <button type="button">SAVE</button>
                </div>
              </div>
            </div>
          </div>`;
      }
    }

    htmlRooms += htmlSchedules;
    htmlRooms += `
          </div>
        </section>
      </div>`;
  }

  roomsContainer.innerHTML = htmlRooms;

  const chartContainers = document.querySelectorAll('.c-circular-progress__chart');
  chartContainers.forEach((container, index) => {
    const { options } = chartsToRender[index];
    const chart = new ApexCharts(container, options);
    chart.render();
  });

  const room_containers = document.querySelectorAll('.js-room__container');
  room_containers.forEach((room_container) => {
    const room_id = parseInt(room_container.dataset.room_id);
    const schedule_containers = room_container.querySelectorAll('.js-schedule__container');
    const input_containers = room_container.querySelectorAll('.js-input_container');

    if (room_id % 2 === 0) {
      room_container.classList.add('c-grey-background');
      schedule_containers.forEach((schedule_container) => {
        schedule_container.classList.add('c-white-background');
      });
      input_containers.forEach((input_container) => {
        input_container.classList.add('c-white-background');
      });
    } else {
      room_container.classList.add('c-white-background');
      schedule_containers.forEach((schedule_container) => {
        schedule_container.classList.add('c-grey-background');
      });
      input_containers.forEach((input_container) => {
        input_container.classList.add('c-grey-background');
      });
    }

    const lightingCards = room_container.querySelectorAll('.c-lighting-card');
    lightingCards.forEach((card) => {
      const schedule_id = card.dataset.schedule_id;
      showSliders(`light_slider_${schedule_id}`, `value_display_${schedule_id}`, `bulb_icon_${schedule_id}`);
    });
  });
  listenToTimeSchedules();
  listenToValueLightingSchedules();
  listenToValueTemperatureSchedules();
};
// #endregion

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

const getAllSchedules = async () => {
  const url_params = new URLSearchParams(window.location.search);
  const url_param = url_params.get('param');
  const url = ENDPOINT + `/schedules/${url_param}/`;
  const response = await fetch(url).catch((err) => console.error('Fetch-error:', err));
  const json = await response.json().catch((err) => console.error('JSON-error:', err));
  showAllSchedules(json);
};

const getPutTimeSchedule = async (schedule_id, component_id, room_id, time) => {
  const url = ENDPOINT + `/schedules/${schedule_id}/`;
  const data = {
    component_id: component_id,
    room_id: room_id,
    time: time,
  };
  const response = await fetch(url, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  }).catch((err) => console.error('Fetch-error:', err));
  if (!response.ok) {
    console.error('Error updating schedule:', response.statusText);
    return;
  }
  const json = await response.json().catch((err) => console.error('JSON-error:', err));
  console.info(json);
};
// #endregion

// #region ***  Event Listeners - listenTo___            ***********

const listenToSubmitSchedules = () => {
  const time_inputs = document.querySelectorAll('.js-input_container');
  time_inputs.forEach((input) => {
    input.addEventListener('change', (e) => {
      const schedule_container = e.target.closest('.js-schedule__container');
      const schedule_id = schedule_container.dataset.schedule_id;

      const start_time_input = schedule_container.querySelector('.c-lighting-card__schedule-from .js-input_container');
      const end_time_input = schedule_container.querySelector('.c-lighting-card__schedule-to .js-input_container');

      const start_time = start_time_input.value;
      const end_time = end_time_input.value;

      getPutTimeSchedule(schedule_id, start_time, end_time);
    });
  });
};

const listenToValueLightingSchedules = () => {};

const listenToValueTemperatureSchedules = () => {};
// #endregion

// #region ***  Init / DOMContentLoaded                  ***********
const init = () => {
  console.info('DOM loaded');
  showDropdown();
  // new TemperatureControl();
  getAllSchedules();
};

document.addEventListener('DOMContentLoaded', init);
// #endregion

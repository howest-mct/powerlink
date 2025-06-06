'use strict';
const lanIP = `http://192.168.168.169:8000`;
const sio = io(lanIP);
const ENDPOINT = 'http://192.168.168.169:8000/api/v1';

// #region ***  DOM references                           ***********
// #endregion

// #region ***  Callback-Visualisation - show___         ***********
const showSliders = async (light_slider_id, value_display_id, bulb_icon_id) => {
  const slider = document.getElementById(light_slider_id);
  const value_display = document.getElementById(value_display_id);
  const bulb_icon = document.getElementById(bulb_icon_id);
  const bulb_svg = bulb_icon?.querySelector('svg');

  slider.removeAttribute('title');
  value_display.removeAttribute('title');
  bulb_icon.removeAttribute('title');

  function updateSliderVisuals(value) {
    const percentage = value;
    slider.style.background = `linear-gradient(to right, var(--main-color) 0%, var(--main-color) ${percentage}%, #e0e0e0 ${percentage}%, #e0e0e0 100%)`;

    if (value > 0) {
      bulb_svg.style.fill = '#4A90E2';
      bulb_svg.style.opacity = '1';
    } else {
      bulb_svg.style.fill = '#7B7B7B';
      bulb_svg.style.opacity = '0.5';
    }
  }

  slider.addEventListener('input', () => {
    const value = parseInt(slider.value, 10);
    updateSliderVisuals(value);
  });

  const initial_value = parseInt(slider.value, 10);
  updateSliderVisuals(initial_value);
};

const showDropdown = () => {
  const hamburger = document.querySelector('.c-hamburger');
  const nav_popup = document.querySelector('.c-nav-popup');
  const overlay = document.querySelector('.c-overlay');
  const close_icon = document.querySelector('.c-nav-popup__close');

  function toggleMenu() {
    const is_active = nav_popup.classList.toggle('c-nav-popup--active');
    overlay.classList.toggle('c-overlay--active');
    hamburger.setAttribute('aria-expanded', is_active);
    nav_popup.setAttribute('aria-hidden', !is_active);
    overlay.setAttribute('aria-hidden', !is_active);
  }

  if (window.matchMedia('(max-width: 767px)').matches) {
    hamburger.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleMenu();
    });

    close_icon.addEventListener('click', (e) => {
      e.stopPropagation();
      nav_popup.classList.remove('c-nav-popup--active');
      overlay.classList.remove('c-overlay--active');
      hamburger.setAttribute('aria-expanded', 'false');
      nav_popup.setAttribute('aria-hidden', 'true');
      overlay.setAttribute('aria-hidden', 'true');
    });

    overlay.addEventListener('click', () => {
      nav_popup.classList.remove('c-nav-popup--active');
      overlay.classList.remove('c-overlay--active');
      hamburger.setAttribute('aria-expanded', 'false');
      nav_popup.setAttribute('aria-hidden', 'true');
      overlay.setAttribute('aria-hidden', 'true');
    });

    const navLinks = document.querySelectorAll('.c-nav-popup__link');
    navLinks.forEach((link) => {
      link.addEventListener('click', () => {
        nav_popup.classList.remove('c-nav-popup--active');
        overlay.classList.remove('c-overlay--active');
        hamburger.setAttribute('aria-expanded', 'false');
        nav_popup.setAttribute('aria-hidden', 'true');
        overlay.setAttribute('aria-hidden', 'true');
      });
    });

    document.addEventListener('click', (e) => {
      if (!nav_popup.contains(e.target) && !hamburger.contains(e.target)) {
        nav_popup.classList.remove('c-nav-popup--active');
        overlay.classList.remove('c-overlay--active');
        hamburger.setAttribute('aria-expanded', 'false');
        nav_popup.setAttribute('aria-hidden', 'true');
        overlay.setAttribute('aria-hidden', 'true');
      }
    });
  }

  window.addEventListener('resize', () => {
    if (window.matchMedia('(min-width: 768px)').matches) {
      nav_popup.classList.remove('c-nav-popup--active');
      overlay.classList.remove('c-overlay--active');
      hamburger.setAttribute('aria-expanded', 'false');
      nav_popup.setAttribute('aria-hidden', 'true');
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
      const { schedule_id, start_time, end_time, value, enabled, type_id, component_id, room_id, type_name } = schedule;

      if (type_id === 1) {
        htmlSchedules += `
          <div class="c-temperature-control js-schedule__container js-temperature-control c-hover--shadow" data-schedule_id="${schedule_id}" data-component_id="${component_id}" data-room_id="${room_id}">
            <div class="c-switch">
              <h4 class="c-schedule-card__title">${type_name}</h4>
              <label class="switch">
                <input type="checkbox" class="c-card__checkbox  js-schedule__checkbox" id="checkbox_${schedule_id}" ${enabled ? 'checked' : ''}>
                <span class="slider round"></span>
              </label>
            </div>
            <div class="c-circular-progress" data-value="${value}" data-schedule_id="${schedule_id}">
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
                  <div class="c-card__schedule-save__container">
                    <button class="js-card__schedule-save c-card__schedule-save" type="button">SAVE CHANGES</button>
                  </div>
                </div>
              </div>
            </div>
          </div>`;

        const chartId = `chart_${schedule_id}`;
        const chartOptions = {
          series: [((value - 16) / (30 - 16)) * 100],
          chart: {
            type: 'radialBar',
            offsetY: 0,
            sparkline: {
              enabled: false,
            },
            width: '320px',
            height: '320px',
          },
          plotOptions: {
            radialBar: {
              startAngle: -90,
              endAngle: 90,
              track: {
                background: '#E0E0E0',
                strokeWidth: '97%',
                margin: 0,
                dropShadow: {
                  enabled: false,
                  top: 2,
                  left: 0,
                  color: '#444',
                  opacity: 1,
                  blur: 2,
                },
              },
              dataLabels: {
                name: {
                  show: false,
                },
                value: {
                  offsetY: 0,
                  fontSize: '40px',
                  formatter: function (val) {
                    const temp = (val / 100) * (30 - 16) + 16;
                    return temp.toFixed(1) + '°C';
                  },
                },
              },
            },
          },
          grid: {
            padding: {
              top: 0,
            },
          },
          fill: {
            type: 'linear',
            colors: ['#4A90E2'],
          },
          labels: [''],
        };

        chartsToRender.push({
          id: chartId,
          options: chartOptions,
        });
      } else if (type_id === 2) {
        htmlSchedules += `
          <div class="c-lighting-card js-schedule__container c-hover--shadow" data-schedule_id="${schedule_id}" data-component_id="${component_id}" data-room_id="${room_id}">
            <div class="c-schedule-card__header">    
              <h4 class="c-schedule-card__title">${type_name}</h4>
              <label class="switch">
                <input type="checkbox" class="c-card__checkbox  js-schedule__checkbox" id="checkbox_${schedule_id}" ${enabled ? 'checked' : ''}>
                <span class="slider round"></span>
              </label>
            </div>
            <div class="c-card__content">
              <div class="c-bulb-icon" id="bulb_icon_${schedule_id}">
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="#000000" viewBox="0 0 256 256">
                  <path d="M176,232a8,8,0,0,1-8,8H88a8,8,0,0,1,0-16h80A8,8,0,0,1,176,232Zm40-128a87.55,87.55,0,0,1-33.64,69.21A16.24,16.24,0,0,0,176,186v6a16,16,0,0,1-16,16H96a16,16,0,0,1-16-16v-6a16,16,0,0,0-6.23-12.66A87.59,87.59,0,0,1,40,104.49C39.74,56.83,78.26,17.14,125.88,16A88,88,0,0,1,216,104Zm-16,0a72,72,0,0,0-73.74-72c-39,.92-70.47,33.39-70.26,72.39a71.65,71.65,0,0,0,27.64,56.3A32,32,0,0,1,96,186v6h64v-6a32.15,32.15,0,0,1,12.47-25.35A71.65,71.65,0,0,0,200,104Zm-16.11-9.34a57.6,57.6,0,0,0-46.56-46.55,8,8,0,0,0-2.66,15.78c16.57,2.79,30.63,16.85,33.44,33.45A8,8,0,0,0,176,104a9,9,0,0,0,1.35-.11A8,8,0,0,0,183.89,94.66Z"></path>
                </svg>
              </div>
              <input type="range" min="0" max="100" value="${value}" class="c-slider" id="light_slider_${schedule_id}">
              <div class="c-value-display" id="value_display_${schedule_id}">${value}%</div>
            </div>
            <div class="c-card__info">
              <p class="c-card__status">Dim lights automatically</p>
              <div class="c-card__schedule">
                <div class="c-card__schedule-time">
                  <div class="c-card__schedule-from">
                    <p>from</p>
                    <input type="time" class="js-input_container" value="${start_time}">
                  </div>
                  <div class="c-card__schedule-to">
                    <p>to</p>
                    <input type="time" class="js-input_container" value="${end_time}">
                  </div>
                </div>
                <div class="c-card__schedule-save__container">
                  <button class="js-card__schedule-save c-card__schedule-save" type="button">SAVE CHANGES</button>
                </div>
              </div>
            </div>
          </div>`;
      }
      if (enabled) {
      }
    }

    htmlRooms += htmlSchedules;
    htmlRooms += `
          </div>
        </section>
      </div>`;
  }

  roomsContainer.innerHTML = htmlRooms;

  chartsToRender.forEach(({ id, options }) => {
    const container = document.getElementById(id);
    if (container) {
      container.chart = new ApexCharts(container, options);
      container.chart.render();
    }
  });

  const room_containers = document.querySelectorAll('.js-room__container');
  room_containers.forEach((room_container) => {
    const room_id = parseInt(room_container.dataset.room_id);
    const schedule_containers = room_container.querySelectorAll('.js-schedule__container');
    const input_containers = room_container.querySelectorAll('.js-input_container');
    const save_containers = room_container.querySelectorAll('.js-card__schedule-save');

    if (room_id % 2 === 0) {
      room_container.classList.add('c-grey-background');
      schedule_containers.forEach((schedule_container) => {
        schedule_container.classList.add('c-white-background');
      });
      input_containers.forEach((input_container) => {
        input_container.classList.add('c-white-background');
      });
      save_containers.forEach((save_container) => {
        save_container.classList.add('c-white-background');
      });
    } else {
      room_container.classList.add('c-white-background');
      schedule_containers.forEach((schedule_container) => {
        schedule_container.classList.add('c-grey-background');
      });
      input_containers.forEach((input_container) => {
        input_container.classList.add('c-grey-background');
      });
      save_containers.forEach((save_container) => {
        save_container.classList.add('c-grey-background');
      });
    }

    const lightingCards = room_container.querySelectorAll('.c-lighting-card');
    lightingCards.forEach((card) => {
      const schedule_id = card.dataset.schedule_id;
      showSliders(`light_slider_${schedule_id}`, `value_display_${schedule_id}`, `bulb_icon_${schedule_id}`);
    });
  });
  listenToSubmitSchedule();
  listenToTemperatureControl();
};
// #endregion

// #region ***  Callback-No Visualisation - callback___  ***********

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

const getPutSchedule = async (schedule_id, start_time, end_time, value, enabled) => {
  const url = ENDPOINT + `/schedule/${schedule_id}/`;
  const data = {
    start_time: start_time,
    end_time: end_time,
    value: value,
    enabled: enabled,
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
  console.log(json);

  sio.emit('BF2_schedule_updated', {
    schedule_id: schedule_id,
    start_time: start_time,
    end_time: end_time,
    value: value,
    enabled: enabled,
  });
};

// #endregion

// #region ***  Event Listeners - listenTo___            ***********

const listenToSubmitSchedule = () => {
  const saveButtons = document.querySelectorAll('.js-card__schedule-save');
  saveButtons.forEach((button) => {
    button.removeEventListener('click', listenToSaveCLicked);
    button.addEventListener('click', listenToSaveCLicked);
  });
};

const listenToSaveCLicked = (e) => {
  const schedule_container = e.target.closest('.js-schedule__container');
  const schedule_id = parseInt(schedule_container.dataset.schedule_id);

  const time_inputs = schedule_container.querySelectorAll('.js-input_container');
  const start_time = time_inputs[0].value;
  const end_time = time_inputs[1].value;
  const enabled_input = schedule_container.querySelector('.js-schedule__checkbox');
  const enabled = enabled_input.checked ? 1 : 0;

  let value;
  if (schedule_container.classList.contains('c-temperature-control')) {
    const progressDiv = schedule_container.querySelector('.c-circular-progress');
    value = parseFloat(progressDiv.getAttribute('data-value'));
  } else if (schedule_container.classList.contains('c-lighting-card')) {
    const slider_input = schedule_container.querySelector('.c-slider');
    value = parseFloat(slider_input.value);
  } else {
    console.error('Unknown schedule type');
    return;
  }

  getPutSchedule(schedule_id, start_time, end_time, value, enabled);
};

const listenToTemperatureControl = () => {
  const temp_controls = document.querySelectorAll('.js-temperature-control');
  temp_controls.forEach((control) => {
    const schedule_id = control.dataset.schedule_id;
    const decrease_btn = control.querySelector(`#decrease_btn_${schedule_id}`);
    const increase_btn = control.querySelector(`#increase_btn_${schedule_id}`);
    const progressDiv = control.querySelector('.c-circular-progress');
    const chartContainer = control.querySelector(`#chart_${schedule_id}`);

    if (decrease_btn && increase_btn && progressDiv && chartContainer && chartContainer.chart) {
      decrease_btn.addEventListener('click', () => {
        let currentValue = parseFloat(progressDiv.getAttribute('data-value'));
        currentValue -= 0.5;
        if (currentValue < 16) currentValue = 16;
        progressDiv.setAttribute('data-value', currentValue);
        const newSeries = ((currentValue - 16) / (30 - 16)) * 100;
        chartContainer.chart.updateSeries([newSeries]);
      });

      increase_btn.addEventListener('click', () => {
        let currentValue = parseFloat(progressDiv.getAttribute('data-value'));
        currentValue += 0.5;
        if (currentValue > 30) currentValue = 30;
        progressDiv.setAttribute('data-value', currentValue);
        const newSeries = ((currentValue - 16) / (30 - 16)) * 100;
        chartContainer.chart.updateSeries([newSeries]);
      });
    }
  });
};

const listenToSocketIo = () => {
  sio.on('connect', () => {
    console.log('Socket.IO connected');
  });
  sio.on('disconnect', () => {
    console.log('Socket.IO disconnected');
  });
  sio.on('error', (error) => {
    console.log('Socket.IO error:', error);
  });
  sio.on('BF2_schedule_updated', ({ schedule_id: schedule_id, start_time: start_time, end_time: end_time, value: value, enabled: enabled }) => {});
};
// #endregion

// #region ***  Init / DOMContentLoaded                  ***********
const init = () => {
  console.log('DOM loaded');
  showDropdown();
  getAllSchedules();
  listenToSocketIo();
};

document.addEventListener('DOMContentLoaded', init);
// #endregion

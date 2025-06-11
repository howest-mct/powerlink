'use strict';

const lan_ip = `http://192.168.168.169:8000`;
const socket_connection = io(lan_ip);
const api_endpoint = 'http://192.168.168.169:8000/api/v1';

// #region ***  DOM references                           ***********

const schedule_icons = {
  1: 'img/svg/sun-dim.svg',
  2: 'img/svg/moon-stars.svg',
  3: 'img/svg/sun-dim.svg',
  4: 'img/svg/moon-stars.svg',
  5: 'img/svg/sun-dim.svg',
  6: 'img/svg/moon-stars.svg',
};
// #endregion

// #region ***  Callback-Visualisation - show___         ***********
const showSliders = async (light_slider_id, value_display_id, bulb_icon_id) => {
  const slider_element = document.getElementById(light_slider_id);
  const value_display_element = document.getElementById(value_display_id);
  const bulb_icon_element = document.getElementById(bulb_icon_id);
  const bulb_svg_element = bulb_icon_element?.querySelector('svg');

  slider_element.removeAttribute('title');
  value_display_element.removeAttribute('title');
  bulb_icon_element.removeAttribute('title');

  const updateSliderVisuals = (current_value) => {
    const percentage_value = current_value;

    slider_element.style.background = `linear-gradient(to right, var(--main-color) 0%, var(--main-color) ${percentage_value}%, #e0e0e0 ${percentage_value}%, #e0e0e0 100%)`;

    value_display_element.textContent = `${current_value}%`;

    if (current_value > 0) {
      bulb_svg_element.style.fill = '#4A90E2';
      bulb_svg_element.style.opacity = '1';
    } else {
      bulb_svg_element.style.fill = '#7B7B7B';
      bulb_svg_element.style.opacity = '0.5';
    }
  };

  slider_element.addEventListener('input', () => {
    const current_value = parseInt(slider_element.value, 10);
    updateSliderVisuals(current_value);
  });

  const initial_slider_value = parseInt(slider_element.value, 10);
  updateSliderVisuals(initial_slider_value);
};

const showDropdown = () => {
  const hamburger_button = document.querySelector('.c-hamburger');
  const navigation_popup = document.querySelector('.c-nav-popup');
  const page_overlay = document.querySelector('.c-overlay');
  const close_button = document.querySelector('.c-nav-popup__close');

  const toggleMobileMenu = () => {
    const menu_is_active = navigation_popup.classList.toggle('c-nav-popup--active');
    page_overlay.classList.toggle('c-overlay--active');
    hamburger_button.setAttribute('aria-expanded', menu_is_active);
    navigation_popup.setAttribute('aria-hidden', !menu_is_active);
    page_overlay.setAttribute('aria-hidden', !menu_is_active);
  };

  if (window.matchMedia('(max-width: 767px)').matches) {
    hamburger_button.addEventListener('click', (event) => {
      event.stopPropagation();
      toggleMobileMenu();
    });

    close_button.addEventListener('click', (event) => {
      event.stopPropagation();
      navigation_popup.classList.remove('c-nav-popup--active');
      page_overlay.classList.remove('c-overlay--active');
      hamburger_button.setAttribute('aria-expanded', 'false');
      navigation_popup.setAttribute('aria-hidden', 'true');
      page_overlay.setAttribute('aria-hidden', 'true');
    });

    page_overlay.addEventListener('click', () => {
      navigation_popup.classList.remove('c-nav-popup--active');
      page_overlay.classList.remove('c-overlay--active');
      hamburger_button.setAttribute('aria-expanded', 'false');
      navigation_popup.setAttribute('aria-hidden', 'true');
      page_overlay.setAttribute('aria-hidden', 'true');
    });

    const navigation_links = document.querySelectorAll('.c-nav-popup__link');
    navigation_links.forEach((link) => {
      link.addEventListener('click', () => {
        navigation_popup.classList.remove('c-nav-popup--active');
        page_overlay.classList.remove('c-overlay--active');
        hamburger_button.setAttribute('aria-expanded', 'false');
        navigation_popup.setAttribute('aria-hidden', 'true');
        page_overlay.setAttribute('aria-hidden', 'true');
      });
    });

    document.addEventListener('click', (event) => {
      if (!navigation_popup.contains(event.target) && !hamburger_button.contains(event.target)) {
        navigation_popup.classList.remove('c-nav-popup--active');
        page_overlay.classList.remove('c-overlay--active');
        hamburger_button.setAttribute('aria-expanded', 'false');
        navigation_popup.setAttribute('aria-hidden', 'true');
        page_overlay.setAttribute('aria-hidden', 'true');
      }
    });
  }

  window.addEventListener('resize', () => {
    if (window.matchMedia('(min-width: 768px)').matches) {
      navigation_popup.classList.remove('c-nav-popup--active');
      page_overlay.classList.remove('c-overlay--active');
      hamburger_button.setAttribute('aria-expanded', 'false');
      navigation_popup.setAttribute('aria-hidden', 'true');
      page_overlay.setAttribute('aria-hidden', 'true');
    }
  });
};

const showAllSchedules = (all_schedules) => {
  let rooms_html = '';
  const main_container = document.querySelector('.js-main');

  let schedules_by_room = {};
  for (const schedule_item of all_schedules) {
    const room_id = schedule_item.room_id;
    if (!schedules_by_room[room_id]) {
      schedules_by_room[room_id] = [];
    }
    schedules_by_room[room_id].push(schedule_item);
  }

  const charts_to_render = [];
  let room_display_number = 0;

  for (const room_id in schedules_by_room) {
    const room_schedule_data = schedules_by_room[room_id];
    const room_name = room_schedule_data[0].room_name;

    let schedules_html = '';
    rooms_html += `
      <div class="c-room__container js-room__container" data-room_id="${room_id}" data-display_number="${room_display_number}">
        <section class="c-room">
          <h2 class="c-section__title">${room_name}</h2>
          <div class="c-schedules__container">
    `;

    for (const schedule_item of room_schedule_data) {
      const { schedule_id, schedule_name, start_time, end_time, value, value_unit, enabled, type_id, component_id, room_id, type_name } = schedule_item;
      const icon_path = schedule_icons[schedule_id];

      if (type_id === 1) {
        schedules_html += `
          <div class="c-temperature-control js-schedule__container js-temperature-control c-hover--shadow" data-schedule_id="${schedule_id}" data-component_id="${component_id}" data-room_id="${room_id}">
            <div class="c-schedule-card__header">
              <div class="c-schedule-card__header">
                <img src="${icon_path}" alt="${type_name}" class="c-schedule-icon">
                <h4 class="c-schedule-card__title">${schedule_name}</h4>
              </div>
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
                <p class="c-temperature-card__status">${value_unit}</p>
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
                  <button class="js-card__schedule-save c-card__schedule-save" type="button">Save Changes</button>
                </div>
                </div>
              </div>
            </div>
          </div>`;

        const chart_element_id = `chart_${schedule_id}`;
        const chart_configuration = {
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
                  formatter: function (percentage_value) {
                    const temperature = (percentage_value / 100) * (30 - 16) + 16;
                    return temperature.toFixed(1) + '°C';
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

        charts_to_render.push({
          id: chart_element_id,
          options: chart_configuration,
        });
      } else if (type_id === 2) {
        schedules_html += `
          <div class="c-lighting-card js-schedule__container c-hover--shadow" data-schedule_id="${schedule_id}" data-component_id="${component_id}" data-room_id="${room_id}">
            <div class="c-schedule-card__header">
              <div class="c-schedule-card__header">
                <img src="${icon_path}" alt="${type_name}" class="c-schedule-icon">
                <h4 class="c-schedule-card__title">${schedule_name}</h4>
              </div>
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
              <p class="c-card__status">${value_unit}</p>
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
                  <button class="js-card__schedule-save c-card__schedule-save" type="button">Save Changes</button>
                </div>
              </div>
            </div>
          </div>`;
      }
    }

    rooms_html += schedules_html;
    rooms_html += `
          </div>
        </section>
      </div>`;

    room_display_number++;
  }

  main_container.innerHTML = rooms_html;

  charts_to_render.forEach(({ id, options }) => {
    const chart_container = document.getElementById(id);
    if (chart_container) {
      chart_container.chart = new ApexCharts(chart_container, options);
      chart_container.chart.render().then(() => {
        setTimeout(() => {
          const current_series_value = chart_container.chart.w.config.series[0];
          chart_container.chart.updateSeries([current_series_value - 0.001]);

          setTimeout(() => {
            chart_container.chart.updateSeries([current_series_value]);
          }, 1);
        }, 1);
      });
    }
  });

  listenToTemperatureControl();

  const all_room_containers = document.querySelectorAll('.js-room__container');
  all_room_containers.forEach((room_container) => {
    const display_number = parseInt(room_container.dataset.display_number);
    const schedule_containers = room_container.querySelectorAll('.js-schedule__container');
    const input_containers = room_container.querySelectorAll('.js-input_container');
    const save_button_containers = room_container.querySelectorAll('.js-card__schedule-save');

    if (display_number % 2 === 0) {
      room_container.classList.add('c-grey-background');
      schedule_containers.forEach((schedule_container) => {
        schedule_container.classList.add('c-white-background');
      });
      input_containers.forEach((input_container) => {
        input_container.classList.add('c-white-background');
      });
      save_button_containers.forEach((save_container) => {
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
      save_button_containers.forEach((save_container) => {
        save_container.classList.add('c-grey-background');
      });
    }

    const lighting_cards = room_container.querySelectorAll('.c-lighting-card');
    lighting_cards.forEach((lighting_card) => {
      const schedule_id = lighting_card.dataset.schedule_id;
      showSliders(`light_slider_${schedule_id}`, `value_display_${schedule_id}`, `bulb_icon_${schedule_id}`);
    });
  });

  listenToSubmitSchedule();
};
// #endregion

// #region ***  Callback-No Visualisation - callback___  ***********
// #endregion

// #region ***  Data Access - get___                     ***********
const getAllSchedules = async () => {
  const url_parameters = new URLSearchParams(window.location.search);
  const frame_url_parameter = url_parameters.get('frame');
  const request_url = api_endpoint + `/schedules/${frame_url_parameter}/`;
  const server_response = await fetch(request_url).catch((error) => console.error('Fetch-error:', error));
  const json_data = await server_response.json().catch((error) => console.error('JSON-error:', error));
  showAllSchedules(json_data);
};

const getPutSchedule = async (schedule_id, start_time, end_time, value, enabled) => {
  const request_url = api_endpoint + `/schedule/${schedule_id}/`;
  const schedule_data = {
    start_time: start_time,
    end_time: end_time,
    value: value,
    enabled: enabled,
  };

  const server_response = await fetch(request_url, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(schedule_data),
  }).catch((error) => console.error('Fetch-error:', error));

  const response_json = await server_response.json().catch((error) => console.error('JSON-error:', error));

  socket_connection.emit('BF2_schedule_updated', {
    schedule_id: response_json.schedule_id,
    schedule_name: response_json.schedule_name,
    start_time: response_json.start_time,
    end_time: response_json.end_time,
    value: response_json.value,
    enabled: response_json.enabled,
  });
};
// #endregion

// #region ***  Event Listeners - listenTo___            ***********
const listenToSubmitSchedule = () => {
  const all_save_buttons = document.querySelectorAll('.js-card__schedule-save');
  all_save_buttons.forEach((save_button) => {
    save_button.removeEventListener('click', listenToSaveClicked);
    save_button.addEventListener('click', listenToSaveClicked);
  });
};

const listenToSaveClicked = (click_event) => {
  const clicked_button = click_event.target;
  const schedule_container = clicked_button.closest('.js-schedule__container');
  const schedule_id = parseInt(schedule_container.dataset.schedule_id);

  const time_input_elements = schedule_container.querySelectorAll('.js-input_container');
  const start_time = time_input_elements[0].value;
  const end_time = time_input_elements[1].value;

  const enabled_checkbox = schedule_container.querySelector('.js-schedule__checkbox');
  const is_enabled = enabled_checkbox.checked ? 1 : 0;

  let current_value;
  if (schedule_container.classList.contains('c-temperature-control')) {
    const progress_element = schedule_container.querySelector('.c-circular-progress');
    current_value = parseFloat(progress_element.getAttribute('data-value'));
  } else if (schedule_container.classList.contains('c-lighting-card')) {
    const slider_element = schedule_container.querySelector('.c-slider');
    current_value = parseFloat(slider_element.value);
  } else {
    console.error('Unknown schedule type');
    return;
  }

  clicked_button.textContent = 'Saved';
  clicked_button.disabled = true;
  clicked_button.timeoutId = setTimeout(() => {
    clicked_button.textContent = 'Save Changes';
    clicked_button.disabled = false;
    clicked_button.timeoutId = null;
  }, 3000);

  getPutSchedule(schedule_id, start_time, end_time, current_value, is_enabled);

  const room_container = schedule_container.closest('.js-room__container');
  const all_schedules_in_room = room_container.querySelectorAll('.js-schedule__container');
  all_schedules_in_room.forEach((other_schedule) => {
    const other_schedule_id = parseInt(other_schedule.dataset.schedule_id, 10);
    const other_component_id = parseInt(other_schedule.dataset.component_id, 10);
    const current_component_id = parseInt(schedule_container.dataset.component_id, 10);

    if (other_schedule_id !== schedule_id && other_component_id === current_component_id) {
      const inverse_start_time = end_time;
      const inverse_end_time = start_time;

      let other_schedule_value;
      if (other_schedule.classList.contains('c-temperature-control')) {
        other_schedule_value = parseFloat(other_schedule.querySelector('.c-circular-progress').getAttribute('data-value'));
      } else if (other_schedule.classList.contains('c-lighting-card')) {
        other_schedule_value = parseFloat(other_schedule.querySelector('.c-slider').value);
      }

      const other_schedule_enabled = other_schedule.querySelector('.js-schedule__checkbox').checked ? 1 : 0;

      getPutSchedule(other_schedule_id, inverse_start_time, inverse_end_time, other_schedule_value, other_schedule_enabled);

      const other_time_inputs = other_schedule.querySelectorAll('.js-input_container');
      other_time_inputs[0].value = inverse_start_time;
      other_time_inputs[1].value = inverse_end_time;
    }
  });
};

const listenToTemperatureControl = () => {
  const temperature_controls = document.querySelectorAll('.js-temperature-control');
  temperature_controls.forEach((temperature_control) => {
    const schedule_id = temperature_control.dataset.schedule_id;
    const decrease_button = temperature_control.querySelector(`#decrease_btn_${schedule_id}`);
    const increase_button = temperature_control.querySelector(`#increase_btn_${schedule_id}`);
    const progress_element = temperature_control.querySelector('.c-circular-progress');
    const chart_container = temperature_control.querySelector(`#chart_${schedule_id}`);

    if (decrease_button && increase_button && progress_element && chart_container && chart_container.chart) {
      decrease_button.addEventListener('click', () => {
        let current_temperature = parseFloat(progress_element.getAttribute('data-value'));
        current_temperature -= 0.5;
        if (current_temperature < 16) current_temperature = 16;

        progress_element.setAttribute('data-value', current_temperature);
        const new_percentage = ((current_temperature - 16) / (30 - 16)) * 100;
        chart_container.chart.updateSeries([new_percentage]);
      });

      increase_button.addEventListener('click', () => {
        let current_temperature = parseFloat(progress_element.getAttribute('data-value'));
        current_temperature += 0.5;
        if (current_temperature > 30) current_temperature = 30;

        progress_element.setAttribute('data-value', current_temperature);
        const new_percentage = ((current_temperature - 16) / (30 - 16)) * 100;
        chart_container.chart.updateSeries([new_percentage]);
      });
    }
  });
};

const listenToSocketIo = () => {
  socket_connection.on('connect', () => {
    console.log('Socket.IO connected');
  });

  socket_connection.on('disconnect', () => {
    console.log('Socket.IO disconnected');
  });

  socket_connection.on('error', (socket_error) => {
    console.log('Socket.IO error:', socket_error);
  });
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

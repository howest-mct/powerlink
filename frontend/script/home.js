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

const showAllItems = (items) => {
  let htmlRooms = '';
  const rooms_container = document.querySelector('.js-main');

  let rooms_items = {};
  for (const item of items) {
    const room_id = item.room_id;
    if (!rooms_items[room_id]) {
      rooms_items[room_id] = [];
    }
    rooms_items[room_id].push(item);
  }

  const chartsToRender = [];
  let room_display_number = 0;

  for (const room_id in rooms_items) {
    const room_data = rooms_items[room_id];
    const room_name = room_data[0].room_name;

    let htmlSchedules = '';
    htmlRooms += `
      <div class="c-room__container js-room__container" data-room_id="${room_id}" data-display_number="${room_display_number}">
        <section class="c-room">
          <h2 class="c-section__title">${room_name}</h2>
          <div class="c-schedules__container">
    `;

    for (const item of room_data) {
      if (item.component_id === 1) {
        htmlSchedules += `
          <article class="c-article__solar c-hover--shadow" onclick="window.location.href='/frontend/insights.html'">
            <div class="c-solar">
              <h3 class="c-solar_kw js-solar_value">8kW</h3>
              <div class="c-solar__meta">
                <p class="c-solar__status">Solar panels</p>
                <p class="c-solar__capacity js-solar_state">Charging battery</p>
              </div>
            </div>
          </article>
        `;
      } else if (item.component_id === 2) {
        getEnergy24H();
        getEnergy7D();
      } else if (item.component_id === 3) {
        htmlSchedules += `
          <div class="c-temperature-control c-hover--shadow">
            <div class="c-circular-progress">
                <div class="c-progress-ring" id="progressRing"></div>
                <div class="c-temperature-display" id="tempDisplay">
                    <span class="js-temperature_value" id="tempValue">24</span><span class="unit">°C</span>
                </div>
            </div>
            <div class="c-controls">
                <svg class="c-control-btn" id="decreaseBtn" xmlns="http://www.w3.org/2000/svg" width="32"
                    height="32" fill="#000000" viewBox="0 0 256 256">
                    <path d="M224,128a8,8,0,0,1-8,8H40a8,8,0,0,1,0-16H216A8,8,0,0,1,224,128Z"></path>
                </svg>
                <svg class="c-control-btn" id="increaseBtn" xmlns="http://www.w3.org/2000/svg" width="32"
                    height="32" fill="#000000" viewBox="0 0 256 256">
                    <path
                        d="M224,128a8,8,0,0,1-8,8H136v80a8,8,0,0,1-16,0V136H40a8,8,0,0,1,0-16h80V40a8,8,0,0,1,16,0v80h80A8,8,0,0,1,224,128Z">
                    </path>
                </svg>
            </div>
            <div class="c-temperature-card__meta">
                <div class="c-temperature-card__info">
                    <p class="c-temperature-card__status">Climate Control</p>
                    <p class="c-temperature-card__state js-temperature_schedule">Schedule inactive</p>
                </div>
                <a href="schedules.html" class="c-temperature-card__edit c-edit">Edit Schedule</a>
            </div>
        </div>`;
      } else if (item.component_id === 10 || item.component_id === 13) {
        htmlSchedules += `
          <div class="c-lighting-card c-hover--shadow c-grey-background">
            <div class="c-lighting-card__content">
                <div class="c-bulb-icon" id="bulbIconLower">
                    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="#000000" viewBox="0 0 256 256">
                        <path
                            d="M176,232a8,8,0,0,1-8,8H88a8,8,0,0,1,0-16h80A8,8,0,0,1,176,232Zm40-128a87.55,87.55,0,0,1-33.64,69.21A16.24,16.24,0,0,0,176,186v6a16,16,0,0,1-16,16H96a16,16,0,0,1-16-16v-6a16,16,0,0,0-6.23-12.66A87.59,87.59,0,0,1,40,104.49C39.74,56.83,78.26,17.14,125.88,16A88,88,0,0,1,216,104Zm-16,0a72,72,0,0,0-73.74-72c-39,.92-70.47,33.39-70.26,72.39a71.65,71.65,0,0,0,27.64,56.3A32,32,0,0,1,96,186v6h64v-6a32.15,32.15,0,0,1,12.47-25.35A71.65,71.65,0,0,0,200,104Zm-16.11-9.34a57.6,57.6,0,0,0-46.56-46.55,8,8,0,0,0-2.66,15.78c16.57,2.79,30.63,16.85,33.44,33.45A8,8,0,0,0,176,104a9,9,0,0,0,1.35-.11A8,8,0,0,0,183.89,94.66Z">
                        </path>
                    </svg>
                </div class="c-hover--shadow">
                <input type="range" min="0" max="100" value="0" class="c-slider" id="lightSliderLower">
                <div class="c-value-display" id="valueDisplayLower">0%</div>
            </div>
            <div class="c-lighting-card__meta">
                <div class="c-lighting-card__info">
                    <p class="c-lighting-card__status">Lighting</p>
                    <p class="c-lighting-card__state js-schedule_lower">Schedule inactive</p>
                </div>
                <a href="schedules.html" class="c-lighting-card__edit c-edit">Edit Schedule</a>
            </div>
        </div>`;
      } else if (item.component_id === 15) {
        htmlSchedules += `
          <article class="c-article__door-log c-hover--shadow c-grey-background"
            onclick="window.location.href='/frontend/insights.html'">
            <div class="c-door-log">
                <p class="c-door__name js-last_inhabitant">Michiel</p>
                <div class="c-door__meta">
                    <p class="c-door__last">Last entered</p>
                    <p class="c-door__date js-last_inhabitant_date">Today at 11:00 AM</p>
                </div>
            </div>
        </article>`;
      } else if (item.component_id === 17) {
        htmlSchedules += `
          <article class="c-article__door c-hover--shadow c-grey-background">
            <div class="c-door">
                <div class="js-door_state_icon">
                    <svg class="c-door__lock-icon" xmlns="http://www.w3.org/2000/svg" width="48" height="48"
                        fill="#000000" viewBox="0 0 256 256">
                        <path
                            d="M208,80H176V56a48,48,0,0,0-96,0V80H48A16,16,0,0,0,32,96V208a16,16,0,0,0,16,16H208a16,16,0,0,0,16-16V96A16,16,0,0,0,208,80ZM96,56a32,32,0,0,1,64,0V80H96ZM208,208H48V96H208V208Z">
                        </path>
                    </svg>
                </div>
                <div class="c-door__meta">
                    <p class="c-door__lock">Door lock</p>
                    <p class="c-door__state js-door_state">Locked</p>
                </div>
            </div>
        </article>`;
      } else if (item.component_id === 19) {
        htmlSchedules += `
          <article class="c-lighting-outside c-hover--shadow">
            <div class="js-lighting_outside_icon">
                <svg class="c-lighting-outside__icon" xmlns="http://www.w3.org/2000/svg" width="32" height="32"
                    fill="#000000" viewBox="0 0 256 256">
                    <path
                        d="M176,232a8,8,0,0,1-8,8H88a8,8,0,0,1,0-16h80A8,8,0,0,1,176,232Zm40-128a87.55,87.55,0,0,1-33.64,69.21A16.24,16.24,0,0,0,176,186v6a16,16,0,0,1-16,16H96a16,16,0,0,1-16-16v-6a16,16,0,0,0-6.23-12.66A87.59,87.59,0,0,1,40,104.49C39.74,56.83,78.26,17.14,125.88,16A88,88,0,0,1,216,104Zm-16,0a72,72,0,0,0-73.74-72c-39,.92-70.47,33.39-70.26,72.39a71.65,71.65,0,0,0,27.64,56.3A32,32,0,0,1,96,186v6h64v-6a32.15,32.15,0,0,1,12.47-25.35A71.65,71.65,0,0,0,200,104Zm-16.11-9.34a57.6,57.6,0,0,0-46.56-46.55,8,8,0,0,0-2.66,15.78c16.57,2.79,30.63,16.85,33.44,33.45A8,8,0,0,0,176,104a9,9,0,0,0,1.35-.11A8,8,0,0,0,183.89,94.66Z">
                    </path>
                </svg>
            </div>
            <div class="c-lighting-outside__meta">
                <p class="c-lighting-outside__title">Lights</p>
                <p class="c-lighting-outside__value-today js-lighting_outside_state">Off</p>
            </div>
        </article>`;
      } else if (item.component_id === 20) {
      }

      htmlRooms += htmlSchedules;
      htmlRooms += `
          </div>
        </section>
      </div>`;

      room_display_number++;
    }

    rooms_container.innerHTML = htmlRooms;

    const room_containers = document.querySelectorAll('.js-room__container');
    room_containers.forEach((room_container) => {
      const display_number = parseInt(room_container.dataset.display_number);
      const schedule_containers = room_container.querySelectorAll('.js-schedule__container');
      const input_containers = room_container.querySelectorAll('.js-input_container');
      const save_containers = room_container.querySelectorAll('.js-card__schedule-save');

      if (display_number % 2 === 0) {
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
  }
};
// #endregion

// #region ***  Callback-No Visualisation - callback___  ***********

// #endregion

// #region ***  Data Access - get___                     ***********

const getAllItems = async () => {
  const url_params = new URLSearchParams(window.location.search);
  const url_param = url_params.get('param');
  const url = ENDPOINT + `/components/last/${url_param}/`;
  const response = await fetch(url).catch((err) => console.error('Fetch-error:', err));
  const json = await response.json().catch((err) => console.error('JSON-error:', err));
  console.log('Fetched components:', json);
  // showAllItems(json);
};

// #endregion

// #region ***  Event Listeners - listenTo___            ***********

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
};
// #endregion

// #region ***  Init / DOMContentLoaded                  ***********
const init = () => {
  console.log('DOM loaded');
  showDropdown();
  getAllItems();
  listenToSocketIo();
};

document.addEventListener('DOMContentLoaded', init);
// #endregion

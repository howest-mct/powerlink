'use strict';
const lanIP = `http://192.168.168.169:8000`;
const sio = io(lanIP);
const ENDPOINT = 'http://192.168.168.169:8000/api/v1';

// #region ***  DOM references                           ***********
const svg_icons = {
  1: 'img/svg/lightning.svg',
  2: 'img/svg/lightning.svg',
  3: 'img/svg/sliders-horizontal.svg',
  4: 'img/svg/thermometer.svg',
  5: 'img/svg/fire-simple.svg',
  6: 'img/svg/lightning.svg',
  7: 'img/svg/fan.svg',
  8: 'img/svg/lightning.svg',
  9: 'img/svg/toggle-left.svg',
  10: 'img/svg/lightbulb.svg',
  11: 'img/svg/lightning.svg',
  12: 'img/svg/hand-waving.svg',
  13: 'img/svg/lightbulb.svg',
  14: 'img/svg/lightning.svg',
  15: 'img/svg/scan.svg',
  16: 'img/svg/door.svg',
  17: 'img/svg/lock-simple.svg',
  18: 'img/svg/sun.svg',
  19: 'img/svg/lightbulb.svg',
  20: 'img/svg/power.svg',
};
// #endregion

// #region ***  Callback-Visualisation - show___         ***********
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

const showAllLastLogs = (json) => {
  let htmlRooms = '';
  const room_containers = document.querySelector('.js-main');

  let room_components = {};
  for (const schedule of json) {
    const room_id = schedule.room_id;
    if (!room_components[room_id]) {
      room_components[room_id] = [];
    }
    room_components[room_id].push(schedule);
  }

  for (const room_id in room_components) {
    const room_data = room_components[room_id];
    const room_name = room_data[0].room_name;

    let htmlComponents = '';
    htmlRooms += `
      <div class="c-room__container js-room__container" data-room_id="${room_id}" data-room_name="${room_name}">
        <section class="c-room">
          <h2 class="c-section__title">${room_name}</h2>
          <div class="c-room__components">
    `;

    for (const item of room_data) {
      const { log_id, datetime, value, component_id, component_name, value_unit, room_id } = item;
      const formatted_date = new Date(datetime);
      const svg_path = svg_icons[component_id] || 'img/svg/circuitry.svg';
      htmlComponents += `
        <article class="c-article c-hover--shadow js-component__container" data-component_id="${component_id}" data-room_id="${room_id}" data-log_id="${log_id}">
          <div class="c-article__header">
            <a href="#" class="c-article__link">
              <img src="${svg_path}" alt="Component icon" class="c-article__icon">
            </a>
            <h2 class="c-article__title">${component_name}</h2>
          </div>
          <div class="c-card">
            <h3 class="c-card__level">${value} ${value_unit}</h3>
            <div class="c-card__meta">
              <p class="c-card__status">Last log</p>
              <p class="c-card__capacity">${formatDateTime(formatted_date)}</p>
            </div>
          </div>
        </article>
      `;
    }

    htmlRooms += htmlComponents;
    htmlRooms += `
          </div>
        </section>
      </div>
    `;
  }

  room_containers.innerHTML = htmlRooms;

  const room_container = document.querySelectorAll('.js-room__container');
  room_container.forEach((room_container) => {
    const room_id = parseInt(room_container.dataset.room_id);
    const component_containers = room_container.querySelectorAll('.js-component__container');

    if (room_id % 2 === 0) {
      room_container.classList.add('c-grey-background');
      component_containers.forEach((component_container) => {
        component_container.classList.add('c-white-background');
      });
    } else {
      room_container.classList.add('c-white-background');
      component_containers.forEach((component_container) => {
        component_container.classList.add('c-grey-background');
      });
    }
  });
};

const showLastLog = (log) => {
  let log_container = document.querySelector(`.js-component__container[data-component_id="${log.component_id}"]`);
  const formatted_date = new Date(log.datetime);

  if (log_container) {
    const level_element = log_container.querySelector('.c-card__level');
    const capacity_element = log_container.querySelector('.c-card__capacity');

    if (level_element) {
      level_element.textContent = `${log.value} ${log.value_unit}`;
    }

    if (capacity_element) {
      capacity_element.textContent = formatDateTime(formatted_date);
    }

    log_container.setAttribute('data-log_id', log.log_id);
  } else {
    const room_container = document.querySelector(`.js-room__container[data-room_id="${log.room_id}"]`);
    if (room_container) {
      const components_div = room_container.querySelector('.c-room__components');

      if (components_div) {
        const svg_path = svg_icons[log.component_id] || 'img/svg/circuitry.svg';
        components_div.innerHTML += `
          <article class="c-article c-hover--shadow js-component__container" data-component_id="${log.component_id}" data-room_id="${log.room_id}" data-log_id="${log.log_id}">
            <div class="c-article__header">
              <a href="#" class="c-article__link">
                <img src="${svg_path}" alt="Component icon" class="c-article__icon">
              </a>
              <h2 class="c-article__title">${log.component_name}</h2>
            </div>
            <div class="c-card">
              <h3 class="c-card__level">${log.value} ${log.value_unit}</h3>
              <div class="c-card__meta">
                <p class="c-card__status">Last log</p>
                <p class="c-card__capacity">${formatDateTime(formatted_date)}</p>
              </div>
            </div>
          </article>
        `;
        const new_log_container = components_div.querySelector(`.js-component__container[data-component_id="${log.component_id}"]`);
        if (new_log_container) {
          if (parseInt(log.room_id) % 2 === 0) {
            new_log_container.classList.add('c-white-background');
          } else {
            new_log_container.classList.add('c-grey-background');
          }
        } else {
          console.log(`Newly added component with ID ${log.component_id} not found`);
        }
      } else {
        console.log(`Components div not found in room ${log.room_id}`);
      }
    } else {
      console.log(`Room container for ID ${log.room_id} not found`);
    }
  }
};

// #endregion

// #region ***  Callback-No Visualisation - callback___  ***********
const formatDateTime = (isoString) => {
  const date = new Date(isoString);
  return date.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
};
// #endregion

// #region ***  Data Access - get___                     ***********
const getAllLastItems = async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const urlParam = urlParams.get('param');
  let url = ENDPOINT + `/components/last/${urlParam}/`;
  let response = await fetch(url).catch((err) => console.error('Fetch-error:', err));
  const json = await response.json().catch((err) => console.error('JSON-error:', err));
  showAllLastLogs(json);
};
// #endregion

// #region ***  Event Listeners - listenTo___            ***********

const listenToSocket = () => {
  sio.on('connect', () => {
    console.log('Socket connected');
  });
  sio.on('disconnect', () => {
    console.log('Socket disconnected');
  });
  sio.on('error', (error) => {
    console.log('Socket error:', error);
  });
  sio.on('B2F_new_log', (data) => {
    showLastLog(data);
  });
};
// #endregion

// #region ***  Init / DOMContentLoaded                  ***********
const init = () => {
  console.log('DOM loaded');
  getAllLastItems();
  listenToSocket();
};

document.addEventListener('DOMContentLoaded', init);
// #endregion

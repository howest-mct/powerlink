'use strict';
const lanIP = `http://192.168.168.169:8000`;
const socketio = io(lanIP);
const ENDPOINT = 'http://192.168.168.169:8000/api/v1';

// #region ***  DOM references                           ***********
// #endregion

// #region ***  Callback-Visualisation - show___         ***********

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
  let room_display_number = 0;

  for (const room_id in roomSchedules) {
    const room_data = roomSchedules[room_id];
    const room_name = room_data[0].room_name;

    let htmlSchedules = '';
    htmlRooms += `
      <div class="c-room__container js-room__container" data-room_id="${room_id}" data-display_number="${room_display_number}">
        <section class="c-room">
          <h2 class="c-section__title">${room_name}</h2>
          <div class="c-schedules__container">
    `;

    for (const schedule of room_data) {
    }

    htmlRooms += htmlSchedules;
    htmlRooms += `
          </div>
        </section>
      </div>`;

    room_display_number++;
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
  });
};

// #endregion

// #region ***  Callback-No Visualisation - callback___  ***********
// #endregion

// #region ***  Data Access - get___                     ***********
const getAllItems = async () => {};

const getSInsights = async () => {
  const url = ENDPOINT + `/energy/2/24h/`;
  const response = await fetch(url).catch((err) => console.error('Fetch-error:', err));
  const json = await response.json().catch((err) => console.error('JSON-error:', err));
  console.log('JSON:', json);
};

// #endregion

// #region ***  Event Listeners - listenTo___            ***********
// #endregion

// #region ***  Init / DOMContentLoaded                  ***********
const init = () => {
  showDropdown();
  getAllItems();
  getInsights();
};

document.addEventListener('DOMContentLoaded', init);
// #endregion

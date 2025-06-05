'use strict';
const lanIP = `http://192.168.168.169:8000`;
const sio = io(lanIP);
const ENDPOINT = 'http://192.168.168.169:8000/api/v1';

// #region ***  DOM references                           ***********
// #endregion

// #region ***  Callback-Visualisation - show___         ***********

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
      const { log_id, datetime, value, component_id, component_name, value_unit, room_id, room_name } = item;
      htmlComponents += `
        <article class="c-article c-hover--shadow js-component__container" data-component_id="${component_id}" data-room_id="${room_id}">
          <h2 class="c-article__title">${component_name}</h2>
          <div class="c-card">
            <h3 class="c-card__level">${value} ${value_unit}</h3>
            <div class="c-card__meta">
              <p class="c-card__status">Room</p>
              <p class="c-card__capacity">${room_name}</p>
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

const showLastLog = (components) => {};

// #endregion

// #region ***  Callback-No Visualisation - callback___  ***********
// #endregion

// #region ***  Data Access - get___                     ***********
const getAllLastItems = async () => {
  let url = ENDPOINT + `/logs/last/`;
  let response = await fetch(url).catch((err) => console.error('Fetch-error:', err));
  const json = await response.json().catch((err) => console.error('JSON-error:', err));
  showAllLastLogs(json);
};
// #endregion

// #region ***  Event Listeners - listenTo___            ***********

const listenToSocket = () => {
  sio.on('connect', () => {
    console.info('Socket connected');
  });
  sio.on('disconnect', () => {
    console.info('Socket disconnected');
  });
  sio.on('error', (error) => {
    console.error('Socket error:', error);
  });
  sio.on('BF2_logs', (data) => {
    console.info('Socket event BF2_logs received:', data);
    showLastLog(data);
  });
};
// #endregion

// #region ***  Init / DOMContentLoaded                  ***********
const init = () => {
  console.info('DOM loaded');
  getAllLastItems();
  listenToSocket();
};

document.addEventListener('DOMContentLoaded', init);
// #endregion

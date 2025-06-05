'use strict';
const lanIP = `http://192.168.168.169:8000`;
const socketio = io(lanIP);
const ENDPOINT = 'http://192.168.168.169:8000/api/v1';

// #region ***  DOM references                           ***********
// #endregion

// #region ***  Callback-Visualisation - show___         ***********

const showAllLastLogs = (items) => {
  let htmlRooms = '';
  const roomsContainer = document.querySelector('.js-main');

  let roomSchedules = {};
  for (const item of items) {
    const room_id = item.room_id;
    if (!roomSchedules[room_id]) {
      roomSchedules[room_id] = [];
    }
    roomSchedules[room_id].push(item);
  }

  for (const room_id in roomSchedules) {
    const room_data = roomSchedules[room_id];
    const room_name = room_data[0].room_name;

    let htmlString = '';
    htmlString += `
      <div class="c-room__container">
        <section class="c-room lighting-upper">
            <h1 class="c-section__title">Sensors & Actuators</h1>
            <div class="c-room__content js-room__content">
            `;

    for (const item of room_data) {
      const { log_id, datetime, value, component_id, component_name, value_unit, room_name } = item;
      htmlString += `
        <article class="c-article__battery c-white-background c-hover--shadow">
            <h2 class="c-article__title">${component_name}</h2>
            <div class="c-battery">
                <h3 class="c-battery__level">${value} ${value_unit}</h3>
                <div class="c-battery__meta">
                    <p class="c-battery__status">Room</p>
                    <p class="c-battery__capacity">${room_name}</p>
                </div>
            </div>
        </article>
      `;
    }

    htmlString += `
            </div>
        </section>
      </div>
    `;
  }
  roomsContainer.innerHTML = htmlRooms;
};

// #endregion

// #region ***  Callback-No Visualisation - callback___  ***********
// #endregion

// #region ***  Data Access - get___                     ***********
const getAllLastItems = async () => {
  const url = ENDPOINT + '/logs/last/';
  const response = await fetch(url).catch((err) => console.error('Fetch-error:', err));
  const json = await response.json().catch((err) => console.error('JSON-error:', err));
  showAllLastLogs(json);
};
// #endregion

// #region ***  Event Listeners - listenTo___            ***********
// #endregion

// #region ***  Init / DOMContentLoaded                  ***********
const init = () => {
  console.info('DOM loaded');
  getAllLastItems();
};

document.addEventListener('DOMContentLoaded', init);
// #endregion

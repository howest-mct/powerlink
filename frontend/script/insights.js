'use strict';
const lanIP = `http://192.168.168.169:8000`;
const socketio = io(lanIP);
const ENDPOINT = 'http://192.168.168.169:8000/api/v1';

// #region ***  DOM references                           ***********
// #endregion

// #region ***  Callback-Visualisation - show___         ***********

const showAllLastLogs = (logs) => {
  let htmlString = '';
  const room_content = document.querySelector('.js-room__content');
  for (const log of logs) {
    const { log_id, datetime, value, component_id, component_name, value_unit, room_name } = log;
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
  room_content.innerHTML = htmlString;
};

// #endregion

// #region ***  Callback-No Visualisation - callback___  ***********
// #endregion

// #region ***  Data Access - get___                     ***********
const getAllLastLogs = async () => {
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
  getAllLastLogs();
};

document.addEventListener('DOMContentLoaded', init);
// #endregion

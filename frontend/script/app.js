'use strict';
const lanIP = `http://${window.location.hostname}:8000`;
const socketio = io(lanIP);
const API = 'http://127.0.0.1:8000/api/v1';

const init = () => {
  console.info('DOM loaded');
  if (document.querySelector('.js-home')) {
  } else if (document.querySelector('.js-schedules')) {
  } else if (document.querySelector('.js-insights')) {
  } else if (document.querySelector('.js-components')) {
  } else {
  }
};
document.addEventListener('DOMContentLoaded', init);

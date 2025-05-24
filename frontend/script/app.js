'use strict';
const lanIP = `http://${window.location.hostname}:8000`;
const socketio = io(lanIP);
const API = 'http://127.0.0.1:8000/api/v1';

const init = () => {
  console.info('DOM loaded');
};

document.addEventListener('DOMContentLoaded', init);

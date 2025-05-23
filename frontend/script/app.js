'use strict';

const lanIP = `${window.location.hostname}:8000`;
const socketio = io(lanIP);

const clearClassList = (el) => {
  el.classList.remove('c-room--wait');
  el.classList.remove('c-room--on');
};

const getPatchNewStatus = async (id, new_status) => {
  console.log('id:', id, 'new_status:', new_status);

  const url = `http://${lanIP}/api/v1/lampen/${id}/status/`;
  console.log('url:', url);

  const body = JSON.stringify({
    nieuwe_status: new_status,
  });
  const response = await fetch(url, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: body,
  });

  if (!response.ok) {
    console.error('Error:', response.statusText);
    return;
  }
  console.log('response:', response);
  const json = await response.json().catch((err) => console.error('JSON-error:', err));
  console.log('response:', json);
};

const listenToUI = () => {
  const knoppen = document.querySelectorAll('.js-power-btn');
  for (const knop of knoppen) {
    knop.addEventListener('click', () => {
      const id = parseInt(knop.dataset.idlamp);
      console.log('id:', knop.dataset.statuslamp);
      let nieuweStatus;
      if (knop.dataset.statuslamp == 0) {
        nieuweStatus = 1;
      } else {
        nieuweStatus = 0;
      }
      clearClassList(document.querySelector(`.js-room[data-idlamp="${id}"]`));
      document.querySelector(`.js-room[data-idlamp="${id}"]`).classList.add('c-room--wait');
      getPatchNewStatus(id, nieuweStatus);
    });
  }
};

const listenToSocket = () => {
  socketio.on('connect', () => {
    console.log('verbonden met socket webserver');
  });

  //in stap 2
  socketio.on('B2F_alles_uit', (json) => {
    console.log('alle lampen zijn automatisch uitgezet, maar je ziet het niet');
  });

  socketio.on('B2F_status_lampen', (jsonObject) => {
    console.log('Dit is de status van de lampen');
    console.log(jsonObject);
    for (const lamp of jsonObject.lampen) {
      const room = document.querySelector(`.js-room[data-idlamp="${lamp.id}"]`);
      if (room) {
        const knop = room.querySelector('.js-power-btn');
        knop.dataset.statuslamp = lamp.status;
        clearClassList(room);
        if (lamp.status == 1) {
          room.classList.add('c-room--on');
        }
      }
    }
  });

  socketio.on('B2F_verandering_lamp', (jsonObject) => {
    console.log('Er is een status van een lamp veranderd');
    console.log(jsonObject.lamp.id);
    console.log(jsonObject.lamp.status);

    const room = document.querySelector(`.js-room[data-idlamp="${jsonObject.lamp.id}"]`);
    if (room) {
      const knop = room.querySelector('.js-power-btn'); //spreek de room, als start. Zodat je enkel knop krijgt die in de room staat
      knop.dataset.statuslamp = jsonObject.lamp.status;

      clearClassList(room);
      if (jsonObject.lamp.status == 1) {
        room.classList.add('c-room--on');
      }
    }
  });
};

const init = () => {
  console.info('DOM geladen');
  listenToUI();
  listenToSocket();
};

document.addEventListener('DOMContentLoaded', init);

'use strict';

const lan_ip = `http://${window.location.hostname}:8000`;
const api_endpoint = `http://${window.location.hostname}:8000/api/v1`;

// #region ***  DOM references                           ***********
let inhabitants = [];
let editing_inhabitant = null;
// #endregion

// #region ***  HTML Generation Functions               ***********
const createInhabitantRow = (inhabitant) => {
  const row = document.createElement('tr');
  row.className = 'c-table__row';

  row.innerHTML = `
    <td class="c-table__cell">${inhabitant.first_name}</td>
    <td class="c-table__cell">${inhabitant.last_name}</td>
    <td class="c-table__cell">${inhabitant.card_id}</td>
    <td class="c-table__cell c-table__cell--actions">
      <button class="c-table__button c-table__button--edit" 
              data-inhabitant-id="${inhabitant.inhabitant_id}">
        Edit
      </button>
      <button class="c-table__button c-table__button--delete" 
              data-inhabitant-id="${inhabitant.inhabitant_id}">
        Delete
      </button>
    </td>
  `;

  return row;
};
// #endregion

// #region ***  Display Functions                       ***********
const renderInhabitantsTable = () => {
  const tbody = document.querySelector('.c-table tbody');
  tbody.innerHTML = '';

  if (inhabitants.length === 0) {
    tbody.innerHTML = `
      <tr class="c-table__row">
        <td colspan="4" class="c-table__cell" style="text-align: center; padding: 2rem;">
          No family members found.
        </td>
      </tr>
    `;
    return;
  }

  for (let i = 0; i < inhabitants.length; i++) {
    const inhabitant = inhabitants[i];
    const row = createInhabitantRow(inhabitant);
    tbody.appendChild(row);
  }

  setupTableButtons();
};
// #endregion

// #region ***  Data Access Functions                   ***********
const loadInhabitants = async () => {
  const request_url = api_endpoint + '/inhabitants/';

  const server_response = await fetch(request_url).catch((error) => console.error('Fetch-error:', error));
  const json_data = await server_response.json().catch((error) => console.error('JSON-error:', error));

  inhabitants = json_data;
  renderInhabitantsTable();
};

const createInhabitant = async (data) => {
  const request_url = api_endpoint + '/inhabitants/';

  await fetch(request_url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }).catch((error) => console.error('Fetch-error:', error));

  await loadInhabitants();
  resetForm();
};

const updateInhabitant = async (inhabitant_id, data) => {
  const request_url = api_endpoint + `/inhabitants/${inhabitant_id}/`;

  await fetch(request_url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }).catch((error) => console.error('Fetch-error:', error));

  await loadInhabitants();
  resetForm();
};

const deleteInhabitant = async (inhabitant_id) => {
  const request_url = api_endpoint + `/inhabitants/${inhabitant_id}/`;

  await fetch(request_url, {
    method: 'DELETE',
  }).catch((error) => console.error('Fetch-error:', error));

  await loadInhabitants();
};
// #endregion

// #region ***  Event Handler Functions                 ***********
const handleFormSubmit = async (event) => {
  event.preventDefault();

  const form_data = {
    first_name: document.getElementById('fname').value,
    last_name: document.getElementById('lname').value,
    card_id: document.getElementById('card_id').value,
  };

  if (editing_inhabitant) {
    await updateInhabitant(editing_inhabitant.inhabitant_id, form_data);
  } else {
    await createInhabitant(form_data);
  }
};

const handleEditClick = (click_event) => {
  const clicked_button = click_event.target;
  const inhabitant_id = parseInt(clicked_button.dataset.inhabitantId);

  const inhabitant = inhabitants.find((i) => i.inhabitant_id === inhabitant_id);

  editing_inhabitant = inhabitant;

  document.getElementById('fname').value = inhabitant.first_name;
  document.getElementById('lname').value = inhabitant.last_name;
  document.getElementById('card_id').value = inhabitant.card_id;

  document.querySelector('.c-form__submit').value = 'Update Family Member';
};

const handleDeleteClick = async (click_event) => {
  const clicked_button = click_event.target;
  const inhabitant_id = parseInt(clicked_button.dataset.inhabitantId);

  const inhabitant = inhabitants.find((i) => i.inhabitant_id === inhabitant_id);

  if (confirm(`Delete ${inhabitant.first_name} ${inhabitant.last_name}?`)) {
    await deleteInhabitant(inhabitant_id);
  }
};
// #endregion

// #region ***  Setup Functions                         ***********
const setupFormHandler = () => {
  const form = document.querySelector('.c-form');
  form.addEventListener('submit', handleFormSubmit);
};

const setupTableButtons = () => {
  const edit_buttons = document.querySelectorAll('.c-table__button--edit');
  const delete_buttons = document.querySelectorAll('.c-table__button--delete');

  for (let i = 0; i < edit_buttons.length; i++) {
    const edit_button = edit_buttons[i];
    edit_button.removeEventListener('click', handleEditClick);
    edit_button.addEventListener('click', handleEditClick);
  }

  for (let i = 0; i < delete_buttons.length; i++) {
    const delete_button = delete_buttons[i];
    delete_button.removeEventListener('click', handleDeleteClick);
    delete_button.addEventListener('click', handleDeleteClick);
  }
};

const resetForm = () => {
  document.querySelector('.c-form').reset();
  editing_inhabitant = null;
  document.querySelector('.c-form__submit').value = 'Add Family Member';
};
// #endregion

// #region ***  Init Functions                          ***********
const init = () => {
  console.log('DOM loaded');
  setupFormHandler();
  loadInhabitants();
};

document.addEventListener('DOMContentLoaded', init);
// #endregion

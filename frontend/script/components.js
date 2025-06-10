'use strict';
const lan_ip = `http://192.168.168.169:8000`;
const socket_connection = io(lan_ip);
const api_endpoint = 'http://192.168.168.169:8000/api/v1';

// #region ***  DOM references                           ***********
const component_icons = {
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

// #region ***  Dropdown Functions                      ***********
const createComponentDropdown = (room_id, all_components, components_in_current_frame) => {
  let dropdown_options_html = '<div class="dropdown-option check-all-option" data-room="' + room_id + '">Check All</div>';

  const frame_component_ids = new Set(components_in_current_frame.map((component) => component.component_id));

  all_components.forEach((component) => {
    const is_component_checked = frame_component_ids.has(component.component_id) ? 'checked' : '';
    dropdown_options_html += `
      <div class="dropdown-option checkbox-option">
        <label>
          <input type="checkbox" value="${component.component_id}" data-room="${room_id}" data-name="${component.component_name}" ${is_component_checked}>
          ${component.component_name}
        </label>
      </div>
    `;
  });

  return `
    <div class="component-dropdown" data-room="${room_id}">
      <div class="dropdown-trigger">Select Components</div>
      <div class="dropdown-menu">
        ${dropdown_options_html}
      </div>
    </div>
  `;
};

const initDropdownEvents = () => {
  document.addEventListener('click', (event) => {
    if (event.target.classList.contains('dropdown-trigger')) {
      event.stopPropagation();
      const clicked_dropdown = event.target.closest('.component-dropdown');
      const dropdown_menu = clicked_dropdown.querySelector('.dropdown-menu');

      document.querySelectorAll('.dropdown-menu').forEach((menu) => {
        if (menu !== dropdown_menu) menu.style.display = 'none';
      });

      dropdown_menu.style.display = dropdown_menu.style.display === 'block' ? 'none' : 'block';
    }

    if (event.target.classList.contains('check-all-option')) {
      event.stopPropagation();
      const room_id = event.target.dataset.room;
      const clicked_dropdown = event.target.closest('.component-dropdown');
      const all_checkboxes = clicked_dropdown.querySelectorAll('input[type="checkbox"]');
      const all_boxes_checked = Array.from(all_checkboxes).every((checkbox) => checkbox.checked);

      all_checkboxes.forEach((checkbox) => {
        if (all_boxes_checked) {
          checkbox.checked = false;
        } else {
          checkbox.checked = true;
        }
        emitComponentSelection(checkbox);
      });

      updateDropdownLabel(clicked_dropdown);
      event.target.textContent = all_boxes_checked ? 'Check All' : 'Uncheck All';
    }

    if (event.target.type === 'checkbox' && event.target.dataset.room) {
      emitComponentSelection(event.target);
      const parent_dropdown = event.target.closest('.component-dropdown');
      updateDropdownLabel(parent_dropdown);
      updateCheckAllButton(parent_dropdown);
    }

    if (!event.target.closest('.component-dropdown')) {
      document.querySelectorAll('.dropdown-menu').forEach((menu) => {
        menu.style.display = 'none';
      });
    }
  });
};

const updateDropdownLabel = (dropdown_element) => {
  const trigger_button = dropdown_element.querySelector('.dropdown-trigger');
  const all_checkboxes = dropdown_element.querySelectorAll('input[type="checkbox"]');
  const checked_checkboxes = dropdown_element.querySelectorAll('input[type="checkbox"]:checked');

  if (checked_checkboxes.length === 0) {
    trigger_button.textContent = 'Select Components';
  } else if (checked_checkboxes.length === 1) {
    trigger_button.textContent = checked_checkboxes[0].dataset.name;
  } else if (checked_checkboxes.length === all_checkboxes.length) {
    trigger_button.textContent = 'All Components Selected';
  } else {
    trigger_button.textContent = `${checked_checkboxes.length} Components Selected`;
  }
};

const updateCheckAllButton = (dropdown_element) => {
  const check_all_button = dropdown_element.querySelector('.check-all-option');
  const all_checkboxes = dropdown_element.querySelectorAll('input[type="checkbox"]');
  const checked_checkboxes = dropdown_element.querySelectorAll('input[type="checkbox"]:checked');

  if (checked_checkboxes.length === all_checkboxes.length && all_checkboxes.length > 0) {
    check_all_button.textContent = 'Uncheck All';
  } else {
    check_all_button.textContent = 'Check All';
  }
};

const emitComponentSelection = async (checkbox_element) => {
  const component_id = parseInt(checkbox_element.value);
  const room_id = parseInt(checkbox_element.dataset.room);
  const is_checkbox_checked = checkbox_element.checked;

  console.log(`Component ${component_id} in room ${room_id} ${is_checkbox_checked ? 'selected' : 'deselected'}`);

  const update_was_successful = await updateComponentInFrame(component_id, is_checkbox_checked);

  if (update_was_successful) {
    socket_connection.emit('BF2_component_selection', {
      component_id: component_id,
      room_id: room_id,
      selected: is_checkbox_checked,
    });

    let component_card = document.querySelector(`.js-component__container[data-component_id="${component_id}"]`);

    if (is_checkbox_checked) {
      if (component_card) {
        component_card.style.display = 'block';
      } else {
        await createComponentCard(component_id, room_id);
      }
    } else {
      if (component_card) {
        component_card.style.display = 'none';
      }
    }
  }
};

const createComponentCard = async (component_id, room_id) => {
  try {
    const url_parameters = new URLSearchParams(window.location.search);
    const frame_parameter = parseInt(url_parameters.get('frame'));

    const log_url = api_endpoint + `/components/last/${frame_parameter}/`;
    const log_response = await fetch(log_url);
    const all_component_logs = await log_response.json();

    const component_log = all_component_logs.find((log) => log.component_id === component_id);

    if (!component_log) {
      console.log(`No log found for component ${component_id}`);
      return;
    }

    const components_url = api_endpoint + `/components/`;
    const components_response = await fetch(components_url);
    const all_components = await components_response.json();

    const component_details = all_components.find((comp) => comp.component_id === component_id);

    if (!component_details) {
      console.log(`Component ${component_id} not found`);
      return;
    }

    const formatted_date = new Date(component_log.datetime);
    const icon_path = component_icons[component_id] || 'img/svg/circuitry.svg';

    const component_card_html = `
      <article class="c-article c-hover--shadow js-component__container" data-component_id="${component_id}" data-room_id="${room_id}" data-log_id="${component_log.log_id}">
        <div class="c-article__header">
          <a href="#" class="c-article__link">
            <img src="${icon_path}" alt="Component icon" class="c-article__icon">
          </a>
          <h2 class="c-article__title">${component_details.component_name}</h2>
        </div>
        <div class="c-card">
          <h3 class="c-card__level">${component_log.value} ${component_details.value_unit}</h3>
          <div class="c-card__meta">
            <p class="c-card__status">Last log</p>
            <p class="c-card__capacity">${formatDateTime(formatted_date)}</p>
          </div>
        </div>
      </article>
    `;

    const room_container = document.querySelector(`.js-room__container[data-room_id="${room_id}"]`);
    if (room_container) {
      const components_container = room_container.querySelector('.c-room__components');
      if (components_container) {
        components_container.insertAdjacentHTML('beforeend', component_card_html);

        const new_component_card = components_container.querySelector(`.js-component__container[data-component_id="${component_id}"]`);
        if (new_component_card) {
          const room_number = parseInt(room_container.dataset.room_number);
          if (room_number % 2 === 0) {
            new_component_card.classList.add('c-white-background');
          } else {
            new_component_card.classList.add('c-grey-background');
          }
        }
      }
    }
  } catch (error) {
    console.error('Error creating component card:', error);
  }
};
// #endregion

// #region ***  Callback-Visualisation - show___         ***********
const showDropdown = () => {
  const hamburger_button = document.querySelector('.c-hamburger');
  const navigation_popup = document.querySelector('.c-nav-popup');
  const page_overlay = document.querySelector('.c-overlay');
  const close_button = document.querySelector('.c-nav-popup__close');

  if (!hamburger_button || !navigation_popup || !page_overlay || !close_button) {
    console.error('Dropdown elements not found');
    return;
  }

  const toggleMobileMenu = () => {
    const menu_is_active = navigation_popup.classList.toggle('c-nav-popup--active');
    page_overlay.classList.toggle('c-overlay--active');
    hamburger_button.setAttribute('aria-expanded', menu_is_active);
    navigation_popup.setAttribute('aria-hidden', !menu_is_active);
    page_overlay.setAttribute('aria-hidden', !menu_is_active);
  };

  if (window.matchMedia('(max-width: 767px)').matches) {
    hamburger_button.addEventListener('click', (event) => {
      event.stopPropagation();
      toggleMobileMenu();
    });

    close_button.addEventListener('click', (event) => {
      event.stopPropagation();
      navigation_popup.classList.remove('c-nav-popup--active');
      page_overlay.classList.remove('c-overlay--active');
      hamburger_button.setAttribute('aria-expanded', 'false');
      navigation_popup.setAttribute('aria-hidden', 'true');
      page_overlay.setAttribute('aria-hidden', 'true');
    });

    page_overlay.addEventListener('click', () => {
      navigation_popup.classList.remove('c-nav-popup--active');
      page_overlay.classList.remove('c-overlay--active');
      hamburger_button.setAttribute('aria-expanded', 'false');
      navigation_popup.setAttribute('aria-hidden', 'true');
      page_overlay.setAttribute('aria-hidden', 'true');
    });

    const navigation_links = document.querySelectorAll('.c-nav-popup__link');
    navigation_links.forEach((link) => {
      link.addEventListener('click', () => {
        navigation_popup.classList.remove('c-nav-popup--active');
        page_overlay.classList.remove('c-overlay--active');
        hamburger_button.setAttribute('aria-expanded', 'false');
        navigation_popup.setAttribute('aria-hidden', 'true');
        page_overlay.setAttribute('aria-hidden', 'true');
      });
    });

    document.addEventListener('click', (event) => {
      if (!navigation_popup.contains(event.target) && !hamburger_button.contains(event.target)) {
        navigation_popup.classList.remove('c-nav-popup--active');
        page_overlay.classList.remove('c-overlay--active');
        hamburger_button.setAttribute('aria-expanded', 'false');
        navigation_popup.setAttribute('aria-hidden', 'true');
        page_overlay.setAttribute('aria-hidden', 'true');
      }
    });
  }

  window.addEventListener('resize', () => {
    if (window.matchMedia('(min-width: 768px)').matches) {
      navigation_popup.classList.remove('c-nav-popup--active');
      page_overlay.classList.remove('c-overlay--active');
      hamburger_button.setAttribute('aria-expanded', 'false');
      navigation_popup.setAttribute('aria-hidden', 'true');
      page_overlay.setAttribute('aria-hidden', 'true');
    }
  });
};

const showAllRoomsAndComponents = async () => {
  try {
    const [all_rooms, all_components, all_component_logs, components_in_frame] = await Promise.all([getAllRooms(), getAllComponents(), getLastComponentLogs(), getComponentsInFrame()]);

    console.log('Rooms:', all_rooms);
    console.log('Components:', all_components);
    console.log('Component logs:', all_component_logs);
    console.log('Components in frame:', components_in_frame);

    const components_grouped_by_room = {};
    const logs_by_component_id = {};
    const frame_component_ids = new Set(components_in_frame.map((component) => component.component_id));

    all_components.forEach((component) => {
      if (!components_grouped_by_room[component.room_id]) {
        components_grouped_by_room[component.room_id] = [];
      }
      components_grouped_by_room[component.room_id].push(component);
    });

    all_component_logs.forEach((log) => {
      logs_by_component_id[log.component_id] = log;
    });

    let rooms_html = '';
    const main_container = document.querySelector('.js-main');

    all_rooms.forEach((room, room_index) => {
      const room_components = components_grouped_by_room[room.room_id] || [];

      let components_html = '';

      room_components.forEach((component) => {
        const component_is_in_frame = frame_component_ids.has(component.component_id);
        const component_log = logs_by_component_id[component.component_id];

        if (component_is_in_frame && component_log) {
          const formatted_date = new Date(component_log.datetime);
          const icon_path = component_icons[component.component_id] || 'img/svg/circuitry.svg';

          components_html += `
            <article class="c-article c-hover--shadow js-component__container" data-component_id="${component.component_id}" data-room_id="${room.room_id}" data-log_id="${component_log.log_id}">
              <div class="c-article__header">
                <a href="#" class="c-article__link">
                  <img src="${icon_path}" alt="Component icon" class="c-article__icon">
                </a>
                <h2 class="c-article__title">${component.component_name}</h2>
              </div>
              <div class="c-card">
                <h3 class="c-card__level">${component_log.value} ${component.value_unit}</h3>
                <div class="c-card__meta">
                  <p class="c-card__status">Last log</p>
                  <p class="c-card__capacity">${formatDateTime(formatted_date)}</p>
                </div>
              </div>
            </article>
          `;
        }
      });

      const dropdown_html = createComponentDropdown(room.room_id, room_components, components_in_frame);

      rooms_html += `
        <div class="c-room__container js-room__container" data-room_id="${room.room_id}" data-room_name="${room.room_name}" data-room_number="${room_index}">
          <section class="c-room">
            <div class="c-room__header">
              <h2 class="c-section__title">${room.room_name}</h2>
              ${dropdown_html}
            </div>
            <div class="c-room__components">
              ${components_html}
            </div>
          </section>
        </div>
      `;
    });

    main_container.innerHTML = rooms_html;

    const all_room_containers = document.querySelectorAll('.js-room__container');
    all_room_containers.forEach((room_container) => {
      const room_number = parseInt(room_container.dataset.room_number);
      const component_containers = room_container.querySelectorAll('.js-component__container');

      if (room_number % 2 === 0) {
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

    initDropdownEvents();
    updateAllDropdownLabels();
  } catch (error) {
    console.error('Error loading rooms and components:', error);
  }
};

const updateAllDropdownLabels = () => {
  document.querySelectorAll('.component-dropdown').forEach((dropdown) => {
    updateDropdownLabel(dropdown);
    updateCheckAllButton(dropdown);
  });
};

const showAllLastLogs = (json_data) => {
  let rooms_html = '';
  const main_container = document.querySelector('.js-main');

  let room_components = {};
  for (const schedule_item of json_data) {
    const room_id = schedule_item.room_id;
    if (!room_components[room_id]) {
      room_components[room_id] = [];
    }
    room_components[room_id].push(schedule_item);
  }

  let room_display_number = 0;

  for (const room_id in room_components) {
    const room_data = room_components[room_id];
    const room_name = room_data[0].room_name;

    let components_html = '';

    for (const item of room_data) {
      const { log_id, datetime, value, component_id, component_name, value_unit, room_id } = item;
      const formatted_date = new Date(datetime);
      const icon_path = component_icons[component_id] || 'img/svg/circuitry.svg';

      components_html += `
        <article class="c-article c-hover--shadow js-component__container" data-component_id="${component_id}" data-room_id="${room_id}" data-log_id="${log_id}">
          <div class="c-article__header">
            <a href="#" class="c-article__link">
              <img src="${icon_path}" alt="Component icon" class="c-article__icon">
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

    const dropdown_html = createComponentDropdown(room_id, room_data);

    rooms_html += `
      <div class="c-room__container js-room__container" data-room_id="${room_id}" data-room_name="${room_name}" data-room_number="${room_display_number}">
        <section class="c-room">
          <div class="c-room__header">
            <h2 class="c-section__title">${room_name}</h2>
            ${dropdown_html}
          </div>
          <div class="c-room__components">
            ${components_html}
          </div>
        </section>
      </div>
    `;

    room_display_number++;
  }

  main_container.innerHTML = rooms_html;

  const all_room_containers = document.querySelectorAll('.js-room__container');
  all_room_containers.forEach((room_container) => {
    const room_number = parseInt(room_container.dataset.room_number);
    const component_containers = room_container.querySelectorAll('.js-component__container');

    if (room_number % 2 === 0) {
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

  initDropdownEvents();
};

const showLastLog = (log_data) => {
  let existing_log_container = document.querySelector(`.js-component__container[data-component_id="${log_data.component_id}"]`);
  const formatted_date = new Date(log_data.datetime);

  if (existing_log_container) {
    const level_element = existing_log_container.querySelector('.c-card__level');
    const capacity_element = existing_log_container.querySelector('.c-card__capacity');

    if (level_element) {
      level_element.textContent = `${log_data.value} ${log_data.value_unit}`;
    }

    if (capacity_element) {
      capacity_element.textContent = formatDateTime(formatted_date);
    }

    existing_log_container.setAttribute('data-log_id', log_data.log_id);
  } else {
    const room_container = document.querySelector(`.js-room__container[data-room_id="${log_data.room_id}"]`);
    if (room_container) {
      const components_container = room_container.querySelector('.c-room__components');
      const dropdown_element = room_container.querySelector('.component-dropdown');

      if (components_container) {
        const icon_path = component_icons[log_data.component_id] || 'img/svg/circuitry.svg';
        components_container.innerHTML += `
          <article class="c-article c-hover--shadow js-component__container" data-component_id="${log_data.component_id}" data-room_id="${log_data.room_id}" data-log_id="${log_data.log_id}">
            <div class="c-article__header">
              <a href="#" class="c-article__link">
                <img src="${icon_path}" alt="Component icon" class="c-article__icon">
              </a>
              <h2 class="c-article__title">${log_data.component_name}</h2>
            </div>
            <div class="c-card">
              <h3 class="c-card__level">${log_data.value} ${log_data.value_unit}</h3>
              <div class="c-card__meta">
                <p class="c-card__status">Last log</p>
                <p class="c-card__capacity">${formatDateTime(formatted_date)}</p>
              </div>
            </div>
          </article>
        `;

        if (dropdown_element) {
          const existing_checkbox = dropdown_element.querySelector(`input[value="${log_data.component_id}"]`);
          if (!existing_checkbox) {
            const dropdown_menu = dropdown_element.querySelector('.dropdown-menu');
            const new_option = document.createElement('div');
            new_option.className = 'dropdown-option checkbox-option';
            new_option.innerHTML = `
              <label>
                <input type="checkbox" value="${log_data.component_id}" data-room="${log_data.room_id}" data-name="${log_data.component_name}">
                ${log_data.component_name}
              </label>
            `;
            dropdown_menu.appendChild(new_option);
          }
        }

        const new_log_container = components_container.querySelector(`.js-component__container[data-component_id="${log_data.component_id}"]`);
        if (new_log_container) {
          if (parseInt(log_data.room_id) % 2 === 0) {
            new_log_container.classList.add('c-white-background');
          } else {
            new_log_container.classList.add('c-grey-background');
          }
        }
      }
    }
  }
};
// #endregion

// #region ***  Callback-No Visualisation - callback___  ***********
const formatDateTime = (iso_string) => {
  const date_object = new Date(iso_string);
  return date_object.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
};
// #endregion

// #region ***  Data Access - get___                     ***********
const getLastComponentLogs = async () => {
  const url_parameters = new URLSearchParams(window.location.search);
  const frame_url_param = parseInt(url_parameters.get('frame'));
  let request_url = api_endpoint + `/components/last/${frame_url_param}/`;
  let server_response = await fetch(request_url).catch((error) => console.error('Fetch-error:', error));
  const json_data = await server_response.json().catch((error) => console.error('JSON-error:', error));
  return json_data;
};

const getAllComponents = async () => {
  const request_url = api_endpoint + `/components/`;
  const server_response = await fetch(request_url).catch((error) => console.error('Fetch-error:', error));
  const json_data = await server_response.json().catch((error) => console.error('JSON-error:', error));
  return json_data;
};

const getAllRooms = async () => {
  const request_url = api_endpoint + `/rooms/`;
  const server_response = await fetch(request_url).catch((error) => console.error('Fetch-error:', error));
  const json_data = await server_response.json().catch((error) => console.error('JSON-error:', error));
  return json_data;
};

const getComponentsInFrame = async () => {
  const url_parameters = new URLSearchParams(window.location.search);
  const frame_id = parseInt(url_parameters.get('frame'));
  const request_url = api_endpoint + `/frames/${frame_id}/components/`;
  const server_response = await fetch(request_url).catch((error) => console.error('Fetch-error:', error));
  const json_data = await server_response.json().catch((error) => console.error('JSON-error:', error));
  return json_data;
};

const updateComponentInFrame = async (component_id, is_component_selected) => {
  const url_parameters = new URLSearchParams(window.location.search);
  const frame_id = parseInt(url_parameters.get('frame'));

  try {
    if (is_component_selected) {
      const request_url = api_endpoint + `/frames/${frame_id}/components/`;
      const server_response = await fetch(request_url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          component_id: component_id,
          frame_id: frame_id,
        }),
      });

      if (!server_response.ok) {
        if (server_response.status === 409) {
          console.log(`Component ${component_id} already in frame ${frame_id} - no action needed`);
          return true;
        }
        throw new Error(`Failed to add component to frame: ${server_response.statusText}`);
      }

      console.log(`Component ${component_id} added to frame ${frame_id}`);
    } else {
      const request_url = api_endpoint + `/frames/${frame_id}/components/${component_id}/`;
      const server_response = await fetch(request_url, {
        method: 'DELETE',
      });

      if (!server_response.ok) {
        if (server_response.status === 404) {
          console.log(`Component ${component_id} not in frame ${frame_id} - no action needed`);
          return true;
        }
        throw new Error(`Failed to remove component from frame: ${server_response.statusText}`);
      }

      console.log(`Component ${component_id} removed from frame ${frame_id}`);
    }
    return true;
  } catch (error) {
    console.error('Error updating component in frame:', error);

    const checkbox_element = document.querySelector(`input[value="${component_id}"]`);
    if (checkbox_element) {
      checkbox_element.checked = !is_component_selected;
      const parent_dropdown = checkbox_element.closest('.component-dropdown');
      if (parent_dropdown) {
        updateDropdownLabel(parent_dropdown);
        updateCheckAllButton(parent_dropdown);
      }
    }
    return false;
  }
};
// #endregion

// #region ***  Event Listeners - listenTo___            ***********
const listenToSocket = () => {
  socket_connection.on('connect', () => {
    console.log('Socket connected');
  });

  socket_connection.on('disconnect', () => {
    console.log('Socket disconnected');
  });

  socket_connection.on('error', (error) => {
    console.log('Socket error:', error);
  });

  socket_connection.on('B2F_new_log', (data) => {
    showLastLog(data);
  });

  socket_connection.on('B2F_component_selection', (data) => {});
};
// #endregion

// #region ***  Init / DOMContentLoaded                  ***********
const init = () => {
  console.log('DOM loaded');
  showDropdown();
  showAllRoomsAndComponents();
  listenToSocket();
};

document.addEventListener('DOMContentLoaded', init);
// #endregion

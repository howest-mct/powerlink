'use strict';

const lan_ip = `http://${window.location.hostname}:8000`;
const socket_connection = io(lan_ip);
const api_endpoint = `http://${window.location.hostname}:8000/api/v1`;

// #region ***  DOM references                           ***********
const component_icons = {
  1: `img/svg/lightning.svg`,
  2: `img/svg/lightning.svg`,
  3: `img/svg/sliders-horizontal.svg`,
  4: `img/svg/sliders-horizontal.svg`,
  5: `img/svg/thermometer.svg`,
  6: `img/svg/fire-simple.svg`,
  7: `img/svg/lightning.svg`,
  8: `img/svg/fan.svg`,
  9: `img/svg/lightning.svg`,
  10: `img/svg/toggle-left.svg`,
  11: `img/svg/lightbulb.svg`,
  12: `img/svg/lightning.svg`,
  13: `img/svg/hand-waving.svg`,
  14: `img/svg/lightbulb.svg`,
  15: `img/svg/lightning.svg`,
  16: `img/svg/scan.svg`,
  17: `img/svg/door.svg`,
  18: `img/svg/lock-simple.svg`,
  19: `img/svg/sun.svg`,
  20: `img/svg/lightbulb.svg`,
  21: `img/svg/power.svg`,
  22: `img/svg/thermometer.svg`,
};

const LIGHT_COMPONENT_IDS = [11, 14, 20];
const TEMP_CONTROL_COMPONENT_IDS = [4];
const SERVO_COMPONENT_IDS = [18];
// #endregion

// #region ***  Simplified HTML Generation Functions    ***********
const generateServoComponentCardHtml = (component_id, component_name, value, value_unit, room_id, log_id) => {
  const icon_path = component_icons[component_id];
  const is_unlocked = parseInt(value) > 0;
  const servo_text = is_unlocked ? 'Unlocked' : 'Locked';

  return `
    <article class="c-article c-hover--shadow c-light-card js-component__container" data-component_id="${component_id}" data-room_id="${room_id}" data-log_id="${log_id}">
      <div class="c-article__header">
        <a href="#" class="c-article__link">
          <img src="${icon_path}" alt="Servo icon" class="c-article__icon">
        </a>
        <h2 class="c-article__title">${component_name}</h2>
      </div>
      <div class="c-card">
        <h3 class="c-card__level">${servo_text}</h3>
        <div class="c-card__meta">
          <button class="servo-toggle-btn" data-component="${component_id}">Toggle Lock</button>
        </div>
      </div>
    </article>
  `;
};

const generateLightComponentCardHtml = (component_id, component_name, value, value_unit, room_id, log_id) => {
  const icon_path = component_icons[component_id];
  const is_on = parseInt(value) > 0;
  const brightness_text = is_on ? `${value} ${value_unit}` : 'Off';
  let schedule_text = '';
  if (component_id === 11 || component_id === 14) {
    schedule_text = `<a href="schedules.html?page=2" class="c-card__capacity c-card--blue">EDIT SCHEDULES</a>`;
  }

  return `
    <article class="c-article c-hover--shadow c-light-card js-component__container" data-component_id="${component_id}" data-room_id="${room_id}" data-log_id="${log_id}">
      <div class="c-article__header">
        <a href="#" class="c-article__link">
          <img src="${icon_path}" alt="Light icon" class="c-article__icon">
        </a>
        <h2 class="c-article__title">${component_name}</h2>
      </div>
      <div class="c-card c-card--light">
        <h3 class="c-card__level">${brightness_text}</h3>
        <div class="c-card__meta c-card__meta--light">
          <button class="light-toggle-btn" data-component="${component_id}">Toggle Light</button>
          ${schedule_text}
        </div>
      </div>
    </article>
  `;
};

const generateRegularComponentCardHtml = (component_id, component_name, value, value_unit, datetime, log_id, room_id) => {
  const formatted_date = new Date(datetime);
  const icon_path = component_icons[component_id];

  return `
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
};

const generateTempControlComponentCardHtml = (component_id, component_name, value, value_unit, datetime, log_id, room_id) => {
  const icon_path = component_icons[component_id];

  return `
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
          <a href="schedules.html?page=2" class="c-card__capacity c-card--blue">EDIT SCHEDULES</a>
        </div>
      </div>
    </article>
  `;
};

const generateSmartComponentCardHtml = (component_id, component_name, value, value_unit, datetime, log_id, room_id) => {
  if (LIGHT_COMPONENT_IDS.includes(parseInt(component_id))) {
    return generateLightComponentCardHtml(component_id, component_name, value, value_unit, room_id, log_id);
  } else if (TEMP_CONTROL_COMPONENT_IDS.includes(parseInt(component_id))) {
    return generateTempControlComponentCardHtml(component_id, component_name, value, value_unit, datetime, log_id, room_id);
  } else if (SERVO_COMPONENT_IDS.includes(parseInt(component_id))) {
    return generateServoComponentCardHtml(component_id, component_name, value, value_unit, room_id, log_id);
  } else {
    return generateRegularComponentCardHtml(component_id, component_name, value, value_unit, datetime, log_id, room_id);
  }
};

const generateRoomContainerHtml = (room_id, room_name, room_number, components_html, dropdown_html) => {
  return `
    <div class="c-room__container js-room__container" data-room_id="${room_id}" data-room_name="${room_name}" data-room_number="${room_number}">
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
};

const generateDropdownOptionHtml = (component_id, component_name, room_id, is_checked) => {
  let checked_attribute = '';
  if (is_checked === true) {
    checked_attribute = 'checked';
  }

  return `
    <div class="c-dropdown-option c-checkbox-option">
      <label class="c-checkbox">
        <input type="checkbox" value="${component_id}" data-room="${room_id}" data-name="${component_name}" ${checked_attribute}>
        ${component_name}
      </label>
    </div>
  `;
};
// #endregion

// #region ***  Simplified Component Control Functions  ***********
const initSimpleControlEvents = () => {
  document.addEventListener('click', (event) => {
    if (event.target.classList.contains('light-toggle-btn')) {
      event.preventDefault();
      const component_id = parseInt(event.target.dataset.component);
      toggleLight(component_id);
    }
  });

  document.addEventListener('click', (event) => {
    if (event.target.classList.contains('servo-toggle-btn')) {
      event.preventDefault();
      const component_id = parseInt(event.target.dataset.component);
      toggleServo(component_id);
    }
  });
};

const toggleLight = (component_id) => {
  const light_card = document.querySelector(`[data-component_id="${component_id}"]`);
  const level_element = light_card.querySelector('.c-card__level');
  const current_text = level_element.textContent.trim();

  let is_currently_on = false;
  if (current_text.toLowerCase() !== 'off') {
    is_currently_on = true;
  }

  const new_value = is_currently_on ? 0 : 100;

  const new_text = new_value > 0 ? `${new_value} %` : 'Off';
  level_element.textContent = new_text;

  socket_connection.emit('BF2_manual_light_control', {
    component_id: component_id,
    value: new_value,
    manual_override: true,
    timestamp: Date.now(),
  });

  console.log(`Light ${component_id} toggled to ${new_value}`);
};

const toggleServo = (component_id) => {
  const servo_card = document.querySelector(`[data-component_id="${component_id}"]`);
  const level_element = servo_card.querySelector('.c-card__level');
  const current_text = level_element.textContent.trim();

  const is_currently_unlocked = current_text.toLowerCase() === 'unlocked';

  const action = is_currently_unlocked ? 'lock' : 'unlock';

  const new_text = is_currently_unlocked ? 'Locked' : 'Unlocked';
  level_element.textContent = new_text;

  socket_connection.emit('BF2_manual_door_control', {
    component_id: component_id,
    action: action,
    manual_override: true,
    timestamp: Date.now(),
  });

  console.log(`Servo ${component_id} ${action}ed`);
};

const listenToSimpleSocketEvents = () => {
  socket_connection.on('B2F_light_control_success', (data) => {
    console.log(`Light ${data.component_id} successfully changed to ${data.new_value}`);
  });

  socket_connection.on('B2F_light_control_error', (data) => {
    console.log(`Light ${data.component_id} control failed: ${data.error}`);
    alert('Light control failed. Please try again.');
  });

  socket_connection.on('B2F_door_control_success', (data) => {
    console.log(`Door ${data.component_id} successfully ${data.action}ed`);
  });

  socket_connection.on('B2F_door_control_error', (data) => {
    console.log(`Door ${data.component_id} control failed: ${data.error}`);
    alert('Door control failed. Please try again.');
  });
};
// #endregion

// #region ***  Dropdown Functions (kept from original) ***********
const createComponentDropdown = (room_id, all_components, components_in_current_page) => {
  let dropdown_options_html = `<div class="c-dropdown-option c-check-all-option" data-room="${room_id}">Check All</div>`;

  const page_component_ids = [];
  for (let i = 0; i < components_in_current_page.length; i++) {
    page_component_ids.push(components_in_current_page[i].component_id);
  }

  for (let i = 0; i < all_components.length; i++) {
    const component = all_components[i];
    let is_component_checked = false;

    for (let j = 0; j < page_component_ids.length; j++) {
      if (page_component_ids[j] === component.component_id) {
        is_component_checked = true;
        break;
      }
    }

    dropdown_options_html += generateDropdownOptionHtml(component.component_id, component.component_name, room_id, is_component_checked);
  }

  return `
    <div class="c-component-dropdown" data-room="${room_id}">
      <div class="c-dropdown-trigger">Select Components</div>
      <div class="c-dropdown-menu">
        ${dropdown_options_html}
      </div>
    </div>
  `;
};

const initDropdownEvents = () => {
  document.addEventListener('click', (event) => {
    if (event.target.classList.contains('c-dropdown-trigger')) {
      event.stopPropagation();
      const clicked_dropdown = event.target.closest('.c-component-dropdown');
      const dropdown_menu = clicked_dropdown.querySelector('.c-dropdown-menu');

      const all_menus = document.querySelectorAll('.c-dropdown-menu');
      for (let i = 0; i < all_menus.length; i++) {
        const menu = all_menus[i];
        if (menu !== dropdown_menu) {
          menu.style.display = 'none';
        }
      }

      if (dropdown_menu.style.display === 'block') {
        dropdown_menu.style.display = 'none';
      } else {
        dropdown_menu.style.display = 'block';
      }
    }

    if (event.target.classList.contains('c-check-all-option')) {
      event.stopPropagation();
      const room_id = event.target.dataset.room;
      const clicked_dropdown = event.target.closest('.c-component-dropdown');
      const all_checkboxes = clicked_dropdown.querySelectorAll('input[type="checkbox"]');

      let all_boxes_checked = true;
      for (let i = 0; i < all_checkboxes.length; i++) {
        if (all_checkboxes[i].checked === false) {
          all_boxes_checked = false;
          break;
        }
      }

      for (let i = 0; i < all_checkboxes.length; i++) {
        const checkbox = all_checkboxes[i];
        if (all_boxes_checked === true) {
          checkbox.checked = false;
        } else {
          checkbox.checked = true;
        }
        sendComponentSelection(checkbox);
      }

      updateDropdownLabel(clicked_dropdown);

      if (all_boxes_checked === true) {
        event.target.textContent = 'Check All';
      } else {
        event.target.textContent = 'Uncheck All';
      }
    }

    if (event.target.type === 'checkbox' && event.target.dataset.room) {
      sendComponentSelection(event.target);
      const parent_dropdown = event.target.closest('.c-component-dropdown');
      updateDropdownLabel(parent_dropdown);
      updateCheckAllButton(parent_dropdown);
    }

    if (!event.target.closest('.c-component-dropdown')) {
      const all_menus = document.querySelectorAll('.c-dropdown-menu');
      for (let i = 0; i < all_menus.length; i++) {
        all_menus[i].style.display = 'none';
      }
    }
  });
};

const updateDropdownLabel = (dropdown_element) => {
  const trigger_button = dropdown_element.querySelector('.c-dropdown-trigger');
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
  const check_all_button = dropdown_element.querySelector('.c-check-all-option');
  const all_checkboxes = dropdown_element.querySelectorAll('input[type="checkbox"]');
  const checked_checkboxes = dropdown_element.querySelectorAll('input[type="checkbox"]:checked');

  if (checked_checkboxes.length === all_checkboxes.length && all_checkboxes.length > 0) {
    check_all_button.textContent = 'Uncheck All';
  } else {
    check_all_button.textContent = 'Check All';
  }
};

const sendComponentSelection = async (checkbox_element) => {
  const component_id = parseInt(checkbox_element.value);
  const room_id = parseInt(checkbox_element.dataset.room);
  const is_checkbox_checked = checkbox_element.checked;

  const update_was_successful = await updateComponentInPage(component_id, is_checkbox_checked);

  if (update_was_successful === true) {
    socket_connection.emit('BF2_component_selection', {
      component_id: component_id,
      room_id: room_id,
      selected: is_checkbox_checked,
    });

    let component_card = document.querySelector(`.js-component__container[data-component_id="${component_id}"]`);

    if (is_checkbox_checked === true) {
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
    const page_parameter = parseInt(url_parameters.get('page'));

    const log_url = `${api_endpoint}/components/last/${page_parameter}/`;
    const log_response = await fetch(log_url);
    const all_component_logs = await log_response.json();

    let component_log = null;
    for (let i = 0; i < all_component_logs.length; i++) {
      if (all_component_logs[i].component_id === component_id) {
        component_log = all_component_logs[i];
        break;
      }
    }

    const components_url = `${api_endpoint}/components/`;
    const components_response = await fetch(components_url);
    const all_components = await components_response.json();

    let component_details = null;
    for (let i = 0; i < all_components.length; i++) {
      if (all_components[i].component_id === component_id) {
        component_details = all_components[i];
        break;
      }
    }

    const component_card_html = generateSmartComponentCardHtml(component_id, component_details.component_name, component_log.value, component_details.value_unit, component_log.datetime, component_log.log_id, room_id);

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

// #region ***  Display Functions (kept from original)  ***********
const showDropdown = () => {
  const hamburger_button = document.querySelector('.c-hamburger');
  const navigation_popup = document.querySelector('.c-nav-popup');
  const page_overlay = document.querySelector('.c-overlay');
  const close_button = document.querySelector('.c-nav-popup__close');

  const toggleMobileMenu = () => {
    const menu_is_active = navigation_popup.classList.toggle('c-nav-popup--active');
    page_overlay.classList.toggle('c-overlay--active');
    hamburger_button.setAttribute('aria-expanded', menu_is_active);
    navigation_popup.setAttribute('aria-hidden', !menu_is_active);
    page_overlay.setAttribute('aria-hidden', !menu_is_active);
  };

  if (window.matchMedia('(max-width: 767px)').matches) {
    if (hamburger_button) {
      hamburger_button.addEventListener('click', (event) => {
        event.stopPropagation();
        toggleMobileMenu();
      });
    }

    if (close_button) {
      close_button.addEventListener('click', (event) => {
        event.stopPropagation();
        navigation_popup.classList.remove('c-nav-popup--active');
        page_overlay.classList.remove('c-overlay--active');
        hamburger_button.setAttribute('aria-expanded', 'false');
        navigation_popup.setAttribute('aria-hidden', 'true');
        page_overlay.setAttribute('aria-hidden', 'true');
      });
    }

    if (page_overlay) {
      page_overlay.addEventListener('click', () => {
        navigation_popup.classList.remove('c-nav-popup--active');
        page_overlay.classList.remove('c-overlay--active');
        hamburger_button.setAttribute('aria-expanded', 'false');
        navigation_popup.setAttribute('aria-hidden', 'true');
        page_overlay.setAttribute('aria-hidden', 'true');
      });
    }

    const navigation_links = document.querySelectorAll('.c-nav-popup__link');
    for (let i = 0; i < navigation_links.length; i++) {
      navigation_links[i].addEventListener('click', () => {
        navigation_popup.classList.remove('c-nav-popup--active');
        page_overlay.classList.remove('c-overlay--active');
        hamburger_button.setAttribute('aria-expanded', 'false');
        navigation_popup.setAttribute('aria-hidden', 'true');
        page_overlay.setAttribute('aria-hidden', 'true');
      });
    }

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
    const all_rooms = await getAllRooms();
    const all_components = await getAllComponents();
    const all_component_logs = await getLastComponentLogs();
    const components_in_page = await getComponentsInPage();

    const components_grouped_by_room = {};
    for (let i = 0; i < all_components.length; i++) {
      const component = all_components[i];
      if (!components_grouped_by_room[component.room_id]) {
        components_grouped_by_room[component.room_id] = [];
      }
      components_grouped_by_room[component.room_id].push(component);
    }

    const logs_by_component_id = {};
    for (let i = 0; i < all_component_logs.length; i++) {
      const log = all_component_logs[i];
      logs_by_component_id[log.component_id] = log;
    }

    const page_component_ids = [];
    for (let i = 0; i < components_in_page.length; i++) {
      page_component_ids.push(components_in_page[i].component_id);
    }

    let rooms_html = '';
    const main_container = document.querySelector('.js-main');

    for (let room_index = 0; room_index < all_rooms.length; room_index++) {
      const room = all_rooms[room_index];
      const room_components = components_grouped_by_room[room.room_id] || [];

      let components_html = '';

      for (let comp_index = 0; comp_index < room_components.length; comp_index++) {
        const component = room_components[comp_index];
        let component_is_in_page = false;

        for (let page_index = 0; page_index < page_component_ids.length; page_index++) {
          if (page_component_ids[page_index] === component.component_id) {
            component_is_in_page = true;
            break;
          }
        }

        const component_log = logs_by_component_id[component.component_id];

        if (component_is_in_page === true && component_log) {
          components_html += generateSmartComponentCardHtml(component.component_id, component.component_name, component_log.value, component.value_unit, component_log.datetime, component_log.log_id, room.room_id);
        }
      }

      const dropdown_html = createComponentDropdown(room.room_id, room_components, components_in_page);
      rooms_html += generateRoomContainerHtml(room.room_id, room.room_name, room_index, components_html, dropdown_html);
    }

    main_container.innerHTML = rooms_html;

    const all_room_containers = document.querySelectorAll('.js-room__container');
    for (let i = 0; i < all_room_containers.length; i++) {
      const room_container = all_room_containers[i];
      const room_number = parseInt(room_container.dataset.room_number);
      const component_containers = room_container.querySelectorAll('.js-component__container');

      if (room_number % 2 === 0) {
        room_container.classList.add('c-grey-background');
        for (let j = 0; j < component_containers.length; j++) {
          component_containers[j].classList.add('c-white-background');
        }
      } else {
        room_container.classList.add('c-white-background');
        for (let j = 0; j < component_containers.length; j++) {
          component_containers[j].classList.add('c-grey-background');
        }
      }
    }

    initDropdownEvents();
    updateAllDropdownLabels();
  } catch (error) {
    console.error('Error loading rooms and components:', error);
  }
};

const updateAllDropdownLabels = () => {
  const dropdowns = document.querySelectorAll('.c-component-dropdown');
  for (let i = 0; i < dropdowns.length; i++) {
    updateDropdownLabel(dropdowns[i]);
    updateCheckAllButton(dropdowns[i]);
  }
};

const showLastLog = (log_data) => {
  const component_id = log_data.component_id;
  const room_id = log_data.room_id;
  const value = log_data.value;
  const value_unit = log_data.value_unit;
  const datetime = log_data.datetime;
  const log_id = log_data.log_id;
  const component_name = log_data.component_name;

  let existing_log_container = document.querySelector(`.js-component__container[data-component_id="${component_id}"]`);

  if (existing_log_container) {
    const level_element = existing_log_container.querySelector('.c-card__level');

    if (LIGHT_COMPONENT_IDS.includes(parseInt(component_id))) {
      const is_on = parseInt(value) > 0;
      const brightness_text = is_on ? `${value} ${value_unit}` : 'Off';

      if (level_element) {
        level_element.textContent = brightness_text;
      }
    } else if (SERVO_COMPONENT_IDS.includes(parseInt(component_id))) {
      const is_unlocked = parseInt(value) > 0;
      const servo_text = is_unlocked ? 'Unlocked' : 'Locked';

      if (level_element) {
        level_element.textContent = servo_text;
      }
    } else {
      const capacity_element = existing_log_container.querySelector('.c-card__capacity');
      const formatted_date = new Date(datetime);

      if (level_element) {
        level_element.textContent = `${value} ${value_unit}`;
      }

      if (capacity_element) {
        capacity_element.textContent = formatDateTime(formatted_date);
      }
    }

    existing_log_container.setAttribute('data-log_id', log_id);
  } else {
    const room_container = document.querySelector(`.js-room__container[data-room_id="${room_id}"]`);
    if (room_container) {
      const components_container = room_container.querySelector('.c-room__components');
      const dropdown_element = room_container.querySelector('.c-component-dropdown');

      if (components_container) {
        const component_card_html = generateSmartComponentCardHtml(component_id, component_name, value, value_unit, datetime, log_id, room_id);

        components_container.innerHTML += component_card_html;

        if (dropdown_element) {
          const existing_checkbox = dropdown_element.querySelector(`input[value="${component_id}"]`);
          if (!existing_checkbox) {
            const dropdown_menu = dropdown_element.querySelector('.c-dropdown-menu');
            const new_option_html = generateDropdownOptionHtml(component_id, component_name, room_id, false);
            dropdown_menu.insertAdjacentHTML('beforeend', new_option_html);
          }
        }

        const new_log_container = components_container.querySelector(`.js-component__container[data-component_id="${component_id}"]`);
        if (new_log_container) {
          const room_id_num = parseInt(room_id);
          if (room_id_num % 2 === 0) {
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

// #region ***  Helper Functions                        ***********
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

// #region ***  Data Access Functions                   ***********
const getLastComponentLogs = async () => {
  const url_parameters = new URLSearchParams(window.location.search);
  const page_url_param = parseInt(url_parameters.get('page'));
  let request_url = `${api_endpoint}/components/last/${page_url_param}/`;
  let server_response = await fetch(request_url).catch((error) => console.error('Fetch-error:', error));
  const json_data = await server_response.json().catch((error) => console.error('JSON-error:', error));
  return json_data;
};

const getAllComponents = async () => {
  const request_url = `${api_endpoint}/components/`;
  const server_response = await fetch(request_url).catch((error) => console.error('Fetch-error:', error));
  const json_data = await server_response.json().catch((error) => console.error('JSON-error:', error));
  return json_data;
};

const getAllRooms = async () => {
  const request_url = `${api_endpoint}/rooms/`;
  const server_response = await fetch(request_url).catch((error) => console.error('Fetch-error:', error));
  const json_data = await server_response.json().catch((error) => console.error('JSON-error:', error));
  return json_data;
};

const getComponentsInPage = async () => {
  const url_parameters = new URLSearchParams(window.location.search);
  const page_id = parseInt(url_parameters.get('page'));
  const request_url = `${api_endpoint}/pages/${page_id}/components/`;
  const server_response = await fetch(request_url).catch((error) => console.error('Fetch-error:', error));
  const json_data = await server_response.json().catch((error) => console.error('JSON-error:', error));
  return json_data;
};

const updateComponentInPage = async (component_id, is_component_selected) => {
  const url_parameters = new URLSearchParams(window.location.search);
  const page_id = parseInt(url_parameters.get('page'));

  try {
    if (is_component_selected === true) {
      const request_url = `${api_endpoint}/pages/${page_id}/components/`;
      const server_response = await fetch(request_url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          component_id: component_id,
          page_id: page_id,
        }),
      });
    } else {
      const request_url = `${api_endpoint}/pages/${page_id}/components/${component_id}/`;
      const server_response = await fetch(request_url, {
        method: 'DELETE',
      });
    }
    return true;
  } catch (error) {
    console.error('Error updating component in page:', error);

    const checkbox_element = document.querySelector(`input[value="${component_id}"]`);
    if (checkbox_element) {
      checkbox_element.checked = !is_component_selected;
      const parent_dropdown = checkbox_element.closest('.c-component-dropdown');
      if (parent_dropdown) {
        updateDropdownLabel(parent_dropdown);
        updateCheckAllButton(parent_dropdown);
      }
    }
    return false;
  }
};
// #endregion

// #region ***  Socket Event Listeners                  ***********
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

  listenToSimpleSocketEvents();
};
// #endregion

// #region ***  Initialize Application                  ***********
const init = () => {
  console.log('DOM loaded');
  showDropdown();
  showAllRoomsAndComponents();
  listenToSocket();
  initSimpleControlEvents();
};

document.addEventListener('DOMContentLoaded', init);
// #endregion

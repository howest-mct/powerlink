'use strict';

// #region ***  Configuration and Constants              ***********
const lan_ip = `http://${window.location.hostname}:8000`;
const socket_connection = io(lan_ip);
const api_endpoint = `http://${window.location.hostname}:8000/api/v1`;

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
const SERVO_COMPONENT_IDS = [18];
const USAGE_IDS = [1, 2];
// #endregion

// #region ***  HTML Generation Functions               ***********
const generate_servo_component_card_html = (component_id, component_name, value, value_unit, room_id, log_id) => {
  const icon_path = component_icons[component_id];
  const is_unlocked = parseInt(value) > 0;
  const servo_text = is_unlocked ? 'Unlocked' : 'Locked';

  return `
    <article class="c-article c-hover--shadow c-light-card js-component__container" 
             data-component_id="${component_id}" 
             data-room_id="${room_id}" 
             data-log_id="${log_id}" 
             role="button" 
             tabindex="0" 
             aria-label="Toggle ${component_name}" 
             aria-pressed="${is_unlocked}">
      <div class="c-article__header">
        <a href="#" class="c-article__link">
          <img src="${icon_path}" alt="Servo icon" class="c-article__icon">
        </a>
        <h2 class="c-article__title">${component_name}</h2>
      </div>
      <div class="c-card c-card--light">
        <h3 class="c-card__level">${servo_text}</h3>
        <div class="c-card__meta c-card__meta--light">
          <button class="c-card__status c-card__status--toggle" type="button">Tap to toggle</button>
        </div>
      </div>
    </article>
  `;
};

const generate_rfid_card_html = async (component_id, component_name, value, value_unit, datetime, log_id, room_id) => {
  const icon_path = component_icons[component_id];
  const inhabitant_name = await get_inhabitant_name_by_card_id(String(value));

  return `
    <article class="c-article c-hover--shadow js-component__container" 
             data-component_id="${component_id}" 
             data-room_id="${room_id}" 
             data-log_id="${log_id}">
      <div class="c-article__header">
        <a href="#" class="c-article__link">
          <img src="${icon_path}" alt="Component icon" class="c-article__icon">
        </a>
        <h2 class="c-article__title">${component_name}</h2>
      </div>
      <div class="c-card c-card--light">
        <h3 class="c-card__level">${inhabitant_name}</h3>
        <div class="c-card__meta c-card__meta--light">
          <button class="c-card__status c-card__status--toggle" type="button">Edit Family</button>
        </div>
      </div>
    </article>
  `;
};

const generate_light_component_card_html = (component_id, component_name, value, value_unit, room_id, log_id) => {
  const icon_path = component_icons[component_id];
  const is_on = parseInt(value) > 0;
  const brightness_text = is_on ? `${value} ${value_unit}` : 'Off';

  return `
    <article class="c-article c-hover--shadow c-light-card js-component__container" 
             data-component_id="${component_id}" 
             data-room_id="${room_id}" 
             data-log_id="${log_id}" 
             role="button" 
             tabindex="0" 
             aria-label="Toggle ${component_name}" 
             aria-pressed="${is_on}">
      <div class="c-article__header">
        <a href="#" class="c-article__link">
          <img src="${icon_path}" alt="Light icon" class="c-article__icon">
        </a>
        <h2 class="c-article__title">${component_name}</h2>
      </div>
      <div class="c-card c-card--light">
        <h3 class="c-card__level">${brightness_text}</h3>
        <div class="c-card__meta c-card__meta--light">
          <button class="c-card__status c-card__status--toggle" type="button">Tap to toggle</button>
        </div>
      </div>
    </article>
  `;
};

const generate_regular_component_card_html = (component_id, component_name, value, value_unit, datetime, log_id, room_id) => {
  const formatted_date = new Date(datetime);
  const icon_path = component_icons[component_id];

  return `
    <article class="c-article c-hover--shadow js-component__container" 
             data-component_id="${component_id}" 
             data-room_id="${room_id}" 
             data-log_id="${log_id}">
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
          <p class="c-card__capacity">${format_date_time(formatted_date)}</p>
        </div>
      </div>
    </article>
  `;
};

const generate_power_switch_html = (component_id, component_name, value, value_unit, datetime, log_id, room_id) => {
  const formatted_date = new Date(datetime);
  const icon_path = component_icons[component_id];

  return `
    <article class="c-article c-hover--shadow c-light-card js-component__container" 
             data-component_id="${component_id}" 
             data-room_id="${room_id}" 
             data-log_id="${log_id}" 
             role="button" 
             tabindex="0" 
             aria-label="Toggle ${component_name}">
      <div class="c-article__header">
        <a href="#" class="c-article__link">
          <img src="${icon_path}" alt="Power icon" class="c-article__icon">
        </a>
        <h2 class="c-article__title">${component_name}</h2>
      </div>
      <div class="c-card c-card--light">
        <h3 class="c-card__level">Active</h3>
        <div class="c-card__meta c-card__meta--light">
          <button class="c-card__status c-card__status--toggle" type="button">Tap to turn off PowerLink</button>
        </div>
      </div>
    </article>
  `;
};

const generate_usage_card_html = (component_id, component_name, value, value_unit, datetime, log_id, room_id) => {
  const formatted_date = new Date(datetime);
  const icon_path = component_icons[component_id];
  const today_value = 0; // This should probably come from data

  let color_class = '';
  if (today_value > 7) {
    color_class = 'c-card--warning';
  } else if (today_value > 3) {
    color_class = 'c-card--mainblue';
  } else {
    color_class = 'c-card--active';
  }

  return `
    <article class="c-article c-hover--shadow js-component__container" 
             data-component_id="${component_id}" 
             data-room_id="${room_id}" 
             data-log_id="${log_id}">
      <div class="c-article__header">
        <a href="#" class="c-article__link">
          <img src="${icon_path}" alt="Component icon" class="c-article__icon">
        </a>
        <h2 class="c-article__title">${component_name}</h2>
      </div>
      <div class="c-card">
        <h3 class="c-card__level">${value} ${value_unit}</h3>
        <div class="c-card__meta">
          <p class="c-card__capacity">Today's Energy</p>
          <p class="c-card__status ${color_class}">${today_value} Wh</p>
        </div>
      </div>
    </article>
  `;
};

const generate_temp_control_component_card_html = (component_id, component_name, value, value_unit, datetime, log_id, room_id) => {
  const icon_path = component_icons[component_id];

  return `
    <article class="c-article c-hover--shadow js-component__container" 
             data-component_id="${component_id}" 
             data-room_id="${room_id}" 
             data-log_id="${log_id}">
      <div class="c-article__header">
        <a href="#" class="c-article__link">
          <img src="${icon_path}" alt="Component icon" class="c-article__icon">
        </a>
        <h2 class="c-article__title">${component_name}</h2>
      </div>
      <div class="c-card">
        <h3 class="c-card__level">${value} ${value_unit}</h3>
        <div class="c-card__meta">
          <a href="schedules.html?page=2" class="c-card__capacity c-card--blue">EDIT SCHEDULE</a>
        </div>
      </div>
    </article>
  `;
};

const generate_smart_component_card_html = (component_id, component_name, value, value_unit, datetime, log_id, room_id) => {
  if (USAGE_IDS.includes(parseInt(component_id))) {
    return generate_usage_card_html(component_id, component_name, value, value_unit, datetime, log_id, room_id);
  } else if (LIGHT_COMPONENT_IDS.includes(parseInt(component_id))) {
    return generate_light_component_card_html(component_id, component_name, value, value_unit, room_id, log_id);
  } else if (component_id === 4) {
    return generate_temp_control_component_card_html(component_id, component_name, value, value_unit, datetime, log_id, room_id);
  } else if (component_id === 18) {
    return generate_servo_component_card_html(component_id, component_name, value, value_unit, room_id, log_id);
  } else if (component_id === 16) {
    return generate_rfid_card_html(component_id, component_name, value, value_unit, datetime, log_id, room_id);
  } else if (component_id === 21) {
    return generate_power_switch_html(component_id, component_name, value, value_unit, datetime, log_id, room_id);
  } else {
    return generate_regular_component_card_html(component_id, component_name, value, value_unit, datetime, log_id, room_id);
  }
};

const generate_room_container_html = (room_id, room_name, room_number, components_html, dropdown_html) => {
  return `
    <div class="c-room__container js-room__container" 
         data-room_id="${room_id}" 
         data-room_name="${room_name}" 
         data-room_number="${room_number}">
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

const generate_dropdown_option_html = (component_id, component_name, room_id, is_checked) => {
  const checked_attribute = is_checked ? 'checked' : '';

  return `
    <div class="c-dropdown-option c-checkbox-option">
      <label class="c-checkbox">
        <input type="checkbox" 
               value="${component_id}" 
               data-room="${room_id}" 
               data-name="${component_name}" 
               ${checked_attribute}>
        ${component_name}
      </label>
    </div>
  `;
};
// #endregion

// #region ***  Dropdown Functions                      ***********
const create_component_dropdown = (room_id, all_components, components_in_current_page) => {
  let dropdown_options_html = `<div class="c-dropdown-option c-check-all-option" data-room="${room_id}">Check All</div>`;

  const page_component_ids = components_in_current_page.map((component) => component.component_id);

  for (let i = 0; i < all_components.length; i++) {
    const component = all_components[i];
    const is_component_checked = page_component_ids.includes(component.component_id);
    dropdown_options_html += generate_dropdown_option_html(component.component_id, component.component_name, room_id, is_component_checked);
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

const init_dropdown_events = () => {
  document.addEventListener('click', (event) => {
    // Handle dropdown trigger clicks
    if (event.target.classList.contains('c-dropdown-trigger')) {
      handle_dropdown_trigger_click(event);
    }

    // Handle check all button clicks
    if (event.target.classList.contains('c-check-all-option')) {
      handle_check_all_click(event);
    }

    // Handle individual checkbox clicks
    if (event.target.type === 'checkbox' && event.target.dataset.room) {
      handle_checkbox_click(event);
    }

    // Close dropdowns when clicking outside
    if (!event.target.closest('.c-component-dropdown')) {
      close_all_dropdowns();
    }
  });
};

const handle_dropdown_trigger_click = (event) => {
  event.stopPropagation();
  const clicked_dropdown = event.target.closest('.c-component-dropdown');
  const dropdown_menu = clicked_dropdown.querySelector('.c-dropdown-menu');

  // Close other dropdowns
  const all_menus = document.querySelectorAll('.c-dropdown-menu');
  all_menus.forEach((menu) => {
    if (menu !== dropdown_menu) {
      menu.style.display = 'none';
    }
  });

  // Toggle current dropdown
  dropdown_menu.style.display = dropdown_menu.style.display === 'block' ? 'none' : 'block';
};

const handle_check_all_click = (event) => {
  event.stopPropagation();
  const room_id = event.target.dataset.room;
  const clicked_dropdown = event.target.closest('.c-component-dropdown');
  const all_checkboxes = clicked_dropdown.querySelectorAll('input[type="checkbox"]');

  const all_boxes_checked = Array.from(all_checkboxes).every((checkbox) => checkbox.checked);

  all_checkboxes.forEach((checkbox) => {
    checkbox.checked = !all_boxes_checked;
    send_component_selection(checkbox);
  });

  update_dropdown_label(clicked_dropdown);
  event.target.textContent = all_boxes_checked ? 'Check All' : 'Uncheck All';
};

const handle_checkbox_click = (event) => {
  send_component_selection(event.target);
  const parent_dropdown = event.target.closest('.c-component-dropdown');
  update_dropdown_label(parent_dropdown);
  update_check_all_button(parent_dropdown);
};

const close_all_dropdowns = () => {
  const all_menus = document.querySelectorAll('.c-dropdown-menu');
  all_menus.forEach((menu) => {
    menu.style.display = 'none';
  });
};

const update_dropdown_label = (dropdown_element) => {
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

const update_check_all_button = (dropdown_element) => {
  const check_all_button = dropdown_element.querySelector('.c-check-all-option');
  const all_checkboxes = dropdown_element.querySelectorAll('input[type="checkbox"]');
  const checked_checkboxes = dropdown_element.querySelectorAll('input[type="checkbox"]:checked');

  if (checked_checkboxes.length === all_checkboxes.length && all_checkboxes.length > 0) {
    check_all_button.textContent = 'Uncheck All';
  } else {
    check_all_button.textContent = 'Check All';
  }
};

const send_component_selection = async (checkbox_element) => {
  const component_id = parseInt(checkbox_element.value);
  const room_id = parseInt(checkbox_element.dataset.room);
  const is_checkbox_checked = checkbox_element.checked;

  try {
    const update_was_successful = await update_component_in_page(component_id, is_checkbox_checked);

    if (update_was_successful) {
      socket_connection.emit('BF2_component_selection', {
        component_id: component_id,
        room_id: room_id,
        selected: is_checkbox_checked,
      });

      const component_card = document.querySelector(`.js-component__container[data-component_id="${component_id}"]`);

      if (is_checkbox_checked) {
        if (component_card) {
          component_card.style.display = 'block';
        } else {
          await create_component_card(component_id, room_id);
        }
      } else {
        if (component_card) {
          component_card.style.display = 'none';
        }
      }
    }
  } catch (error) {
    console.error('Error in send_component_selection:', error);
  }
};

const create_component_card = async (component_id, room_id) => {
  try {
    const url_parameters = new URLSearchParams(window.location.search);
    const page_parameter = parseInt(url_parameters.get('page'));

    // Get component log
    const log_url = `${api_endpoint}/components/last/${page_parameter}/`;
    const log_response = await fetch(log_url);
    const all_component_logs = await log_response.json();

    const component_log = all_component_logs.find((log) => log.component_id === component_id);

    // Get component details
    const components_url = `${api_endpoint}/components/`;
    const components_response = await fetch(components_url);
    const all_components = await components_response.json();

    const component_details = all_components.find((component) => component.component_id === component_id);

    if (!component_log || !component_details) {
      console.error('Component log or details not found');
      return;
    }

    const component_card_html = generate_smart_component_card_html(component_id, component_details.component_name, component_log.value, component_details.value_unit, component_log.datetime, component_log.log_id, room_id);

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

// #region ***  Component Control Functions             ***********
const init_component_card_events = () => {
  document.addEventListener('click', (event) => {
    const toggle_button = event.target.closest('.c-card__status--toggle');

    if (toggle_button) {
      const component_card = toggle_button.closest('.js-component__container');

      if (component_card) {
        const component_id = parseInt(component_card.dataset.component_id);

        if (LIGHT_COMPONENT_IDS.includes(component_id)) {
          handle_light_toggle(event, component_card, component_id);
        }

        if (SERVO_COMPONENT_IDS.includes(component_id)) {
          handle_servo_toggle(event, component_card, component_id);
        }
      }
    }
  });
};

const handle_light_toggle = (event, component_card, component_id) => {
  event.preventDefault();
  event.stopPropagation();

  if (component_card.classList.contains('c-light-disabled')) {
    return;
  }

  const level_element = component_card.querySelector('.c-card__level');
  if (level_element) {
    const current_text = level_element.textContent.trim();
    let current_value = 0;

    if (current_text.toLowerCase() === 'off') {
      current_value = 0;
    } else {
      current_value = parseInt(current_text.split(' ')[0]) || 0;
    }

    const new_value = current_value > 0 ? 0 : 100;
    add_loading_state(component_card);
    toggle_light(component_id, new_value, component_card);
  }
};

const handle_servo_toggle = (event, component_card, component_id) => {
  event.preventDefault();
  event.stopPropagation();

  if (component_card.classList.contains('c-servo-disabled')) {
    return;
  }

  const level_element = component_card.querySelector('.c-card__level');
  if (level_element) {
    const current_text = level_element.textContent.trim();
    const is_unlocked = current_text.toLowerCase() === 'unlocked';
    const action = is_unlocked ? 'lock' : 'unlock';

    add_servo_loading_state(component_card);
    toggle_door_lock(component_id, action, component_card);
  }
};

const add_loading_state = (card_element) => {
  card_element.classList.add('c-light-disabled');
  card_element.style.pointerEvents = 'none';

  setTimeout(() => {
    remove_loading_state(card_element);
  }, 2000);
};

const remove_loading_state = (card_element) => {
  card_element.classList.remove('c-light-disabled');
  card_element.style.pointerEvents = '';
};

const add_toggle_animation = (card_element) => {
  card_element.classList.add('toggling');
  setTimeout(() => {
    card_element.classList.remove('toggling');
  }, 300);
};

const add_servo_loading_state = (card_element) => {
  card_element.classList.add('c-servo-disabled');
  card_element.style.pointerEvents = 'none';

  setTimeout(() => {
    remove_servo_loading_state(card_element);
  }, 3000);
};

const remove_servo_loading_state = (card_element) => {
  card_element.classList.remove('c-servo-disabled');
  card_element.style.pointerEvents = '';
};

const add_servo_toggle_animation = (card_element) => {
  card_element.classList.add('servo-toggling');
  setTimeout(() => {
    card_element.classList.remove('servo-toggling');
  }, 500);
};

const toggle_light = (component_id, new_value, card_element) => {
  try {
    socket_connection.emit('BF2_manual_light_control', {
      component_id: component_id,
      value: new_value,
      manual_override: true,
      timestamp: Date.now(),
    });

    console.log(`Toggling light ${component_id} to ${new_value}`);

    if (!window.pending_light_toggles) {
      window.pending_light_toggles = new Map();
    }
    window.pending_light_toggles.set(component_id, card_element);
  } catch (error) {
    console.error('Error toggling light:', error);
    remove_loading_state(card_element);
  }
};

const toggle_door_lock = (component_id, action, card_element) => {
  try {
    socket_connection.emit('BF2_manual_door_control', {
      component_id: component_id,
      action: action,
      manual_override: true,
      timestamp: Date.now(),
    });

    console.log(`Toggling door lock ${component_id} to ${action}`);

    if (!window.pending_servo_toggles) {
      window.pending_servo_toggles = new Map();
    }
    window.pending_servo_toggles.set(component_id, card_element);
  } catch (error) {
    console.error('Error toggling door lock:', error);
    remove_servo_loading_state(card_element);
  }
};

const listen_to_light_control_feedback = () => {
  socket_connection.on('B2F_light_control_success', (data) => {
    const component_id = data.component_id;
    const new_value = data.new_value;

    if (window.pending_light_toggles && window.pending_light_toggles.has(component_id)) {
      const card_element = window.pending_light_toggles.get(component_id);
      remove_loading_state(card_element);
      add_toggle_animation(card_element);
      window.pending_light_toggles.delete(component_id);

      console.log(`Light ${component_id} successfully toggled to ${new_value}`);
    }
  });

  socket_connection.on('B2F_light_control_error', (data) => {
    const component_id = data.component_id;
    const error_message = data.error || 'Unknown error';

    if (window.pending_light_toggles && window.pending_light_toggles.has(component_id)) {
      const card_element = window.pending_light_toggles.get(component_id);
      remove_loading_state(card_element);
      window.pending_light_toggles.delete(component_id);

      console.error(`Light ${component_id} toggle failed:`, error_message);
    }
  });
};

const listen_to_door_control_feedback = () => {
  socket_connection.on('B2F_door_control_success', (data) => {
    const component_id = data.component_id;
    const action = data.action;
    const new_state = data.new_state;

    if (window.pending_servo_toggles && window.pending_servo_toggles.has(component_id)) {
      const card_element = window.pending_servo_toggles.get(component_id);
      remove_servo_loading_state(card_element);
      add_servo_toggle_animation(card_element);
      window.pending_servo_toggles.delete(component_id);

      const level_element = card_element.querySelector('.c-card__level');
      if (level_element) {
        level_element.textContent = new_state > 0 ? 'Unlocked' : 'Locked';
      }

      card_element.setAttribute('aria-pressed', (new_state > 0).toString());

      console.log(`Door lock ${component_id} successfully ${action}ed`);
    }
  });

  socket_connection.on('B2F_door_control_error', (data) => {
    const component_id = data.component_id;
    const error_message = data.error || 'Unknown error';

    if (window.pending_servo_toggles && window.pending_servo_toggles.has(component_id)) {
      const card_element = window.pending_servo_toggles.get(component_id);
      remove_servo_loading_state(card_element);
      window.pending_servo_toggles.delete(component_id);

      console.error(`Door lock ${component_id} toggle failed:`, error_message);
      alert(`Failed to control door lock: ${error_message}`);
    }
  });
};
// #endregion

// #region ***  Mobile Navigation Functions             ***********
const show_dropdown = () => {
  const hamburger_button = document.querySelector('.c-hamburger');
  const navigation_popup = document.querySelector('.c-nav-popup');
  const page_overlay = document.querySelector('.c-overlay');
  const close_button = document.querySelector('.c-nav-popup__close');

  const toggle_mobile_menu = () => {
    const menu_is_active = navigation_popup.classList.toggle('c-nav-popup--active');
    page_overlay.classList.toggle('c-overlay--active');
    hamburger_button.setAttribute('aria-expanded', menu_is_active);
    navigation_popup.setAttribute('aria-hidden', !menu_is_active);
    page_overlay.setAttribute('aria-hidden', !menu_is_active);
  };

  const close_mobile_menu = () => {
    navigation_popup.classList.remove('c-nav-popup--active');
    page_overlay.classList.remove('c-overlay--active');
    hamburger_button.setAttribute('aria-expanded', 'false');
    navigation_popup.setAttribute('aria-hidden', 'true');
    page_overlay.setAttribute('aria-hidden', 'true');
  };

  // Only set up mobile menu if we're on mobile
  if (window.matchMedia('(max-width: 767px)').matches) {
    if (hamburger_button) {
      hamburger_button.addEventListener('click', (event) => {
        event.stopPropagation();
        toggle_mobile_menu();
      });
    }

    if (close_button) {
      close_button.addEventListener('click', (event) => {
        event.stopPropagation();
        close_mobile_menu();
      });
    }

    if (page_overlay) {
      page_overlay.addEventListener('click', close_mobile_menu);
    }

    const navigation_links = document.querySelectorAll('.c-nav-popup__link');
    navigation_links.forEach((link) => {
      link.addEventListener('click', close_mobile_menu);
    });

    document.addEventListener('click', (event) => {
      if (!navigation_popup.contains(event.target) && !hamburger_button.contains(event.target)) {
        close_mobile_menu();
      }
    });
  }

  // Handle window resize
  window.addEventListener('resize', () => {
    if (window.matchMedia('(min-width: 768px)').matches) {
      close_mobile_menu();
    }
  });
};
// #endregion

// #region ***  Display Functions                       ***********
const show_all_rooms_and_components = async () => {
  try {
    const all_rooms = await get_all_rooms();
    const all_components = await get_all_components();
    const all_component_logs = await get_last_component_logs();
    const components_in_page = await get_components_in_page();

    // Group components by room
    const components_grouped_by_room = {};
    all_components.forEach((component) => {
      if (!components_grouped_by_room[component.room_id]) {
        components_grouped_by_room[component.room_id] = [];
      }
      components_grouped_by_room[component.room_id].push(component);
    });

    // Index logs by component ID
    const logs_by_component_id = {};
    all_component_logs.forEach((log) => {
      logs_by_component_id[log.component_id] = log;
    });

    // Get list of component IDs that should be displayed on this page
    const page_component_ids = components_in_page.map((component) => component.component_id);

    let rooms_html = '';
    const main_container = document.querySelector('.js-main');

    for (let room_index = 0; room_index < all_rooms.length; room_index++) {
      const room = all_rooms[room_index];
      const room_components = components_grouped_by_room[room.room_id] || [];

      let components_html = '';

      // Generate HTML for components that should be shown on this page
      room_components.forEach((component) => {
        const component_is_in_page = page_component_ids.includes(component.component_id);
        const component_log = logs_by_component_id[component.component_id];

        if (component_is_in_page && component_log) {
          components_html += generate_smart_component_card_html(component.component_id, component.component_name, component_log.value, component.value_unit, component_log.datetime, component_log.log_id, room.room_id);
        }
      });

      const dropdown_html = create_component_dropdown(room.room_id, room_components, components_in_page);
      rooms_html += generate_room_container_html(room.room_id, room.room_name, room_index, components_html, dropdown_html);
    }

    main_container.innerHTML = rooms_html;

    // Apply alternating background colors
    apply_room_background_colors();

    init_dropdown_events();
    update_all_dropdown_labels();
  } catch (error) {
    console.error('Error loading rooms and components:', error);
  }
};

const apply_room_background_colors = () => {
  const all_room_containers = document.querySelectorAll('.js-room__container');

  all_room_containers.forEach((room_container, index) => {
    const room_number = parseInt(room_container.dataset.room_number);
    const component_containers = room_container.querySelectorAll('.js-component__container');

    if (room_number % 2 === 0) {
      room_container.classList.add('c-grey-background');
      component_containers.forEach((component) => {
        component.classList.add('c-white-background');
      });
    } else {
      room_container.classList.add('c-white-background');
      component_containers.forEach((component) => {
        component.classList.add('c-grey-background');
      });
    }
  });
};

const update_all_dropdown_labels = () => {
  const dropdowns = document.querySelectorAll('.c-component-dropdown');
  dropdowns.forEach((dropdown) => {
    update_dropdown_label(dropdown);
    update_check_all_button(dropdown);
  });
};

const show_all_last_logs = (json_data) => {
  let rooms_html = '';
  const main_container = document.querySelector('.js-main');

  // Group data by room
  const room_components = {};
  json_data.forEach((schedule_item) => {
    const room_id = schedule_item.room_id;
    if (!room_components[room_id]) {
      room_components[room_id] = [];
    }
    room_components[room_id].push(schedule_item);
  });

  let room_display_number = 0;

  // Generate HTML for each room
  Object.keys(room_components).forEach((room_id) => {
    const room_data = room_components[room_id];
    const room_name = room_data[0].room_name;

    let components_html = '';
    room_data.forEach((item) => {
      components_html += generate_smart_component_card_html(item.component_id, item.component_name, item.value, item.value_unit, item.datetime, item.log_id, item.room_id);
    });

    const dropdown_html = create_component_dropdown(room_id, room_data, []);
    rooms_html += generate_room_container_html(room_id, room_name, room_display_number, components_html, dropdown_html);

    room_display_number++;
  });

  main_container.innerHTML = rooms_html;
  apply_room_background_colors();
  init_dropdown_events();
};

const show_last_log = (log_data) => {
  const component_id = log_data.component_id;
  const room_id = log_data.room_id;
  const value = log_data.value;
  const value_unit = log_data.value_unit;
  const datetime = log_data.datetime;
  const log_id = log_data.log_id;
  const component_name = log_data.component_name;

  const existing_log_container = document.querySelector(`.js-component__container[data-component_id="${component_id}"]`);

  if (existing_log_container) {
    update_existing_component(existing_log_container, component_id, value, value_unit, datetime, log_id);
  } else {
    create_new_component_in_room(component_id, component_name, value, value_unit, datetime, log_id, room_id);
  }
};

const update_existing_component = (container, component_id, value, value_unit, datetime, log_id) => {
  const level_element = container.querySelector('.c-card__level');

  if (LIGHT_COMPONENT_IDS.includes(parseInt(component_id))) {
    const is_on = parseInt(value) > 0;
    const brightness_text = is_on ? `${value} ${value_unit}` : 'Off';

    if (level_element) {
      level_element.textContent = brightness_text;
    }
    container.setAttribute('aria-pressed', is_on.toString());
  } else if (SERVO_COMPONENT_IDS.includes(parseInt(component_id))) {
    const is_unlocked = parseInt(value) > 0;
    const servo_text = is_unlocked ? 'Unlocked' : 'Locked';

    if (level_element) {
      level_element.textContent = servo_text;
    }
    container.setAttribute('aria-pressed', is_unlocked.toString());
  } else {
    const capacity_element = container.querySelector('.c-card__capacity');
    const formatted_date = new Date(datetime);

    if (level_element) {
      level_element.textContent = `${value} ${value_unit}`;
    }
    if (capacity_element) {
      capacity_element.textContent = format_date_time(formatted_date);
    }
  }

  container.setAttribute('data-log_id', log_id);
};

const create_new_component_in_room = (component_id, component_name, value, value_unit, datetime, log_id, room_id) => {
  const room_container = document.querySelector(`.js-room__container[data-room_id="${room_id}"]`);
  if (!room_container) return;

  const components_container = room_container.querySelector('.c-room__components');
  const dropdown_element = room_container.querySelector('.c-component-dropdown');

  if (components_container) {
    const component_card_html = generate_smart_component_card_html(component_id, component_name, value, value_unit, datetime, log_id, room_id);

    components_container.insertAdjacentHTML('beforeend', component_card_html);

    // Add to dropdown if not already there
    if (dropdown_element) {
      const existing_checkbox = dropdown_element.querySelector(`input[value="${component_id}"]`);
      if (!existing_checkbox) {
        const dropdown_menu = dropdown_element.querySelector('.c-dropdown-menu');
        const new_option_html = generate_dropdown_option_html(component_id, component_name, room_id, false);
        dropdown_menu.insertAdjacentHTML('beforeend', new_option_html);
      }
    }

    // Apply background color to new component
    const new_log_container = components_container.querySelector(`.js-component__container[data-component_id="${component_id}"]`);
    if (new_log_container) {
      const room_number = parseInt(room_container.dataset.room_number);
      if (room_number % 2 === 0) {
        new_log_container.classList.add('c-white-background');
      } else {
        new_log_container.classList.add('c-grey-background');
      }
    }
  }
};
// #endregion

// #region ***  Utility Functions                       ***********
const format_date_time = (date_object) => {
  return date_object.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
};
// #endregion

// #region ***  Data Access Functions                   ***********
const get_last_component_logs = async () => {
  try {
    const url_parameters = new URLSearchParams(window.location.search);
    const page_url_param = parseInt(url_parameters.get('page'));
    const request_url = `${api_endpoint}/components/last/${page_url_param}/`;
    const server_response = await fetch(request_url);
    const json_data = await server_response.json();
    return json_data;
  } catch (error) {
    console.error('Error fetching component logs:', error);
    return [];
  }
};

const get_all_components = async () => {
  try {
    const request_url = `${api_endpoint}/components/`;
    const server_response = await fetch(request_url);
    const json_data = await server_response.json();
    return json_data;
  } catch (error) {
    console.error('Error fetching components:', error);
    return [];
  }
};

const get_all_rooms = async () => {
  try {
    const request_url = `${api_endpoint}/rooms/`;
    const server_response = await fetch(request_url);
    const json_data = await server_response.json();
    return json_data;
  } catch (error) {
    console.error('Error fetching rooms:', error);
    return [];
  }
};

const get_components_in_page = async () => {
  try {
    const url_parameters = new URLSearchParams(window.location.search);
    const page_id = parseInt(url_parameters.get('page'));
    const request_url = `${api_endpoint}/pages/${page_id}/components/`;
    const server_response = await fetch(request_url);
    const json_data = await server_response.json();
    return json_data;
  } catch (error) {
    console.error('Error fetching page components:', error);
    return [];
  }
};

const update_component_in_page = async (component_id, is_component_selected) => {
  const url_parameters = new URLSearchParams(window.location.search);
  const page_id = parseInt(url_parameters.get('page'));

  try {
    if (is_component_selected) {
      const request_url = `${api_endpoint}/pages/${page_id}/components/`;
      await fetch(request_url, {
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
      await fetch(request_url, {
        method: 'DELETE',
      });
    }
    return true;
  } catch (error) {
    console.error('Error updating component in page:', error);

    // Revert checkbox state on error
    const checkbox_element = document.querySelector(`input[value="${component_id}"]`);
    if (checkbox_element) {
      checkbox_element.checked = !is_component_selected;
      const parent_dropdown = checkbox_element.closest('.c-component-dropdown');
      if (parent_dropdown) {
        update_dropdown_label(parent_dropdown);
        update_check_all_button(parent_dropdown);
      }
    }
    return false;
  }
};

const get_inhabitant_name_by_card_id = async (card_id) => {
  try {
    const request_url = `${api_endpoint}/entered/${card_id}/last/`;
    const server_response = await fetch(request_url);
    const json_data = await server_response.json();
    return json_data;
  } catch (error) {
    console.error('Error fetching inhabitant name:', error);
    return 'Unknown';
  }
};
// #endregion

// #region ***  Socket Event Listeners                  ***********
const listen_to_socket = () => {
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
    show_last_log(data);
  });

  listen_to_light_control_feedback();
  listen_to_door_control_feedback();
};
// #endregion

// #region ***  Initialization                          ***********
const init = () => {
  console.log('DOM loaded');
  show_dropdown();
  show_all_rooms_and_components();
  listen_to_socket();
  init_component_card_events();
};

document.addEventListener('DOMContentLoaded', init);
// #endregion

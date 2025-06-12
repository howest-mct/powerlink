'use strict';

const lan_ip = `http://${window.location.hostname}:8000`;
const socket_connection = io(lan_ip);
const api_endpoint = `http://localhost:8000/api/v1`;

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
  20: `img/svg/power.svg`,
  21: `img/svg/toggle-left.svg`,
  22: `img/svg/thermometer.svg`,
};
// #endregion

// #region ***  HTML Generation Functions               ***********
const generateChartParams = async (component_id, component_name, timeframe) => {
  const component_history = await getComponentHistory(component_id, timeframe);

  if (!component_history || component_history.length === 0) {
    return null;
  }

  const chart_data = [];
  component_history.forEach((entry) => {
    const date_time = new Date(entry.chart_date).getTime();
    const value = parseFloat(entry.average_value) || 0;
    chart_data.push({
      x: date_time,
      y: value,
    });
  });

  chart_data.sort((a, b) => a.x - b.x);

  const options = {
    series: [
      {
        name: component_name,
        data: chart_data,
      },
    ],
    chart: {
      height: 350,
      type: 'line',
      zoom: {
        enabled: true,
      },
      toolbar: {
        show: true,
      },
    },
    colors: ['#77B6EA'],
    dataLabels: {
      enabled: false,
    },
    stroke: {
      curve: 'smooth',
      width: 3,
    },
    title: {
      text: component_name + ' - ' + timeframe.toUpperCase() + ' History',
      align: 'left',
    },
    grid: {
      borderColor: '#e7e7e7',
    },
    markers: {
      size: 4,
    },
    xaxis: {
      type: 'datetime',
      title: {
        text: 'Time',
      },
    },
    yaxis: {
      title: {
        text: 'Value',
      },
    },
    legend: {
      position: 'top',
      horizontalAlign: 'right',
    },
  };

  return options;
};

const generateChartParams24H = (component_id, component_name) => {
  return generateChartParams(component_id, component_name, '24h');
};

const generateChartParams7D = (component_id, component_name) => {
  return generateChartParams(component_id, component_name, '7d');
};

const generateChartParams14D = (component_id, component_name) => {
  return generateChartParams(component_id, component_name, '14d');
};

const generateComponentCardHtml = (component_id, component_name, component_log) => {
  const icon_path = component_icons[component_id] || 'img/svg/lightning.svg';
  let current_value = 'No data';
  let last_updated = 'Never';
  let log_id = '';

  if (component_log) {
    current_value = component_log.value + ' ' + (component_log.value_unit || '');
    last_updated = formatDateTime(component_log.datetime);
    log_id = component_log.log_id;
  }

  return `
    <div class="c-component__container js-component__container" 
         data-component_id="${component_id}" 
         data-log_id="${log_id}">
      <div class="c-card">
        <div class="c-card__chart">
          <div id="chart_${component_id}" class="apex-chart"></div>
        </div>
      </div>
    </div>
  `;
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
  if (is_checked) {
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

// #region ***  Chart Functions                         ***********
const renderChart = async (component_id, component_name, timeframe) => {
  const chart_element_id = 'chart_' + component_id;
  const chart_container = document.getElementById(chart_element_id);

  const chart_options = await generateChartParams(component_id, component_name, timeframe);

  if (chart_container.chart) {
    chart_container.chart.destroy();
  }

  chart_container.chart = new ApexCharts(chart_container, chart_options);
  chart_container.chart.render();
};

const initTimeframeButtons = () => {
  document.addEventListener('click', async (event) => {
    if (event.target.classList.contains('c-btn--timeframe')) {
      const component_id = parseInt(event.target.dataset.component);
      const timeframe = event.target.dataset.timeframe;

      const card_container = event.target.closest('.c-component__container');
      const all_buttons = card_container.querySelectorAll('.c-btn--timeframe');

      all_buttons.forEach((btn) => {
        btn.classList.remove('active');
      });

      event.target.classList.add('active');

      const component_name = card_container.querySelector('.c-card__title').textContent;

      await renderChart(component_id, component_name, timeframe);
    }
  });
};
// #endregion

// #region ***  Dropdown Functions                      ***********
const createComponentDropdown = (room_id, all_components, components_in_current_page) => {
  let dropdown_options_html = `<div class="c-dropdown-option c-check-all-option" data-room="${room_id}">Check All</div>`;

  const page_component_ids = [];
  components_in_current_page.forEach((component) => {
    page_component_ids.push(component.component_id);
  });

  all_components.forEach((component) => {
    let is_component_checked = false;

    page_component_ids.forEach((page_component_id) => {
      if (page_component_id === component.component_id) {
        is_component_checked = true;
      }
    });

    dropdown_options_html += generateDropdownOptionHtml(component.component_id, component.component_name, room_id, is_component_checked);
  });

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
      all_menus.forEach((menu) => {
        if (menu !== dropdown_menu) {
          menu.style.display = 'none';
        }
      });

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
      all_checkboxes.forEach((checkbox) => {
        if (!checkbox.checked) {
          all_boxes_checked = false;
        }
      });

      all_checkboxes.forEach((checkbox) => {
        if (all_boxes_checked) {
          checkbox.checked = false;
        } else {
          checkbox.checked = true;
        }
        sendComponentSelection(checkbox);
      });

      updateDropdownLabel(clicked_dropdown);

      if (all_boxes_checked) {
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
      all_menus.forEach((menu) => {
        menu.style.display = 'none';
      });
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
    trigger_button.textContent = checked_checkboxes.length + ' Components Selected';
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

  if (update_was_successful) {
    socket_connection.emit('BF2_component_selection', {
      component_id: component_id,
      room_id: room_id,
      selected: is_checkbox_checked,
    });

    let component_card = document.querySelector('.js-component__container[data-component_id="' + component_id + '"]');

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
  const url_parameters = new URLSearchParams(window.location.search);
  const page_parameter = parseInt(url_parameters.get('page'));

  const log_url = api_endpoint + '/components/last/' + page_parameter + '/';
  const log_response = await fetch(log_url);
  const all_component_logs = await log_response.json();

  let component_log = null;
  all_component_logs.forEach((log) => {
    if (log.component_id === component_id) {
      component_log = log;
    }
  });

  const components_url = api_endpoint + '/components/';
  const components_response = await fetch(components_url);
  const all_components = await components_response.json();

  let component_details = null;
  all_components.forEach((comp) => {
    if (comp.component_id === component_id) {
      component_details = comp;
    }
  });

  if (!component_details) {
    return;
  }

  const component_card_html = generateComponentCardHtml(component_id, component_details.component_name, component_log);

  const room_container = document.querySelector('.js-room__container[data-room_id="' + room_id + '"]');
  if (room_container) {
    const components_container = room_container.querySelector('.c-room__components');
    if (components_container) {
      components_container.insertAdjacentHTML('beforeend', component_card_html);

      const new_component_card = components_container.querySelector('.js-component__container[data-component_id="' + component_id + '"]');
      if (new_component_card) {
        const room_number = parseInt(room_container.dataset.room_number);
        if (room_number % 2 === 0) {
          new_component_card.classList.add('c-white-background');
        } else {
          new_component_card.classList.add('c-grey-background');
        }
      }

      await renderChart(component_id, component_details.component_name, '24h');
    }
  }
};
// #endregion

// #region ***  Callback-Visualisation - show___         ***********
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
  const all_rooms = await getAllRooms();
  const all_components = await getAllComponents();
  const all_component_logs = await getLastComponentLogs();
  const components_in_page = await getComponentsInPage();

  const components_grouped_by_room = {};
  all_components.forEach((component) => {
    if (!components_grouped_by_room[component.room_id]) {
      components_grouped_by_room[component.room_id] = [];
    }
    components_grouped_by_room[component.room_id].push(component);
  });

  const logs_by_component_id = {};
  all_component_logs.forEach((log) => {
    logs_by_component_id[log.component_id] = log;
  });

  const page_component_ids = [];
  components_in_page.forEach((component) => {
    page_component_ids.push(component.component_id);
  });

  let rooms_html = '';
  const main_container = document.querySelector('.js-main');

  all_rooms.forEach((room, room_index) => {
    const room_components = components_grouped_by_room[room.room_id] || [];

    let components_html = '';

    room_components.forEach((component) => {
      let component_is_in_page = false;
      page_component_ids.forEach((page_component_id) => {
        if (page_component_id === component.component_id) {
          component_is_in_page = true;
        }
      });

      const component_log = logs_by_component_id[component.component_id];

      if (component_is_in_page && component_log) {
        components_html += generateComponentCardHtml(component.component_id, component.component_name, component_log);
      }
    });

    const dropdown_html = createComponentDropdown(room.room_id, room_components, components_in_page);

    rooms_html += generateRoomContainerHtml(room.room_id, room.room_name, room_index, components_html, dropdown_html);
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

  const charts_to_render = [];
  all_rooms.forEach((room) => {
    const room_components = components_grouped_by_room[room.room_id] || [];
    room_components.forEach((component) => {
      let component_is_in_page = false;
      page_component_ids.forEach((page_component_id) => {
        if (page_component_id === component.component_id) {
          component_is_in_page = true;
        }
      });

      if (component_is_in_page) {
        charts_to_render.push(renderChart(component.component_id, component.component_name, '24h'));
      }
    });
  });

  for (let i = 0; i < charts_to_render.length; i++) {
    await charts_to_render[i];
  }

  initDropdownEvents();
  initTimeframeButtons();
  updateAllDropdownLabels();
};

const updateAllDropdownLabels = () => {
  const dropdowns = document.querySelectorAll('.c-component-dropdown');
  dropdowns.forEach((dropdown) => {
    updateDropdownLabel(dropdown);
    updateCheckAllButton(dropdown);
  });
};

const showAllLastLogs = (json_data) => {
  let rooms_html = '';
  const main_container = document.querySelector('.js-main');

  const room_components = {};
  json_data.forEach((schedule_item) => {
    const room_id = schedule_item.room_id;
    if (!room_components[room_id]) {
      room_components[room_id] = [];
    }
    room_components[room_id].push(schedule_item);
  });

  let room_display_number = 0;

  Object.keys(room_components).forEach((room_id) => {
    const room_data = room_components[room_id];
    const room_name = room_data[0].room_name;

    let components_html = '';

    room_data.forEach((item) => {
      components_html += generateComponentCardHtml(item.component_id, item.component_name, item);
    });

    const dropdown_html = createComponentDropdown(room_id, room_data, []);

    rooms_html += generateRoomContainerHtml(room_id, room_name, room_display_number, components_html, dropdown_html);

    room_display_number++;
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
};

const showLastLog = (log_data) => {
  const component_id = log_data.component_id;
  const room_id = log_data.room_id;
  const value = log_data.value;
  const value_unit = log_data.value_unit;
  const datetime = log_data.datetime;
  const log_id = log_data.log_id;
  const component_name = log_data.component_name;

  let existing_log_container = document.querySelector('.js-component__container[data-component_id="' + component_id + '"]');
  const formatted_date = new Date(datetime);

  if (existing_log_container) {
    const level_element = existing_log_container.querySelector('.c-card__level');
    const capacity_element = existing_log_container.querySelector('.c-card__capacity');

    if (level_element) {
      level_element.textContent = value + ' ' + value_unit;
    }

    if (capacity_element) {
      capacity_element.textContent = formatDateTime(formatted_date);
    }

    existing_log_container.setAttribute('data-log_id', log_id);
  } else {
    const room_container = document.querySelector('.js-room__container[data-room_id="' + room_id + '"]');
    if (room_container) {
      const components_container = room_container.querySelector('.c-room__components');
      const dropdown_element = room_container.querySelector('.c-component-dropdown');

      if (components_container) {
        const component_card_html = generateComponentCardHtml(component_id, component_name, log_data);

        components_container.innerHTML += component_card_html;

        if (dropdown_element) {
          const existing_checkbox = dropdown_element.querySelector('input[value="' + component_id + '"]');
          if (!existing_checkbox) {
            const dropdown_menu = dropdown_element.querySelector('.c-dropdown-menu');
            const new_option_html = generateDropdownOptionHtml(component_id, component_name, room_id, false);
            dropdown_menu.insertAdjacentHTML('beforeend', new_option_html);
          }
        }

        const new_log_container = components_container.querySelector('.js-component__container[data-component_id="' + component_id + '"]');
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
  const page_url_param = parseInt(url_parameters.get('page'));
  const request_url = api_endpoint + '/components/last/' + page_url_param + '/';
  const server_response = await fetch(request_url);
  const json_data = await server_response.json();
  return json_data;
};

const getAllComponents = async () => {
  const request_url = api_endpoint + '/components/';
  const server_response = await fetch(request_url);
  const json_data = await server_response.json();
  return json_data;
};

const getAllRooms = async () => {
  const request_url = api_endpoint + '/rooms/';
  const server_response = await fetch(request_url);
  const json_data = await server_response.json();
  return json_data;
};

const getComponentsInPage = async () => {
  const url_parameters = new URLSearchParams(window.location.search);
  const page_id = parseInt(url_parameters.get('page'));
  const request_url = api_endpoint + '/pages/' + page_id + '/components/';
  const server_response = await fetch(request_url);
  const json_data = await server_response.json();
  return json_data;
};

const updateComponentInPage = async (component_id, is_component_selected) => {
  const url_parameters = new URLSearchParams(window.location.search);
  const page_id = parseInt(url_parameters.get('page'));

  if (is_component_selected) {
    const request_url = api_endpoint + '/pages/' + page_id + '/components/';
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
    return true;
  } else {
    const request_url = api_endpoint + '/pages/' + page_id + '/components/' + component_id + '/';
    const server_response = await fetch(request_url, {
      method: 'DELETE',
    });
    return true;
  }
};

const getComponentHistory = async (component_id, timeframe) => {
  const url = api_endpoint + '/history/' + component_id + '/' + timeframe + '/';
  const response = await fetch(url);
  const json = await response.json();
  return json;
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

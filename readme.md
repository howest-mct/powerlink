# PowerLink

PowerLink is a smart home automation system for an energy-efficient house, built around a Raspberry Pi. It combines a real-time FastAPI/Socket.IO backend, a MariaDB database, and a web dashboard to monitor and control lighting, climate, door access, and power usage — both automatically (via schedules and sensors) and manually.

## Features

- **Real-time dashboard** — live sensor and actuator state pushed to the browser over Socket.IO (no polling).
- **Climate control** — temperature sensor + potentiometer drive a heating pad and fan, with hysteresis to avoid rapid switching.
- **Lighting** — indoor LEDs (manual + scheduled) and motion-activated + light-sensor-activated outdoor lighting.
- **Access control** — RFID card reader unlocks a servo-driven door lock, tied to a reed switch to confirm the door actually opened/closed. Recognized inhabitants are logged.
- **Family / inhabitant management** — add, edit, and remove RFID card holders.
- **Schedules** — day/night schedules per component (lighting, climate) configurable from the dashboard.
- **Power monitoring** — per-component wattage via INA219 current sensors behind a TCA9548A I2C multiplexer, with a simulated battery/power-bank charge level.
- **History & insights** — logs and aggregated charts over 15 minutes, 24 hours, 7 days, and 14 days.
- **Graceful shutdown** — a long-press power button (or dashboard control) cleans up GPIO state and safely powers down the Pi.

## Tech stack

- **Backend:** Python, FastAPI, python-socketio, uvicorn
- **Database:** MariaDB / MySQL (`mysql-connector-python`)
- **Frontend:** HTML, CSS, vanilla JavaScript, Socket.IO client
- **Hardware I/O:** RPi.GPIO / rpi-lgpio, spidev, smbus

## Hardware

- Raspberry Pi
- DS18B20 temperature sensor
- MCP3008 ADC (potentiometer + light sensor)
- LDR light sensor
- SR501 PIR motion sensor
- MFRC522 RFID reader
- Reed switch + SG90 servo (door lock)
- INA219 current/power monitors + TCA9548A I2C multiplexer
- PCF8574 I2C I/O expander
- 16x2 LCD display (PCF8574-based)
- Heating pad, 5V fan, indoor/outdoor LEDs
- 2N2222A / SS8050 / TIP120 transistors, MP1584EN buck converter, 18650 Li-ion charger

Datasheets for all components are in [docs/components](docs/components).

## Project structure

```
backend/           FastAPI app, models, and database repositories
frontend/           Dashboard pages (home, family, schedules, insights)
database/           SQL schema and ERD
docs/               Setup guides and component datasheets
fritzing/            Breadboard and electrical schematics
```

## Getting started

1. **Database** — import [database/power_link.sql](database/power_link.sql) into MariaDB/MySQL.
2. **Configuration** — copy `backend/config_example.ini` to `backend/config.ini` and fill in your database credentials.
3. **Dependencies**

   ```bash
   python -m venv venv
   source venv/bin/activate   # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

4. **Run the backend**

   ```bash
   python backend/app.py
   ```

   The API is served at `http://<host>:8000/api/v1`.

5. **Frontend** — serve the `frontend/` folder (e.g. via Apache or a static file server) and open `index.html`.

The GPIO/hardware-dependent code only runs on a Raspberry Pi with the sensors and actuators wired up as described in [docs/dev/commands.md](docs/dev/commands.md) and the [fritzing schematics](fritzing).

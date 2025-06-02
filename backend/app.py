# region Setup -----------------------------------------
import asyncio
import socketio
import uvicorn
import logging
from RPi import GPIO
import time
import datetime
import socket

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from repositories.DataRepository import DataRepository
from models.backend_models import Log, DTOLog, Schedule, DTOSchedule, Card, DTOCard

from models.device_models import (
    DS18B20,
    LCD_Display,
    DCMotor,
    HeatingPad,
    LED,
    SolenoidLock,
    MCP3008,
    TCA9548A,
    RFIDReader,
    PowerMonitoringSystem,
)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True,
)
logger = logging.getLogger(__name__)
# endregion Setup ********************************

# region Global Variables ---------------------------------
# Database IDs
heater_id = 1
airco_id = 2
led_bottom_id = 3
led_top_id = 4
led_outdoors_id = 5
solenoid_lock_id = 6
motion_sensor_id = 7
button_lights_id = 8
reed_switch_id = 9
card_reader_id = 10
temp_sensor_id = 11
light_sensor_id = 12
wh_led_bottom_id = 13
wh_led_top_id = 14
wh_heater_id = 15
wh_airco_id = 16
wh_bat_in_id = 17
wh_bat_out_id = 18
button_power_id = 19

# Devices
MOTION_SENSOR = None
LED_BUTTON = None
POWER_BUTTON = None
REED_SWITCH = None
TEMP_SENSOR = None
CARD_READER = None
LCD = None
DOOR_LOCK = None
LED_OUTDOORS = None
LED_BOTTOM = None
LED_TOP = None
HEATING = None
AIRCO = None
MCP = None
I2C_EXPANDER = None

# Values and States
raspi_power = None
motion_detected = None
prev_state_motion = False
last_motion_time = None
led_top_last_state = None
switch_state = False
switch_state_power = False
last_log_time_switch = 0
previous_state_switch = False
last_state_led = None
temp_id = None
temp = None
pot_value = None
ldr_value = None
scanned_card = None
lcd_string = None
door_state = None
led_outdoors_brightness = None
led_bottom_brightness = None
led_top_brightness = None
heating_value = None
airco_value = None
serial_string = None
power_monitor = None
current_usage = 0.0
battery_level = 0.0
kw_led_bottom = 0.0
kw_led_top = 0.0
kw_heating = 0.0
kw_airco = 0.0
current_usage = None
battery_level = None
ip_address = None

GPIO.setmode(GPIO.BCM)
# endregion Global Variables **************************


# region Functions ---------------------------------
def lights_button(pin):
    global switch_state, button_lights_id, led_bottom_id
    try:
        switch_state = not switch_state
        DataRepository.create_log(switch_state, button_lights_id)
        DataRepository.create_log(100, led_bottom_id)
        print("Button pressed, switch state:", switch_state)
    except Exception as e:
        logger.error(f"Error in lights_button: {e}")


def power_button(pin):
    global switch_state_power, button_power_id
    try:
        switch_state_power = not switch_state_power
        DataRepository.create_log(switch_state_power, button_power_id)
        print("Button pressed, switch state:", switch_state_power)
    except Exception as e:
        logger.error(f"Error in power_button: {e}")


def motion_callback(pin):
    global LED_TOP, motion_sensor_id, led_top_id

    try:
        if GPIO.input(pin) == GPIO.LOW:
            LED_TOP.set_brightness(100)
            DataRepository.create_log(100, led_top_id)
            DataRepository.create_log(1, motion_sensor_id)
            print("Motion detected: LED TOP ON")
        else:
            LED_TOP.set_brightness(0)
            DataRepository.create_log(0, led_top_id)
            DataRepository.create_log(0, motion_sensor_id)
            print("No motion: LED TOP OFF")
    except Exception as e:
        logger.error(f"Error in motion_callback: {e}")


async def lights_top():
    global LED_TOP, MOTION_SENSOR, led_top_id, motion_sensor_id, prev_state_motion, motion_detected
    while True:
        try:
            motion_detected = MOTION_SENSOR.motion_detected()

            if motion_detected != prev_state_motion:
                if motion_detected:
                    LED_TOP.set_brightness(100)
                    DataRepository.create_log(100, led_top_id)
                    DataRepository.create_log(1, motion_sensor_id)
                    print("LED TOP: ON")
                else:
                    LED_TOP.set_brightness(0)
                    DataRepository.create_log(0, led_top_id)
                    print("LED TOP: OFF")
                prev_state_motion = motion_detected

        except Exception as e:
            logger.error(f"Error in lights_top: {e}")

        await asyncio.sleep(0.05)


def lights_bottom():
    global LED_BOTTOM, switch_state, last_log_time_switch, previous_state_switch
    try:
        if switch_state and not previous_state_switch:
            current_time = time.time()
            if current_time - last_log_time_switch >= 1:
                LED_BOTTOM.set_brightness(100)
                DataRepository.create_log(1, button_lights_id)
                last_log_time_switch = current_time
            previous_state_switch = True
        elif not switch_state:
            LED_BOTTOM.off()
            previous_state_switch = False
    except Exception as e:
        logger.error(f"Error in lights_bottom: {e}")


def lights_outdoors():
    global LED_OUTDOORS, MCP, last_state_led, ldr_value, light_sensor_id, led_outdoors_id
    try:
        ldr_value = round((MCP.read_channel(1) * 100) / 1023, 0)
        top_limit = 75
        low_limit = 70
        if last_state_led is None or not last_state_led:
            current_state = ldr_value > top_limit
        else:
            current_state = ldr_value >= low_limit
        if current_state != last_state_led:
            if current_state:
                LED_OUTDOORS.set_brightness(100)
                DataRepository.create_log(100, led_outdoors_id)
                DataRepository.create_log(ldr_value, light_sensor_id)
            else:
                LED_OUTDOORS.off()
                DataRepository.create_log(0, led_outdoors_id)
                DataRepository.create_log(ldr_value, light_sensor_id)
            last_state_led = current_state
    except Exception as e:
        logger.error(f"Error in lights_outdoors: {e}")


def handle_tag(card_id):
    global scanned_card
    scanned_card = card_id


async def front_door():
    global scanned_card, DOOR_LOCK, REED_SWITCH, card_reader_id, solenoid_lock_id, reed_switch_id
    while True:
        if scanned_card is not None:
            print("scanned card", scanned_card)
            try:
                DataRepository.read_card_by_id(scanned_card)
                DataRepository.create_log(scanned_card, card_reader_id)
                DOOR_LOCK.unlock()
                logger.debug("Door is unlocked")
                DataRepository.create_log(1, solenoid_lock_id)
                start_time = time.time()

                while GPIO.input(REED_SWITCH) == 1:
                    if time.time() - start_time > 3:
                        logger.info("Door did not open in time (3 seconds)")
                        break
                    await asyncio.sleep(0.1)

                if GPIO.input(REED_SWITCH) == 0:
                    logger.debug("Door is opened")
                    DataRepository.create_log(1, reed_switch_id)
                    start_time = time.time()
                    while GPIO.input(REED_SWITCH) == 0:
                        if time.time() - start_time > 3:
                            logger.info("Door did not close in time (3 seconds)")
                            break
                        await asyncio.sleep(0.1)

                    if GPIO.input(REED_SWITCH) == 1:
                        logger.debug("Door is closed")
                        DataRepository.create_log(0, reed_switch_id)
                DOOR_LOCK.lock()
                logger.debug("Door is locked")
                DataRepository.create_log(0, solenoid_lock_id)

            except Exception as e:
                logger.error(f"Error: {e}")

            finally:
                scanned_card = None
        else:
            await asyncio.sleep(0.1)


def get_ip_address():
    global ip_address
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    except socket.error as e:
        logger.error(f"Error getting IP address: {e}")
        return None


async def display_lcd():
    global LCD, lcd_string, ip_address, temp, current_usage, battery_level
    while True:
        try:
            LCD.string("IP Address:", 1)
            LCD.string(get_ip_address(), 2)
            await asyncio.sleep(2)
            LCD.string("Current temp:", 1)
            LCD.string(f"{temp} degrees C", 2)
            await asyncio.sleep(2)
            LCD.string("Current Watt:", 1)
            LCD.string(f"{current_usage}W", 2)
            await asyncio.sleep(2)
            LCD.string("Battery level:", 1)
            LCD.string(f"{battery_level}%", 2)
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Error in display_lcd: {e}")
            lcd_string = None
            await asyncio.sleep(1)


def initialize_power_monitoring():
    global power_monitor

    try:
        power_monitor = PowerMonitoringSystem(tca_address=0x70, ina_address=0x40)
        logger.info("Power monitoring system with TCA9548A initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize power monitoring: {e}")
        power_monitor = None


async def get_wattage():
    global power_monitor, current_usage, battery_level
    global kw_led_bottom, kw_led_top, kw_heating, kw_airco

    while True:
        try:
            if power_monitor is None:
                logger.warning(
                    "Power monitor not initialized, attempting to reinitialize..."
                )
                initialize_power_monitoring()
                await asyncio.sleep(5)
                continue

            readings = power_monitor.read_all_sensors()

            kw_led_bottom = readings.get("led_bottom", 0.0)
            kw_led_top = readings.get("led_top", 0.0)
            kw_heating = readings.get("heating", 0.0)
            kw_airco = readings.get("airco", 0.0)

            battery_in_power = readings.get("battery_in", 0.0)
            battery_out_power = readings.get("battery_out", 0.0)

            current_usage = kw_led_bottom + kw_led_top + kw_heating + kw_airco

            if battery_out_power > 0.1:
                battery_level = max(
                    0, min(100, (battery_in_power / battery_out_power) * 100)
                )
            else:
                battery_level = 100.0

            DataRepository.create_log(kw_led_bottom, wh_led_bottom_id)
            DataRepository.create_log(kw_led_top, wh_led_top_id)
            DataRepository.create_log(kw_heating, wh_heater_id)
            DataRepository.create_log(kw_airco, wh_airco_id)
            DataRepository.create_log(battery_in_power, wh_bat_in_id)
            DataRepository.create_log(battery_out_power, wh_bat_out_id)

            logger.debug(
                f"Power readings - LED Bottom: {kw_led_bottom:.3f}W, "
                f"LED Top: {kw_led_top:.3f}W, Heating: {kw_heating:.3f}W, "
                f"Airco: {kw_airco:.3f}W, Total: {current_usage:.3f}W, "
                f"Battery: {battery_level:.1f}%"
            )

        except Exception as e:
            logger.error(f"Error in get_wattage: {e}")
            if power_monitor:
                try:
                    power_monitor.close()
                except:
                    pass
                power_monitor = None

        await asyncio.sleep(3)


# endregion Functions ****************************


# region Async Containers ---------------------------------
async def run_lights_outdoors():
    while True:
        lights_outdoors()
        await asyncio.sleep(0.5)


async def run_lights_bottom():
    while True:
        lights_bottom()
        await asyncio.sleep(0.1)


async def run_get_temp():
    global temp
    while True:
        temp = TEMP_SENSOR.get_temp(temp_id)
        print("Current temperature:", temp)
        await asyncio.sleep(3)


# endregion Async Wrappers ******************************


# region App Setup ---------------------------------
@asynccontextmanager
async def lifespan_manager(app: FastAPI):
    logger.info("Starting application...")
    GPIO.setmode(GPIO.BCM)
    try:
        global MOTION_SENSOR, LED_BUTTON, REED_SWITCH, TEMP_SENSOR
        global LCD, DOOR_LOCK, LED_OUTDOORS, LED_BOTTOM, LED_TOP
        global HEATING, AIRCO, MCP, CARD_READER
        global temp_id, ip_address

        MOTION_SENSOR = 26
        GPIO.setup(MOTION_SENSOR, GPIO.IN)
        GPIO.add_event_detect(
            MOTION_SENSOR, GPIO.BOTH, callback=motion_callback, bouncetime=300
        )
        LED_BUTTON = 13
        GPIO.setup(LED_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        POWER_BUTTON = 27
        GPIO.setup(POWER_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        REED_SWITCH = 22
        GPIO.setup(REED_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        TEMP_SENSOR = DS18B20()
        CARD_READER = RFIDReader(handle_tag)
        LCD = LCD_Display(0x38, 5, 6)
        DOOR_LOCK = SolenoidLock(15)
        LED_OUTDOORS = LED(14)
        LED_BOTTOM = LED(25)
        LED_TOP = LED(24)
        HEATING = HeatingPad(16)
        AIRCO = DCMotor(12)
        MCP = MCP3008(1)
        I2C_EXPANDER = TCA9548A()

        temp_id = TEMP_SENSOR.get_id()
        ip_address = get_ip_address()

        tasks = [
            # asyncio.create_task(run_lights_outdoors()), !!!!
            # asyncio.create_task(lights_top()),
            asyncio.create_task(run_lights_bottom()),
            # asyncio.create_task(run_get_temp()),
            # asyncio.create_task(front_door()), !!!!!
            # asyncio.create_task(display_lcd()),
            # asyncio.create_task(get_wattage()),
        ]

        GPIO.add_event_detect(
            LED_BUTTON, GPIO.FALLING, callback=lights_button, bouncetime=150
        )
        GPIO.add_event_detect(
            POWER_BUTTON, GPIO.FALLING, callback=power_button, bouncetime=150
        )

        yield

    finally:
        logger.info("Shutting down application...")
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        CARD_READER.cleanup()
        LCD.close()
        DOOR_LOCK.cleanup()
        LED_OUTDOORS.cleanup()
        LED_BOTTOM.cleanup()
        LED_TOP.cleanup()
        HEATING.cleanup()
        AIRCO.cleanup()
        MCP.close()
        GPIO.cleanup()
        I2C_EXPANDER.close()
        power_monitor.close()
        logger.info("GPIO cleaned up. Bye!")


app = FastAPI(lifespan=lifespan_manager)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi", logger=True)
sio_app = socketio.ASGIApp(sio, app)

ENDPOINT = "/api/v1"
# endregion App Setup ********************************


# region FastAPI Endpoints ---------------------------------
@app.get("/")
async def root():
    return "Server werkt, maar hier geen API endpoint gevonden."


@app.get(ENDPOINT + "/logs/", response_model=list[Log], tags=["logs"])
async def get_all_logs():
    data = DataRepository.read_all_logs()
    if not data:
        raise HTTPException(status_code=404, detail="No logs found in the database")
    return data


@app.get(ENDPOINT + "/logs/{id}/all/", response_model=list[Log], tags=["logs"])
async def get_all_logs_by_component_id(id: int):
    data = DataRepository.read_all_logs_by_component_id(id)
    if not data:
        raise HTTPException(status_code=404, detail=f"No logs for component ID {id}")
    return data


@app.get(ENDPOINT + "/logs/{id}/last/", response_model=Log, tags=["logs"])
async def get_last_log_by_id(id: int):
    data = DataRepository.read_last_log_by_component_id(id)
    if not data:
        raise HTTPException(
            status_code=404, detail=f"No last log for component ID {id}"
        )
    return data


@app.get(ENDPOINT + "/logs/{id}/24h/", response_model=list[Log], tags=["logs"])
async def get_logs_last_24_hours_by_id(id: int):
    data = DataRepository.read_logs_last_24_hours_by_component_id(id)
    if not data:
        raise HTTPException(
            status_code=404, detail=f"No logs for last 24h for component ID {id}"
        )
    return data


@app.get(ENDPOINT + "/logs/{id}/week/", response_model=list[Log], tags=["logs"])
async def get_logs_last_week_by_id(id: int):
    data = DataRepository.read_logs_last_week_by_component_id(id)
    if not data:
        raise HTTPException(
            status_code=404, detail=f"No logs for last week for component ID {id}"
        )
    return data


@app.get(ENDPOINT + "/logs/{id}/week2/", response_model=list[Log], tags=["logs"])
async def get_logs_between_1_and_2_weeks_by_component_id(id: int):
    data = DataRepository.read_logs_between_1_and_2_weeks_by_component_id(id)
    if not data:
        raise HTTPException(
            status_code=404, detail=f"No logs between 1-2 weeks for component ID {id}"
        )
    return data


@app.get(ENDPOINT + "/schedules/{id}/", response_model=Schedule, tags=["schedules"])
async def get_schedule_by_id(id: int):
    data = DataRepository.read_schedule_by_id(id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Schedule with ID {id} not found")
    return data


@app.put(ENDPOINT + "/schedules/{id}/", response_model=Schedule, tags=["schedules"])
async def update_schedule(id: int, schedule: DTOSchedule):
    existing = DataRepository.read_schedule_by_id(id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Schedule with ID {id} not found")
    updated = DataRepository.update_schedule(
        id, schedule.start_time, schedule.end_time, schedule.value, schedule.enabled
    )
    if updated == 0:
        raise HTTPException(status_code=400, detail="Failed to update schedule")
    return DataRepository.read_schedule_by_id(id)


# endregion FastAPI Endpoints *************************


# region Socket.IO Handlers ---------------------------------
@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")


# endregion Socket.IO Handlers *************************

# region Run The App ---------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "app:sio_app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=False,
        reload_dirs=["backend"],
    )
# endregion Run The App **************************

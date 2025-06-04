# region Setup -----------------------------------------
import asyncio
import socketio
import uvicorn
import logging
from RPi import GPIO
import time
import datetime
import socket
import threading
import re
import subprocess

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from repositories.DataRepository import DataRepository
from models.backend_models import (
    Log,
    DTOLog,
    Schedule,
    DTOSchedule,
    Card,
    DTOCard,
    UpdatedSchedule,
)

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
fan_id = 2
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
pot_id = 20

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
motion_detected = False
last_motion_time = 0
light_duration = 10
last_motion_time = None
prev_state_motion = False
led_top_last_state = None
switch_state = False
switch_state_power = False
last_log_time_switch = 0
previous_state_switch = False
last_state_led = None
temp_id = None
temp = None
target_temp = None
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
def gpio_keep_alive():
    while True:
        front_door()
        lights_outdoors()
        time.sleep(0.5)


def lights_button(pin):
    global switch_state, button_lights_id, led_bottom_id
    try:
        switch_state = not switch_state
        DataRepository.create_log(switch_state, button_lights_id)
        if switch_state:
            DataRepository.create_log(100, led_bottom_id)
        else:
            DataRepository.create_log(0, led_bottom_id)
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


def motion_sensor_callback(pin):
    global motion_detected, last_motion_time
    if GPIO.input(pin):
        motion_detected = True
        last_motion_time = time.time()
        print("Motion detected!")


async def lights_top():
    global LED_TOP, led_top_id, motion_sensor_id, prev_state_motion, motion_detected, last_motion_time

    while True:
        try:
            if motion_detected == True:
                print("Motion detected, turning on LED_TOP")
        except Exception as e:
            logger.error(f"Error in lights_top: {e}")
            motion_detected = False

        await asyncio.sleep(0.1)


def lights_bottom():
    global LED_BOTTOM, switch_state, last_log_time_switch, previous_state_switch
    try:
        if switch_state and not previous_state_switch:
            current_time = time.time()
            if current_time - last_log_time_switch >= 1:
                LED_BOTTOM.set_brightness(100)
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
        top_limit = 35
        low_limit = 30
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


def cut_card(card_id):
    return card_id[:6] + "000000"


def front_door():
    global DOOR_LOCK, REED_SWITCH, CARD_READER, scanned_card, door_state
    global solenoid_lock_id, reed_switch_id, card_reader_id

    door_state = GPIO.input(REED_SWITCH)
    scanned_card = CARD_READER.read()

    if scanned_card is not None:
        scanned_card = str(scanned_card)
        snipped_card = cut_card(scanned_card)
        print(snipped_card)

        try:
            checked_card = DataRepository.read_card_by_id(snipped_card)

            if checked_card is None:
                logger.error(f"Unauthorized card scanned: {scanned_card}")
                DataRepository.create_log(-1, card_reader_id)
                return

            DataRepository.create_log(snipped_card, card_reader_id)

            DOOR_LOCK.unlock(pull_duty=100, hold_duty=40, pull_time=0.1)
            logger.debug("Door is unlocked")
            DataRepository.create_log(1, solenoid_lock_id)

            logger.debug("Waiting for door to open")
            start_time = time.time()

            while GPIO.input(REED_SWITCH) == 1:
                if time.time() - start_time > 3:
                    logger.info("Door did not open in time (3 seconds)")
                    DOOR_LOCK.lock()
                    DataRepository.create_log(0, solenoid_lock_id)
                    return
                time.sleep(0.1)

            logger.debug("Door is opened")
            DataRepository.create_log(1, reed_switch_id)

            logger.debug("Waiting for door to close")
            start_time = time.time()

            while GPIO.input(REED_SWITCH) == 0:
                if time.time() - start_time > 3:
                    logger.info("Door did not close in time (3 seconds)")
                    DOOR_LOCK.lock()
                    DataRepository.create_log(0, solenoid_lock_id)
                    return
                time.sleep(0.1)

            logger.debug("Door is closed")
            DataRepository.create_log(0, reed_switch_id)

            DOOR_LOCK.lock()
            logger.debug("Door is locked")
            DataRepository.create_log(0, solenoid_lock_id)

        except Exception as e:
            logger.error(f"Error: {e}")


def get_ip(interface):
    try:
        output = subprocess.check_output(["ip", "a", "show", interface]).decode()
        match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", output)
        if match:
            return match.group(1)
        else:
            return "Geen IP"
    except subprocess.CalledProcessError:
        return "Interface fout"


async def display_lcd():
    global LCD, lcd_string, ip_address, temp, current_usage, battery_level
    while True:
        try:
            eth0_ip = get_ip("eth0")
            wlan0_ip = get_ip("wlan0")
            LCD.string("IP ETH0:", 1)
            LCD.string(eth0_ip, 2)
            await asyncio.sleep(3)
            LCD.string("IP WLAN0:", 1)
            LCD.string(wlan0_ip, 2)
            await asyncio.sleep(3)
            LCD.string("Current temp:", 1)
            LCD.string(f"{temp} degrees C", 2)
            await asyncio.sleep(3)
            LCD.string("Current Watt:", 1)
            LCD.string(f"{round(current_usage, 3)}W", 2)
            await asyncio.sleep(3)
            LCD.string("Battery level:", 1)
            LCD.string(f"{battery_level}%", 2)
            await asyncio.sleep(3)
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

            print(
                f"LED Bottom: {kw_led_bottom}W, LED Top: {kw_led_top}W, "
                f"Heater: {kw_heating}W, Airco: {kw_airco}W, "
                f"Battery In: {battery_in_power}W, Battery Out: {battery_out_power}W, "
                f"Current Usage: {current_usage}W, Battery Level: {battery_level}%"
            )

            DataRepository.create_log(kw_led_bottom, wh_led_bottom_id)
            DataRepository.create_log(kw_led_top, wh_led_top_id)
            DataRepository.create_log(kw_heating, wh_heater_id)
            DataRepository.create_log(kw_airco, wh_airco_id)
            DataRepository.create_log(battery_in_power, wh_bat_in_id)
            DataRepository.create_log(battery_out_power, wh_bat_out_id)

        except Exception as e:
            logger.error(f"Error in get_wattage: {e}")
            if power_monitor:
                try:
                    power_monitor.close()
                except Exception as e:
                    logger.error(f"Error closing power monitor: {e}")
                power_monitor = None

        await asyncio.sleep(3)


async def climate_control(target_temp, temp_id):
    global HEATING, AIRCO, temp, temp_sensor_id
    hysteresis = 0.5
    max_range = 2.0
    lower_bound = target_temp - hysteresis / 2
    upper_bound = target_temp + hysteresis / 2
    max_lower = target_temp - max_range
    max_upper = target_temp + max_range
    min_heater_power = 20
    min_fan_speed = 80

    try:
        while True:
            current_temp = TEMP_SENSOR.get_temp(temp_id)
            DataRepository.create_log(current_temp, temp_sensor_id)

            if current_temp < lower_bound:
                if current_temp <= max_lower:
                    heater_power = 100
                    DataRepository.create_log(100, heater_id)
                    DataRepository.create_log(0, fan_id)

                else:
                    heater_power = min_heater_power + (100 - min_heater_power) * (
                        lower_bound - current_temp
                    ) / (lower_bound - max_lower)
                    DataRepository.create_log(heater_power, heater_id)
                    DataRepository.create_log(0, fan_id)

                HEATING.set_power(max(0, min(100, heater_power)))
                AIRCO.stop()

            elif current_temp > upper_bound:
                if current_temp >= max_upper:
                    fan_speed = 100
                    DataRepository.create_log(100, fan_id)
                    DataRepository.create_log(0, heater_id)

                else:
                    fan_speed = min_fan_speed + (100 - min_fan_speed) * (
                        current_temp - upper_bound
                    ) / (max_upper - upper_bound)
                    DataRepository.create_log(fan_speed, fan_id)
                    DataRepository.create_log(0, heater_id)

                AIRCO.set_speed(max(0, min(100, fan_speed)))
                HEATING.off()

            else:
                pass

            temp = current_temp

            await asyncio.sleep(3)

    except Exception as e:
        logger.error(f"Error in climate_control: {e}")


# endregion Functions ****************************


# region Async Containers ---------------------------------


async def run_lights_bottom():
    while True:
        lights_bottom()
        await asyncio.sleep(0.1)


# endregion Async Containers ******************************


# region App Setup ---------------------------------
@asynccontextmanager
async def lifespan_manager(app: FastAPI):
    logger.info("Starting application...")
    GPIO.setmode(GPIO.BCM)

    # tasks = []

    try:
        global MOTION_SENSOR, LED_BUTTON, REED_SWITCH, TEMP_SENSOR
        global LCD, DOOR_LOCK, LED_OUTDOORS, LED_BOTTOM, LED_TOP
        global HEATING, AIRCO, MCP, CARD_READER
        global temp_id, ip_address

        MOTION_SENSOR = 26
        GPIO.setup(MOTION_SENSOR, GPIO.IN)
        LED_BUTTON = 13
        GPIO.setup(LED_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        POWER_BUTTON = 27
        GPIO.setup(POWER_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        REED_SWITCH = 22
        GPIO.setup(REED_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        TEMP_SENSOR = DS18B20()
        temp_id = TEMP_SENSOR.get_id()
        CARD_READER = RFIDReader()
        LCD = LCD_Display(0x38, 5, 6)
        DOOR_LOCK = SolenoidLock(18)
        LED_OUTDOORS = LED(14)
        LED_BOTTOM = LED(25)
        LED_TOP = LED(21)
        HEATING = HeatingPad(20)
        AIRCO = DCMotor(12)
        MCP = MCP3008(0, 1)
        I2C_EXPANDER = TCA9548A()

        threading.Thread(
            target=gpio_keep_alive,
            daemon=True,
        ).start()

        tasks = [
            asyncio.create_task(run_lights_bottom()),
            asyncio.create_task(lights_top()),
            asyncio.create_task(display_lcd()),
            asyncio.create_task(get_wattage()),
            asyncio.create_task(climate_control(25.0, temp_id)),
        ]

        GPIO.add_event_detect(
            LED_BUTTON, GPIO.FALLING, callback=lights_button, bouncetime=150
        )
        GPIO.add_event_detect(
            POWER_BUTTON, GPIO.FALLING, callback=power_button, bouncetime=150
        )

        GPIO.add_event_detect(
            MOTION_SENSOR,
            GPIO.FALLING,
            callback=motion_sensor_callback,
            bouncetime=4000,
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
        CARD_READER.cleanup()
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


@app.get(ENDPOINT + "/logs/last/", response_model=list[Log], tags=["logs"])
async def get_all_last_logs():
    data = DataRepository.read_all_last_logs()
    if not data:
        raise HTTPException(status_code=404, detail="No last logs found")
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


@app.get(
    ENDPOINT + "/schedules/{frame_name}/",
    response_model=list[Schedule],
    summary="Retrieve all schedules",
    response_description="A list of all available schedules",
    tags=["schedules"],
)
async def get_all_schedules(frame_name: str):
    print(frame_name)
    data = DataRepository.read_all_schedules_by_frame_id(frame_name)
    if data is None or len(data) == 0:
        raise HTTPException(
            status_code=404, detail=f"No schedules found in the database"
        )
    return data


@app.get(ENDPOINT + "/schedules/{id}/", response_model=Schedule, tags=["schedules"])
async def get_schedule_by_id(id: int):
    data = DataRepository.read_schedule_by_id(id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Schedule with ID {id} not found")
    return data


@app.put(
    ENDPOINT + "/schedules/{id}/lighting/",
    response_model=UpdatedSchedule,
    tags=["schedules"],
)
async def update_lighting_schedule(id: int, schedule: DTOSchedule):
    existing = DataRepository.read_schedule_by_id(id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Schedule with ID {id} not found")
    updated = DataRepository.update_lighting_schedule(
        id, schedule.start_time, schedule.end_time, schedule.value, schedule.enabled
    )
    if updated == 0:
        raise HTTPException(status_code=400, detail="Failed to update schedule")
    return DataRepository.read_schedule_by_id(id)


@app.get(
    ENDPOINT + "/inhabitants/{card_id}/",
    response_model=Card,
    summary="Retrieve a inhabitant by ID",
    response_description="The inhabitant with the specified ID",
    tags=["inhabitants"],
)
async def get_inhabitant_by_id(card_id: int):
    data = DataRepository.read_inhabitant_by_card_id(card_id)
    if data is None:
        raise HTTPException(
            status_code=404, detail=f"inhabitant with ID {card_id} not found"
        )
    return data


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
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False,
        reload_dirs=["backend"],
    )
# endregion Run The App **************************

# region Setup -----------------------------------------
import asyncio
import socketio
import uvicorn
import logging
from RPi import GPIO
import time
import re
import subprocess
import threading

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from repositories.DataRepository import DataRepository
from models.backend_models import (
    Log,
    Schedule,
    DTOSchedule,
    Card,
    UpdatedSchedule,
)

from models.device_models import (
    DS18B20,
    LCD_Display,
    DCMotor,
    HeatingPad,
    LED,
    MCP3008,
    TCA9548A,
    RFIDReader,
    PowerMonitoringSystem,
    ServoLock,
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
switch_state = False
switch_state_power = False
last_log_time_switch = 0
previous_state_switch = False
last_state_led = None
temp_id = None
temp = None
ldr_value = None
scanned_card = None
door_state = None
light_duration = 10
prev_led_brightness = None
power_monitor = None
current_usage = 0.0
battery_level = 0.0
kw_led_bottom = 0.0
kw_led_top = 0.0
kw_heating = 0.0
kw_airco = 0.0

GPIO.setmode(GPIO.BCM)
# endregion Global Variables **************************


# region Functions ---------------------------------
def gpio_keep_alive():
    while True:
        front_door()
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
    except Exception as e:
        logger.error(f"Error in lights_button: {e}")


def power_button(pin):
    global switch_state_power, button_power_id
    try:
        switch_state_power = not switch_state_power
        DataRepository.create_log(switch_state_power, button_power_id)
    except Exception as e:
        logger.error(f"Error in power_button: {e}")


async def lights_top():
    global LED_TOP, led_top_id, motion_sensor_id, MOTION_SENSOR, light_duration

    last_motion = 0

    prev_values = {
        "motion_sensor": None,
        "led_brightness": None,
    }

    while True:
        try:
            motion_now = GPIO.input(MOTION_SENSOR)

            if motion_now == 1 and last_motion == 0:
                GPIO.output(LED_TOP, GPIO.HIGH)

                if 1 != prev_values["motion_sensor"]:
                    DataRepository.create_log(1, motion_sensor_id)
                prev_values["motion_sensor"] = 1

                if 100 != prev_values["led_brightness"]:
                    DataRepository.create_log(100, led_top_id)
                prev_values["led_brightness"] = 100

                await asyncio.sleep(light_duration)

            elif motion_now == 0 and last_motion == 1:
                GPIO.output(LED_TOP, GPIO.LOW)

                if 0 != prev_values["motion_sensor"]:
                    DataRepository.create_log(0, motion_sensor_id)
                prev_values["motion_sensor"] = 0

                if 0 != prev_values["led_brightness"]:
                    DataRepository.create_log(0, led_top_id)
                prev_values["led_brightness"] = 0

            last_motion = motion_now

            await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"Something went wrong: {e}")
            last_motion = 0
            prev_values["motion_sensor"] = None
            prev_values["led_brightness"] = None
            await asyncio.sleep(1)


def lights_bottom():
    global LED_BOTTOM, switch_state, last_log_time_switch, previous_state_switch
    global prev_led_brightness

    try:
        if switch_state and not previous_state_switch:
            current_time = time.time()
            if current_time - last_log_time_switch >= 1:
                LED_BOTTOM.set_brightness(100)

                if 100 != prev_led_brightness:
                    DataRepository.create_log(100, led_bottom_id)
                prev_led_brightness = 100

                last_log_time_switch = current_time
            previous_state_switch = True
        elif not switch_state:
            LED_BOTTOM.off()

            if 0 != prev_led_brightness:
                DataRepository.create_log(0, led_bottom_id)
            prev_led_brightness = 0

            previous_state_switch = False
    except Exception as e:
        logger.error(f"Error in lights_bottom: {e}")
        prev_led_brightness = None


async def lights_outdoors():
    global LED_OUTDOORS, MCP, last_state_led, ldr_value, light_sensor_id, led_outdoors_id

    prev_values = {
        "ldr_value": None,
        "led_brightness": None,
    }

    while True:
        try:
            raw_ldr = MCP.read_channel(1)
            ldr_value = round((raw_ldr * 100) / 1023, 0)
            if last_state_led is None:
                last_state_led = False

            if not last_state_led:
                current_state = ldr_value > 70
            else:
                current_state = ldr_value >= 65

            if current_state != last_state_led:
                if current_state:
                    LED_OUTDOORS.set_brightness(100)
                    if 100 != prev_values["led_brightness"]:
                        DataRepository.create_log(100, led_outdoors_id)
                    prev_values["led_brightness"] = 100
                else:
                    LED_OUTDOORS.off()
                    if prev_values["led_brightness"] != 0:
                        DataRepository.create_log(0, led_outdoors_id)
                    prev_values["led_brightness"] = 0

                if ldr_value != prev_values["ldr_value"]:
                    DataRepository.create_log(ldr_value, light_sensor_id)
                prev_values["ldr_value"] = ldr_value

                last_state_led = current_state
            else:
                if ldr_value != prev_values["ldr_value"]:
                    DataRepository.create_log(ldr_value, light_sensor_id)
                    prev_values["ldr_value"] = ldr_value

            await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error in lights_outdoors: {e}")
            last_state_led = None
            prev_values["ldr_value"] = None
            prev_values["led_brightness"] = None
            await asyncio.sleep(1)


def cut_card(card_id):
    return card_id[:6] + "000000"


def front_door():
    global DOOR_LOCK, REED_SWITCH, CARD_READER, scanned_card
    global solenoid_lock_id, reed_switch_id, card_reader_id

    scanned_card = CARD_READER.read_no_block()

    if scanned_card is not None:
        scanned_card = str(scanned_card)
        snipped_card = cut_card(scanned_card)
        logger.info(f"Snipped card: {snipped_card}")

        try:
            checked_card = DataRepository.read_card_by_id(snipped_card)

            if checked_card is None:
                logger.info("Invalid card scanned")
                DataRepository.create_log(-1, card_reader_id)
                return

            logger.info("Valid card scanned")
            DataRepository.create_log(snipped_card, card_reader_id)

            if DOOR_LOCK.is_unlocked():
                logger.debug("Door is already unlocked")
                return

            DOOR_LOCK.unlock()
            logger.debug("Door is unlocked")
            DataRepository.create_log(1, solenoid_lock_id)

            logger.debug("Waiting for door to open")
            start_time = time.time()

            while GPIO.input(REED_SWITCH) == 1:
                if time.time() - start_time > 5:
                    logger.info("Door did not open in time (5 seconds) - locking again")
                    DOOR_LOCK.lock()
                    DataRepository.create_log(0, solenoid_lock_id)
                    return
                time.sleep(0.1)

            logger.debug("Door is opened")
            DataRepository.create_log(1, reed_switch_id)

            logger.debug("Waiting for door to close")
            start_time = time.time()

            while GPIO.input(REED_SWITCH) == 0:
                if time.time() - start_time > 10:
                    logger.info(
                        "Door did not close in time (10 seconds) - locking again"
                    )
                    return
                time.sleep(0.1)

            logger.debug("Door is closed")
            DataRepository.create_log(0, reed_switch_id)

            DOOR_LOCK.lock()
            logger.debug("Door is locked")
            DataRepository.create_log(0, solenoid_lock_id)

        except Exception as e:
            logger.error(f"Error: {e}")
            try:
                DOOR_LOCK.lock()
            except Exception as e:
                logger.error(f"Error locking door: {e}")


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
    global LCD, temp, current_usage, battery_level
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

    prev_values = {
        "led_bottom": None,
        "led_top": None,
        "heating": None,
        "airco": None,
        "battery_in": None,
        "battery_out": None,
    }

    while True:
        try:
            if power_monitor is None:
                initialize_power_monitoring()
                await asyncio.sleep(5)
                continue

            readings = power_monitor.read_all_sensors()

            kw_led_bottom = round(readings.get("led_bottom", 0.0), 3)
            kw_led_top = round(readings.get("led_top", 0.0), 3)
            kw_heating = round(readings.get("heating", 0.0), 3)
            kw_airco = round(readings.get("airco", 0.0), 3)

            battery_in_power = round(readings.get("battery_in", 0.0), 3)
            battery_out_power = round(readings.get("battery_out", 0.0), 3)

            current_usage = kw_led_bottom + kw_led_top + kw_heating + kw_airco

            if battery_out_power > 0.1:
                battery_level = max(
                    0, min(100, (battery_in_power / battery_out_power) * 100)
                )
            else:
                battery_level = 100.0

            if kw_led_bottom != 0 or prev_values["led_bottom"] != 0:
                DataRepository.create_log(kw_led_bottom, wh_led_bottom_id)

            if kw_led_top != 0 or prev_values["led_top"] != 0:
                DataRepository.create_log(kw_led_top, wh_led_top_id)

            if kw_heating != 0 or prev_values["heating"] != 0:
                DataRepository.create_log(kw_heating, wh_heater_id)

            if kw_airco != 0 or prev_values["airco"] != 0:
                DataRepository.create_log(kw_airco, wh_airco_id)

            if battery_in_power != 0 or prev_values["battery_in"] != 0:
                DataRepository.create_log(battery_in_power, wh_bat_in_id)

            if battery_out_power != 0 or prev_values["battery_out"] != 0:
                DataRepository.create_log(battery_out_power, wh_bat_out_id)

            prev_values["led_bottom"] = kw_led_bottom
            prev_values["led_top"] = kw_led_top
            prev_values["heating"] = kw_heating
            prev_values["airco"] = kw_airco
            prev_values["battery_in"] = battery_in_power
            prev_values["battery_out"] = battery_out_power

        except Exception as e:
            logger.error(f"Error in get_wattage: {e}")
            if power_monitor:
                try:
                    power_monitor.close()
                except Exception as e:
                    logger.error(f"Error closing power monitor: {e}")
                power_monitor = None

        await asyncio.sleep(3)


async def climate_control(temp_id):
    global HEATING, AIRCO, temp, temp_sensor_id, pot_id, MCP, TEMP_SENSOR
    hysteresis = 0.5
    max_range = 2.0
    min_heater_power = 20

    prev_values = {
        "target_temp_pot": None,
        "current_temp": None,
        "heater_power": None,
        "fan_state": None,
    }

    try:
        while True:
            current_pot = MCP.read_channel(0)
            target_temp_pot = round((16 + (current_pot / 1023) * 14) * 2) / 2
            if target_temp_pot != prev_values["target_temp_pot"]:
                DataRepository.create_log(target_temp_pot, pot_id)

            lower_bound = target_temp_pot - hysteresis / 2
            upper_bound = target_temp_pot + hysteresis / 2
            max_lower = target_temp_pot - max_range

            current_temp = round(TEMP_SENSOR.get_temp(temp_id), 1)
            logger.debug(
                f"Current temperature value: {current_temp}°C, Target temperature: {target_temp_pot}°C"
            )

            if current_temp != prev_values["current_temp"]:
                DataRepository.create_log(current_temp, temp_sensor_id)

            if current_temp < lower_bound:
                if current_temp <= max_lower:
                    heater_power = 100
                else:
                    heater_power = min_heater_power + (100 - min_heater_power) * (
                        lower_bound - current_temp
                    ) / (lower_bound - max_lower)

                HEATING.set_power(max(0, min(100, heater_power)))
                AIRCO.off()

                if heater_power != prev_values["heater_power"]:
                    DataRepository.create_log(heater_power, heater_id)

                if 0 != prev_values["fan_state"]:
                    DataRepository.create_log(0, fan_id)

                prev_values["heater_power"] = heater_power
                prev_values["fan_state"] = 0

            elif current_temp > upper_bound:
                HEATING.off()

                if 0 != prev_values["heater_power"]:
                    DataRepository.create_log(0, heater_id)

                if 1 != prev_values["fan_state"]:
                    DataRepository.create_log(1, fan_id)

                prev_values["heater_power"] = 0
                prev_values["fan_state"] = 1

            else:
                HEATING.off()
                AIRCO.off()

                if 0 != prev_values["heater_power"]:
                    DataRepository.create_log(0, heater_id)

                if 0 != prev_values["fan_state"]:
                    DataRepository.create_log(0, fan_id)

                prev_values["heater_power"] = 0
                prev_values["fan_state"] = 0

            prev_values["target_temp_pot"] = target_temp_pot
            prev_values["current_temp"] = current_temp

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

    tasks = []

    try:
        global MOTION_SENSOR, LED_BUTTON, REED_SWITCH, TEMP_SENSOR
        global LCD, DOOR_LOCK, LED_OUTDOORS, LED_BOTTOM, LED_TOP
        global HEATING, AIRCO, MCP, CARD_READER
        global temp_id, POWER_BUTTON, I2C_EXPANDER

        MOTION_SENSOR = 19
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
        DOOR_LOCK = ServoLock(12)
        LED_OUTDOORS = LED(21)
        LED_BOTTOM = LED(25)
        LED_TOP = 17
        GPIO.setup(LED_TOP, GPIO.OUT)
        HEATING = HeatingPad(20)
        AIRCO = DCMotor(18)
        MCP = MCP3008(0, 1)
        I2C_EXPANDER = TCA9548A()

        threading.Thread(
            target=gpio_keep_alive,
            daemon=True,
        ).start()

        tasks = [
            asyncio.create_task(run_lights_bottom()),
            asyncio.create_task(lights_top()),
            asyncio.create_task(lights_outdoors()),
            asyncio.create_task(display_lcd()),
            asyncio.create_task(get_wattage()),
            asyncio.create_task(climate_control(temp_id)),
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


@app.get(
    ENDPOINT + "/logs/last/",
    response_model=list[Log],
    summary="Retrieve all logs",
    response_description="A list of all available logs",
    tags=["logs"],
)
async def read_all_last_logs():
    data = DataRepository.read_all_last_logs()
    if data is None or len(data) == 0:
        raise HTTPException(status_code=404, detail=f"No logs found in the database")
    return data


@app.get(
    ENDPOINT + "/schedules/{frame_name}/",
    response_model=list[Schedule],
    summary="Retrieve all schedules",
    response_description="A list of all available schedules",
    tags=["schedules"],
)
async def get_all_schedules(frame_name: str):
    data = DataRepository.read_all_schedules_by_frame_id(frame_name)
    if data is None or len(data) == 0:
        raise HTTPException(
            status_code=404, detail=f"No schedules found in the database"
        )
    return data


@app.put(
    ENDPOINT + "/schedule/{id}/",
    response_model=UpdatedSchedule,
    tags=["schedule"],
)
async def update_lighting_schedule(id: int, schedule: DTOSchedule):
    existing = DataRepository.read_schedule_by_id(id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Schedule with ID {id} not found")
    updated = DataRepository.update_schedule(
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

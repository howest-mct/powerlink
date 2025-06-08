# region Setup -----------------------------------------
import asyncio
import socketio
import uvicorn
import logging
from RPi import GPIO
import time
import re
import subprocess

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

# region Socket.IO Setup Functions ---------------------------------
sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi", logger=False)


async def log_and_emit_async(value, component_id):
    try:
        log_id = DataRepository.create_log(value, component_id)
        if log_id is None:
            logger.error(
                f"Failed to create log for component {component_id} with value {value}"
            )
            return

        data = DataRepository.read_last_log_by_id(log_id)
        if data and "datetime" in data:
            data["datetime"] = data["datetime"].isoformat()

        await sio.emit("B2F_new_log", data)

    except Exception as e:
        logger.error(f"Error in log_and_emit_async: {e}")
        errors += 1
        return


def log_and_emit_sync(value, component_id):
    try:
        log_id = DataRepository.create_log(value, component_id)
        if log_id is None:
            logger.error(
                f"Failed to create log for component {component_id} with value {value}"
            )
            return

        data = DataRepository.read_last_log_by_id(log_id)
        if data and "datetime" in data:
            data["datetime"] = data["datetime"].isoformat()

        try:
            loop = asyncio.get_event_loop()
            time.sleep(1)
            loop.create_task(sio.emit("B2F_new_log", data))

        except RuntimeError:
            sio.emit("B2F_new_log", data)

    except Exception as e:
        logger.error(f"Error in log_and_emit_sync: {e}")
        errors += 1
        return


# endregion Socket.IO Setup **************************************************

# region Globals ---------------------------------
# Database IDs
wh_bat_in_id = 1
wh_bat_out_id = 2
pot_id = 3
temp_sensor_id = 4
heater_id = 5
wh_heater_id = 6
fan_id = 7
wh_fan_id = 8
button_lights_id = 9
led_bottom_id = 10
wh_led_bottom_id = 11
motion_sensor_id = 12
led_top_id = 13
wh_led_top_id = 14
card_reader_id = 15
reed_switch_id = 16
servo_lock_id = 17
light_sensor_id = 18
led_outdoors_id = 19
button_power_id = 20

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
battery_level = 0.0
kw_led_bottom = 0.0
kw_led_top = 0.0
kw_heating = 0.0
kw_airco = 0.0
kw_bat_out = 0.0
current_usage = 0.0
power_monitor = None
temp_id = None
temp = None
switch_state = False
lights_button_pressed = False
last_log_time_switch = 0
previous_state_switch = False
last_state_led = None
light_duration = 10
prev_led_brightness = None
ldr_value = None
scanned_card = None
door_state = None
switch_state_power = False
errors = 0
sleep_lcd = 3
sleep_fast = 0.25
sleep_medium = 1
sleep_slow = 2
sleep_long = 5

# Schedules
try:
    all_schedules = DataRepository.read_all_schedules()
    dict_schedules = {}

    for schedule in all_schedules:
        schedule_name = schedule.get("schedule_name")
        if schedule_name and schedule_name not in dict_schedules:
            dict_schedules[schedule_name] = {}

        if schedule_name:
            dict_schedules[schedule_name] = schedule

except Exception as e:
    logger.error(f"Error reading schedules from database: {e}")
    dict_schedules = {}
    errors += 1

try:
    GPIO.setmode(GPIO.BCM)

except RuntimeError as e:
    logger.error(f"Error setting GPIO mode: {e}")
    GPIO.cleanup()
    errors += 1

# endregion Globals ******************************


# region Functions ---------------------------------


def get_ip(interface):
    global errors

    try:
        output = subprocess.check_output(["ip", "a", "show", interface]).decode()
        match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", output)

        if match:
            return match.group(1)

        else:
            return "Geen IP"

    except subprocess.CalledProcessError:
        errors += 1
        return "Interface fout"


async def display_lcd():
    global LCD, temp, current_usage, battery_level, eth0_ip, wlan0_ip
    global errors

    LCD.string(f"Project loaded", 1)
    LCD.string(f"{errors} error(s)", 2)
    await asyncio.sleep(sleep_long)

    while True:
        try:
            eth0_ip = get_ip("eth0")
            wlan0_ip = get_ip("wlan0")
            LCD.string("IP ETH0:", 1)
            LCD.string(eth0_ip, 2)
            await asyncio.sleep(sleep_lcd)

            LCD.string("IP WLAN0:", 1)
            LCD.string(wlan0_ip, 2)
            await asyncio.sleep(sleep_lcd)

            LCD.string("Current temp:", 1)
            LCD.string(f"{temp} degrees C", 2)
            await asyncio.sleep(sleep_lcd)

            LCD.string("Current Watt:", 1)
            LCD.string(f"{round(current_usage, 3)}W", 2)
            await asyncio.sleep(sleep_lcd)

            LCD.string("Battery level:", 1)
            LCD.string(f"{battery_level}%", 2)
            await asyncio.sleep(sleep_lcd)

            LCD.string("Program running", 1)
            LCD.string(f"{errors} error(s)", 2)
            await asyncio.sleep(sleep_lcd)

        except Exception as e:
            errors += 1
            logger.error(f"Error in display_lcd: {e}")
            await asyncio.sleep(sleep_long)


def initialize_power_monitoring():
    global power_monitor

    try:
        power_monitor = PowerMonitoringSystem(tca_address=0x70, ina_address=0x40)
        logger.info("Power monitoring system with TCA9548A initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize power monitoring: {e}")
        power_monitor = None
        errors += 1


async def get_wattage():
    global power_monitor, current_usage, battery_level, errors
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
                await asyncio.sleep(sleep_long)
                continue

            readings = power_monitor.read_all_sensors()

            kw_led_bottom = round(readings.get("led_bottom", 0.0), 2)
            kw_led_top = round(readings.get("led_top", 0.0), 2)
            kw_heating = round(readings.get("heating", 0.0), 2)
            kw_airco = round(readings.get("airco", 0.0), 2)
            battery_in_power = round(readings.get("battery_in", 0.0), 2)
            battery_out_power = round(readings.get("battery_out", 0.0), 2)

            current_usage = kw_led_bottom + kw_led_top + kw_heating + kw_airco

            if battery_out_power > 0.1:
                battery_level = max(
                    0, min(100, (battery_in_power / battery_out_power) * 100)
                )

            else:
                battery_level = 100.0

            if kw_led_bottom != 0 or prev_values.get("led_bottom", 0) != 0:
                await log_and_emit_async(kw_led_bottom, wh_led_bottom_id)

            if kw_led_top != 0 or prev_values.get("led_top", 0) != 0:
                await log_and_emit_async(kw_led_top, wh_led_top_id)

            if kw_heating != 0 or prev_values.get("heating", 0) != 0:
                await log_and_emit_async(kw_heating, wh_heater_id)

            if kw_airco != 0 or prev_values.get("airco", 0) != 0:
                await log_and_emit_async(kw_airco, wh_fan_id)

            if battery_in_power != 0 or prev_values.get("battery_in", 0) != 0:
                await log_and_emit_async(battery_in_power, wh_bat_in_id)

            if battery_out_power != 0 or prev_values.get("battery_out", 0) != 0:
                await log_and_emit_async(battery_out_power, wh_bat_out_id)

            prev_values["led_bottom"] = kw_led_bottom
            prev_values["led_top"] = kw_led_top
            prev_values["heating"] = kw_heating
            prev_values["airco"] = kw_airco
            prev_values["battery_in"] = battery_in_power
            prev_values["battery_out"] = battery_out_power

        except Exception as e:
            logger.error(f"Error in get_wattage: {e}")
            errors += 1
            if power_monitor:
                try:
                    power_monitor.close()

                except Exception as e:
                    logger.error(f"Error closing power monitor: {e}")
                power_monitor = None

        await asyncio.sleep(sleep_slow)


async def climate_control(temp_id):
    global HEATING, AIRCO, temp, temp_sensor_id, pot_id, MCP, TEMP_SENSOR, dict_schedules
    global errors, heater_id

    hysteresis = 1.0
    max_range = 2.0
    fan_active = False
    min_heater_power = 50

    prev_values = {
        "target_temp": None,
        "current_temp": None,
        "heater_power": None,
        "fan_state": None,
    }

    while True:
        try:
            current_time = time.strftime("%H:%M", time.localtime())

            current_pot = MCP.read_channel(0)
            pot_temp = round((16 + (current_pot / 1023) * 14) * 2) / 2

            schedule = dict_schedules.get("Heater Schedule", {})
            use_schedule = schedule.get("enabled") == 1
            schedule_start = schedule.get("start_time", "00:00")
            schedule_end = schedule.get("end_time", "23:59")
            schedule_value = schedule.get("value", pot_temp)

            if use_schedule and schedule_start <= current_time <= schedule_end:
                target_temp = schedule_value
                fan_active = True

            elif use_schedule:
                target_temp = 16
                fan_active = False

            else:
                target_temp = pot_temp
                fan_active = True

            if target_temp != prev_values.get("target_temp"):
                await log_and_emit_async(target_temp, pot_id)

            lower_bound = target_temp - hysteresis / 2
            upper_bound = target_temp + hysteresis / 2
            max_lower = target_temp - max_range

            current_temp = round(TEMP_SENSOR.get_temp(temp_id), 1)
            if current_temp != prev_values.get("current_temp"):
                await log_and_emit_async(current_temp, temp_sensor_id)

            if current_temp < lower_bound:
                if current_temp <= max_lower:
                    heater_power = 100

                else:
                    calculated_power = round(
                        100 * (lower_bound - current_temp) / (lower_bound - max_lower),
                        2,
                    )
                    heater_power = max(min_heater_power, calculated_power)

                HEATING.set_power(heater_power)
                AIRCO.off()

                if heater_power != prev_values.get("heater_power"):
                    await log_and_emit_async(heater_power, heater_id)

                if prev_values.get("fan_state") != 0:
                    await log_and_emit_async(0, fan_id)

                prev_values["heater_power"] = heater_power
                prev_values["fan_state"] = 0

            elif current_temp > upper_bound:
                HEATING.off()
                if fan_active:
                    AIRCO.on()

                    if prev_values.get("heater_power") != 0:
                        await log_and_emit_async(0, heater_id)

                    if prev_values.get("fan_state") != 1:
                        await log_and_emit_async(1, fan_id)

                    prev_values["heater_power"] = 0
                    prev_values["fan_state"] = 1
                else:
                    AIRCO.off()

                    if prev_values.get("heater_power") != 0:
                        await log_and_emit_async(0, heater_id)

                    if prev_values.get("fan_state") != 0:
                        await log_and_emit_async(0, fan_id)

                    prev_values["heater_power"] = 0
                    prev_values["fan_state"] = 0
            else:
                HEATING.off()
                AIRCO.off()

                if prev_values.get("heater_power") != 0:
                    await log_and_emit_async(0, heater_id)

                if prev_values.get("fan_state") != 0:
                    await log_and_emit_async(0, fan_id)

                prev_values["heater_power"] = 0
                prev_values["fan_state"] = 0

            prev_values["target_temp"] = target_temp
            prev_values["current_temp"] = current_temp
            temp = current_temp

            await asyncio.sleep(sleep_medium)

        except Exception as e:
            logger.error(f"Error in climate_control: {e}")
            errors += 1


def lights_button(pin):
    global lights_button_pressed

    lights_button_pressed = True


async def do_lights_button():
    global lights_button_pressed, switch_state, lights_button_pressed, errors

    while True:
        try:
            if lights_button_pressed:
                lights_button_pressed = False
                switch_state = not switch_state
                await log_and_emit_async(switch_state, button_lights_id)

            await asyncio.sleep(sleep_fast)

        except Exception as e:
            logger.error(f"Error in do_lights_button: {e}")
            lights_button_pressed = False
            await asyncio.sleep(sleep_slow)
            errors += 1


async def lights_bottom():
    global LED_BOTTOM, switch_state, last_log_time_switch, previous_state_switch, dict_schedules
    global prev_led_brightness, errors

    prev_led_brightness = 0
    previous_state_switch = False
    last_log_time_switch = 0

    while True:
        try:
            schedule = dict_schedules.get("Lights Downstairs Schedule", {})
            use_schedule = schedule.get("enabled", False)

            if switch_state:
                if use_schedule:
                    target_brightness = schedule.get("value", 0)

                else:
                    target_brightness = 100

            else:
                target_brightness = 0

            if target_brightness != prev_led_brightness:
                current_time_stamp = time.time()

                if current_time_stamp - last_log_time_switch >= 1:
                    if target_brightness > 0:
                        LED_BOTTOM.set_brightness(target_brightness)
                        logger.info(
                            f"LED Bottom brightness set to: {target_brightness}"
                        )
                    else:
                        LED_BOTTOM.off()
                        logger.info("LED Bottom turned off")

                    await log_and_emit_async(target_brightness, led_bottom_id)

                    prev_led_brightness = target_brightness
                    last_log_time_switch = current_time_stamp

            await asyncio.sleep(sleep_fast)

        except Exception as e:
            logger.error(f"Error in lights_bottom: {e}")
            errors += 1
            prev_led_brightness = None
            await asyncio.sleep(sleep_slow)


async def lights_top():
    global LED_TOP, led_top_id, motion_sensor_id, MOTION_SENSOR, light_duration, dict_schedules
    global last_motion, errors

    last_motion = 0

    prev_values = {
        "motion_sensor": None,
        "led_brightness": None,
    }

    while True:
        try:
            motion_now = GPIO.input(MOTION_SENSOR)

            if motion_now == 1 and last_motion == 0:
                current_time = time.strftime("%H:%M", time.localtime())
                schedule = dict_schedules.get("Lights Upstairs Schedule", {})
                use_schedule = schedule.get("enabled") == 1
                schedule_start = schedule.get("start_time", "00:00")
                schedule_end = schedule.get("end_time", "23:59")
                schedule_value = schedule.get("value", 100)

                if use_schedule and schedule_start <= current_time <= schedule_end:
                    brightness = schedule_value

                else:
                    brightness = 100

                LED_TOP.set_brightness(brightness)
                if 1 != prev_values.get("motion_sensor"):
                    await log_and_emit_async(1, motion_sensor_id)

                prev_values["motion_sensor"] = 1

                if brightness != prev_values.get("led_brightness"):
                    await log_and_emit_async(brightness, led_top_id)

                prev_values["led_brightness"] = brightness

                await asyncio.sleep(light_duration)

            elif motion_now == 0 and last_motion == 1:
                LED_TOP.off()

                if 0 != prev_values.get("motion_sensor"):
                    await log_and_emit_async(0, motion_sensor_id)
                prev_values["motion_sensor"] = 0

                if 0 != prev_values.get("led_brightness"):
                    await log_and_emit_async(0, led_top_id)

                prev_values["led_brightness"] = 0

            last_motion = motion_now
            await asyncio.sleep(sleep_fast)

        except Exception as e:
            logger.error(f"Something went wrong: {e}")
            last_motion = 0
            prev_values["motion_sensor"] = None
            prev_values["led_brightness"] = None
            errors += 1
            await asyncio.sleep(sleep_slow)


def cut_card(card_id):
    return card_id[:6] + "000000"


async def front_door():
    global DOOR_LOCK, REED_SWITCH, CARD_READER, scanned_card
    global servo_lock_id, reed_switch_id, card_reader_id, errors

    while True:
        try:
            scanned_card = CARD_READER.read_no_block()

            if scanned_card is not None:
                scanned_card = str(scanned_card)
                snipped_card = cut_card(scanned_card)
                logger.info(f"Card scanned: {snipped_card}")

                try:
                    checked_card = DataRepository.read_card_by_id(snipped_card)

                    if checked_card is None:
                        await log_and_emit_async(snipped_card, card_reader_id)
                        continue

                    await log_and_emit_async(snipped_card, card_reader_id)

                    DOOR_LOCK.unlock()
                    await log_and_emit_async(1, servo_lock_id)

                    start_time = time.time()

                    while GPIO.input(REED_SWITCH) == 1:
                        if time.time() - start_time > 5:
                            logger.info(
                                "Door did not open in time (5 seconds) - locking again"
                            )
                            DOOR_LOCK.lock()

                            await log_and_emit_async(0, servo_lock_id)
                            break

                        await asyncio.sleep(sleep_fast)

                    else:
                        await log_and_emit_async(1, reed_switch_id)
                        start_time = time.time()

                        while GPIO.input(REED_SWITCH) == 0:
                            if time.time() - start_time > 10:
                                logger.info(
                                    "Door did not close in time (10 seconds) - locking anyway"
                                )

                                break

                            await asyncio.sleep(sleep_fast)

                        await log_and_emit_async(0, reed_switch_id)
                        DOOR_LOCK.lock()
                        await log_and_emit_async(0, servo_lock_id)

                except Exception as e:
                    logger.error(f"Error processing card: {e}")
                    errors += 1
                    try:
                        DOOR_LOCK.lock()
                        await log_and_emit_async(0, servo_lock_id)

                    except Exception as lock_error:
                        logger.error(f"Error locking door: {lock_error}")

            await asyncio.sleep(sleep_fast)

        except Exception as e:
            logger.error(f"Error in front_door: {e}")
            errors += 1
            await asyncio.sleep(sleep_slow)


async def lights_outdoors():
    global LED_OUTDOORS, MCP, last_state_led, ldr_value, light_sensor_id, led_outdoors_id, errors

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
                current_state = ldr_value < 25
            else:
                current_state = ldr_value < 30

            if current_state != last_state_led:
                if current_state:
                    GPIO.output(LED_OUTDOORS, GPIO.HIGH)
                    if 100 != prev_values.get("led_brightness"):
                        await log_and_emit_async(100, led_outdoors_id)
                    prev_values["led_brightness"] = 100

                else:
                    GPIO.output(LED_OUTDOORS, GPIO.LOW)
                    if prev_values.get("led_brightness") != 0:
                        await log_and_emit_async(0, led_outdoors_id)
                    prev_values["led_brightness"] = 0

                if ldr_value != prev_values.get("ldr_value"):
                    await log_and_emit_async(ldr_value, light_sensor_id)

                prev_values["ldr_value"] = ldr_value
                last_state_led = current_state

            else:
                if ldr_value != prev_values.get("ldr_value"):
                    await log_and_emit_async(ldr_value, light_sensor_id)
                    prev_values["ldr_value"] = ldr_value

            await asyncio.sleep(sleep_medium)

        except Exception as e:
            logger.error(f"Error in lights_outdoors: {e}")
            last_state_led = None
            prev_values["ldr_value"] = None
            prev_values["led_brightness"] = None
            errors += 1
            await asyncio.sleep(sleep_slow)


def power_button(pin):
    global switch_state_power, button_power_id, errors

    try:
        switch_state_power = not switch_state_power
        log_and_emit_sync(switch_state_power, button_power_id)

    except Exception as e:
        logger.error(f"Error in power_button: {e}")
        errors += 1


# endregion Functions ****************************


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

        MOTION_SENSOR = 17
        GPIO.setup(MOTION_SENSOR, GPIO.IN)
        LED_BUTTON = 21
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
        LED_OUTDOORS = 24
        GPIO.setup(LED_OUTDOORS, GPIO.OUT)
        LED_BOTTOM = LED(13)
        LED_TOP = LED(19)
        HEATING = HeatingPad(20)
        AIRCO = DCMotor(18)
        MCP = MCP3008(0, 1)
        I2C_EXPANDER = TCA9548A()

        tasks = [
            asyncio.create_task(get_wattage()),
            asyncio.create_task(climate_control(temp_id)),
            asyncio.create_task(do_lights_button()),
            asyncio.create_task(lights_bottom()),
            asyncio.create_task(lights_top()),
            asyncio.create_task(front_door()),
            asyncio.create_task(lights_outdoors()),
            asyncio.create_task(display_lcd()),
        ]

        GPIO.add_event_detect(
            LED_BUTTON, GPIO.FALLING, callback=lights_button, bouncetime=250
        )
        GPIO.add_event_detect(
            POWER_BUTTON, GPIO.FALLING, callback=power_button, bouncetime=250
        )

        yield

    finally:
        logger.info("Shutting down application...")

        try:
            log_and_emit_sync(0, heater_id)
            log_and_emit_sync(0, fan_id)
            log_and_emit_sync(0, led_bottom_id)
            log_and_emit_sync(0, led_top_id)
            log_and_emit_sync(0, led_outdoors_id)
            log_and_emit_sync(0, servo_lock_id)
            log_and_emit_sync(0, wh_heater_id)
            log_and_emit_sync(0, wh_fan_id)
            log_and_emit_sync(0, wh_led_bottom_id)
            log_and_emit_sync(0, wh_led_top_id)
            log_and_emit_sync(0, wh_bat_in_id)
            log_and_emit_sync(0, wh_bat_out_id)

            logger.info("All component shutdown states logged")

        except Exception as e:
            logger.error(f"Error logging shutdown states: {e}")

        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

        if LED_TOP:
            LED_TOP.cleanup()

        if LED_BOTTOM:
            LED_BOTTOM.cleanup()

        if HEATING:
            HEATING.cleanup()

        if AIRCO:
            AIRCO.cleanup()

        if DOOR_LOCK:
            DOOR_LOCK.cleanup()

        if CARD_READER:
            CARD_READER.cleanup()

        if LCD:
            LCD.close()

        if MCP:
            MCP.close()

        if I2C_EXPANDER:
            I2C_EXPANDER.close()

        if power_monitor:
            power_monitor.close()

        if GPIO:
            GPIO.cleanup()
        logger.info("GPIO cleaned up. Bye!")


app = FastAPI(lifespan=lifespan_manager)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sio_app = socketio.ASGIApp(sio, app)

ENDPOINT = "/api/v1"
# endregion App Setup ********************************


# region FastAPI Endpoints ---------------------------------
@app.get("/")
async def root():
    return "Server werkt, maar hier geen API endpoint gevonden."


@app.get(
    ENDPOINT + "/components/last/{frame_name}/",
    response_model=list[Log],
    summary="Retrieve all logs",
    response_description="A list of all available logs",
    tags=["logs"],
)
async def read_all_last_logs(frame_name: str):
    data = DataRepository.read_all_last_logs(frame_name)
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


@sio.on("BF2_schedule_updated")
async def handler(sid, data):
    global dict_schedules
    dict_schedules[data["schedule_name"]] = data
    print(f"Received schedule update: {data}")


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

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
    EnergyLog,
    Component,
    Room,
    ComponentPage,
    DTOComponentPage,
    HistoryLog,
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
wh_bat_in_id = 1
wh_bat_out_id = 2
pot_id = 3
temp_control_id = 4
temp_sensor_id = 5
heater_id = 6
wh_heater_id = 7
fan_id = 8
wh_fan_id = 9
button_lights_id = 10
led_bottom_id = 11
wh_led_bottom_id = 12
motion_sensor_id = 13
led_top_id = 14
wh_led_top_id = 15
card_reader_id = 16
reed_switch_id = 17
servo_lock_id = 18
light_sensor_id = 19
led_outdoors_id = 20
button_power_id = 21
cpu_temp_sensor_id = 22


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
sleep_lcd = 6
sleep_fast = 0.25
sleep_medium = 1
sleep_slow = 2
sleep_long = 5

try:
    all_schedules = DataRepository.read_all_schedules()
    dict_schedules = {}

    for schedule in all_schedules:
        schedule_name = schedule.get("schedule_id")
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


def get_cpu_temperature():
    global errors, cpu_temp, cpu_temp_sensor_id
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_raw = f.read().strip()
            cpu_temp = round(int(temp_raw) / 1000.0, 1)
            log_and_emit_sync(cpu_temp, cpu_temp_sensor_id)
            return cpu_temp

    except Exception as e:
        errors += 1
        logger.error(f"Error reading CPU temperature: {e}")
        return "Temp Error"


def is_time_in_range(start_time, end_time, current_time):
    start = start_time.replace(":", "")
    end = end_time.replace(":", "")
    now = current_time.replace(":", "")

    if start <= end:
        return start <= now <= end
    else:
        return now >= start or now <= end


async def display_lcd():
    global LCD, current_usage, battery_level, eth0_ip, wlan0_ip
    global errors, cpu_temp_sensor_id

    LCD.string(f"Project loaded", 1)
    LCD.string(f"{errors} error(s)", 2)
    await asyncio.sleep(sleep_long)

    while True:
        try:
            wlan0_ip = get_ip("wlan0")
            cpu_temp = get_cpu_temperature()

            LCD.string("PowerLink IP:", 1)
            LCD.string(wlan0_ip, 2)
            await asyncio.sleep(sleep_lcd)

            LCD.string("CPU temp:", 1)
            LCD.string(f"{cpu_temp} degrees C", 2)
            await asyncio.sleep(sleep_lcd)

            LCD.string("Current Watt:", 1)
            LCD.string(f"{round(current_usage, 3)}W", 2)
            await asyncio.sleep(sleep_lcd)

            LCD.string("Battery level:", 1)
            LCD.string(f"{battery_level}%", 2)
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

            current_usage = battery_out_power

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
    global errors, heater_id, fan_id, sleep_medium, temp_control_id

    hysteresis = 0.5
    max_range = 1.0
    fan_active = False
    min_heater_power = 50

    prev_values = {
        "pot_temp": None,
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

            if pot_temp != prev_values.get("pot_temp"):
                await log_and_emit_async(pot_temp, pot_id)
                prev_values["pot_temp"] = pot_temp

            day_schedule = dict_schedules.get(1, {})
            night_schedule = dict_schedules.get(2, {})

            day_enabled = day_schedule.get("enabled") == 1
            day_start = day_schedule.get("start_time", "07:00")
            day_end = day_schedule.get("end_time", "23:00")
            day_value = day_schedule.get("value", pot_temp)

            night_enabled = night_schedule.get("enabled") == 1
            night_start = night_schedule.get("start_time", "23:00")
            night_end = night_schedule.get("end_time", "07:00")
            night_value = night_schedule.get("value", pot_temp)

            target_temp = pot_temp
            fan_active = True

            if day_enabled and is_time_in_range(day_start, day_end, current_time):
                target_temp = day_value
                fan_active = True
            elif night_enabled and is_time_in_range(
                night_start, night_end, current_time
            ):
                target_temp = night_value
                fan_active = False
            else:
                target_temp = pot_temp
                fan_active = True

            if target_temp != prev_values.get("target_temp"):
                await log_and_emit_async(target_temp, temp_control_id)
                prev_values["target_temp"] = target_temp

            lower_bound = target_temp - hysteresis / 2
            upper_bound = target_temp + hysteresis / 2
            max_lower = target_temp - max_range

            current_temp = round(TEMP_SENSOR.get_temp(temp_id) * 2) / 2
            if current_temp != prev_values.get("current_temp"):
                await log_and_emit_async(current_temp, temp_sensor_id)
                prev_values["current_temp"] = current_temp

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
                    prev_values["heater_power"] = heater_power

                if prev_values.get("fan_state") != 0:
                    await log_and_emit_async(0, fan_id)
                    prev_values["fan_state"] = 0

            elif current_temp > upper_bound:
                HEATING.off()
                if fan_active:
                    AIRCO.on()

                    if prev_values.get("heater_power") != 0:
                        await log_and_emit_async(0, heater_id)
                        prev_values["heater_power"] = 0

                    if prev_values.get("fan_state") != 1:
                        await log_and_emit_async(1, fan_id)
                        prev_values["fan_state"] = 1
                else:
                    AIRCO.off()

                    if prev_values.get("heater_power") != 0:
                        await log_and_emit_async(0, heater_id)
                        prev_values["heater_power"] = 0

                    if prev_values.get("fan_state") != 0:
                        await log_and_emit_async(0, fan_id)
                        prev_values["fan_state"] = 0
            else:
                HEATING.off()
                AIRCO.off()

                if prev_values.get("heater_power") != 0:
                    await log_and_emit_async(0, heater_id)
                    prev_values["heater_power"] = 0

                if prev_values.get("fan_state") != 0:
                    await log_and_emit_async(0, fan_id)
                    prev_values["fan_state"] = 0

            temp = current_temp
            await asyncio.sleep(sleep_medium)

        except Exception as e:
            logger.error(f"Error in climate_control: {e}")
            errors += 1
            await asyncio.sleep(1)


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
    global prev_led_brightness, errors, led_bottom_id, sleep_fast, sleep_slow

    prev_led_brightness = 0
    previous_state_switch = False
    last_log_time_switch = 0

    while True:
        try:
            current_time = time.strftime("%H:%M", time.localtime())

            day_schedule = dict_schedules.get(3, {})
            night_schedule = dict_schedules.get(4, {})

            day_enabled = day_schedule.get("enabled", False)
            day_start = day_schedule.get("start_time", "07:00")
            day_end = day_schedule.get("end_time", "23:00")
            day_value = day_schedule.get("value", 100)

            night_enabled = night_schedule.get("enabled", False)
            night_start = night_schedule.get("start_time", "23:00")
            night_end = night_schedule.get("end_time", "07:00")
            night_value = night_schedule.get("value", 50)

            target_brightness = 0

            if switch_state:
                if day_enabled and is_time_in_range(day_start, day_end, current_time):
                    target_brightness = day_value
                elif night_enabled and is_time_in_range(
                    night_start, night_end, current_time
                ):
                    target_brightness = night_value
                else:
                    target_brightness = 100
            else:
                target_brightness = 0

            if target_brightness != prev_led_brightness:
                current_time_stamp = time.time()

                if current_time_stamp - last_log_time_switch >= 1:
                    if target_brightness > 0:
                        LED_BOTTOM.set_brightness(target_brightness)

                    else:
                        LED_BOTTOM.off()

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
    global last_motion, errors, sleep_fast, sleep_slow

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

                day_schedule = dict_schedules.get("Lights Upstairs Schedule", {})
                night_schedule = dict_schedules.get(
                    "Lights Upstairs Night Schedule", {}
                )

                day_enabled = day_schedule.get("enabled", False)
                day_start = day_schedule.get("start_time", "07:00")
                day_end = day_schedule.get("end_time", "23:00")
                day_value = day_schedule.get("value", 100)

                night_enabled = night_schedule.get("enabled", False)
                night_start = night_schedule.get("start_time", "23:00")
                night_end = night_schedule.get("end_time", "07:00")
                night_value = night_schedule.get("value", 50)

                brightness = 100

                if day_enabled and is_time_in_range(day_start, day_end, current_time):
                    brightness = day_value
                elif night_enabled and is_time_in_range(
                    night_start, night_end, current_time
                ):
                    brightness = night_value
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
                await log_and_emit_async(snipped_card, card_reader_id)

                try:
                    checked_card = DataRepository.read_card_by_id(snipped_card)

                    if checked_card is None:
                        continue

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
                            continue

                        await asyncio.sleep(sleep_fast)

                    else:
                        await log_and_emit_async(1, reed_switch_id)
                        start_time = time.time()

                        while GPIO.input(REED_SWITCH) == 0:
                            if time.time() - start_time > 10:
                                logger.info(
                                    "Door did not close in time (10 seconds) - locking anyway"
                                )

                                continue

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
                current_state = ldr_value < 45
            else:
                current_state = ldr_value < 50

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
            log_and_emit_sync(0, button_lights_id)
            log_and_emit_sync(0, led_top_id)
            log_and_emit_sync(0, led_outdoors_id)
            log_and_emit_sync(0, servo_lock_id)
            log_and_emit_sync(0, wh_heater_id)
            log_and_emit_sync(0, wh_fan_id)
            log_and_emit_sync(0, wh_led_bottom_id)
            log_and_emit_sync(0, wh_led_top_id)
            log_and_emit_sync(0, wh_bat_in_id)
            log_and_emit_sync(0, wh_bat_out_id)
            log_and_emit_sync(0, button_power_id)

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
    ENDPOINT + "/components/",
    response_model=list[Component],
    summary="Retrieve all components",
    response_description="A list of all available components",
    tags=["components"],
)
async def get_all_components():
    data = DataRepository.read_all_components()
    if data is None or len(data) == 0:
        raise HTTPException(
            status_code=404, detail=f"No components found in the database"
        )
    return data


@app.get(
    ENDPOINT + "/rooms/",
    response_model=list[Room],
    summary="Retrieve all rooms",
    response_description="A list of all available rooms",
    tags=["rooms"],
)
async def get_all_rooms():
    data = DataRepository.read_all_rooms()
    if data is None or len(data) == 0:
        raise HTTPException(status_code=404, detail=f"No rooms found in the database")
    return data


@app.get(
    ENDPOINT + "/components/last/{page_id}/",
    response_model=list[Log],
    summary="Retrieve all logs",
    response_description="A list of all available logs",
    tags=["logs"],
)
async def read_all_last_logs(page_id: int):
    data = DataRepository.read_all_last_logs(page_id)
    return data if data else []


@app.get(
    ENDPOINT + "/pages/{page_id}/components/",
    response_model=list[ComponentPage],
    summary="Retrieve all components in a page",
    response_description="A list of all available components in the specified page",
    tags=["pages"],
)
async def get_all_components_in_page(page_id: str):
    data = DataRepository.read_all_components_in_page(page_id)
    return data if data else []


@app.post(
    ENDPOINT + "/pages/{page_id}/components/",
    response_model=ComponentPage,
    summary="Add a component to a page",
    response_description="The component successfully added to the page",
    tags=["pages"],
)
async def add_component_to_page(page_id: str, component_data: DTOComponentPage):
    if int(page_id) != component_data.page_id:
        raise HTTPException(
            status_code=400,
            detail="Page ID in URL does not match page ID in request body",
        )

    if DataRepository.check_component_in_page_exists(
        component_data.component_id, component_data.page_id
    ):
        raise HTTPException(
            status_code=409,
            detail=f"Component {component_data.component_id} already exists in page {page_id}",
        )

    result = DataRepository.add_component_to_page(
        component_data.component_id, component_data.page_id
    )
    if not result:
        raise HTTPException(status_code=500, detail="Failed to add component to page")

    return ComponentPage(
        component_id=component_data.component_id, page_id=component_data.page_id
    )


@app.delete(
    ENDPOINT + "/pages/{page_id}/components/{component_id}/",
    summary="Remove a component from a page",
    response_description="Component successfully removed from page",
    tags=["pages"],
)
async def remove_component_from_page(page_id: str, component_id: str):
    if not DataRepository.check_component_in_page_exists(
        int(component_id), int(page_id)
    ):
        raise HTTPException(
            status_code=404,
            detail=f"Component {component_id} not found in page {page_id}",
        )

    result = DataRepository.remove_component_from_page(int(component_id), int(page_id))
    if not result:
        raise HTTPException(
            status_code=500, detail="Failed to remove component from page"
        )

    return {
        "message": f"Component {component_id} successfully removed from page {page_id}"
    }


@app.get(
    ENDPOINT + "/schedules/{page_id}/",
    response_model=list[Schedule],
    summary="Retrieve all schedules",
    response_description="A list of all available schedules",
    tags=["schedules"],
)
async def get_all_schedules(page_id: str):
    data = DataRepository.read_all_schedules_by_page_id(page_id)
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
async def update_schedule(id: str, schedule: DTOSchedule):
    existing = DataRepository.read_schedule_by_id(id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Schedule with ID {id} not found")
    elif (
        schedule.start_time == existing["start_time"]
        and schedule.end_time == existing["end_time"]
        and schedule.value == existing["value"]
        and schedule.enabled == existing["enabled"]
    ):
        return existing
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
async def get_inhabitant_by_id(card_id: str):
    data = DataRepository.read_inhabitant_by_card_id(card_id)
    if data is None:
        raise HTTPException(
            status_code=404, detail=f"inhabitant with ID {card_id} not found"
        )
    return data


@app.get(
    ENDPOINT + "/energy/{id}/24h/",
    response_model=EnergyLog,
    summary="Retrieve a energy_log by ID",
    response_description="The energy_log with the specified ID",
    tags=["energy"],
)
async def get_energy_log_24h_by_id(id: str):
    data = DataRepository.read_energy_24h(id)
    if data is None:
        raise HTTPException(
            status_code=404, detail=f"energy_log with ID {id} not found"
        )
    return data


@app.get(
    ENDPOINT + "/energy/{id}/7d/",
    response_model=EnergyLog,
    summary="Retrieve a energy_log by ID",
    response_description="The energy_log with the specified ID",
    tags=["energy"],
)
async def get_energy_log_7d_by_id(id: int):
    data = DataRepository.read_energy_7d(id)
    if data is None:
        raise HTTPException(
            status_code=404, detail=f"energy_log with ID {id} not found"
        )
    return data


@app.get(
    ENDPOINT + "/history/{component_id}/24h/",
    response_model=list[HistoryLog],
    summary="Retrieve all history",
    response_description="A list of all available history",
    tags=["history"],
)
async def get_all_history_24h(component_id: int):
    data = DataRepository.read_log_history_24h(component_id)
    if data is None or len(data) == 0:
        raise HTTPException(status_code=404, detail=f"No history found in the database")
    return data


@app.get(
    ENDPOINT + "/history/{component_id}/7d/",
    response_model=list[HistoryLog],
    summary="Retrieve all history",
    response_description="A list of all available history",
    tags=["history"],
)
async def get_all_history_7d(component_id: int):
    data = DataRepository.read_log_history_7d(component_id)
    if data is None or len(data) == 0:
        raise HTTPException(status_code=404, detail=f"No history found in the database")
    return data


@app.get(
    ENDPOINT + "/history/{component_id}/14d/",
    response_model=list[HistoryLog],
    summary="Retrieve all history",
    response_description="A list of all available history",
    tags=["history"],
)
async def get_all_history_14d(component_id: int):
    data = DataRepository.read_log_history_14d(component_id)
    if data is None or len(data) == 0:
        raise HTTPException(status_code=404, detail=f"No history found in the database")
    return data


# endregion FastAPI Endpoints *************************


# region Socket.IO Handlers ---------------------------------
@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")


@sio.on("BF2_schedule_updated")
async def schedule_handler(sid, data):
    global dict_schedules
    dict_schedules[data["schedule_id"]] = data


@sio.on("BF2_component_selection")
async def component_selection_handler(sid, data):
    pass


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

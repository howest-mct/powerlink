# region Setup -----------------------------------------
import asyncio
import socketio
import uvicorn
import logging
import threading
import os
import signal
import subprocess
import time
import re
from RPi import GPIO
from datetime import datetime

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
    LogAmount,
    LogCountHistory,
    LastEntered,
    DTOInhabitant,
    Inhabitant,
    PasswordVerificationRequest,
    PasswordVerificationResponse,
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

from mfrc522 import SimpleMFRC522

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

powerlink_shutdown_requested = False

power_button_hold_start = None
power_button_held = False


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

battery_level = 98.0
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
light_duration = 15
prev_led_brightness = None
ldr_value = None
door_state = None
switch_state_power = False
sleep_lcd = 6
sleep_fast = 0.25
sleep_medium = 1
sleep_slow = 2
sleep_long = 5
powerbank_capacity = 0.055
battery_efficiency = 0.85
total_energy_in = 0.0
total_energy_out = 0.0
last_time = None
powerlink_password = "powerlink"

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

try:
    GPIO.setmode(GPIO.BCM)

except RuntimeError as e:
    logger.error(f"Error setting GPIO mode: {e}")
    GPIO.cleanup()
# endregion Globals ******************************


# region Functions ---------------------------------


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


def get_cpu_temperature():
    global cpu_temp, cpu_temp_sensor_id
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_raw = f.read().strip()
            cpu_temp = round(int(temp_raw) / 1000.0, 1)
            log_and_emit_sync(cpu_temp, cpu_temp_sensor_id)
            return cpu_temp

    except Exception as e:
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
    global cpu_temp_sensor_id

    while True:
        try:
            get_cpu_temperature()
            wlan0_ip = get_ip("wlan0")

            LCD.string("PowerLink IP:", 1)
            LCD.string(wlan0_ip, 2)
            await asyncio.sleep(sleep_lcd)

            LCD.string("Current Usage:", 1)
            LCD.string(f"{round(current_usage, 3)}W", 2)
            await asyncio.sleep(sleep_lcd)

            LCD.string("Battery level:", 1)
            LCD.string(f"{battery_level}%", 2)
            await asyncio.sleep(sleep_lcd)

        except Exception as e:
            await asyncio.sleep(sleep_long)


def initialize_power_monitoring():
    global power_monitor

    try:
        power_monitor = PowerMonitoringSystem(tca_address=0x70, ina_address=0x40)
        logger.info("Power monitoring system with TCA9548A initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize power monitoring: {e}")
        power_monitor = None


def reset_battery_tracking():

    global total_energy_in, total_energy_out, last_time, battery_level

    total_energy_in = 0.0
    total_energy_out = 0.0
    last_time = None
    battery_level = 100.0


def update_battery_level(power_in, power_out):
    global total_energy_in, total_energy_out, battery_level, last_time
    global powerbank_capacity, battery_efficiency

    try:
        current_time = time.time()

        if last_time is None:
            last_time = current_time
            return

        hours_passed = (current_time - last_time) / 3600.0

        energy_in_this_period = power_in * hours_passed / 1000.0
        energy_out_this_period = power_out * hours_passed / 1000.0

        total_energy_in += energy_in_this_period
        total_energy_out += energy_out_this_period

        usable_energy = (total_energy_in * battery_efficiency) - total_energy_out
        new_battery_level = max(0, min(100, (usable_energy / powerbank_capacity) * 100))

        if abs(new_battery_level - battery_level) > 0.5:
            old_battery_level = battery_level
            battery_level = new_battery_level

            loop = asyncio.get_event_loop()
            loop.create_task(
                sio.emit(
                    "B2F_battery_level",
                    {
                        "battery_level": round(battery_level, 1),
                        "previous_level": round(old_battery_level, 1),
                        "total_energy_in": round(total_energy_in, 3),
                        "total_energy_out": round(total_energy_out, 3),
                        "timestamp": current_time,
                    },
                )
            )
            logger.debug(
                f"Battery level: {battery_level:.1f}% (was {old_battery_level:.1f}%)"
            )
        else:
            battery_level = new_battery_level

        last_time = current_time

    except Exception as e:
        logger.error(f"Error updating battery level: {e}")


async def shutdown_powerlink_system():
    """
    Gracefully shutdown the PowerLink system by stopping the service and shutting down the Pi
    """
    global powerlink_shutdown_requested

    try:
        logger.info("=== INITIATING POWERLINK SYSTEM SHUTDOWN ===")
        powerlink_shutdown_requested = True

        # Give some time for any final operations
        await asyncio.sleep(1)

        # Stop the powerlink service
        logger.info("Stopping powerlink.service...")
        try:
            subprocess.run(
                ["sudo", "systemctl", "stop", "powerlink.service"],
                check=True,
                timeout=10,
            )
            logger.info("PowerLink service stopped successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stop powerlink service: {e}")
        except subprocess.TimeoutExpired:
            logger.error("Timeout while stopping powerlink service")

        # Wait a moment for service to fully stop
        await asyncio.sleep(2)

        # Shutdown the Raspberry Pi
        logger.info("Shutting down Raspberry Pi...")
        try:
            subprocess.run(["sudo", "shutdown", "-h", "now"], check=True, timeout=5)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to shutdown Pi: {e}")
            # Fallback to alternative shutdown command
            try:
                subprocess.run(["sudo", "halt"], check=True, timeout=5)
            except subprocess.CalledProcessError as e2:
                logger.error(f"Fallback shutdown also failed: {e2}")
        except subprocess.TimeoutExpired:
            logger.error("Timeout while shutting down Pi")

    except Exception as e:
        logger.error(f"Error during system shutdown: {e}")
        # Emergency fallback - just kill the current process
        os.kill(os.getpid(), signal.SIGTERM)


async def get_wattage():
    global power_monitor, current_usage, battery_level
    global kw_led_bottom, kw_led_top, kw_heating, kw_airco, kw_bat_out

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

            update_battery_level(battery_in_power, battery_out_power)

            current_usage = battery_out_power
            kw_bat_out = battery_out_power

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
            if power_monitor:
                try:
                    power_monitor.close()
                except Exception as e:
                    logger.error(f"Error closing power monitor: {e}")
                power_monitor = None

        await asyncio.sleep(sleep_slow)


async def climate_control(temp_id):
    global HEATING, AIRCO, temp, temp_sensor_id, pot_id, MCP, TEMP_SENSOR, dict_schedules
    global heater_id, fan_id, sleep_medium, temp_control_id
    global CARD_READER, scanned_card
    scanned_card = None

    hysteresis = 0.75
    max_range = 1.0
    fan_active = False
    min_heater_power = 25

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
            await asyncio.sleep(1)


def lights_button(pin):
    global lights_button_pressed

    lights_button_pressed = True


async def do_lights_button():
    global lights_button_pressed, switch_state, lights_button_pressed

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


async def lights_bottom():
    global LED_BOTTOM, switch_state, last_log_time_switch, previous_state_switch, dict_schedules
    global prev_led_brightness, led_bottom_id, sleep_fast, sleep_slow

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
            prev_led_brightness = None
            await asyncio.sleep(sleep_slow)


async def lights_top():
    global LED_TOP, led_top_id, motion_sensor_id, MOTION_SENSOR, light_duration, dict_schedules
    global last_motion, sleep_fast, sleep_slow

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

                day_schedule = dict_schedules.get(5, {})
                night_schedule = dict_schedules.get(6, {})

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
            await asyncio.sleep(sleep_slow)


def cut_card(card_id):
    return card_id[:6] + "000000"


# async def front_door():
#     global CARD_READER
#     scanned_card = None

#     while True:
#         try:
#             scanned_card = CARD_READER.read_no_block()
#             print(f"Scanned card: {scanned_card}")
#             await asyncio.sleep(0)

#             if scanned_card is not None:
#                 print(f"Card {scanned_card} detected at the front door.")

#         except Exception as e:
#             print(f"Error reading card: {e}")


async def front_door():
    global DOOR_LOCK, REED_SWITCH, CARD_READER
    global servo_lock_id, reed_switch_id, card_reader_id
    scanned_card = None

    while True:
        try:
            scanned_card = CARD_READER.read_no_block()
            print(f"Scanned card: {scanned_card}")
            await asyncio.sleep(0)

            if scanned_card is not None:
                scanned_card = str(scanned_card)
                snipped_card = cut_card(scanned_card)
                log_and_emit_async(snipped_card, card_reader_id)

                try:
                    checked_card = DataRepository.read_card_by_id(snipped_card)

                    if checked_card is None:
                        continue

                    DOOR_LOCK.unlock()
                    log_and_emit_async(1, servo_lock_id)

                    start_time = time.time()

                    while GPIO.input(REED_SWITCH) == 1:
                        if time.time() - start_time > 5:
                            logger.info(
                                "Door did not open in time (5 seconds) - locking again"
                            )
                            DOOR_LOCK.lock()

                            log_and_emit_async(0, servo_lock_id)
                            continue

                        time.sleep(sleep_fast)

                    else:
                        log_and_emit_async(1, reed_switch_id)
                        start_time = time.time()

                        while GPIO.input(REED_SWITCH) == 0:
                            if time.time() - start_time > 10:
                                logger.info(
                                    "Door did not close in time (10 seconds) - locking anyway"
                                )

                                continue

                            time.sleep(sleep_fast)

                        log_and_emit_async(0, reed_switch_id)
                        DOOR_LOCK.lock()
                        log_and_emit_async(0, servo_lock_id)

                except Exception as e:
                    logger.error(f"Error processing card: {e}")
                    try:
                        DOOR_LOCK.lock()
                        log_and_emit_async(0, servo_lock_id)

                    except Exception as lock_error:
                        logger.error(f"Error locking door: {lock_error}")

            time.sleep(sleep_fast)

        except Exception as e:
            logger.error(f"Error in front_door: {e}")
            time.sleep(sleep_slow)


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
            await asyncio.sleep(sleep_slow)


def power_button(pin):
    global power_button_hold_start, power_button_held

    try:
        current_state = GPIO.input(pin)

        if current_state == 0 and power_button_hold_start is None:
            power_button_hold_start = time.time()
            logger.info("Power button pressed - starting 3-second hold timer")

    except Exception as e:
        logger.error(f"Error in power_button: {e}")


async def monitor_power_button():
    global POWER_BUTTON, power_button_hold_start, power_button_held
    global switch_state_power, button_power_id, powerlink_shutdown_requested

    while True:
        try:
            if POWER_BUTTON and power_button_hold_start is not None:
                current_state = GPIO.input(POWER_BUTTON)
                hold_duration = time.time() - power_button_hold_start

                if current_state == 1:
                    if hold_duration < 3.0:
                        logger.info(
                            f"Power button released after {hold_duration:.1f}s - too short"
                        )
                    power_button_hold_start = None
                    power_button_held = False

                elif hold_duration >= 3.0 and not power_button_held:
                    power_button_held = True
                    logger.info(
                        "=== POWER BUTTON HELD FOR 3 SECONDS - SHUTDOWN INITIATED ==="
                    )

                    switch_state_power = not switch_state_power
                    log_and_emit_sync(switch_state_power, button_power_id)

                    if not switch_state_power:
                        # Use the new shutdown function
                        await shutdown_powerlink_system()

            await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Error in monitor_power_button: {e}")
            power_button_hold_start = None
            power_button_held = False
            await asyncio.sleep(1)


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
        CARD_READER = SimpleMFRC522()
        LCD = LCD_Display(0x38, 5, 6)
        DOOR_LOCK = ServoLock(12)
        LED_OUTDOORS = 13
        GPIO.setup(LED_OUTDOORS, GPIO.OUT)
        LED_BOTTOM = LED(24)
        LED_TOP = LED(19)
        HEATING = HeatingPad(20)
        AIRCO = DCMotor(18)
        MCP = MCP3008(0, 1)
        I2C_EXPANDER = TCA9548A()

        tasks = [
            # asyncio.create_task(front_door()),
            asyncio.create_task(get_wattage()),
            asyncio.create_task(climate_control(temp_id)),
            asyncio.create_task(do_lights_button()),
            asyncio.create_task(lights_bottom()),
            asyncio.create_task(lights_top()),
            asyncio.create_task(lights_outdoors()),
            asyncio.create_task(display_lcd()),
            asyncio.create_task(monitor_power_button()),
        ]

        GPIO.add_event_detect(
            LED_BUTTON, GPIO.FALLING, callback=lights_button, bouncetime=250
        )
        GPIO.add_event_detect(
            POWER_BUTTON, GPIO.BOTH, callback=power_button, bouncetime=50
        )

        yield

    finally:
        logger.info("Shutting down application...")

        log_and_emit_sync(0, wh_bat_in_id)
        log_and_emit_sync(0, wh_bat_out_id)
        log_and_emit_sync(0, heater_id)
        log_and_emit_sync(0, wh_heater_id)
        log_and_emit_sync(0, fan_id)
        log_and_emit_sync(0, wh_fan_id)
        log_and_emit_sync(0, button_lights_id)
        log_and_emit_sync(0, led_bottom_id)
        log_and_emit_sync(0, wh_led_bottom_id)
        log_and_emit_sync(0, motion_sensor_id)
        log_and_emit_sync(0, led_top_id)
        log_and_emit_sync(0, wh_led_top_id)
        log_and_emit_sync(0, reed_switch_id)
        log_and_emit_sync(0, servo_lock_id)
        log_and_emit_sync(0, led_outdoors_id)
        log_and_emit_sync(0, button_power_id)

        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        try:
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
            # if CARD_READER:
            #     CARD_READER.cleanup()
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

            logger.info("GPIO cleaned up. Normal shutdown completed.")

        except Exception as e:
            logger.error(f"Error during normal cleanup: {e}")


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
async def get_inhabitant_by_id_card(card_id: str):
    data = DataRepository.read_inhabitant_by_card_id(card_id)
    if data is None:
        raise HTTPException(
            status_code=404, detail=f"inhabitant with ID {card_id} not found"
        )
    return data


@app.get(ENDPOINT + "/inhabitants/")
async def get_all_inhabitants():
    data = DataRepository.read_all_inhabitants()
    return data if data else []


@app.get(ENDPOINT + "/inhabitants/{inhabitant_id}/")
async def get_inhabitant_by_id(inhabitant_id: int):
    data = DataRepository.read_inhabitant_by_id(inhabitant_id)
    if not data:
        raise HTTPException(status_code=404, detail="Inhabitant not found")
    return data


@app.post(ENDPOINT + "/inhabitants/")
async def create_inhabitant(inhabitant_data: DTOInhabitant):
    inhabitant_id = DataRepository.create_inhabitant(
        inhabitant_data.first_name, inhabitant_data.last_name, inhabitant_data.card_id
    )
    return DataRepository.read_inhabitant_by_id(inhabitant_id)


@app.put(ENDPOINT + "/inhabitants/{inhabitant_id}/")
async def update_inhabitant(inhabitant_id: int, inhabitant_data: DTOInhabitant):
    DataRepository.update_inhabitant(
        inhabitant_id,
        inhabitant_data.first_name,
        inhabitant_data.last_name,
        inhabitant_data.card_id,
    )
    return DataRepository.read_inhabitant_by_id(inhabitant_id)


@app.delete(ENDPOINT + "/inhabitants/{inhabitant_id}/")
async def delete_inhabitant(inhabitant_id: int):
    DataRepository.delete_inhabitant(inhabitant_id)
    return {"message": "Inhabitant deleted"}


@app.get(
    ENDPOINT + "/history/temperature/${component_id}/15m/",
    response_model=list[HistoryLog],
    summary="Retrieve 15 minutes history",
    response_description="A list of history for the last 15 minutes",
    tags=["history"],
)
async def get_all_history_15min(component_id: int):
    data = DataRepository.read_log_history_15min(component_id)
    if data is None or len(data) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No history found in the database for the last 15 minutes",
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


@app.get("/api/v1/history/{component_id}/7d/")
async def get_component_history_7d(component_id: int, chart_type: str = "default"):

    try:
        if chart_type == "temperature":
            history_data = DataRepository.read_temperature_history_7d(component_id)
        else:
            history_data = DataRepository.read_log_history_7d(component_id)

        return history_data
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching component history: {str(e)}"
        )


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


@app.get(ENDPOINT + "/history/temperature/{component_id}/7d/")
async def get_temperature_history_7d(component_id: int):
    try:
        history_data = DataRepository.read_temperature_daily_history_7d(component_id)
        return history_data
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching temperature history: {str(e)}"
        )


@app.get(
    ENDPOINT + "/history/{component_id}/",
    response_model=LogAmount,
    summary="Retrieve a log_amount by ID",
    response_description="The log_amount with the specified ID",
    tags=["history"],
)
async def get_log_amount_by_id(component_id: int):
    data = DataRepository.read_log_history_amount_7d_by_id(component_id)
    if data is None:
        raise HTTPException(
            status_code=404, detail=f"log_amount with ID {component_id} not found"
        )
    return data


@app.get(
    ENDPOINT + "/history/{component_id}/count/7d/",
    response_model=list[LogCountHistory],
    summary="Retrieve 7-day log count history by component ID",
    response_description="The 7-day log count history for the specified component",
    tags=["history"],
)
async def get_log_count_history_7d_by_id(component_id: int):
    data = DataRepository.read_log_count_history_7d_by_id(component_id)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Log count history for component ID {component_id} not found",
        )
    return data


@app.get(
    ENDPOINT + "/energy/{component_id}/24h/",
    response_model=EnergyLog,
    summary="Retrieve a energy_log by ID",
    response_description="The energy_log with the specified ID",
    tags=["energy"],
)
async def get_energy_log_by_id(component_id: int):
    data = DataRepository.read_energy_24h(component_id)
    if data is None:
        raise HTTPException(
            status_code=404, detail=f"energy_log with ID {component_id} not found"
        )
    return data


@app.get(
    ENDPOINT + "/energy/{component_id}/7d/",
    response_model=EnergyLog,
    summary="Retrieve an energy_log by ID",
    response_description="The energy_log with the specified ID",
    tags=["energy"],
)
async def get_energy_log_7d(component_id: int):
    data = DataRepository.read_energy_7d(component_id)
    if data is None:
        return {"total_kwh": 0}
    return data


@app.get(
    ENDPOINT + "/energy/{component_id}/24h/",
    response_model=EnergyLog,
    summary="Retrieve an energy_log by ID",
    response_description="The energy_log with the specified ID",
    tags=["energy"],
)
async def get_energy_log_24h(component_id: int):
    data = DataRepository.read_energy_24h(component_id)
    if data is None:
        return {"total_kwh": 0}
    return data


@app.get(
    ENDPOINT + "/entered/{card_id}/last/",
    response_model=LastEntered,
    summary="Retrieve last entered person by card ID",
    response_description="The last person who entered with the specified card ID",
    tags=["entered"],
)
async def get_last_entered_by_card_id(card_id: str):
    data = DataRepository.read_last_entered(card_id)
    return data


@app.post(
    ENDPOINT + "/verify-powerlink-password/",
    response_model=PasswordVerificationResponse,
    summary="Verify PowerLink password",
    response_description="Result of the password verification",
    tags=["powerlink"],
)
async def verify_powerlink_password(password: PasswordVerificationRequest):
    if password.password == powerlink_password:
        return {"valid": True, "message": "Password verified."}
    else:
        raise HTTPException(status_code=401, detail="Incorrect password")


@app.get(
    ENDPOINT + "/battery/level/",
    summary="Get current battery level",
    response_description="Current battery level percentage",
    tags=["battery"],
)
async def get_current_battery_level():
    return {"battery_level": round(battery_level, 1)}


# endregion FastAPI Endpoints *************************


# region Socket.IO Handlers ---------------------------------
@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")


@sio.on("BF2_schedule_updated")
async def schedule_handler(sid, data):
    global dict_schedules
    dict_schedules[data["schedule_id"]] = data


@sio.on("BF2_manual_door_control")
async def manual_door_control_handler(sid, data):
    component_id = data.get("component_id")
    action = data.get("action")

    if not DOOR_LOCK:
        return

    if action == "unlock":
        DOOR_LOCK.unlock()
        new_state = 1
    else:
        DOOR_LOCK.lock()
        new_state = 0

    await log_and_emit_async(new_state, servo_lock_id)

    await sio.emit(
        "B2F_door_control_success",
        {
            "component_id": component_id,
            "action": action,
            "new_state": new_state,
        },
    )


@sio.on("BF2_manual_light_control")
async def manual_light_control_handler(sid, data):
    global switch_state
    component_id = data.get("component_id")
    new_value = data.get("value", 0)

    if component_id == led_bottom_id and LED_BOTTOM:
        if new_value > 0:
            LED_BOTTOM.set_brightness(new_value)
            switch_state = True
        else:
            LED_BOTTOM.off()
            switch_state = False

    elif component_id == led_top_id and LED_TOP:
        if new_value > 0:
            LED_TOP.set_brightness(new_value)
        else:
            LED_TOP.off()

    elif component_id == led_outdoors_id and LED_OUTDOORS:
        GPIO.output(LED_OUTDOORS, GPIO.HIGH if new_value > 0 else GPIO.LOW)

    else:
        return

    await log_and_emit_async(new_value, component_id)

    await sio.emit(
        "B2F_light_control_success",
        {
            "component_id": component_id,
            "new_value": new_value,
        },
    )


@sio.on("BF2_manual_powerlink_control")
async def manual_powerlink_control_handler(sid, data):
    global powerlink_shutdown_requested
    component_id = data.get("component_id")
    action = data.get("action")

    await log_and_emit_async(0 if action == "off" else 1, component_id)

    if action == "off":
        logger.info("=== POWERLINK SHUTDOWN INITIATED VIA MANUAL CONTROL ===")

        await sio.emit(
            "B2F_powerlink_control_success",
            {
                "component_id": component_id,
                "action": action,
                "message": "System shutdown initiated",
            },
        )

        # Give the frontend time to receive the message
        await asyncio.sleep(2)

        # Use the new shutdown function
        await shutdown_powerlink_system()

    else:
        await sio.emit(
            "B2F_powerlink_control_success",
            {
                "component_id": component_id,
                "action": action,
            },
        )


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

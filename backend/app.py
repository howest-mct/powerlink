# region Setup -----------------------------------------

import asyncio
import socketio
import uvicorn
import logging
import threading
from RPi import GPIO
import time
import datetime

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from repositories.DataRepository import DataRepository
from models.backend_models import Log, DTOLog, Schedule, DTOSchedule

from models.device_models import (
    DS18B20,
    INA219,
    SR501,
    LCD_Display,
    DCMotor,
    HeatingPad,
    LED,
    SolenoidLock,
    MCP3008,
    SerialComm,
    PCF8574A,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True,
)
logger = logging.getLogger(__name__)

# endregion Setup ********************************


# region Global Variables ---------------------------------

# Database ID's
heater_id = 1
airco_id = 2
led_bottom_id = 3
led_top_id = 4
led_outdoors_id = 5
solenoid_lock_id = 6
motion_sensor_id = 7
button_lights_id = 8
reed_switch_id = 9
rfid_id = 10
temp_sensor_id = 11
light_sensor_id = 12
wh_led_bottom_id = 13
wh_led_top_id = 14
wh_heater_id = 15
wh_airco_id = 16
wh_bat_in_id = 17
wh_bat_out_id = 18

# Devices
MOTION_SENSOR = None
LED_BUTTON = None
REED_SWITCH = None
TEMP_SENSOR = None

LCD = None
DOOR_LOCK = None
LED_OUTDOORS = None
LED_BOTTOM = None
LED_TOP = None
HEATING = None
AIRCO = None
SERIAL = None
MCP = None

INA_LED_BOTTOM = None
INA_LED_TOP = None
INA_HEATING = None
INA_AIRCO = None
INA_BAT_IN = None
INA_BAT_OUT = None

# Values
background_loop = None
raspi_power = None

motion = None
switch_state = None
temp_id = None
temp = None
pot_value = None
ldr_value = None

lcd_string = None
lock_state = None

led_outdoors_brightness = None
led_bottom_brightness = None
led_top_brightness = None

heating_value = None
airco_value = None
serial_string = None

kw_led_bottom = None
kw_led_top = None
kw_heating = None
kw_airco = None

GPIO.setmode(GPIO.BCM)

# endregion Global Variables **************************


# region Functions ---------------------------------


def lights_button(pin):
    global switch_state
    switch_state = not switch_state
    DataRepository.create_log(value=switch_state, component_id=button_lights_id)


def lights_top():
    global LED_OUTDOORS, MOTION_SENSOR, led_outdoors_brightness
    motion_detected = MOTION_SENSOR.motion_detected()
    print(f"Motion detected: {motion_detected}")
    if motion_detected:
        LED_TOP.set_brightness(100)
    else:
        LED_TOP.set_brightness(0)


def lights_bottom():
    global LED_BOTTOM, switch_state, led_bottom_brightness
    if switch_state:
        LED_BOTTOM.set_brightness(100)
    else:
        LED_BOTTOM.set_brightness(0)


def lights_outdoors():
    global LED_OUTDOORS, led_outdoors_brightness
    ldr_value = round((MCP.read_channel(1) * 100) / 1023, 0)
    if ldr_value > 75:
        LED_OUTDOORS.set_brightness(100)
    else:
        LED_OUTDOORS.off()


# endregion Functions ****************************


# region Tasks ---------------------------------


def main():
    global motion, temp_id, temp, pot_value, ldr_value
    temp_id = TEMP_SENSOR.get_id()

    while True:
        lights_outdoors()
        lights_bottom()
        lights_top()

        time.sleep(0.5)


async def allesuit():
    pass


async def tweede_thread():
    pass


# endregion Tasks ****************************


# region App Setup ---------------------------------

background_loop = None


@asynccontextmanager
async def lifespan_manager(app: FastAPI):
    logger.info("Starting application...")

    GPIO.setmode(GPIO.BCM)

    try:
        global MOTION_SENSOR, LED_BUTTON, REED_SWITCH, TEMP_SENSOR
        global LCD, DOOR_LOCK, LED_OUTDOORS, LED_BOTTOM, LED_TOP
        global HEATING, AIRCO, SERIAL, MCP, INA_LED_BOTTOM, INA_LED_TOP
        global INA_HEATING, INA_AIRCO, INA_BAT_IN, INA_BAT_OUT

        MOTION_SENSOR = SR501(26)
        LED_BUTTON = 19
        GPIO.setup(LED_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        REED_SWITCH = 13
        GPIO.setup(REED_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        TEMP_SENSOR = DS18B20()

        LCD = LCD_Display(0x38, 5, 6)
        DOOR_LOCK = SolenoidLock(21)
        LED_OUTDOORS = LED(20)
        LED_BOTTOM = LED(25)
        LED_TOP = LED(24)
        HEATING = HeatingPad(16)
        AIRCO = DCMotor(12)
        SERIAL = SerialComm()
        MCP = MCP3008()

        INA_LED_BOTTOM = INA219(1, 0x45)
        INA_LED_TOP = INA219(1, 0x41)
        INA_HEATING = INA219(1, 0x40)
        INA_AIRCO = INA219(1, 0x44)
        INA_BAT_IN = None
        INA_BAT_OUT = None

        logger.info("GPIO devices initialized successfully")

        global background_loop
        background_loop = asyncio.get_running_loop()
        threading.Thread(target=main, daemon=True).start()

        GPIO.add_event_detect(
            LED_BUTTON, GPIO.FALLING, callback=lights_button, bouncetime=150
        )

        yield

    finally:
        logger.info("Shutting down application...")
        MOTION_SENSOR.cleanup()
        GPIO.cleanup()
        logger.info("GPIO cleaned up. Bye!")

        MOTION_SENSOR.cleanup()

        LCD.close()
        DOOR_LOCK.cleanup()
        LED_OUTDOORS.cleanup()
        LED_BOTTOM.cleanup()
        LED_TOP.cleanup()
        HEATING.cleanup()
        AIRCO.cleanup()

        SERIAL.close()
        MCP.close()
        INA_LED_BOTTOM.close()
        INA_LED_TOP.close()
        INA_HEATING.close()
        INA_AIRCO.close()


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
    ENDPOINT + "/logs/",
    response_model=list[Log],
    summary="Retrieve all logs",
    response_description="A list of all available logs",
    tags=["logs"],
)
async def get_all_logs():
    data = DataRepository.read_all_logs()
    if data is None or len(data) == 0:
        raise HTTPException(status_code=404, detail="No logs found in the database")
    return data


@app.get(
    ENDPOINT + "/logs/{id}/all/",
    response_model=list[Log],
    summary="Retrieve a log by ID",
    response_description="The log with the specified ID",
    tags=["logs"],
)
async def get_all_logs_by_component_id(id: int):
    data = DataRepository.read_all_logs_by_component_id(id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"log with ID {id} not found")
    return data


@app.get(
    ENDPOINT + "/logs/{id}/last/",
    response_model=Log,
    summary="Retrieve a log by ID",
    response_description="The last log with the specified ID",
    tags=["logs"],
)
async def get_last_log_by_id(id: int):
    data = DataRepository.read_last_log_by_component_id(id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"log with ID /{id} not found")
    return data


@app.get(
    ENDPOINT + "/logs/{id}/24h/",
    response_model=list[Log],
    summary="Retrieve a last log by ID",
    response_description="The last 24h logs with the specified ID",
    tags=["logs"],
)
async def get_logs_last_24_hours_by_id(id: int):
    data = DataRepository.read_logs_last_24_hours_by_component_id(id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"last log with ID {id} not found")
    return data


@app.get(
    ENDPOINT + "/logs/{id}/week/",
    response_model=list[Log],
    summary="Retrieve logs last week by ID",
    response_description="Thr logs last week with the specified ID",
    tags=["logs"],
)
async def get_logs_last_week_by_id(id: int):
    data = DataRepository.read_logs_last_week_by_component_id(id)
    if data is None:
        raise HTTPException(
            status_code=404, detail=f"logs last week with ID {id} not found"
        )
    return data


@app.get(
    ENDPOINT + "/logs/{id}/week2/",
    response_model=list[Log],
    summary="Retrieve a logs between 1 and 2 weeks by ID",
    response_description="The logs between 1 and 2 weeks with the specified ID",
    tags=["logs"],
)
async def get_logs_between_1_and_2_weeks_by_component_id(id: int):
    data = DataRepository.read_logs_between_1_and_2_weeks_by_component_id(id)
    if data is None:
        raise HTTPException(
            status_code=404, detail=f"logs between 1 and 2 weeks with ID {id} not found"
        )
    return data


@app.get(
    ENDPOINT + "/schedules/{id}/",
    response_model=Schedule,
    summary="Retrieve a schedule by ID",
    response_description="The schedule with the specified ID",
    tags=["schedules"],
)
async def get_schedule_by_id(id: int):
    data = DataRepository.read_schedule_by_id(id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"schedule with ID {id} not found")
    return data


@app.put(
    ENDPOINT + "/schedules/{id}/",
    response_model=Schedule,
    summary="Update a schedule",
    response_description="The updated schedule",
    tags=["schedules"],
)
async def update_schedule(id: int, schedule: DTOSchedule):
    item_data = DataRepository.read_schedule_by_id(id)
    if item_data is None:
        raise HTTPException(status_code=404, detail=f"schedule with ID {id} not found")
    column_1 = schedule.start_time
    column_2 = schedule.end_time
    column_3 = schedule.value
    column_4 = schedule.enabled
    update_result = DataRepository.update_schedule(
        id, column_1, column_2, column_3, column_4
    )
    if update_result == 0:
        raise HTTPException(
            status_code=400,
            detail="Failed to update schedule due to invalid data or server error",
        )
    return DataRepository.read_schedule_by_id(id)


# endregion FastAPI Endpoints *************************


# region Socket.IO Handlers ---------------------------------


@sio.event
async def connect(sid, environ):
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

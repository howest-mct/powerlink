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
    Button,
    ReedSwitch,
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


# region App Setup ---------------------------------

background_loop = None


@asynccontextmanager
async def lifespan_manager(app: FastAPI):
    logger.info("Starting application...")

    # Set GPIO mode
    GPIO.setmode(GPIO.BCM)

    try:
        MOTION_SENSOR = SR501(26)
        LIGHT_BUTTON = Button(19)
        REED_SWITCH = ReedSwitch(13)
        TEMP_SENSOR = DS18B20()
        LCD = LCD_Display(0x38, 5, 6)
        DOOR_LOCK = SolenoidLock(21)
        LIGHTS_OUTDOORS = LED(20)
        LIGHTS_BOTTOM = LED(25)
        LIGHTS_TOP = LED(24)
        HEATING = HeatingPad(16)
        AIRCO = DCMotor(12)
        SERIAL = SerialComm()
        MCP = MCP3008()
        INA_LIGHTS_BOTTOM = INA219(1, 0x45)
        INA_LIGHTS_TOP = INA219(1, 0x41)
        INA_HEATING = INA219(1, 0x40)
        INA_AIRCO = INA219(1, 0x44)

        logger.info("GPIO devices initialized successfully")

        global background_loop
        background_loop = asyncio.get_running_loop()
        threading.Thread(target=main, daemon=True).start()

        yield

    finally:
        logger.info("Shutting down application...")
        if MOTION_SENSOR:
            MOTION_SENSOR.cleanup()
        if LIGHT_BUTTON:
            LIGHT_BUTTON.cleanup()
        if REED_SWITCH:
            REED_SWITCH.cleanup()
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

sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi", logger=True)
sio_app = socketio.ASGIApp(sio, app)

ENDPOINT = "/api/v1"

# endregion App Setup ********************************


# region Background Tasks ---------------------------------


def main():
    pass


async def allesuit():
    pass


async def tweede_thread():
    pass


# endregion Background Tasks ****************************


# region FastAPI Endpoints ---------------------------------


# region GET Endpoints ---------------------------------


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
    # Fetch the resource by ID from the repository
    data = DataRepository.read_all_logs_by_component_id(id)
    # Check if the resource exists
    if data is None:
        raise HTTPException(status_code=404, detail=f"log with ID {id} not found")
    # Return the resource
    return data


@app.get(
    ENDPOINT + "/logs/{id}/last/",
    response_model=Log,
    summary="Retrieve a log by ID",
    response_description="The last log with the specified ID",
    tags=["logs"],
)
async def get_last_log_by_id(id: int):
    # Fetch the resource by ID from the repository
    data = DataRepository.read_last_log_by_component_id(id)
    # Check if the resource exists
    if data is None:
        raise HTTPException(status_code=404, detail=f"log with ID {id} not found")
    # Return the resource
    return data


@app.get(
    ENDPOINT + "/logs/{id}/24h/",
    response_model=list[Log],
    summary="Retrieve a last log by ID",
    response_description="The last 24h logs with the specified ID",
    tags=["logs"],
)
async def get_logs_last_24_hours_by_id(id: int):
    # Fetch the resource by ID from the repository
    data = DataRepository.read_logs_last_24_hours_by_component_id(id)
    # Check if the resource exists
    if data is None:
        raise HTTPException(status_code=404, detail=f"last log with ID {id} not found")
    # Return the resource
    return data


@app.get(
    ENDPOINT + "/logs/{id}/week/",
    response_model=list[Log],
    summary="Retrieve logs last week by ID",
    response_description="Thr logs last week with the specified ID",
    tags=["logs"],
)
async def get_logs_last_week_by_id(id: int):
    # Fetch the resource by ID from the repository
    data = DataRepository.read_logs_last_week_by_component_id(id)
    # Check if the resource exists
    if data is None:
        raise HTTPException(
            status_code=404, detail=f"logs last week with ID {id} not found"
        )
    # Return the resource
    return data


@app.get(
    ENDPOINT + "/logs/{id}/week2/",
    response_model=list[Log],
    summary="Retrieve a logs between 1 and 2 weeks by ID",
    response_description="The logs between 1 and 2 weeks with the specified ID",
    tags=["logs"],
)
async def get_logs_between_1_and_2_weeks_by_component_id(id: int):
    # Fetch the resource by ID from the repository
    data = DataRepository.read_logs_between_1_and_2_weeks_by_component_id(id)
    # Check if the resource exists
    if data is None:
        raise HTTPException(
            status_code=404, detail=f"logs between 1 and 2 weeks with ID {id} not found"
        )
    # Return the resource
    return data


@app.get(
    ENDPOINT + "/schedules/{id}/",
    response_model=Schedule,
    summary="Retrieve a schedule by ID",
    response_description="The schedule with the specified ID",
    tags=["schedules"],
)
async def get_schedule_by_id(id: int):
    # Fetch the resource by ID from the repository
    data = DataRepository.read_schedule_by_id(id)
    # Check if the resource exists
    if data is None:
        raise HTTPException(status_code=404, detail=f"schedule with ID {id} not found")

    # Return the resource
    return data


# endregion GET Endpoints *************************


# region POST Endpoints ---------------------------------


# endregion PATCH Endpoints *************************


@app.put(
    ENDPOINT + "/schedules/{id}/",
    response_model=Schedule,
    summary="Update a schedule",
    response_description="The updated schedule",
    tags=["schedules"],
)
async def update_schedule(id: int, schedule: DTOSchedule):
    # Check if the resource exists
    item_data = DataRepository.read_schedule_by_id(id)
    if item_data is None:
        raise HTTPException(status_code=404, detail=f"schedule with ID {id} not found")
    # Extract fields from the request body
    column_1 = schedule.start_time
    column_2 = schedule.end_time
    column_3 = schedule.value
    column_4 = schedule.enabled
    # Update the resource using separate parameters
    update_result = DataRepository.update_schedule(
        id, column_1, column_2, column_3, column_4
    )
    if update_result == 0:
        raise HTTPException(
            status_code=400,
            detail="Failed to update schedule due to invalid data or server error",
        )
    return DataRepository.read_schedule_by_id(id)


# region PATCH Endpoints ---------------------------------


# endregion POST Endpoints *************************


# region FastAPI Endpoints *************************


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
        reload=False,  # False to avoid GPIO conflicts
        reload_dirs=["backend"],
    )

# endregion Run The App **************************

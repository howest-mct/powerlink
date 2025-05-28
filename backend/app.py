# region Setup -----------------------------------------

import asyncio
import socketio
import uvicorn
import logging
import threading
from RPi import GPIO
import time

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from repositories.DataRepository import DataRepository

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


# region GPIO Pins ---------------------------------
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


GPIO.setmode(GPIO.BCM)


# endregion GPIO Pins ********************************


# region App Setup ---------------------------------
background = None


@asynccontextmanager
async def lifespan_manager(app: FastAPI):
    logger.info("GPIO initialised")

    global background
    background = asyncio.get_running_loop()
    background.create_task()
    threading.Thread(target=main, daemon=True).start()

    yield

    GPIO.cleanup()

    logger.info("Bye!")


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

# GLOBAL VARIABLES


# endregion App Setup ********************************


# region Background Tasks ---------------------------------


# endregion Background Tasks ****************************


def main():
    """Registreert de knop‑callback en houdt de thread ‘alive’."""

    def button_pressed(channel):
        global led_state
        led_state = 1 - led_state
        DataRepository.update_status_lamp(1, led_state)
        GPIO.output(LED, led_state)
        lamp_data = DataRepository.read_status_lamp_by_id(1)

        # ⬇️ We zitten nu in een *andere* thread dan de FastAPI‑event‑loop
        future = asyncio.run_coroutine_threadsafe(
            sio.emit("B2F_verandering_lamp", {"lamp": lamp_data}),
            loop,
        )
        # `run_coroutine_threadsafe` post de coroutine naar de hoofd‑event‑loop
        # en geeft een *Future* terug waarmee je (optioneel) op fouten kunt wachten.
        logger.debug("Emit scheduled from GPIO thread – future: %s", future)

    GPIO.add_event_detect(BUTTON, GPIO.FALLING, button_pressed, bouncetime=200)
    logger.info("gpio_keep_alive gestart; wacht op button events…")

    while True:
        time.sleep(1)  # de thread levend houden


async def allesuit():
    print("[allesuit] Gestart. Alles uit!")
    DataRepository.update_status_alle_lampen(0)
    global led_state
    led_state = 0
    GPIO.output(LED, 0)

    # 1) B2F_alles_uit
    await sio.emit("B2F_alles_uit", {"status": "connected"})

    # 2) B2F_status_lampen => updated states
    new_statuses = DataRepository.read_status_lampen()
    await sio.emit("B2F_status_lampen", {"lampen": new_statuses})

    return {"message": "Alles uit!"}


async def tweede_thread():
    # This function is called every 10 seconds to set all lights to OFF
    # and emit the status to all connected clients.
    print("[alles_uit] Gestart.")
    while True:
        await allesuit()
        await asyncio.sleep(10)


# region FastAPI Endpoints ---------------------------------


@app.get("/")
async def root():
    return "Server werkt, maar hier geen API endpoint gevonden."


@app.patch(
    ENDPOINT + "/lampen/{lamp_id}/status/",
    response_model=LampStatus,
    summary="Update lamp status",
)
async def update_lamp_status(lamp_id: int, status: DTOLampStatus):
    print(f"[RESTAPI] => Lamp {lamp_id} naar {status.nieuwe_status}")
    DataRepository.update_status_lamp(lamp_id, status.nieuwe_status)

    if lamp_id == 1:
        global led_state
        led_state = status.nieuwe_status
        GPIO.output(LED, led_state)

    lamp_data = DataRepository.read_status_lamp_by_id(lamp_id)
    print(lamp_data)
    await sio.emit("B2F_verandering_lamp", {"lamp": lamp_data})
    return LampStatus(lamp=lamp_id, status=lamp_data["status"])


# endregion FastAPI Endpoints *************************


# region Socket.IO Handlers ---------------------------------


@sio.event
async def connect(sid, environ):
    print(f"[Socket.IO] Client geconnecteerd: {sid}")
    lampenstatus = DataRepository.read_status_lampen()
    await sio.emit("B2F_status_lampen", {"lampen": lampenstatus}, to=sid)


# endregion Socket.IO Handlers *************************


# region Run The App ---------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "app:sio_app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True,
        reload_dirs=["backend"],
    )

# endregion Run The App **************************

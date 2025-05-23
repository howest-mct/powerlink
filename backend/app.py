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
from models.models import LampStatus, DTOLampStatus

# ----------------------------------------------------

logging.basicConfig(
    level=logging.INFO,  # alles ≥ INFO‑niveau tonen
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",  # Europees datum‑formaat
    force=True,  # herconfigureer bij auto‑reload
)
logger = logging.getLogger(__name__)


BUTTON = 20
LED = 21


# ----------------------------------------------------
# App setup
# ----------------------------------------------------
loop = None


@asynccontextmanager
# Lifespan Manager (Startup/Shutdown)
async def lifespan_manager(app: FastAPI):
    # Start background taken (process_queue + all_out) op in de applicatie
    global loop

    loop = asyncio.get_running_loop()

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(LED, GPIO.OUT)
    logger.info("GPIO initialised")

    threading.Thread(
        target=gpio_keep_alive,
        daemon=True,  # 🔑 daemon‑threads stoppen automatisch bij app‑exit
    ).start()

    loop.create_task(
        tweede_thread()
    )  # loop.create_task for asyncio world / async tasks
    # Geef controle aan FastAPI/Socket.IO

    # Geef controle aan FastAPI/Socket.IO
    yield

    GPIO.cleanup()
    logger.info("GPIO cleaned up – bye!")


# Create a FastAPI app, add CORS middleware, initialize Socket.IO server + ASGI app, create async queue for messages
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

ENDPOINT = "/api/v1"  # Define the endpoint for the API

led_state = 0  # globale staat bovenaan


# ----------------------------------------------------
# Background Tasks
# ----------------------------------------------------


def gpio_keep_alive():
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


# ----------------------------------------------------
# FastAPI Endpoints
# ----------------------------------------------------


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


# ----------------------------------------------------
# Socket.IO Handlers
# ----------------------------------------------------


@sio.event
async def connect(sid, environ):
    print(f"[Socket.IO] Client geconnecteerd: {sid}")
    lampenstatus = DataRepository.read_status_lampen()
    await sio.emit("B2F_status_lampen", {"lampen": lampenstatus}, to=sid)


# ----------------------------------------------------
# Run the app
# ----------------------------------------------------
if __name__ == "__main__":
    logger.info("Starting Uvicorn server")
    uvicorn.run(sio_app, host="0.0.0.0", port=8000, log_level="info")

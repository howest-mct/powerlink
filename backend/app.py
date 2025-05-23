import asyncio
import socketio
import uvicorn

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from repositories.DataRepository import DataRepository


# TODO: Add logging

# TODO: Add hardware constants
# ----------------------------------------------------
# App setup
# ----------------------------------------------------


@asynccontextmanager
# Lifespan Manager (Startup/Shutdown)
async def lifespan_manager(app: FastAPI):
    # Start background taken (process_queue + all_out) op in de applicatie
    loop = asyncio.get_running_loop()

    # TODO: Add GPIO setup

    loop.create_task(
        tweede_thread()
    )  # loop.create_task for asyncio world / async tasks
    # Geef controle aan FastAPI/Socket.IO
    yield

    # TODO: GPIO cleanup and goodbye


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

# TODO: global variables (like led_state)

# ----------------------------------------------------
# Background Tasks
# ----------------------------------------------------

# TODO: Add GPIO keep alive thread


# TODO: Hernoem allesuit thread
async def allesuit():
    print("[allesuit] Gestart. Alles uit!")
    DataRepository.update_status_alle_lampen(0)

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

    # TODO: Add GPIO update

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
    uvicorn.run(
        "app:sio_app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True,
        reload_dirs=["backend"],
    )

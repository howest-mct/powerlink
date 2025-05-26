import asyncio
import socketio
import uvicorn

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from repositories.DataRepository import DataRepository


# ----------------------------------------------------
# App setup
# ----------------------------------------------------


# ----------------------------------------------------
# Background Tasks
# ----------------------------------------------------


# ----------------------------------------------------
# FastAPI Endpoints
# ----------------------------------------------------


# ----------------------------------------------------
# Socket.IO Handlers
# ----------------------------------------------------


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

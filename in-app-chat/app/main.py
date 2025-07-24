from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os, uvicorn
import logging
from contextlib import asynccontextmanager
from app.database import create_tables
from app.routes import app_chat
import socketio
from app.routes.server import sio

log = logging.getLogger("uvicorn")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    log.info("Starting up...")
    yield
    log.info("Shutting down...")

app = FastAPI(lifespan=lifespan, debug=True)

# Include FastAPI routers first
app.include_router(app_chat.router)

# Mount Socket.IO app at /socket.io path
app.mount("/socket.io", socketio.ASGIApp(sio))
# Filter out None values to avoid CORS errors``
allowed_orgins = list(filter(None, [
    os.getenv("LOCALHOST_URL"),
    os.getenv("WEBAPP_URL"),
    os.getenv("UAT_WEBAPP_URL")
]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_orgins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/__health")
def read_root():
    return {"status": "online"}

@app.get("/")
def read_root():
    return {"message": "Welcome to In-App chat"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8046)
    print(f"Starting server on 8046")
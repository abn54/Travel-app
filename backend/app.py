"""FastAPI application setup for Expedia Lite."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api_routes import router
from database import initialize_database
from hotel_chat_controller import initialize_hotel_assistant_prompt


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Prepare the SQLite model before the API accepts requests."""
    initialize_database()
    initialize_hotel_assistant_prompt()
    yield


app = FastAPI(title="Expedia Lite Part 2 API", version="2.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

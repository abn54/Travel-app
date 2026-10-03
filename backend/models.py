"""Request models for Expedia Lite's SQLite travel data."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


BookingStatus = Literal["confirmed", "cancelled"]


class BookingCreate(BaseModel):
    """A request to create one simulated booking for an offered stay."""

    user_id: str
    trip_id: str


class BookingStatusUpdate(BaseModel):
    """A request to retain a booking while changing its status."""

    status: BookingStatus


class LocalHotelCreate(BaseModel):
    """A provider-backed hotel location saved for local course-data searches."""

    place_id: str = Field(min_length=1, max_length=240)
    name: str | None = Field(default=None, max_length=240)
    address: str | None = Field(default=None, max_length=500)
    latitude: float
    longitude: float
    search_postcode: str = Field(min_length=5, max_length=5)
    locality: str | None = Field(default=None, max_length=160)


class HotelChatRequest(BaseModel):
    """A natural-language question answered from saved local hotel data."""

    question: str = Field(min_length=3, max_length=600)

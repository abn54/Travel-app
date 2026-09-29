"""Request models for Expedia Lite's SQLite travel data."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


BookingStatus = Literal["confirmed", "cancelled"]


class BookingCreate(BaseModel):
    """A request to create one simulated booking for an offered stay."""

    user_id: str
    trip_id: str


class BookingStatusUpdate(BaseModel):
    """A request to retain a booking while changing its status."""

    status: BookingStatus

"""Thin FastAPI routes that map requests to Expedia Lite controllers."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from config import geoapify_key_is_configured
from database import DATABASE_PATH
from hotel_discovery_controller import discover_hotels
from location_controller import lookup_zip_location
from models import BookingCreate, BookingStatusUpdate
from travel_controller import (
    BookingNotFoundError,
    StayNotFoundError,
    TravelerNotFoundError,
    create_booking,
    delete_booking,
    list_booking_history,
    list_travelers,
    search_stays,
    update_booking_status,
)


router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict:
    """Show safe service and configuration status without exposing a key."""
    configuration_status = (
        "key is configured"
        if geoapify_key_is_configured()
        else "key is not configured"
    )
    return {
        "ok": True,
        "database": DATABASE_PATH.name,
        "geoapify": configuration_status,
    }


@router.get("/demo/zip-location")
def demo_zip_location() -> dict:
    """Return the fixed classroom ZIP demonstration result."""
    return location_or_error(lookup_zip_location("16802"))


@router.get("/zip-location")
def zip_location(postcode: str = "") -> dict:
    """Return a safe location response for an entered U.S. ZIP code."""
    return location_or_error(lookup_zip_location(postcode))


def location_or_error(location: dict) -> dict:
    """Map ZIP controller outcomes to safe HTTP responses."""
    if location["status"] == "resolved":
        return location
    if location["status"] == "configuration_error":
        raise HTTPException(
            status_code=503, detail="Location lookup is not configured."
        )
    if location["status"] == "unresolved":
        raise HTTPException(status_code=404, detail="ZIP location could not be resolved.")
    raise HTTPException(status_code=502, detail="Location provider is unavailable.")


@router.get("/hotel-discovery")
def hotel_discovery(postcode: str = "") -> dict:
    """Find provider-backed hotels near the verified center of a U.S. ZIP."""
    result = discover_hotels(postcode)
    if result["status"] in {"resolved", "no_results"}:
        return result
    if result["status"] == "invalid_input":
        raise HTTPException(status_code=422, detail="Enter a five-digit U.S. ZIP code.")
    if result["status"] == "configuration_error":
        raise HTTPException(status_code=503, detail="Hotel discovery is not configured.")
    if result["status"] == "unresolved":
        raise HTTPException(
            status_code=404,
            detail="ZIP code could not be resolved to a U.S. location.",
        )
    raise HTTPException(status_code=502, detail="Hotel discovery service is unavailable.")


@router.get("/search")
def search(hotel_name: str = "") -> list[dict]:
    return search_stays(hotel_name)


@router.get("/users")
def users() -> list[dict]:
    return list_travelers()


@router.get("/bookings")
def bookings(user_id: str = "") -> list[dict]:
    return list_booking_history(user_id)


@router.post("/bookings", status_code=status.HTTP_201_CREATED)
def create_booking_route(payload: BookingCreate) -> dict:
    try:
        return create_booking(payload)
    except TravelerNotFoundError as error:
        raise HTTPException(status_code=404, detail="Traveler was not found.") from error
    except StayNotFoundError as error:
        raise HTTPException(status_code=404, detail="Stay was not found.") from error


@router.patch("/bookings/{booking_id}")
def update_booking_status_route(
    booking_id: str, payload: BookingStatusUpdate
) -> dict:
    try:
        return update_booking_status(booking_id, payload.status)
    except BookingNotFoundError as error:
        raise HTTPException(status_code=404, detail="Booking was not found.") from error


@router.delete("/bookings/{booking_id}")
def delete_booking_route(booking_id: str) -> dict:
    try:
        return delete_booking(booking_id)
    except BookingNotFoundError as error:
        raise HTTPException(status_code=404, detail="Booking was not found.") from error

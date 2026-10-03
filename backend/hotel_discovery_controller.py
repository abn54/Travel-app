"""Backend-only Geoapify hotel discovery around a verified U.S. ZIP center."""
from __future__ import annotations

import json
import math
from typing import Any
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from config import get_geoapify_api_key
from location_controller import ZIP_CODE_PATTERN, lookup_zip_location

PLACES_URL = "https://api.geoapify.com/v2/places"
REQUEST_TIMEOUT_SECONDS = 5
SEARCH_RADIUS_METERS = 5_000
MAX_HOTEL_RESULTS = 20
MAX_PROVIDER_ATTEMPTS = 2


def _number(value: Any, minimum: float, maximum: float) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or not minimum <= number <= maximum:
        return None
    return number


def _optional_text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _search_center(location: dict) -> dict:
    """Return only the location fields needed by the browser."""
    center = {
        "postcode": location["postcode"],
        "country_code": location["country_code"],
        "latitude": location["latitude"],
        "longitude": location["longitude"],
    }
    if location.get("locality"):
        center["locality"] = location["locality"]
    return center


def _hotel_from_feature(feature: Any) -> dict | None:
    """Normalize only provider-supplied, displayable hotel fields."""
    if not isinstance(feature, dict):
        return None
    properties = feature.get("properties")
    geometry = feature.get("geometry")
    if not isinstance(properties, dict) or not isinstance(geometry, dict):
        return None

    place_id = _optional_text(properties.get("place_id"))
    coordinates = geometry.get("coordinates")
    if not place_id or not isinstance(coordinates, list) or len(coordinates) < 2:
        return None
    longitude = _number(coordinates[0], -180, 180)
    latitude = _number(coordinates[1], -90, 90)
    if longitude is None or latitude is None:
        return None

    hotel = {
        "place_id": place_id,
        "name": _optional_text(properties.get("name")),
        "address": _optional_text(properties.get("formatted"))
        or _optional_text(properties.get("address_line2")),
        "latitude": latitude,
        "longitude": longitude,
    }
    distance = _number(properties.get("distance"), 0, float("inf"))
    if distance is not None:
        hotel["distance_meters"] = distance
    return hotel


def _fetch_places(request: Request) -> dict | None:
    """Retry one transient provider failure without treating it as no results."""
    for _ in range(MAX_PROVIDER_ATTEMPTS):
        try:
            with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if isinstance(payload, dict) and isinstance(payload.get("features"), list):
                return payload
        except (OSError, URLError, UnicodeDecodeError, json.JSONDecodeError):
            continue
    return None


def discover_hotels(postcode: str) -> dict:
    """Resolve a ZIP, then find provider-backed hotels inside a 5 km circle."""
    requested_postcode = postcode.strip()
    if not ZIP_CODE_PATTERN.fullmatch(requested_postcode):
        return {"status": "invalid_input", "postcode": requested_postcode}

    location = lookup_zip_location(requested_postcode)
    if location["status"] != "resolved":
        return location

    key = get_geoapify_api_key()
    if not key:
        return {"status": "configuration_error", "postcode": requested_postcode}

    longitude = location["longitude"]
    latitude = location["latitude"]
    query = urlencode(
        {
            "categories": "accommodation.hotel",
            "filter": f"circle:{longitude},{latitude},{SEARCH_RADIUS_METERS}",
            "bias": f"proximity:{longitude},{latitude}",
            "limit": MAX_HOTEL_RESULTS,
            "apiKey": key,
        }
    )
    request = Request(f"{PLACES_URL}?{query}", headers={"Accept": "application/json"})
    payload = _fetch_places(request)
    if payload is None:
        return {"status": "provider_error", "postcode": requested_postcode}

    features = payload["features"]

    hotels = [hotel for feature in features if (hotel := _hotel_from_feature(feature))]
    result = {
        "status": "resolved" if hotels else "no_results",
        "search_center": _search_center(location),
        "hotels": hotels,
    }
    return result

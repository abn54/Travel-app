"""Backend-only Geoapify postcode lookup controller."""
from __future__ import annotations

import json
import math
import re
from typing import Any
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from config import get_geoapify_api_key

GEOCODE_SEARCH_URL = "https://api.geoapify.com/v1/geocode/search"
REQUEST_TIMEOUT_SECONDS = 5
ZIP_CODE_PATTERN = re.compile(r"\d{5}")


def _valid_coordinate(value: Any, minimum: float, maximum: float) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        coordinate = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(coordinate) or not minimum <= coordinate <= maximum:
        return None
    return coordinate


def _location_from_result(result: Any, requested_postcode: str) -> dict | None:
    if not isinstance(result, dict):
        return None

    country_code = str(result.get("country_code", "")).strip()
    provider_postcode = str(result.get("postcode", "")).strip()
    latitude = _valid_coordinate(result.get("lat"), -90, 90)
    longitude = _valid_coordinate(result.get("lon"), -180, 180)
    if (
        country_code.casefold() != "us"
        or provider_postcode != requested_postcode
        or latitude is None
        or longitude is None
    ):
        return None

    location = {
        "status": "resolved",
        "postcode": provider_postcode,
        "country_code": country_code.upper(),
        "latitude": latitude,
        "longitude": longitude,
    }
    for field in ("city", "town", "village", "municipality"):
        locality = result.get(field)
        if isinstance(locality, str) and locality.strip():
            location["locality"] = locality.strip()
            break
    return location


def lookup_zip_location(postcode: str) -> dict:
    """Look up a U.S. ZIP code without exposing provider credentials or errors."""
    requested_postcode = postcode.strip()
    if not ZIP_CODE_PATTERN.fullmatch(requested_postcode):
        return {"status": "unresolved", "postcode": requested_postcode}

    key = get_geoapify_api_key()
    if not key:
        return {"status": "configuration_error", "postcode": requested_postcode}

    query = urlencode(
        {
            "postcode": requested_postcode,
            "type": "postcode",
            "filter": "countrycode:us",
            "format": "json",
            "apiKey": key,
        }
    )
    request = Request(f"{GEOCODE_SEARCH_URL}?{query}", headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, UnicodeDecodeError, json.JSONDecodeError):
        return {"status": "provider_error", "postcode": requested_postcode}

    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        return {"status": "provider_error", "postcode": requested_postcode}

    for result in payload["results"]:
        location = _location_from_result(result, requested_postcode)
        if location is not None:
            return location
    return {"status": "unresolved", "postcode": requested_postcode}

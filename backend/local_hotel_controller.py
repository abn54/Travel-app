"""SQLite controller for locally saved provider hotels and demo stay data."""
from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta, timezone

from database import get_connection
from models import LocalHotelCreate


DEMO_STAY_START = date(2026, 10, 10)
DEMO_STAY_DATES = tuple(
    (DEMO_STAY_START + timedelta(days=offset)).isoformat() for offset in range(7)
)


class LocalHotelNotFoundError(Exception):
    """Raised when a requested locally saved hotel is no longer present."""


def _demo_nights(place_id: str) -> list[tuple[str, float, int]]:
    """Create repeatable, clearly simulated course data for one saved location."""
    seed = sum(ord(character) for character in place_id) % 65
    base_rate = 120 + seed
    return [
        (
            stay_date,
            float(base_rate + (offset * 9)),
            1 + ((seed + (offset * 2)) % 5),
        )
        for offset, stay_date in enumerate(DEMO_STAY_DATES)
    ]


def _serialize_local_hotel(
    connection: sqlite3.Connection, row: sqlite3.Row
) -> dict:
    nights = connection.execute(
        """
        SELECT stay_date, nightly_rate_usd, available_rooms
        FROM demo_hotel_nights
        WHERE place_id = ?
        ORDER BY stay_date
        """,
        (row["place_id"],),
    ).fetchall()
    return {
        "place_id": row["place_id"],
        "name": row["name"] or "Name not provided",
        "address": row["address"] or "Address not provided",
        "locality": row["locality"],
        "latitude": float(row["latitude"]),
        "longitude": float(row["longitude"]),
        "search_postcode": row["search_postcode"],
        "saved_at": row["saved_at"],
        "demo_nights": [
            {
                "stay_date": night["stay_date"],
                "nightly_rate_usd": float(night["nightly_rate_usd"]),
                "available_rooms": int(night["available_rooms"]),
            }
            for night in nights
        ],
        "rates_and_availability_are_simulated": True,
    }


def list_local_hotels(query: str = "") -> list[dict]:
    """Read saved provider locations, optionally filtering local SQLite records."""
    search_term = query.strip()
    connection = get_connection()
    try:
        statement = """
            SELECT place_id, name, address, locality, latitude, longitude,
                   search_postcode, saved_at
            FROM local_hotels
        """
        parameters: tuple[str, ...] = ()
        if search_term:
            pattern = f"%{search_term}%"
            statement += """
                WHERE name LIKE ? COLLATE NOCASE
                   OR address LIKE ? COLLATE NOCASE
                   OR locality LIKE ? COLLATE NOCASE
                   OR search_postcode LIKE ? COLLATE NOCASE
            """
            parameters = (pattern, pattern, pattern, pattern)
        statement += " ORDER BY saved_at DESC, name COLLATE NOCASE"
        rows = connection.execute(statement, parameters).fetchall()
        return [_serialize_local_hotel(connection, row) for row in rows]
    finally:
        connection.close()


def save_local_hotel(payload: LocalHotelCreate) -> dict:
    """Persist one provider location once and give it dated simulated course data."""
    connection = get_connection()
    try:
        existing = connection.execute(
            "SELECT place_id FROM local_hotels WHERE place_id = ?", (payload.place_id,)
        ).fetchone()
        created = existing is None
        if created:
            connection.execute(
                """
                INSERT INTO local_hotels (
                    place_id, name, address, locality, latitude, longitude,
                    search_postcode, saved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.place_id,
                    payload.name.strip() if payload.name else None,
                    payload.address.strip() if payload.address else None,
                    payload.locality.strip() if payload.locality else None,
                    payload.latitude,
                    payload.longitude,
                    payload.search_postcode,
                    datetime.now(timezone.utc).isoformat(timespec="seconds"),
                ),
            )
            connection.executemany(
                """
                INSERT INTO demo_hotel_nights (
                    place_id, stay_date, nightly_rate_usd, available_rooms
                ) VALUES (?, ?, ?, ?)
                """,
                [
                    (payload.place_id, stay_date, nightly_rate, rooms)
                    for stay_date, nightly_rate, rooms in _demo_nights(payload.place_id)
                ],
            )
            connection.commit()
        row = connection.execute(
            """
            SELECT place_id, name, address, locality, latitude, longitude,
                   search_postcode, saved_at
            FROM local_hotels WHERE place_id = ?
            """,
            (payload.place_id,),
        ).fetchone()
        return {"created": created, "hotel": _serialize_local_hotel(connection, row)}
    finally:
        connection.close()


def delete_local_hotel(place_id: str) -> dict:
    """Remove a saved location and its simulated night records from SQLite."""
    connection = get_connection()
    try:
        deleted = connection.execute(
            "DELETE FROM local_hotels WHERE place_id = ?", (place_id,)
        )
        if deleted.rowcount == 0:
            raise LocalHotelNotFoundError
        connection.commit()
        return {"deleted_id": place_id}
    finally:
        connection.close()

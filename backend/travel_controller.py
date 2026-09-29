"""Database controller for Expedia Lite hotel stays and booking CRUD."""
from __future__ import annotations

import sqlite3
from datetime import date

from database import get_connection
from models import BookingCreate, BookingStatus


class TravelerNotFoundError(Exception):
    """Raised when a create request uses an unknown supplied traveler."""


class StayNotFoundError(Exception):
    """Raised when a create request uses an unknown offered stay."""


class BookingNotFoundError(Exception):
    """Raised when an update or delete target does not exist."""


def serialize_stay(row: sqlite3.Row) -> dict:
    """Turn a joined hotel/trip row into frontend-ready stay data."""
    nights = (date.fromisoformat(row["check_out"]) - date.fromisoformat(row["check_in"])).days
    nightly_rate = float(row["nightly_rate_usd"])
    return {
        "trip_id": row["trip_id"],
        "hotel_id": row["hotel_id"],
        "hotel_name": row["hotel_name"],
        "city": row["city"],
        "state": row["state"],
        "trip_name": row["trip_name"],
        "nightly_rate": nightly_rate,
        "check_in": row["check_in"],
        "check_out": row["check_out"],
        "nights": nights,
        "stay_price": nights * nightly_rate,
    }


def booking_details(connection: sqlite3.Connection, booking_id: str) -> dict | None:
    """Return one booking joined to its traveler, stay, and hotel."""
    row = connection.execute(
        """
        SELECT b.booking_id, b.booked_on, b.status, u.user_id, u.display_name,
               t.trip_id, t.trip_name, t.check_in, t.check_out,
               h.hotel_id, h.hotel_name, h.city, h.state, h.nightly_rate_usd
        FROM bookings AS b
        JOIN users AS u ON u.user_id = b.user_id
        JOIN trips AS t ON t.trip_id = b.trip_id
        JOIN hotels AS h ON h.hotel_id = t.hotel_id
        WHERE b.booking_id = ?
        """,
        (booking_id,),
    ).fetchone()
    if row is None:
        return None
    booking = serialize_stay(row)
    booking.update(
        {
            "booking_id": row["booking_id"],
            "booked_on": row["booked_on"],
            "status": row["status"],
            "user_id": row["user_id"],
            "display_name": row["display_name"],
        }
    )
    return booking


def search_stays(hotel_name: str) -> list[dict]:
    """Search SQLite hotel and trip records by hotel name or city."""
    query = hotel_name.strip()
    if not query:
        return []
    pattern = f"%{query}%"
    connection = get_connection()
    try:
        rows = connection.execute(
            """
            SELECT t.trip_id, t.hotel_id, t.trip_name, t.check_in, t.check_out,
                   h.hotel_name, h.city, h.state, h.nightly_rate_usd
            FROM trips AS t
            JOIN hotels AS h ON h.hotel_id = t.hotel_id
            WHERE h.hotel_name LIKE ? COLLATE NOCASE
               OR h.city LIKE ? COLLATE NOCASE
            ORDER BY t.check_in, t.trip_id
            """,
            (pattern, pattern),
        ).fetchall()
        return [serialize_stay(row) for row in rows]
    finally:
        connection.close()


def list_travelers() -> list[dict]:
    """Read the supplied demo travelers from SQLite."""
    connection = get_connection()
    try:
        rows = connection.execute(
            "SELECT user_id, display_name FROM users ORDER BY user_id"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def list_booking_history(user_id: str = "") -> list[dict]:
    """Read booking history, optionally for one traveler."""
    connection = get_connection()
    try:
        query = """
            SELECT b.booking_id, b.booked_on, b.status, u.user_id, u.display_name,
                   t.trip_id, t.trip_name, t.check_in, t.check_out,
                   h.hotel_id, h.hotel_name, h.city, h.state, h.nightly_rate_usd
            FROM bookings AS b
            JOIN users AS u ON u.user_id = b.user_id
            JOIN trips AS t ON t.trip_id = b.trip_id
            JOIN hotels AS h ON h.hotel_id = t.hotel_id
        """
        parameters: tuple[str, ...] = ()
        if user_id.strip():
            query += " WHERE b.user_id = ?"
            parameters = (user_id.strip(),)
        query += " ORDER BY b.booked_on DESC, b.booking_id DESC"
        rows = connection.execute(query, parameters).fetchall()
        bookings = []
        for row in rows:
            booking = serialize_stay(row)
            booking.update(
                {
                    "booking_id": row["booking_id"],
                    "booked_on": row["booked_on"],
                    "status": row["status"],
                    "user_id": row["user_id"],
                    "display_name": row["display_name"],
                }
            )
            bookings.append(booking)
        return bookings
    finally:
        connection.close()


def create_booking(payload: BookingCreate) -> dict:
    """Create one persisted booking with the next never-reused B### ID."""
    connection = get_connection()
    try:
        if connection.execute(
            "SELECT 1 FROM users WHERE user_id = ?", (payload.user_id,)
        ).fetchone() is None:
            raise TravelerNotFoundError
        if connection.execute(
            "SELECT 1 FROM trips WHERE trip_id = ?", (payload.trip_id,)
        ).fetchone() is None:
            raise StayNotFoundError
        sequence_row = connection.execute(
            "SELECT state_value FROM app_state WHERE state_key = ?",
            ("next_booking_number",),
        ).fetchone()
        if sequence_row is None:
            raise RuntimeError("Booking sequence is unavailable.")
        sequence = int(sequence_row["state_value"])
        booking_id = f"B{sequence:03d}"
        connection.execute(
            """
            INSERT INTO bookings (booking_id, user_id, trip_id, booked_on, status)
            VALUES (?, ?, ?, ?, 'confirmed')
            """,
            (booking_id, payload.user_id, payload.trip_id, date.today().isoformat()),
        )
        connection.execute(
            "UPDATE app_state SET state_value = ? WHERE state_key = ?",
            (str(sequence + 1), "next_booking_number"),
        )
        connection.commit()
        return booking_details(connection, booking_id) or {}
    finally:
        connection.close()


def update_booking_status(booking_id: str, booking_status: BookingStatus) -> dict:
    """Update a persisted booking status without deleting its record."""
    connection = get_connection()
    try:
        updated = connection.execute(
            "UPDATE bookings SET status = ? WHERE booking_id = ?",
            (booking_status, booking_id),
        )
        if updated.rowcount == 0:
            raise BookingNotFoundError
        connection.commit()
        return booking_details(connection, booking_id) or {}
    finally:
        connection.close()


def delete_booking(booking_id: str) -> dict:
    """Delete only the selected test booking from SQLite."""
    connection = get_connection()
    try:
        deleted = connection.execute(
            "DELETE FROM bookings WHERE booking_id = ?", (booking_id,)
        )
        if deleted.rowcount == 0:
            raise BookingNotFoundError
        connection.commit()
        return {"deleted_id": booking_id}
    finally:
        connection.close()

"""Expedia FastAPI service: SQLite search and booking CRUD for Part 2."""
from __future__ import annotations

import csv
import sqlite3
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DATA_DIR = Path(__file__).resolve().parent / "data"
DATABASE_PATH = Path(__file__).resolve().parent / "travel.db"


class BookingCreate(BaseModel):
    user_id: str
    trip_id: str


class BookingStatusUpdate(BaseModel):
    status: Literal["confirmed", "cancelled"]


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA_DIR / f"{name}.csv").open(newline="", encoding="utf-8-sig") as source:
        return list(csv.DictReader(source))


def create_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS hotels (
            hotel_id TEXT PRIMARY KEY,
            hotel_name TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            nightly_rate_usd REAL NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS trips (
            trip_id TEXT PRIMARY KEY,
            hotel_id TEXT NOT NULL REFERENCES hotels(hotel_id),
            trip_name TEXT NOT NULL,
            check_in TEXT NOT NULL,
            check_out TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            display_name TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(user_id),
            trip_id TEXT NOT NULL REFERENCES trips(trip_id),
            booked_on TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('confirmed', 'cancelled'))
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS app_state (
            state_key TEXT PRIMARY KEY,
            state_value TEXT NOT NULL
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_trips_hotel_id ON trips(hotel_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_bookings_user_id ON bookings(user_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_bookings_trip_id ON bookings(trip_id)"
    )


def seed_new_database(connection: sqlite3.Connection) -> None:
    """Load the starter pack only while creating a brand-new database file."""
    connection.executemany(
        """
        INSERT INTO hotels (hotel_id, hotel_name, city, state, nightly_rate_usd)
        VALUES (:hotel_id, :hotel_name, :city, :state, :nightly_rate_usd)
        """,
        read_csv("hotels"),
    )
    connection.executemany(
        """
        INSERT INTO trips (trip_id, hotel_id, trip_name, check_in, check_out)
        VALUES (:trip_id, :hotel_id, :trip_name, :check_in, :check_out)
        """,
        read_csv("trips"),
    )
    connection.executemany(
        "INSERT INTO users (user_id, display_name) VALUES (:user_id, :display_name)",
        read_csv("users"),
    )
    connection.executemany(
        """
        INSERT INTO bookings (booking_id, user_id, trip_id, booked_on, status)
        VALUES (:booking_id, :user_id, :trip_id, :booked_on, :status)
        """,
        read_csv("bookings"),
    )
    highest_seed_number = max(int(row["booking_id"][1:]) for row in read_csv("bookings"))
    connection.execute(
        "INSERT INTO app_state (state_key, state_value) VALUES (?, ?)",
        ("next_booking_number", str(highest_seed_number + 1)),
    )


def initialize_database() -> None:
    is_new_database = not DATABASE_PATH.exists()
    connection = get_connection()
    try:
        create_schema(connection)
        if is_new_database:
            seed_new_database(connection)
        connection.execute("PRAGMA optimize")
        connection.commit()
    finally:
        connection.close()


def serialize_stay(row: sqlite3.Row) -> dict:
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


def get_booking(connection: sqlite3.Connection, booking_id: str) -> dict | None:
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


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="Expedia Part 2 API", version="2.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "database": DATABASE_PATH.name}


@app.get("/api/search")
def search(hotel_name: str = "") -> list[dict]:
    """Search the SQLite hotel and trip records by hotel name or city."""
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


@app.get("/api/users")
def list_users() -> list[dict]:
    connection = get_connection()
    try:
        rows = connection.execute(
            "SELECT user_id, display_name FROM users ORDER BY user_id"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


@app.get("/api/bookings")
def list_bookings(user_id: str = "") -> list[dict]:
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


@app.post("/api/bookings", status_code=status.HTTP_201_CREATED)
def create_booking(payload: BookingCreate) -> dict:
    connection = get_connection()
    try:
        if connection.execute(
            "SELECT 1 FROM users WHERE user_id = ?", (payload.user_id,)
        ).fetchone() is None:
            raise HTTPException(status_code=404, detail="Traveler was not found.")
        if connection.execute(
            "SELECT 1 FROM trips WHERE trip_id = ?", (payload.trip_id,)
        ).fetchone() is None:
            raise HTTPException(status_code=404, detail="Stay was not found.")
        sequence = int(
            connection.execute(
                "SELECT state_value FROM app_state WHERE state_key = ?",
                ("next_booking_number",),
            ).fetchone()["state_value"]
        )
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
        return get_booking(connection, booking_id) or {}
    finally:
        connection.close()


@app.patch("/api/bookings/{booking_id}")
def update_booking_status(booking_id: str, payload: BookingStatusUpdate) -> dict:
    connection = get_connection()
    try:
        updated = connection.execute(
            "UPDATE bookings SET status = ? WHERE booking_id = ?",
            (payload.status, booking_id),
        )
        if updated.rowcount == 0:
            raise HTTPException(status_code=404, detail="Booking was not found.")
        connection.commit()
        return get_booking(connection, booking_id) or {}
    finally:
        connection.close()


@app.delete("/api/bookings/{booking_id}")
def delete_booking(booking_id: str) -> dict:
    connection = get_connection()
    try:
        deleted = connection.execute(
            "DELETE FROM bookings WHERE booking_id = ?", (booking_id,))
        if deleted.rowcount == 0:
            raise HTTPException(status_code=404, detail="Booking was not found.")
        connection.commit()
        return {"deleted_id": booking_id}
    finally:
        connection.close()

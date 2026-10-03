"""SQLite model setup and one-time CSV seed for Expedia Lite."""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent / "data"
DATABASE_PATH = Path(__file__).resolve().parent / "travel.db"
SEED_STATE_KEY = "starter_data_v1"


def get_connection() -> sqlite3.Connection:
    """Open an SQLite connection with dictionary-like rows and FK checks."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def read_csv(name: str) -> list[dict[str, str]]:
    """Read a supplied CSV, including the source files' UTF-8 BOM header."""
    with (DATA_DIR / f"{name}.csv").open(newline="", encoding="utf-8-sig") as source:
        return list(csv.DictReader(source))


def create_schema(connection: sqlite3.Connection) -> None:
    """Create the relational travel model without changing existing rows."""
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
        """
        CREATE TABLE IF NOT EXISTS local_hotels (
            place_id TEXT PRIMARY KEY,
            name TEXT,
            address TEXT,
            locality TEXT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            search_postcode TEXT NOT NULL,
            saved_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS demo_hotel_nights (
            place_id TEXT NOT NULL REFERENCES local_hotels(place_id) ON DELETE CASCADE,
            stay_date TEXT NOT NULL,
            nightly_rate_usd REAL NOT NULL CHECK(nightly_rate_usd >= 0),
            available_rooms INTEGER NOT NULL CHECK(available_rooms >= 0),
            PRIMARY KEY (place_id, stay_date)
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
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_demo_hotel_nights_date ON demo_hotel_nights(stay_date)"
    )


def seed_new_database(connection: sqlite3.Connection) -> None:
    """Load the starter records exactly once, when the database file is new."""
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
    booking_rows = read_csv("bookings")
    connection.executemany(
        """
        INSERT INTO bookings (booking_id, user_id, trip_id, booked_on, status)
        VALUES (:booking_id, :user_id, :trip_id, :booked_on, :status)
        """,
        booking_rows,
    )
    highest_seed_number = max(int(row["booking_id"][1:]) for row in booking_rows)
    connection.execute(
        "INSERT INTO app_state (state_key, state_value) VALUES (?, ?)",
        ("next_booking_number", str(highest_seed_number + 1)),
    )
    connection.execute(
        "INSERT INTO app_state (state_key, state_value) VALUES (?, ?)",
        (SEED_STATE_KEY, "complete"),
    )


def repair_legacy_empty_booking_seed(connection: sqlite3.Connection) -> None:
    """Repair one legacy database created before the starter-seed marker existed.

    The marker prevents a later user deletion from reloading starter records.
    Only an older database with no marker and no booking rows receives the
    supplied booking seed once; its existing booking-ID sequence is preserved.
    """
    marker = connection.execute(
        "SELECT 1 FROM app_state WHERE state_key = ?", (SEED_STATE_KEY,)
    ).fetchone()
    if marker is not None:
        return

    booking_count = connection.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
    if booking_count == 0:
        connection.executemany(
            """
            INSERT INTO bookings (booking_id, user_id, trip_id, booked_on, status)
            VALUES (:booking_id, :user_id, :trip_id, :booked_on, :status)
            """,
            read_csv("bookings"),
        )
    connection.execute(
        "INSERT INTO app_state (state_key, state_value) VALUES (?, ?)",
        (SEED_STATE_KEY, "complete"),
    )


def initialize_database() -> None:
    """Create a new SQLite database from the CSV seed without reseeding later."""
    is_new_database = not DATABASE_PATH.exists()
    connection = get_connection()
    try:
        create_schema(connection)
        if is_new_database:
            seed_new_database(connection)
        else:
            repair_legacy_empty_booking_seed(connection)
        connection.execute("PRAGMA optimize")
        connection.commit()
    finally:
        connection.close()

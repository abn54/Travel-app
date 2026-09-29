"""SQLite CRUD and persistence checks for the Assignment 1 Part 2 controller."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database
import travel_controller
from models import BookingCreate


class TravelControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        temporary_database = Path(self.temporary_directory.name) / "travel.db"
        self.database_path = patch.object(database, "DATABASE_PATH", temporary_database)
        self.database_path.start()
        database.initialize_database()

    def tearDown(self) -> None:
        self.database_path.stop()
        self.temporary_directory.cleanup()

    def test_search_returns_the_supplied_stay(self) -> None:
        stays = travel_controller.search_stays("Valley Trail Inn")

        self.assertEqual([stay["trip_id"] for stay in stays], ["T008"])
        self.assertEqual(stays[0]["hotel_name"], "Valley Trail Inn")

    def test_create_cancel_delete_and_restart_preserve_expected_rows(self) -> None:
        traveler = travel_controller.list_travelers()[-1]
        stay = travel_controller.search_stays("Valley Trail Inn")[0]

        created = travel_controller.create_booking(
            BookingCreate(user_id=traveler["user_id"], trip_id=stay["trip_id"])
        )
        self.assertEqual(created["booking_id"], "B007")
        self.assertEqual(created["status"], "confirmed")

        cancelled = travel_controller.update_booking_status(
            created["booking_id"], "cancelled"
        )
        self.assertEqual(cancelled["status"], "cancelled")

        test_booking = travel_controller.create_booking(
            BookingCreate(user_id=traveler["user_id"], trip_id=stay["trip_id"])
        )
        self.assertEqual(test_booking["booking_id"], "B008")
        self.assertEqual(
            travel_controller.delete_booking(test_booking["booking_id"]),
            {"deleted_id": "B008"},
        )

        database.initialize_database()
        history = travel_controller.list_booking_history(traveler["user_id"])
        persisted = {booking["booking_id"]: booking for booking in history}
        self.assertEqual(persisted["B007"]["status"], "cancelled")
        self.assertNotIn("B008", persisted)
        self.assertEqual(len(travel_controller.list_booking_history()), 7)

    def test_legacy_empty_booking_table_is_repaired_only_once(self) -> None:
        connection = database.get_connection()
        try:
            connection.execute("DELETE FROM bookings")
            connection.execute(
                "DELETE FROM app_state WHERE state_key = ?", (database.SEED_STATE_KEY,)
            )
            connection.commit()
        finally:
            connection.close()

        database.initialize_database()
        self.assertEqual(len(travel_controller.list_booking_history()), 6)

        connection = database.get_connection()
        try:
            connection.execute("DELETE FROM bookings")
            connection.commit()
        finally:
            connection.close()

        database.initialize_database()
        self.assertEqual(travel_controller.list_booking_history(), [])

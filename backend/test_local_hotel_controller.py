"""SQLite checks for local provider-hotel storage and demo stay records."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database
import local_hotel_controller
from models import LocalHotelCreate


SAVED_HOTEL = LocalHotelCreate(
    place_id="provider-state-college-1",
    name="Example Local Hotel",
    address="1 College Avenue, State College, PA",
    latitude=40.8,
    longitude=-77.86,
    search_postcode="16802",
    locality="State College",
)


class LocalHotelControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        temporary_database = Path(self.temporary_directory.name) / "travel.db"
        self.database_path = patch.object(database, "DATABASE_PATH", temporary_database)
        self.database_path.start()
        database.initialize_database()

    def tearDown(self) -> None:
        self.database_path.stop()
        self.temporary_directory.cleanup()

    def test_save_prevents_duplicates_and_keeps_demo_nights_after_restart(self) -> None:
        first_save = local_hotel_controller.save_local_hotel(SAVED_HOTEL)
        duplicate_save = local_hotel_controller.save_local_hotel(SAVED_HOTEL)

        self.assertTrue(first_save["created"])
        self.assertFalse(duplicate_save["created"])
        self.assertEqual(len(first_save["hotel"]["demo_nights"]), 7)
        self.assertTrue(first_save["hotel"]["rates_and_availability_are_simulated"])
        self.assertEqual(
            first_save["hotel"]["demo_nights"][0]["stay_date"], "2026-10-10"
        )

        database.initialize_database()
        saved = local_hotel_controller.list_local_hotels("college")
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]["place_id"], SAVED_HOTEL.place_id)
        self.assertEqual(len(saved[0]["demo_nights"]), 7)

    def test_delete_removes_saved_hotel_and_its_local_nights(self) -> None:
        local_hotel_controller.save_local_hotel(SAVED_HOTEL)

        self.assertEqual(
            local_hotel_controller.delete_local_hotel(SAVED_HOTEL.place_id),
            {"deleted_id": SAVED_HOTEL.place_id},
        )
        self.assertEqual(local_hotel_controller.list_local_hotels(), [])

        database.initialize_database()
        self.assertEqual(local_hotel_controller.list_local_hotels(), [])

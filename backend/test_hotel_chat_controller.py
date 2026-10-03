"""Mocked checks for the Assignment 2 Part 2 RAG workflow."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database
import hotel_chat_controller
import local_hotel_controller
from models import LocalHotelCreate


LOCAL_HOTEL = LocalHotelCreate(
    place_id="provider-chat-1",
    name="Chat Test Hotel",
    address="1 Example Road, State College, PA",
    latitude=40.8,
    longitude=-77.86,
    search_postcode="16802",
    locality="State College",
)

VALID_PROPOSAL = '''{
  "sql": "SELECT h.name, n.stay_date, n.nightly_rate_usd, n.available_rooms FROM local_hotels h JOIN demo_hotel_nights n ON n.place_id = h.place_id WHERE n.stay_date = ? AND n.available_rooms > 0 ORDER BY n.nightly_rate_usd ASC LIMIT 10",
  "parameters": ["2026-10-10"]
}'''


class HotelChatControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        temporary_database = Path(self.temporary_directory.name) / "travel.db"
        self.database_path = patch.object(database, "DATABASE_PATH", temporary_database)
        self.chat_database_path = patch.object(
            hotel_chat_controller, "DATABASE_PATH", temporary_database
        )
        self.database_path.start()
        self.chat_database_path.start()
        database.initialize_database()
        local_hotel_controller.save_local_hotel(LOCAL_HOTEL)

    def tearDown(self) -> None:
        self.chat_database_path.stop()
        self.database_path.stop()
        self.temporary_directory.cleanup()

    @patch("hotel_chat_controller.request_chat_completion")
    def test_question_runs_two_model_steps_around_readonly_retrieval(self, mock_completion) -> None:
        mock_completion.side_effect = [
            VALID_PROPOSAL,
            "Chat Test Hotel is the lowest-priced local option for Oct. 10. Its rate and rooms are simulated course data.",
        ]

        result = hotel_chat_controller.ask_hotel_assistant(
            "Which saved hotel costs the least on October 10?"
        )

        self.assertEqual(mock_completion.call_count, 2)
        self.assertEqual(result["parameters"], ["2026-10-10"])
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(result["records"][0]["name"], "Chat Test Hotel")
        self.assertIn("simulated course data", result["answer"])
        answer_messages = mock_completion.call_args_list[1].args[0]
        self.assertIn("Chat Test Hotel", answer_messages[1]["content"])

    @patch("hotel_chat_controller.request_chat_completion")
    def test_no_match_is_answered_after_a_successful_empty_local_query(self, mock_completion) -> None:
        mock_completion.side_effect = [
            '''{"sql": "SELECT h.name, n.stay_date FROM local_hotels h JOIN demo_hotel_nights n ON n.place_id = h.place_id WHERE n.stay_date = ? LIMIT 10", "parameters": ["2026-12-31"]}''',
            "There are no saved local hotel records for that date.",
        ]

        result = hotel_chat_controller.ask_hotel_assistant(
            "What is available on December 31?"
        )

        self.assertEqual(result["records"], [])
        self.assertIn("no saved local hotel records", result["answer"])
        self.assertEqual(mock_completion.call_count, 2)

    def test_disallowed_sql_is_rejected_before_any_database_write(self) -> None:
        with self.assertRaises(hotel_chat_controller.ChatQueryRejectedError):
            hotel_chat_controller.validate_sql("DELETE FROM local_hotels LIMIT 1", [])

        self.assertEqual(len(local_hotel_controller.list_local_hotels()), 1)

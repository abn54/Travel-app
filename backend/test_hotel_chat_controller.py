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
  "sql": "SELECT h.name, z.postcode, n.stay_date, n.nightly_rate_usd, n.available_rooms FROM saved_hotels h JOIN saved_hotel_zips z ON z.hotel_id = h.hotel_id JOIN demo_hotel_nights n ON n.hotel_id = h.hotel_id WHERE z.postcode = ? AND n.stay_date = ? AND n.available_rooms > 0 ORDER BY n.nightly_rate_usd ASC LIMIT 10",
  "parameters": ["16802", "2026-10-10"]
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
        self.assertEqual(result["parameters"], ["16802", "2026-10-10"])
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(result["records"][0]["name"], "Chat Test Hotel")
        self.assertIn("simulated course data", result["answer"])
        answer_messages = mock_completion.call_args_list[1].args[0]
        self.assertIn("Chat Test Hotel", answer_messages[1]["content"])
        trace = hotel_chat_controller.get_conversation_trace(result["conversation_id"])
        self.assertEqual(
            [entry["stage"] for entry in trace],
            ["user_question", "proposed_sql", "executed_sql", "retrieval_result", "final_answer"],
        )

    @patch("hotel_chat_controller.request_chat_completion")
    def test_no_match_is_answered_after_a_successful_empty_local_query(self, mock_completion) -> None:
        mock_completion.side_effect = [
            '''{"sql": "SELECT h.name, n.stay_date FROM saved_hotels h JOIN demo_hotel_nights n ON n.hotel_id = h.hotel_id WHERE n.stay_date = ? LIMIT 10", "parameters": ["2026-12-31"]}''',
            "There are no saved local hotel records for that date.",
        ]

        result = hotel_chat_controller.ask_hotel_assistant(
            "What is available on December 31?"
        )

        self.assertEqual(result["records"], [])
        self.assertIn("no saved local hotel records", result["answer"])
        self.assertEqual(mock_completion.call_count, 2)

    @patch("hotel_chat_controller.request_chat_completion")
    def test_follow_up_uses_saved_conversation_context(self, mock_completion) -> None:
        mock_completion.side_effect = [
            VALID_PROPOSAL,
            "Chat Test Hotel is available on Oct. 10.",
            VALID_PROPOSAL,
            "Chat Test Hotel also has simulated data for the follow-up.",
        ]

        first = hotel_chat_controller.ask_hotel_assistant("What is available on October 10?")
        second = hotel_chat_controller.ask_hotel_assistant("What about October 12?", first["conversation_id"])

        self.assertEqual(first["conversation_id"], second["conversation_id"])
        proposal_messages = mock_completion.call_args_list[2].args[0]
        self.assertTrue(any(message["content"] == "What is available on October 10?" for message in proposal_messages))
        self.assertTrue(any(message["content"] == "Chat Test Hotel is available on Oct. 10." for message in proposal_messages))
        self.assertEqual(len(second["conversation"]), 4)
        database.initialize_database()
        self.assertEqual(len(hotel_chat_controller.get_conversation_trace(first["conversation_id"])), 10)

    @patch("hotel_chat_controller.request_chat_completion", side_effect=hotel_chat_controller.ChatProviderError)
    def test_provider_failure_is_saved_without_a_fabricated_answer(self, _mock_completion) -> None:
        with self.assertRaises(hotel_chat_controller.ChatProviderError):
            hotel_chat_controller.ask_hotel_assistant("What is available on October 10?")

        connection = database.get_connection()
        try:
            stages = [row[0] for row in connection.execute(
                "SELECT stage FROM conversation_messages ORDER BY message_id"
            ).fetchall()]
        finally:
            connection.close()
        self.assertEqual(stages, ["user_question", "provider_error"])

    def test_disallowed_sql_is_rejected_before_any_database_write(self) -> None:
        with self.assertRaises(hotel_chat_controller.ChatQueryRejectedError):
            hotel_chat_controller.validate_sql("DELETE FROM saved_hotels LIMIT 1", [])

        self.assertEqual(len(local_hotel_controller.list_local_hotels()), 1)

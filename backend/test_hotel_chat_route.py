"""Safe route mapping checks for the RAG chatbot endpoint."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi import HTTPException

import api_routes
from hotel_chat_controller import ChatConfigurationError, ChatProviderError
from models import HotelChatRequest


class HotelChatRouteTests(unittest.TestCase):
    @patch("api_routes.ask_hotel_assistant")
    def test_route_returns_the_checked_workflow_details(self, mock_assistant) -> None:
        mock_assistant.return_value = {
            "question": "Which option is lowest?",
            "proposed_sql": "SELECT name FROM local_hotels LIMIT 10",
            "parameters": [],
            "records": [],
            "answer": "No local records are saved.",
            "conversation_id": "hotel-test-1234",
        }

        response = api_routes.hotel_chat(HotelChatRequest(question="Which option is lowest?"))

        self.assertEqual(response, mock_assistant.return_value)
        mock_assistant.assert_called_once_with("Which option is lowest?", None)

    @patch("api_routes.ask_hotel_assistant", side_effect=ChatConfigurationError)
    def test_route_hides_missing_configuration_details(self, _mock_assistant) -> None:
        with self.assertRaises(HTTPException) as raised:
            api_routes.hotel_chat(HotelChatRequest(question="Which option is lowest?"))

        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(raised.exception.detail, "Hotel assistant is not configured.")

    @patch("api_routes.ask_hotel_assistant", side_effect=ChatProviderError)
    def test_route_hides_provider_failure_details(self, _mock_assistant) -> None:
        with self.assertRaises(HTTPException) as raised:
            api_routes.hotel_chat(HotelChatRequest(question="Which option is lowest?"))

        self.assertEqual(raised.exception.status_code, 502)
        self.assertEqual(raised.exception.detail, "Hotel assistant is temporarily unavailable.")

    @patch("api_routes.get_conversation_trace")
    def test_conversation_route_returns_saved_trace(self, mock_trace) -> None:
        mock_trace.return_value = [{"message_id": 1, "stage": "user_question"}]

        response = api_routes.hotel_conversation("hotel-example-1234")

        self.assertEqual(response["conversation_id"], "hotel-example-1234")
        self.assertEqual(response["trace"], mock_trace.return_value)

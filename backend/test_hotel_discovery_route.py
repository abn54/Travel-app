"""Mocked checks for the Part 1 hotel-discovery FastAPI route."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi import HTTPException

import api_routes


class HotelDiscoveryRouteTests(unittest.TestCase):
    @patch("api_routes.discover_hotels")
    def test_route_returns_successful_no_results_without_an_error(self, mock_discover) -> None:
        mock_discover.return_value = {
            "status": "no_results",
            "search_center": {"postcode": "00501"},
            "hotels": [],
        }

        result = api_routes.hotel_discovery("00501")

        self.assertEqual(result, mock_discover.return_value)
        mock_discover.assert_called_once_with("00501")

    @patch("api_routes.discover_hotels", return_value={"status": "invalid_input"})
    def test_route_maps_invalid_input_to_a_clear_error(self, _mock_discover) -> None:
        with self.assertRaises(HTTPException) as raised:
            api_routes.hotel_discovery("12")

        self.assertEqual(raised.exception.status_code, 422)
        self.assertEqual(raised.exception.detail, "Enter a five-digit U.S. ZIP code.")

    @patch("api_routes.discover_hotels", return_value={"status": "provider_error"})
    def test_route_maps_provider_failure_to_a_clear_error(self, _mock_discover) -> None:
        with self.assertRaises(HTTPException) as raised:
            api_routes.hotel_discovery("00501")

        self.assertEqual(raised.exception.status_code, 502)
        self.assertEqual(raised.exception.detail, "Hotel discovery service is unavailable.")

"""Mocked checks for the thin demo ZIP FastAPI route."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi import HTTPException

import api_routes


class DemoZipRouteTests(unittest.TestCase):
    @patch("api_routes.lookup_zip_location")
    def test_route_returns_resolved_location(self, mock_lookup) -> None:
        mock_lookup.return_value = {
            "status": "resolved",
            "postcode": "16802",
            "country_code": "US",
            "latitude": 40.7982,
            "longitude": -77.8599,
            "locality": "State College",
        }

        location = api_routes.demo_zip_location()

        self.assertEqual(location, mock_lookup.return_value)
        mock_lookup.assert_called_once_with("16802")

    @patch("api_routes.lookup_zip_location")
    def test_entered_zip_route_passes_the_query_value_to_controller(
        self, mock_lookup
    ) -> None:
        mock_lookup.return_value = {
            "status": "resolved",
            "postcode": "94103",
            "country_code": "US",
            "latitude": 37.773972,
            "longitude": -122.431297,
        }

        location = api_routes.zip_location("94103")

        self.assertEqual(location, mock_lookup.return_value)
        mock_lookup.assert_called_once_with("94103")

    @patch("api_routes.lookup_zip_location", return_value={"status": "configuration_error"})
    def test_route_maps_missing_configuration_to_safe_error(self, _mock_lookup) -> None:
        with self.assertRaises(HTTPException) as raised:
            api_routes.demo_zip_location()

        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(raised.exception.detail, "Location lookup is not configured.")

    @patch("api_routes.lookup_zip_location", return_value={"status": "unresolved"})
    def test_route_maps_unresolved_zip_to_safe_error(self, _mock_lookup) -> None:
        with self.assertRaises(HTTPException) as raised:
            api_routes.demo_zip_location()

        self.assertEqual(raised.exception.status_code, 404)
        self.assertEqual(raised.exception.detail, "ZIP location could not be resolved.")

    @patch("api_routes.lookup_zip_location", return_value={"status": "unresolved"})
    def test_entered_zip_route_maps_unresolved_to_safe_error(self, _mock_lookup) -> None:
        with self.assertRaises(HTTPException) as raised:
            api_routes.zip_location("94103")

        self.assertEqual(raised.exception.status_code, 404)
        self.assertEqual(raised.exception.detail, "ZIP location could not be resolved.")

    @patch("api_routes.lookup_zip_location", return_value={"status": "provider_error"})
    def test_route_maps_provider_failure_to_safe_error(self, _mock_lookup) -> None:
        with self.assertRaises(HTTPException) as raised:
            api_routes.demo_zip_location()

        self.assertEqual(raised.exception.status_code, 502)
        self.assertEqual(raised.exception.detail, "Location provider is unavailable.")

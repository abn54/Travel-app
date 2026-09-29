"""Mocked checks for the backend-only Geoapify ZIP lookup controller."""
from __future__ import annotations

import json
import unittest
from unittest.mock import patch
from urllib.error import URLError
from urllib.parse import parse_qs, urlparse

import location_controller


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.body = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


class LocationControllerTests(unittest.TestCase):
    @patch("location_controller.get_geoapify_api_key", return_value="test-key")
    @patch("location_controller.urlopen")
    def test_matching_us_postcode_returns_small_location(
        self, mock_urlopen, _mock_key
    ) -> None:
        mock_urlopen.return_value = FakeResponse(
            {
                "results": [
                    {
                        "postcode": "16802",
                        "country_code": "us",
                        "lat": 40.7982,
                        "lon": -77.8599,
                        "city": "State College",
                    }
                ]
            }
        )

        location = location_controller.lookup_zip_location("16802")

        self.assertEqual(
            location,
            {
                "status": "resolved",
                "postcode": "16802",
                "country_code": "US",
                "latitude": 40.7982,
                "longitude": -77.8599,
                "locality": "State College",
            },
        )
        request = mock_urlopen.call_args.args[0]
        query = parse_qs(urlparse(request.full_url).query)
        self.assertEqual(query["postcode"], ["16802"])
        self.assertEqual(query["type"], ["postcode"])
        self.assertEqual(query["filter"], ["countrycode:us"])
        self.assertEqual(query["format"], ["json"])
        self.assertEqual(mock_urlopen.call_args.kwargs["timeout"], 5)

    @patch("location_controller.get_geoapify_api_key", return_value="test-key")
    @patch("location_controller.urlopen")
    def test_an_entered_five_digit_zip_is_sent_to_geoapify(
        self, mock_urlopen, _mock_key
    ) -> None:
        mock_urlopen.return_value = FakeResponse(
            {
                "results": [
                    {
                        "postcode": "94103",
                        "country_code": "us",
                        "lat": 37.773972,
                        "lon": -122.431297,
                        "city": "San Francisco",
                    }
                ]
            }
        )

        location = location_controller.lookup_zip_location("94103")

        self.assertEqual(location["postcode"], "94103")
        self.assertEqual(location["locality"], "San Francisco")
        request = mock_urlopen.call_args.args[0]
        query = parse_qs(urlparse(request.full_url).query)
        self.assertEqual(query["postcode"], ["94103"])

    @patch("location_controller.get_geoapify_api_key", return_value="test-key")
    @patch("location_controller.urlopen")
    def test_mismatched_or_invalid_results_are_unresolved(
        self, mock_urlopen, _mock_key
    ) -> None:
        mock_urlopen.return_value = FakeResponse(
            {
                "results": [
                    {
                        "postcode": "16802",
                        "country_code": "ca",
                        "lat": 40.7982,
                        "lon": -77.8599,
                    },
                    {
                        "postcode": "16801",
                        "country_code": "us",
                        "lat": 40.7982,
                        "lon": -77.8599,
                    },
                    {
                        "postcode": "16802",
                        "country_code": "us",
                        "lat": "invalid",
                        "lon": -77.8599,
                    },
                ]
            }
        )

        self.assertEqual(
            location_controller.lookup_zip_location("16802"),
            {"status": "unresolved", "postcode": "16802"},
        )

    @patch("location_controller.get_geoapify_api_key", return_value="test-key")
    @patch("location_controller.urlopen", side_effect=URLError("unavailable"))
    def test_provider_failure_does_not_return_error_details(
        self, _mock_urlopen, _mock_key
    ) -> None:
        self.assertEqual(
            location_controller.lookup_zip_location("16802"),
            {"status": "provider_error", "postcode": "16802"},
        )

    @patch("location_controller.get_geoapify_api_key", return_value="")
    @patch("location_controller.urlopen")
    def test_missing_configuration_skips_provider_request(
        self, mock_urlopen, _mock_key
    ) -> None:
        self.assertEqual(
            location_controller.lookup_zip_location("16802"),
            {"status": "configuration_error", "postcode": "16802"},
        )
        mock_urlopen.assert_not_called()

    @patch("location_controller.get_geoapify_api_key")
    @patch("location_controller.urlopen")
    def test_invalid_zip_skips_provider_request(self, mock_urlopen, _mock_key) -> None:
        self.assertEqual(
            location_controller.lookup_zip_location("not-a-zip"),
            {"status": "unresolved", "postcode": "not-a-zip"},
        )
        mock_urlopen.assert_not_called()

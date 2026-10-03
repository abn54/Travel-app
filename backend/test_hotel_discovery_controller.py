"""Mocked checks for the Part 1 Geoapify hotel discovery controller."""
from __future__ import annotations

import json
import unittest
from unittest.mock import patch
from urllib.error import URLError
from urllib.parse import parse_qs, urlparse

import hotel_discovery_controller


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.body = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


RESOLVED_LOCATION = {
    "status": "resolved",
    "postcode": "00501",
    "country_code": "US",
    "latitude": 40.9223,
    "longitude": -72.6371,
    "locality": "Holtsville",
}


class HotelDiscoveryControllerTests(unittest.TestCase):
    @patch("hotel_discovery_controller.lookup_zip_location", return_value=RESOLVED_LOCATION)
    @patch("hotel_discovery_controller.get_geoapify_api_key", return_value="test-key")
    @patch("hotel_discovery_controller.urlopen")
    def test_returns_only_provider_backed_hotel_fields(
        self, mock_urlopen, _mock_key, _mock_location
    ) -> None:
        mock_urlopen.return_value = FakeResponse(
            {
                "features": [
                    {
                        "properties": {
                            "place_id": "provider-place-1",
                            "name": "Provider Hotel",
                            "formatted": "1 Example Road, Holtsville, NY",
                            "distance": 350.4,
                        },
                        "geometry": {"coordinates": [-72.638, 40.923]},
                    }
                ]
            }
        )

        result = hotel_discovery_controller.discover_hotels("00501")

        self.assertEqual(result["status"], "resolved")
        self.assertEqual(result["search_center"]["postcode"], "00501")
        self.assertEqual(
            result["hotels"],
            [
                {
                    "place_id": "provider-place-1",
                    "name": "Provider Hotel",
                    "address": "1 Example Road, Holtsville, NY",
                    "latitude": 40.923,
                    "longitude": -72.638,
                    "distance_meters": 350.4,
                }
            ],
        )
        request = mock_urlopen.call_args.args[0]
        query = parse_qs(urlparse(request.full_url).query)
        self.assertEqual(query["categories"], ["accommodation.hotel"])
        self.assertEqual(query["filter"], ["circle:-72.6371,40.9223,5000"])
        self.assertEqual(query["bias"], ["proximity:-72.6371,40.9223"])
        self.assertEqual(query["limit"], ["20"])
        self.assertEqual(mock_urlopen.call_args.kwargs["timeout"], 5)

    @patch("hotel_discovery_controller.lookup_zip_location")
    @patch("hotel_discovery_controller.urlopen")
    def test_invalid_zip_does_not_call_either_provider(self, mock_urlopen, mock_location) -> None:
        self.assertEqual(
            hotel_discovery_controller.discover_hotels("12"),
            {"status": "invalid_input", "postcode": "12"},
        )
        mock_location.assert_not_called()
        mock_urlopen.assert_not_called()

    @patch("hotel_discovery_controller.lookup_zip_location", return_value={"status": "unresolved", "postcode": "00501"})
    @patch("hotel_discovery_controller.urlopen")
    def test_unresolved_zip_skips_places_request(self, mock_urlopen, _mock_location) -> None:
        self.assertEqual(
            hotel_discovery_controller.discover_hotels("00501"),
            {"status": "unresolved", "postcode": "00501"},
        )
        mock_urlopen.assert_not_called()

    @patch("hotel_discovery_controller.lookup_zip_location", return_value=RESOLVED_LOCATION)
    @patch("hotel_discovery_controller.get_geoapify_api_key", return_value="test-key")
    @patch("hotel_discovery_controller.urlopen")
    def test_empty_feature_list_is_a_successful_no_results_state(
        self, mock_urlopen, _mock_key, _mock_location
    ) -> None:
        mock_urlopen.return_value = FakeResponse({"features": []})

        result = hotel_discovery_controller.discover_hotels("00501")

        self.assertEqual(result["status"], "no_results")
        self.assertEqual(result["hotels"], [])
        self.assertEqual(result["search_center"]["postcode"], "00501")

    @patch("hotel_discovery_controller.lookup_zip_location", return_value=RESOLVED_LOCATION)
    @patch("hotel_discovery_controller.get_geoapify_api_key", return_value="test-key")
    @patch("hotel_discovery_controller.urlopen")
    def test_one_transient_provider_failure_retries_then_returns_results(
        self, mock_urlopen, _mock_key, _mock_location
    ) -> None:
        mock_urlopen.side_effect = [
            URLError("temporary"),
            FakeResponse(
                {
                    "features": [
                        {
                            "properties": {"place_id": "retry-hotel", "name": "Retry Hotel"},
                            "geometry": {"coordinates": [-72.638, 40.923]},
                        }
                    ]
                }
            ),
        ]

        result = hotel_discovery_controller.discover_hotels("00501")

        self.assertEqual(result["status"], "resolved")
        self.assertEqual(result["hotels"][0]["name"], "Retry Hotel")
        self.assertEqual(mock_urlopen.call_count, 2)

    @patch("hotel_discovery_controller.lookup_zip_location", return_value=RESOLVED_LOCATION)
    @patch("hotel_discovery_controller.get_geoapify_api_key", return_value="test-key")
    @patch("hotel_discovery_controller.urlopen", side_effect=URLError("unavailable"))
    def test_provider_failure_is_not_an_empty_result(
        self, _mock_urlopen, _mock_key, _mock_location
    ) -> None:
        self.assertEqual(
            hotel_discovery_controller.discover_hotels("00501"),
            {"status": "provider_error", "postcode": "00501"},
        )

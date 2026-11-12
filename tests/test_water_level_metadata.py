"""Public offline tests for the NOAA-style water-level metadata adapter."""
import json
import tempfile
import unittest
from pathlib import Path

from tools.water_level_metadata import main, validate_station_metadata, station_records


class TestWaterLevelMetadata(unittest.TestCase):
    def valid(self, **changes):
        station = {
            "id": "9414290", "name": "San Francisco",
            "lat": 37.806, "lng": -122.465,
            "tidal": True, "greatlakes": False,
            "sensors": {"self": "https://api.tidesandcurrents.noaa.gov/mdapi/dev/"},
        }
        station.update(changes)
        return station

    def test_noaa_collection_and_single_station(self):
        for doc in (
            [self.valid()],
            {"stations": [self.valid()]},
            {"stationList": [self.valid()]},
            {"station": self.valid()},
            self.valid(),
        ):
            with self.subTest(wrapper=type(doc).__name__):
                result = validate_station_metadata(doc)
                self.assertEqual(result["structurally_valid_rows"], 1)
                self.assertEqual(result["invalid_rows"], 0)
                self.assertFalse(result["instrument_accuracy_verified"])
                self.assertFalse(result["datum_reference_validated"])

    def test_unsafe_and_incomplete_metadata_is_rejected_without_echo(self):
        bad = [
            self.valid(id="9414290"),
            self.valid(id="9414290"),
            self.valid(id=123),
            self.valid(lat=float("nan")),
            self.valid(lng=201),
            self.valid(tidal="true"),
            self.valid(name=" "),
            self.valid(lat=True),
            "not a station",
        ]
        result = validate_station_metadata(bad)
        self.assertEqual(result["total_rows"], len(bad))
        self.assertEqual(result["structurally_valid_rows"], 1)
        self.assertEqual(result["invalid_rows"], len(bad)-1)
        codes = {e["code"] for e in result["errors"]}
        self.assertIn("duplicate_station_id", codes)
        self.assertIn("invalid_station_id", codes)
        self.assertIn("invalid_latitude", codes)
        self.assertIn("invalid_longitude", codes)
        self.assertIn("invalid_tidal_flag", codes)
        self.assertIn("invalid_station_name", codes)
        self.assertIn("station_not_object", codes)
        self.assertNotIn("San Francisco", json.dumps(result))

    def test_bounded_collection_and_type(self):
        with self.assertRaises(ValueError):
            station_records({"stations": {}})
        with self.assertRaises(ValueError):
            station_records([{}] * 5001)
        with self.assertRaises(ValueError):
            station_records({"wrong": []})

    def test_cli_offline_valid_and_invalid_exit_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stations.json"
            path.write_text(json.dumps({"stations": [self.valid()]}))
            self.assertEqual(main([str(path)]), 0)
            path.write_text(json.dumps({"stations": [self.valid(lng=1000)]}))
            self.assertEqual(main([str(path)]), 1)
            path.write_text("not JSON")
            self.assertEqual(main([str(path)]), 2)


if __name__ == "__main__":
    unittest.main()

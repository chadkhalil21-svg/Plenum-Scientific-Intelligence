"""Offline empirical-evidence tests; synthetic fixtures are never called observations."""
from datetime import timedelta
from hashlib import sha256
import io
import json
import unittest
from math import sin, cos, pi

from plenum_ai.noaa_empirical import (
    START, CUTOFF, STATIONS, HARMONIC_PERIODS_HOURS,
    data_url, fetch_data, parse_observations, score_station, run_empirical_forecast,
)


def synthetic_rows(days=17, mode="tidal"):
    rows = []
    for h in range(days*24):
        t = START + timedelta(hours=h)
        level = 1.8 + sum(
            amp * sin(2*pi*h/period + .17)
            for amp, period in zip((1.0, .21, .14, .11), HARMONIC_PERIODS_HOURS)
        ) if mode == "tidal" else 1.5
        rows.append({"t": t.strftime("%Y-%m-%d %H:%M"), "v": str(level)})
    return rows


class HttpStream(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *unused):
        self.close()


class MeasuredDataTests(unittest.TestCase):
    def test_fixed_noaa_observed_data_request(self):
        self.assertEqual(set(STATIONS), {"8443970", "8723214"})
        url = data_url("8443970")
        self.assertIn("hourly_height", url)
        self.assertIn("20250601", url)
        self.assertIn("20250617", url)
        self.assertNotIn("product=predictions", url)
        with self.assertRaises(ValueError):
            data_url("unreviewed-station")

    def test_training_isolated_and_model_recovers_known_harmonics(self):
        result = score_station("8443970", synthetic_rows(), "0"*64)
        self.assertEqual(result["training_observations"], 16*24)
        self.assertEqual(result["holdout_observations"], 24)
        self.assertTrue(result["model_beats_baseline"])
        self.assertLess(result["model_mae_m"], 1e-8)
        self.assertGreater(result["baseline_mae_m"], .01)
        self.assertFalse(result["selected_after_examining_holdout"])
        self.assertTrue(result["observations_from_independent_measured_future_day"])
        self.assertFalse(result["scientific_discovery_verified"])

    def test_hypothesis_may_fail_without_program_crashing(self):
        rows = synthetic_rows()
        prior = {r["t"]: r["v"] for r in rows}
        for item in rows:
            if item["t"].startswith("2025-06-17"):
                # Exactly repeat the prior day's measured hourly heights.
                # This makes 24h persistence perfect by construction.
                item["v"] = prior[item["t"].replace("2025-06-17", "2025-06-16")]
        report = score_station("8723214", rows, "0"*64)
        self.assertFalse(report["model_beats_baseline"])
        self.assertTrue(report["model_mae_m"] > .1)

    def test_inadequate_coverage_refused(self):
        with self.assertRaises(ValueError):
            score_station("8443970", synthetic_rows(days=6), "0"*64)
        rows = synthetic_rows()
        rows = [row for row in rows if not row["t"].startswith("2025-06-17")]
        with self.assertRaises(ValueError):
            score_station("8443970", rows, "0"*64)

    def test_duplicate_time_refused(self):
        rows = synthetic_rows()
        with self.assertRaises(ValueError):
            parse_observations(rows+[rows[0]])

    def test_noaa_response_error_not_fabricated(self):
        def fake_error(request, timeout):
            return HttpStream(b'{"error":{"message":"No station data"}}')
        with self.assertRaises(ValueError):
            fetch_data("8443970", opener=fake_error)

    def test_end_to_end_two_station_offline_http_fixture(self):
        rows = synthetic_rows()
        response = json.dumps({"data": rows}).encode()
        requests = []
        def fake_http(req, timeout):
            requests.append(req.full_url)
            return HttpStream(response)
        result = run_empirical_forecast(opener=fake_http)
        self.assertTrue(result["hypothesis_supported_at_both_stations"])
        self.assertEqual(len(requests), 2)
        self.assertFalse(result["new_scientific_discovery_verified"])
        self.assertFalse(result["AI_self_improvement_proven"])
        self.assertFalse(result["model_parameters_fit_on_test_data"])


if __name__ == "__main__":
    unittest.main()

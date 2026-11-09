"""Guardrails for a real-observation NOAA shadow-model replay. All fixtures synthetic."""
from datetime import timedelta
from math import pi, sin
from hashlib import sha256
import io
import json
import unittest

from plenum_ai.noaa_empirical import START, HARMONIC_PERIODS_HOURS
from plenum_ai.noaa_shadow_twin import GAIN, MIN_PAIRS, SCHEMA, replay_station, run_replay


def rows(days=17, mode="tidal"):
    result = []
    for h in range(days * 24):
        t = START + timedelta(hours=h)
        value = (1.3 + sum(amp * sin(2 * pi * h / period + 0.12)
                  for amp, period in zip((0.9, 0.21, 0.12, 0.08),
                                         HARMONIC_PERIODS_HOURS))
                 if mode == "tidal" else 1.4)
        result.append({"t": t.strftime("%Y-%m-%d %H:%M"), "v": str(value)})
    return result


class Stream(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *unused):
        self.close()


class ShadowTwinTests(unittest.TestCase):
    def test_reuse_existing_harmonic_model_and_real_source_contract(self):
        report = replay_station("8443970", rows(), "a" * 64)
        self.assertEqual(report["evaluation_pairs"], 23)
        self.assertEqual(report["train_observations"], 16 * 24)
        self.assertEqual(report["frozen_state_update_gain"], GAIN)
        self.assertTrue(report["state_update_uses_only_observed_prior_hour"])
        self.assertLess(report["shadow_mae_m"], 1e-8)
        self.assertLess(report["frozen_harmonic_mae_m"], 1e-8)
        self.assertEqual(report["raw_payload_sha256"], "a" * 64)

    def test_forecast_issued_before_target_observation(self):
        base = rows()
        changed = [dict(item) for item in base]
        changed[-1]["v"] = "9.0"  # Last measurement altered AFTER prediction issuance.
        a = replay_station("8723214", base, "b" * 64)
        b = replay_station("8723214", changed, "b" * 64)
        last_a = a["sample_prequential_forecasts"][-1]
        last_b = b["sample_prequential_forecasts"][-1]
        self.assertEqual(last_a["shadow_predicted_m"], last_b["shadow_predicted_m"])
        self.assertNotEqual(last_a["observed_target_m"], last_b["observed_target_m"])
        self.assertNotEqual(a["final_residual_bias_state_m"], b["final_residual_bias_state_m"])
        for item in a["sample_prequential_forecasts"]:
            self.assertLess(item["issued_at_utc"], item["target_at_utc"])

    def test_retains_failure_when_stronger_baseline_wins(self):
        report = replay_station("8443970", rows(mode="constant"), "c" * 64)
        self.assertFalse(report["beats_one_hour_persistence"])

    def test_missing_data_and_duplicate_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            replay_station("8443970", rows(days=6), "a" * 64)
        malformed = rows()
        with self.assertRaises(ValueError):
            replay_station("8443970", malformed + [malformed[-1]], "a" * 64)

    def test_http_mock_proves_source_route_without_claiming_live_data(self):
        payload = json.dumps({"data": rows()}).encode()
        urls = []
        def opener(request, timeout):
            urls.append(request.full_url)
            return Stream(payload)
        result = run_replay(opener=opener)
        self.assertEqual(result["schema"], SCHEMA)
        self.assertEqual(len(urls), 2)
        self.assertTrue(all("product=hourly_height" in url for url in urls))
        self.assertEqual(len(result["stations"]), 2)
        self.assertFalse(result["physically_calibrated_operational_digital_twin"])
        self.assertTrue(result["historical_replay_not_live_sensor_sync"])
        self.assertFalse(result["AGI_or_autonomous_discovery_demonstrated"])


if __name__ == "__main__":
    unittest.main()

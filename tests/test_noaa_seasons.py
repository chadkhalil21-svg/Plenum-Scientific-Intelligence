"""Offline tests for predeclared cross-season observational holdouts."""
from datetime import timedelta
from math import sin, pi
import io
import json
import unittest

from plenum_ai.noaa_empirical import HARMONIC_PERIODS_HOURS, START
from plenum_ai.noaa_seasons import (
    PREDECLARED_HOLDOUT_DAYS, range_query, fetch_range,
    evaluate_predeclared_window, run_seasonal_validation,
)


def rows_for(cutoff):
    origin = cutoff - timedelta(days=16)
    rows = []
    for h in range(17*24):
        timestamp = origin + timedelta(hours=h)
        hours = (timestamp-START).total_seconds()/3600.0
        value = 1.4 + sum(
            scale * sin(2*pi*hours/period+phase) for period,scale,phase in zip(
                HARMONIC_PERIODS_HOURS,
                (0.8, 0.3, 0.2, 0.16),
                (0.12, 0.5, 0.7, 0.2)
            )
        )
        rows.append({"t":timestamp.strftime("%Y-%m-%d %H:%M"),"v":str(value)})
    return rows


class Stream(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self,*args): self.close()


class SeasonalValidationTests(unittest.TestCase):
    def test_precommitted_dates_and_observed_product(self):
        self.assertEqual(
            [d.strftime("%Y-%m-%d") for d in PREDECLARED_HOLDOUT_DAYS],
            ["2025-03-17","2025-09-17","2025-12-17"])
        for dt in PREDECLARED_HOLDOUT_DAYS:
            url=range_query("8443970",dt)
            self.assertIn("hourly_height",url)
            self.assertNotIn("product=predictions",url)
        with self.assertRaises(ValueError):
            range_query("9999999",PREDECLARED_HOLDOUT_DAYS[0])

    def test_frozen_physics_model_recovers_synthetic_harmonics(self):
        for cutoff in PREDECLARED_HOLDOUT_DAYS:
            with self.subTest(cutoff=cutoff):
                report=evaluate_predeclared_window(
                    "8723214",cutoff,rows_for(cutoff),"a"*64)
                self.assertEqual(report["train_observations"],16*24)
                self.assertEqual(report["test_observations"],24)
                self.assertTrue(report["harmonic_better"])
                self.assertLess(report["harmonic_mae_m"],1e-8)
                self.assertFalse(report["test_actuals_used_for_fitting"])
                self.assertFalse(report["algorithm_changed_since_june_17"])

    def test_failed_hypothesis_is_reported_not_discarded(self):
        cutoff=PREDECLARED_HOLDOUT_DAYS[0]
        entries=rows_for(cutoff)
        existing={r["t"]:r["v"] for r in entries}
        for row in entries:
            if row["t"].startswith("2025-03-17"):
                one_day_ago=(cutoff - timedelta(days=1)).strftime("%Y-%m-%d")
                row["v"]=existing[row["t"].replace("2025-03-17",one_day_ago)]
        report=evaluate_predeclared_window("8443970",cutoff,entries,"b"*64)
        self.assertFalse(report["harmonic_better"])
        self.assertAlmostEqual(report["persistence_mae_m"],0)

    def test_missing_measurements_rejected(self):
        cutoff=PREDECLARED_HOLDOUT_DAYS[1]
        with self.assertRaises(ValueError):
            evaluate_predeclared_window("8443970",cutoff,
                                       rows_for(cutoff)[:40],"a"*64)

    def test_end_to_end_six_fixed_station_day_pairs(self):
        calls=[]
        def fetch(request,timeout=25):
            from urllib.parse import urlsplit,parse_qs
            params=parse_qs(urlsplit(request.full_url).query)
            start=params["begin_date"][0]
            cutoff=params["end_date"][0]
            dt=next(d for d in PREDECLARED_HOLDOUT_DAYS if d.strftime("%Y%m%d")==cutoff)
            self.assertEqual(
                start,(dt-timedelta(days=16)).strftime("%Y%m%d"))
            calls.append((params["station"][0],cutoff))
            return Stream(json.dumps({"data":rows_for(dt)}).encode())
        report=run_seasonal_validation(opener=fetch)
        self.assertEqual(len(calls),6)
        self.assertEqual(report["number_of_station_day_tests"],6)
        self.assertEqual(report["number_of_independent_heldout_hourly_readings"],144)
        self.assertTrue(report["hypothesis_supported"])
        self.assertEqual(report["wins"],6)
        self.assertFalse(report["AI_devised_the_hypothesis"])
        self.assertFalse(report["scientific_discovery_verified"])


if __name__ == "__main__":
    unittest.main()

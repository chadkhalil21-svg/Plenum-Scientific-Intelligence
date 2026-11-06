"""Offline tests for NASA public-data and Astropy experiment."""
import io
import unittest

from plenum_ai.nasa_exoplanets import (
    SQL, query_url, nasa_records, predicted_period_days, assess_catalog,
)


class Response(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()


class NasaExoplanetTests(unittest.TestCase):
    def test_earth_analogue_period(self):
        result = predicted_period_days(1.0, 1.0)
        self.assertAlmostEqual(result, 365.25, delta=0.4)

    def test_kepler_mass_and_radius_scaling(self):
        p = predicted_period_days(1.0, 1.0)
        self.assertAlmostEqual(predicted_period_days(4.0, 1.0) / p, 8.0, places=10)
        self.assertAlmostEqual(predicted_period_days(1.0, 4.0) / p, 0.5, places=10)

    def test_fixed_bounded_nasa_query(self):
        self.assertIn("top 80", SQL)
        self.assertIn("default_flag=1", SQL)
        self.assertTrue(query_url().startswith("https://exoplanetarchive.ipac.caltech.edu/TAP/sync?"))

    def test_offline_parsing_both_nasa_response_schemas(self):
        def open_list(request, timeout):
            self.assertEqual(timeout, 25)
            return Response(b'[{"pl_name":"Earth analogue"}]')
        self.assertEqual(nasa_records(opener=open_list)[0]["pl_name"], "Earth analogue")
        def open_columns(request, timeout):
            return Response(
                b'{"metadata":[{"name":"pl_name"},{"name":"pl_orbper"}],'
                b'"data":[["Example",365.25]]}'
            )
        self.assertEqual(nasa_records(opener=open_columns)[0]["pl_orbper"], 365.25)

    def test_catalog_check_is_not_invented_physical_proof(self):
        period = predicted_period_days(1.0, 1.0)
        rows = [{
            "pl_name": "Synthetic_" + str(i),
            "pl_orbper": period,
            "pl_orbsmax": 1.0,
            "st_mass": 1.0,
        } for i in range(12)]
        results = assess_catalog(rows)
        self.assertEqual(results["observations_evaluated"], 12)
        self.assertTrue(results["catalog_consistency_condition_met"])
        self.assertLess(results["median_absolute_fractional_difference"], 1e-10)
        self.assertFalse(results["independent_empirical_validation"])
        self.assertFalse(results["new_scientific_discovery_verified"])
        self.assertFalse(results["experimental_result_verified"])

    def test_inconsistent_catalog_is_not_silently_passed(self):
        rows = [{
            "pl_name": "Synthetic_" + str(i),
            "pl_orbper": 1.0,
            "pl_orbsmax": 1.0,
            "st_mass": 1.0,
        } for i in range(12)]
        results = assess_catalog(rows)
        self.assertFalse(results["catalog_consistency_condition_met"])

    def test_bad_input_and_small_sample_rejected(self):
        with self.assertRaises(ValueError):
            predicted_period_days(0, 1)
        with self.assertRaises(ValueError):
            predicted_period_days(1, float("nan"))
        with self.assertRaises(ValueError):
            assess_catalog([{"pl_name":"Bad","pl_orbper":1,"pl_orbsmax":1,"st_mass":1}])
        with self.assertRaises(ValueError):
            nasa_records(opener=lambda *a, **k: Response(b'{"unexpected":[] }'))


if __name__ == "__main__":
    unittest.main()

"""Independent offline validation for the optional battery simulation engine."""
import unittest
from plenum_ai.battery_model import assess_voltage_samples


class BatteryValidationTests(unittest.TestCase):
    def test_voltage_trace_summary_and_provenance(self):
        report=assess_voltage_samples(
            [0.0, 60.0, 120.0, 180.0],
            [4.2, 4.15, 4.07, 3.99],
            "SPM"
        )
        self.assertTrue(report["voltage_finite_and_in_range"])
        self.assertTrue(report["declining_voltage_under_discharge"])
        self.assertAlmostEqual(report["voltage_drop_v"], 0.21)
        self.assertFalse(report["independent_cell_validation"])

    def test_reject_bad_time_voltage_traces(self):
        examples = [
            ([0, 0, 2, 3], [4.1, 4.0, 3.9, 3.8]),
            ([0, 1, 2, 3], [4.1, 4.0, float("nan"), 3.8]),
            ([0, 1, 2, 3], [4.1, 4.0, 3.9, 0.0]),
            ([0, 1, 2], [4.1, 4.0, 3.9]),
        ]
        for times, voltages in examples:
            with self.subTest(times=times, voltages=voltages):
                with self.assertRaises(ValueError):
                    assess_voltage_samples(times, voltages, "SPM")

    def test_increasing_voltage_is_not_discharge(self):
        report = assess_voltage_samples(
            [0, 1, 2, 3],
            [3.5, 3.6, 3.7, 3.8], "SPM"
        )
        self.assertFalse(report["declining_voltage_under_discharge"])


if __name__ == "__main__":
    unittest.main()

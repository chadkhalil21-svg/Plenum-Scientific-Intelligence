"""Only new Plenum adapter contracts; do NOT rerun upstream PyBaMM science fixtures."""
from __future__ import annotations

from math import isclose
from unittest import TestCase
from unittest.mock import patch

from plenum_ai.battery_first_use import independent_amp_hours, main


class BatteryFirstUseContract(TestCase):
    def test_independent_charge_integral_uses_actual_variable_current(self):
        self.assertTrue(isclose(
            independent_amp_hours((0, 60, 180), (1, 2, 3)),
            (90 + 300) / 3600,
            rel_tol=1e-12,
        ))
        self.assertTrue(isclose(
            independent_amp_hours((0, 60, 120), (2, 2, 2)),
            240 / 3600,
            rel_tol=1e-12,
        ))

    def test_disallow_nonphysical_timestamps_or_missing_samples(self):
        for times, amps in (
            ((0,), (1,)),
            ((0, 1), (2,)),
            ((0, 1), (1, 2, 3)),
            ((0, 0), (1, 1)),
            ((1, 0), (1, 1)),
            ((0, float("nan")), (1, 1)),
            ((0, 1), (1, float("inf"))),
        ):
            with self.subTest(times=times, amps=amps), self.assertRaises(ValueError):
                independent_amp_hours(times, amps)

    def test_cli_rejects_any_output_outside_sandbox_reports_without_solver(self):
        for bad in ("/tmp/report.json", "../out.json", "out.json", "reports/out.txt"):
            with self.subTest(bad=bad):
                with patch("sys.argv", ["battery_first_use", "--out", bad]):
                    with patch("plenum_ai.battery_first_use.run_spm_first_use") as execute:
                        with self.assertRaises(SystemExit):
                            main()
                        execute.assert_not_called()


if __name__ == "__main__":
    import unittest
    unittest.main()

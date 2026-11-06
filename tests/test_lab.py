"""Checks five real scientific libraries/models and rejects unapproved tool calls."""
import unittest
from plenum_ai.lab import DOMAINS, solve, run_lab, benchmark_methods


class ScientificLabTests(unittest.TestCase):
    def test_five_disciplines(self):
        for domain in DOMAINS:
            with self.subTest(domain=domain):
                finding = solve(domain)
                self.assertTrue(finding["verified_fixture"], finding)

    def test_three_scipy_integrators(self):
        for method in ("RK45","DOP853","Radau"):
            for domain in DOMAINS[:4]:
                with self.subTest(method=method, domain=domain):
                    self.assertTrue(solve(domain,method)["verified_fixture"])

    def test_tool_allowlist(self):
        with self.assertRaises(ValueError):
            solve("arbitrary_python")
        with self.assertRaises(ValueError):
            solve("chemistry","exec")
        with self.assertRaises(ValueError):
            run_lab("test",domains=["mechanics","mechanics"])
        with self.assertRaises(ValueError):
            run_lab("",domains=["chemistry"])

    def test_agent_roles_report_limits(self):
        r = run_lab("Investigate known orbital and molecule benchmarks",
                    domains=["mechanics","molecules"])
        self.assertTrue(r["known_model_checks_passed"])
        self.assertFalse(r["scientific_discovery_verified"])
        self.assertFalse(r["self_modified"])
        self.assertEqual(len(r["agent_roles"]), 4)

    def test_method_comparison_no_auto_deploy(self):
        r = benchmark_methods()
        self.assertTrue(all(x["all_passed"] for x in r["methods"]))
        self.assertIsNotNone(r["least_calls_in_known_fixtures"])
        self.assertFalse(r["candidate_deployed"])


if __name__ == "__main__":
    unittest.main()

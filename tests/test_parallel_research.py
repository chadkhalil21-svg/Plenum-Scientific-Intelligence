"""Tests multi-tool parallel fan-out, bounded tool registry, and dependency verification."""
import unittest

from plenum_ai.parallel_research import run_network, _execute_tool
from plenum_ai.tool_registry import TOOLS, approve_request, get_registry, route_request
from plenum_ai.openmdao_adapter import optimize_cooling_area
from plenum_ai.lab import solve


class ToolNetworkTests(unittest.TestCase):
    def test_four_independent_tools_and_one_dependent_optimization(self):
        report = run_network(
            "Test orbital, thermal, chemical and molecular numerical fixtures",
            offline=True
        )
        self.assertEqual(report["parallel_tool_count"], 4)
        self.assertEqual(len(report["workers"]), 4)
        self.assertTrue(report["known_model_integration_passed"], report)
        self.assertTrue(report["dependent_optimization"]["verified_fixture"])
        self.assertEqual(report["dependent_optimization"]["dependent_input"],
                         "scipy.thermal.observed")
        self.assertFalse(report["scientific_discovery_verified"])
        self.assertFalse(report["model_inference_used"])

    def test_four_tools_return_independently_in_order(self):
        first = run_network("Parallel known scientific fixtures", offline=True)
        self.assertEqual([v["tool"] for v in first["workers"]],
                         first["requested_tools"])
        self.assertTrue(all(x["status"] == "completed" for x in first["workers"]))
        self.assertTrue(first["verification"]["all_requested_tools_reported"])

    def test_openmdao_uses_scipy_thermal_measurement(self):
        thermal = solve("materials")
        optimum = optimize_cooling_area(thermal)
        self.assertTrue(optimum["verified_fixture"])
        self.assertGreater(optimum["optimized_area_m2"], 0)
        self.assertAlmostEqual(
            optimum["optimized_area_m2"],
            optimum["analytical_minimum_area_m2"],
            places=3,
        )

    def test_explicit_parallel_execution_without_dependent_tool(self):
        report = run_network("Orbital mechanics known fixture",
                             tool_keys=["scipy.orbit"],
                             optimize=False)
        self.assertTrue(report["known_model_integration_passed"])
        self.assertEqual(report["dependent_optimization"]["status"], "not_requested")

    def test_external_search_does_not_fake_papers_offline(self):
        report = run_network("Open-source astronomy and computing",
                             tool_keys=["scipy.orbit", "openalex.metadata"],
                             offline=True, optimize=False)
        self.assertTrue(report["known_model_integration_passed"])
        search = next(x for x in report["workers"] if x["tool"] == "openalex.metadata")
        self.assertEqual(search["status"], "skipped_offline")
        self.assertEqual(search["papers"], [])

    def test_offline_federated_registry_tool(self):
        report=run_network("Scientific memory",tool_keys=["scipy.thermal","federated.metadata"],
                           offline=True,optimize=True)
        self.assertTrue(report["known_model_integration_passed"],report)
        literature=next(x for x in report["workers"] if x["tool"]=="federated.metadata")
        self.assertEqual(len(literature["evidence"]["providers"]),3)
        self.assertEqual(literature["status"],"skipped_offline")

    def test_explicit_deterministic_routing_covers_multiple_domains(self):
        route = route_request("Optimize a thermal battery circuit and orbital trajectory")
        self.assertIn("scipy.thermal", route["tool_keys"])
        self.assertIn("scipy.orbit", route["tool_keys"])
        self.assertIn("scipy.electronics", route["tool_keys"])
        self.assertTrue(route["enable_optimization"])
        self.assertFalse(route["model_selected_tools"])
        self.assertLessEqual(len(route["tool_keys"]), 5)

    def test_auto_routed_two_tools_and_dependent_optimization(self):
        routing=route_request("optimize cooling for electrical circuits")
        report=run_network("optimize cooling for electrical circuits",
                           tool_keys=routing["tool_keys"],
                           optimize=routing["enable_optimization"],offline=True)
        self.assertTrue(report["known_model_integration_passed"],report)

    def test_missing_dependency_is_rejected(self):
        with self.assertRaises(ValueError):
            run_network("No thermal result", tool_keys=["scipy.orbit"], optimize=True)

    def test_reference_only_or_dangerous_tools_not_executable(self):
        for key in ("kdense.skills", "sakana.scientist", "nasa.gmat",
                    "nasa.aviary", "openmdao.cooling", "shell", "arbitrary-python"):
            with self.subTest(tool=key):
                with self.assertRaises(ValueError):
                    approve_request([key])
        with self.assertRaises(ValueError):
            approve_request(["scipy.orbit"] * 2)
        with self.assertRaises(ValueError):
            approve_request(["scipy.orbit"] * 6)

    def test_tool_registry_keeps_constraints_and_versions(self):
        registry = get_registry()
        self.assertGreaterEqual(len(registry["tools"]), 9)
        self.assertEqual(TOOLS["openmdao.cooling"].depends_on, ("scipy.thermal",))
        self.assertEqual(TOOLS["kdense.skills"].status, "metadata_only")
        self.assertFalse(registry["all_external_execution_approved"])

    def test_bad_dependency_never_accepted(self):
        thermal = solve("materials")
        thermal["verified_fixture"] = False
        with self.assertRaises(ValueError):
            optimize_cooling_area(thermal)
        self.assertEqual(_execute_tool("nasa.gmat", "test", True)["status"], "failed")


if __name__ == "__main__":
    unittest.main()

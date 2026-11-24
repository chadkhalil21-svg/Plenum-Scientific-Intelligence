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

    def test_nasa_astronomy_is_not_fabricated_offline(self):
        report = run_network(
            "exoplanet orbital periods",
            tool_keys=["scipy.orbit", "nasa.exoplanets"],
            offline=True,
            optimize=False,
        )
        self.assertTrue(report["known_model_integration_passed"])
        nasa = next(x for x in report["workers"] if x["tool"] == "nasa.exoplanets")
        self.assertEqual(nasa["status"], "skipped_offline")
        self.assertFalse(nasa["independent_empirical_validation"])

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


    def test_durable_offline_graph_continues_after_real_workers_finish(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from plenum_ai.durable_graph import run_persistent, inspect_persistent
        question = "Preserve completed orbital and thermal work during interruption"
        keys = ["scipy.orbit", "scipy.thermal"]
        with TemporaryDirectory() as folder:
            db = Path(folder) / "mission.sqlite"
            with patch("plenum_ai.parallel_research._optimize",
                       side_effect=RuntimeError("simulated interruption after workers")):
                with self.assertRaisesRegex(RuntimeError, "simulated interruption"):
                    run_persistent(question, db, "original-resume", tool_keys=keys)
            saved = inspect_persistent(db, "original-resume")
            self.assertFalse(saved["finished"])
            self.assertEqual(saved["workers_recorded"], 2)
            # A changed scope must not consume or modify the old checkpoint.
            with self.assertRaises(ValueError):
                run_persistent(question, db, "original-resume", tool_keys=keys, optimize=False)
            with self.assertRaises(ValueError):
                run_persistent(question, db, "original-resume", tool_keys=keys, offline=False)
            # Existing actual workers are already complete. Native LangGraph
            # continuation must run only the unfinished dependency and verifier.
            with patch("plenum_ai.parallel_research._execute_tool",
                       side_effect=AssertionError("must not rerun accepted tools")) as worker:
                completed = run_persistent(question, db, "original-resume", tool_keys=keys)
                worker.assert_not_called()
            self.assertTrue(completed["resumed_unfinished_graph"])
            self.assertTrue(completed["checkpoint"]["finished"])
            self.assertEqual(completed["checkpoint"]["workers_recorded"], 2)
            self.assertTrue(completed["result"]["known_model_integration_passed"])
            self.assertTrue(completed["result"]["dependent_optimization"]["verified_fixture"])
            with patch("plenum_ai.parallel_research._execute_tool",
                       side_effect=AssertionError("completed replay is read only")) as worker:
                replay = run_persistent(question, db, "original-resume", tool_keys=keys)
                worker.assert_not_called()
            self.assertEqual(replay["status"], "recovered")
            self.assertFalse(replay["new_scientific_work_executed"])

    def test_interrupted_online_graph_cannot_automatically_resume(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from plenum_ai.durable_graph import run_persistent, inspect_persistent
        question = "Known thermal fixture with online mode authorized originally"
        with TemporaryDirectory() as folder:
            db = Path(folder) / "online.sqlite"
            with patch("plenum_ai.parallel_research._optimize", side_effect=RuntimeError("interruption")):
                with self.assertRaisesRegex(RuntimeError, "interruption"):
                    run_persistent(question, db, "online-resume", tool_keys=["scipy.thermal"], offline=False)
            with patch("plenum_ai.parallel_research._execute_tool",
                       side_effect=AssertionError("no automatic online replay")) as worker:
                with self.assertRaises(PermissionError):
                    run_persistent(question, db, "online-resume", tool_keys=["scipy.thermal"], offline=False)
                worker.assert_not_called()
            self.assertFalse(inspect_persistent(db, "online-resume")["finished"])


    def test_original_science_worker_automatically_resumes_interrupted_dependency(self):
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from plenum_ai.workforce_public_inbox import run_issue
        from test_workforce_team_dispatch import event
        from plenum_ai import parallel_research as science
        optimize = science._optimize
        original_worker = science._execute_tool
        attempts=[]
        def interrupted_once(state):
            attempts.append(1)
            if len(attempts)==1:
                raise RuntimeError("simulated dependency interruption")
            return optimize(state)
        with tempfile.TemporaryDirectory() as folder, patch.object(
            science, "_optimize", side_effect=interrupted_once
        ), patch.object(science, "_execute_tool", wraps=original_worker) as worker:
            report=run_issue(event("public_science","Run known orbital and thermal science fixtures"),
                             output_dir=Path(folder))
            self.assertTrue(report["verified"])
            self.assertTrue(report["continued_unfinished_graph"])
            self.assertEqual(len(attempts),2)
            self.assertEqual(worker.call_count,2)
            receipt=json.loads((Path(folder)/"issue-901/public-science-summary.json").read_text())
            self.assertTrue(receipt["continued_unfinished_graph"])
            self.assertEqual(receipt["workers"],2)


if __name__ == "__main__":
    unittest.main()

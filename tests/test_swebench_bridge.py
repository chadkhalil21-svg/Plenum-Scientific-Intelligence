"""Pure offline verification of the external official evaluator integration."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from plenum_ai import swebench_bridge as b


GOOD_HOST = {"architecture": "x86_64", "ram_gib": 20, "free_storage_gib": 140}


class OfficialSWEbenchGateTests(unittest.TestCase):
    def test_default_plan_is_review_only_and_original_harness(self):
        p = b.plan()
        self.assertEqual(p["upstream_version"], "5.0.2")
        self.assertEqual(p["phase"], "gold")
        self.assertEqual(p["official_dataset"], "SWE-bench/SWE-bench_Verified")
        self.assertEqual(p["command_argv"][:4], ["swebench", "eval", "verified", "--gold"])
        self.assertIn(b.INSTANCE, p["command_argv"])
        self.assertIsNone(p["official_issue_resolved"])
        self.assertFalse(p["official_evaluation_executed"])
        self.assertFalse(p["external_agent_inference_executed"])
        self.assertFalse(p["cost_authorized"])
        self.assertFalse(p["AGI_demonstrated"])

    def test_candidate_uses_upstream_not_custom_grader(self):
        p = b.plan("candidate", "one-issue-candidate-v1")
        self.assertEqual(p["command_argv"][3:5], ["-p", str(b.PREDICTIONS)])
        self.assertEqual(p["command_argv"][-6:], ["--run-id", "one-issue-candidate-v1", "-j", "1", "-t", "900"])
        self.assertTrue(p["original_official_scorer"])

    def test_invalid_stage_and_cache_key_fail_closed(self):
        for stage, key in [
            ("arbitrary", "safe-name"), ("gold", "../../bad"),
            ("gold", "UPPER"), ("gold", "spaces here"),
            ("gold", ""), ("gold", "a" * 51)]:
            with self.subTest(stage=stage, key=key), self.assertRaises(ValueError):
                b.plan(stage, key)

    def test_approval_and_package_pin_required_without_execution(self):
        p = b.plan()
        with self.assertRaises(PermissionError):
            b.execute(p, installed_version=b.VERSION)
        with self.assertRaises(RuntimeError):
            b.execute(p, approved=True, installed_version="5.0.1", resources=GOOD_HOST)

    def test_modified_plan_never_runs(self):
        p = b.plan()
        edited = copy.deepcopy(p)
        edited["command_argv"].extend(["--modal", "true"])
        with self.assertRaises(ValueError):
            b.execute(edited, approved=True, installed_version=b.VERSION,
                      resources=GOOD_HOST)

    def test_resource_guards_fail_before_upstream_runner(self):
        p = b.plan()
        def never_run(*args, **kwargs):
            self.fail("No Docker or benchmark run on an unsuitable host")
        for host in [
            {"architecture": "arm64", "ram_gib": 32, "free_storage_gib": 200},
            {"architecture": "x86_64", "ram_gib": 8, "free_storage_gib": 200},
            {"architecture": "x86_64", "ram_gib": 32, "free_storage_gib": 25}]:
            with self.subTest(host=host), self.assertRaises(RuntimeError):
                b.execute(p, approved=True, installed_version=b.VERSION,
                          resources=host, runner=never_run, docker_runner=never_run)

    def test_predictions_accept_only_one_reviewed_instance(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "one.jsonl"
            source = {
                "instance_id": b.INSTANCE,
                "model_patch": "diff --git a/a.py b/a.py\n+pass\n",
                "model_name_or_path": "reviewed-local-model",
            }
            with patch.object(b, "PREDICTIONS", path):
                path.write_text(json.dumps(source) + "\n", encoding="utf-8")
                self.assertTrue(b.validate_candidate())
                source["instance_id"] = "unapproved__issue-1"
                path.write_text(json.dumps(source) + "\n", encoding="utf-8")
                with self.assertRaises(ValueError):
                    b.validate_candidate()
                source["instance_id"] = b.INSTANCE
                path.write_text(json.dumps(source) + "\n" + json.dumps(source) + "\n")
                with self.assertRaises(ValueError):
                    b.validate_candidate()
            with self.assertRaises(ValueError):
                b.validate_candidate(path)

    def test_runner_delegates_without_claiming_code_pass_or_exposing_keys(self):
        calls = []
        def fake_run(argv, **kwargs):
            calls.append((argv, kwargs))
            return subprocess.CompletedProcess(argv, 0)
        p = b.plan("gold", "unique-reference-v1")
        with patch.dict("os.environ", {"OPENAI_API_KEY": "should-not-leak",
                                     "GITHUB_TOKEN": "should-not-leak"}):
            report = b.execute(p, approved=True, installed_version=b.VERSION,
                               resources=GOOD_HOST, runner=fake_run, docker_runner=fake_run)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][0], ["docker", "info"])
        self.assertEqual(calls[1][0], p["command_argv"])
        self.assertNotIn("OPENAI_API_KEY", calls[1][1]["env"])
        self.assertNotIn("GITHUB_TOKEN", calls[1][1]["env"])
        self.assertEqual(calls[1][1]["timeout"], b.MAX_RUN_SECONDS)
        self.assertTrue(calls[1][1]["check"])
        self.assertNotIn("shell", calls[1][1])
        self.assertTrue(report["official_evaluation_executed"])
        self.assertIsNone(report["official_issue_resolved"])
        self.assertTrue(report["independent_score_review_required"])
        self.assertFalse(report["AGI_demonstrated"])


if __name__ == "__main__":
    unittest.main()

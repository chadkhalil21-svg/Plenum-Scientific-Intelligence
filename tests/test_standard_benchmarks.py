"""Tests for strict opt-in integration with reviewed upstream benchmarks."""
import json
from unittest import TestCase
from unittest.mock import patch
from plenum_ai import standard_benchmarks as b


class ProvenEvaluationAdapterTests(TestCase):
    def test_pinned_library_plan_does_not_run_or_buy_inference(self):
        p=b.preflight("Qwen/Qwen3-1.7B",["arc_easy","hellaswag"],4)
        self.assertEqual(p["upstream_release"],"v0.4.13")
        self.assertEqual(p["upstream_license"],"MIT")
        self.assertEqual(p["model_revision"],
                         "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e")
        self.assertEqual(p["command"][:3],["lm-eval","run","--model"])
        self.assertIn("--limit",p["command"])
        self.assertFalse(p["model_download_enabled_by_default"])
        self.assertFalse(p["AGI_demonstrated"])
        self.assertFalse(p["scientific_discovery_verified"])

    def test_input_allowlist_prevents_command_injection(self):
        for model in ("other-model","Qwen/Qwen3-1.7B,--device=cuda",
                      "my-model; rm -rf /",None):
            with self.subTest(model=model),self.assertRaises(ValueError):
                b.preflight(model,["arc_easy"],4)
        for tasks in (["injected"],["arc_easy","arc_easy"],
                      ["arc_easy","hellaswag","piqa"],[],["arc_easy;ls"]):
            with self.subTest(tasks=tasks),self.assertRaises(ValueError):
                b.preflight("Qwen/Qwen3-1.7B",tasks,4)

    def test_resource_limits_are_strict(self):
        for limit in (0,-1,17,False,3.5,"4"):
            with self.subTest(limit=limit),self.assertRaises(ValueError):
                b.preflight("Qwen/Qwen3-1.7B",["arc_easy"],limit)

    def test_missing_library_fails_before_subprocess(self):
        manifest=b.preflight("Qwen/Qwen3-1.7B",["arc_easy"],4)
        with patch.object(b.importlib.metadata,"version",side_effect=b.importlib.metadata.PackageNotFoundError):
            with patch.object(b.subprocess,"run") as shell:
                with self.assertRaisesRegex(RuntimeError,"not installed"):
                    b.invoke(manifest)
                shell.assert_not_called()

    def test_wrong_upstream_version_fails_closed(self):
        manifest=b.preflight("Qwen/Qwen3-1.7B",["arc_easy"],4)
        with patch.object(b.importlib.metadata,"version",return_value="0.4.12"):
            with patch.object(b.subprocess,"run") as run:
                with self.assertRaisesRegex(RuntimeError,"not approved"):
                    b.invoke(manifest)
                run.assert_not_called()

    def test_only_reviewed_list_of_argv_may_be_executed(self):
        manifest=b.preflight("HuggingFaceTB/SmolLM2-1.7B-Instruct",["hellaswag"],3)
        with patch.object(b.importlib.metadata,"version",return_value=b.PACKAGE_VERSION):
            with patch.object(b.subprocess,"run",return_value=type("Result",(),{"returncode":0})()) as runner:
                self.assertEqual(b.invoke(manifest),0)
                args,kwargs=runner.call_args
                self.assertIs(args[0],manifest["command"])
                self.assertNotIn("shell",kwargs)
                self.assertLessEqual(kwargs["timeout"],2400)

    def test_failed_upstream_run_cannot_be_reported_as_success(self):
        manifest=b.preflight("Qwen/Qwen3-1.7B",["arc_easy"],4)
        with patch.object(b.importlib.metadata,"version",return_value=b.PACKAGE_VERSION):
            with patch.object(b.subprocess,"run",return_value=type("Result",(),{"returncode":13})()):
                with self.assertRaisesRegex(RuntimeError,"failed"):
                    b.invoke(manifest)


if __name__=="__main__":
    import unittest
    unittest.main()

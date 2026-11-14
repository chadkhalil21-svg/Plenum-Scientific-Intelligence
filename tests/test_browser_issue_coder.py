"""Founder browser coding-agent public scope; never calls inference in tests."""
import tempfile
import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from plenum_ai.browser_issue_coder import parse_issue, run, TITLE, MAGIC, REPO, OWNER, _require_implemented_candidate


def fixture(objective="Create a safe selector helper for the existing browser navigation engine"):
    return {
        "action": "opened",
        "repository": {"full_name": REPO},
        "issue": {
            "number": 450,
            "user": {"login": OWNER},
            "title": TITLE,
            "body": MAGIC + "\nobjective: " + objective,
        },
    }


class FounderPublicCoderContract(unittest.TestCase):
    def test_pinned_local_non_thinking_model_uses_official_sdk_flags(self):
        from plenum_ai.browser_issue_coder import local_coder_llm_options
        cfg = local_coder_llm_options()
        self.assertEqual(cfg["model"], "ollama/qwen3.5:9b-q4_K_M")
        self.assertEqual(cfg["reasoning_effort"], "none")
        self.assertEqual(cfg["max_output_tokens"], 1024)
        self.assertEqual(cfg["capability_overrides"]["thinking_mode"], "none")
        self.assertIs(cfg["capability_overrides"]["supports_reasoning_effort"], True)
        self.assertFalse(cfg["enable_encrypted_reasoning"])
        self.assertEqual(cfg["base_url"], "http://127.0.0.1:11434")

    def test_exact_founder_input_and_review_only_authority(self):
        task = parse_issue(fixture())
        self.assertEqual(task["issue"], 450)
        self.assertEqual(task["output_kind"], "REVIEW_ONLY_SOURCE")
        self.assertFalse(task["production_writes_authorized"])

    def test_fails_closed_for_nonowner_or_unsafe_task(self):
        examples = []
        e = fixture()
        e["issue"]["user"]["login"] = "outsider"
        examples.append(e)
        e = fixture()
        e["repository"]["full_name"] = "other/repository"
        examples.append(e)
        e = fixture("Store user password and token in GitHub and deploy automatically")
        examples.append(e)
        e = fixture()
        e["issue"]["title"] = "Unrelated task"
        examples.append(e)
        e = fixture()
        e["issue"]["body"] += "\nextra: true"
        examples.append(e)
        for event in examples:
            with self.subTest(event=event["issue"]["body"][:50]):
                with self.assertRaises((PermissionError, ValueError)):
                    parse_issue(event)

    def test_rejects_actual_failed_openhands_placeholder_generically(self):
        failed = (
            b"def get_approved_elements():\n    pass\n"
            b"def rank_elements(elements):\n    pass\n"
        )
        with self.assertRaises(ValueError):
            _require_implemented_candidate(failed)
        with self.assertRaises(ValueError):
            _require_implemented_candidate(
                b"def unimplemented():\n    return ...\n"
            )
        with self.assertRaises(ValueError):
            _require_implemented_candidate(
                b"def no_work():\n    raise NotImplementedError()\n"
            )

    def test_accepts_actual_implementation_not_just_valid_syntax(self):
        real = (
            b"def rank_visible(elements):\n"
            b"    return [x for x in elements if x.get('visible') is True]\n"
        )
        self.assertIsNone(_require_implemented_candidate(real))
        with self.assertRaises(PermissionError):
            _require_implemented_candidate(
                b"def dangerous():\n    return eval('2 + 2')\n"
            )

    def test_preflight_has_no_model_or_external_access(self):
        with tempfile.TemporaryDirectory() as root:
            with patch("plenum_ai.browser_issue_coder._out_dir",
                       return_value=Path(root) / "browser"):
                result = run(fixture(), execute=False)
                self.assertEqual(result["status"], "PREFLIGHT_ONLY")
                self.assertFalse(result["model_executed"])
                self.assertFalse(result["independent_behavior_verified"])
                self.assertTrue((Path(root) / "browser/result.json").is_file())


    def test_failed_inference_preserves_redacted_failure_receipt(self):
        sdk = types.ModuleType("openhands.sdk")
        editor = types.ModuleType("openhands.tools.file_editor")
        editor.FileEditorTool = types.SimpleNamespace(name="file_editor")
        sdk.Agent = lambda **kw: object()
        sdk.LLM = lambda **kw: object()
        sdk.Tool = lambda **kw: object()
        captured = {}
        class FailedConversation:
            def __init__(self, **kw):
                captured.update(kw)
            def send_message(self, text):
                pass
            def run(self):
                raise TimeoutError("DO_NOT_PUBLISH private token or raw model text")
        sdk.Conversation = FailedConversation
        modules = {"openhands": types.ModuleType("openhands"),
                   "openhands.sdk": sdk,
                   "openhands.tools": types.ModuleType("openhands.tools"),
                   "openhands.tools.file_editor": editor}
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / "receipt"
            with patch.dict(sys.modules, modules), patch.dict("os.environ", {
                "PLENUM_EPHEMERAL_RUNNER": "confirmed",
                "PLENUM_OPENHANDS_MODEL": "ollama/qwen3.5:9b-q4_K_M",
                "PLENUM_OPENHANDS_BASE_URL": "http://127.0.0.1:11434",
            }), patch("plenum_ai.browser_issue_coder.importlib.metadata.version", return_value="1.60.1"), patch("plenum_ai.browser_issue_coder._out_dir", return_value=output):
                with self.assertRaises(TimeoutError):
                    run(fixture(), execute=True)
            receipt = json.loads((output / "result.json").read_text())
            self.assertEqual(receipt["status"], "BLOCKED_EXECUTION_FAILED")
            self.assertEqual(receipt["conversation_runs_attempted"], 1)
            self.assertEqual(receipt["conversation_runs_completed"], 0)
            self.assertFalse(receipt["model_response_observed"])
            self.assertFalse(receipt["source_candidate_syntax_verified"])
            self.assertEqual(receipt["failure_category"], "TIMEOUT")
            self.assertIn("persistence_dir", captured)
            self.assertFalse(Path(captured["persistence_dir"]).exists())
            self.assertNotIn("DO_NOT_PUBLISH", (output / "result.json").read_text())
            self.assertEqual(sorted(x.name for x in output.iterdir()), ["events-redacted.json", "result.json"])

    def test_redacted_callback_records_response_and_tool_without_contents(self):
        from plenum_ai.browser_issue_coder import PublicEventTrace
        trace = PublicEventTrace()
        action = type("ActionEvent", (), {"source": "agent", "thought": "DO_NOT_PUBLISH"})()
        observation = type("ObservationEvent", (), {"source": "environment", "observation": "DO_NOT_PUBLISH"})()
        for _ in range(100):
            trace(action)
            trace(observation)
        data = trace.snapshot()
        self.assertTrue(data["model_response_observed"])
        self.assertEqual(data["tool_observations_seen"], 100)
        self.assertEqual(len(data["events"]), 64)
        self.assertTrue(data["truncated"])
        self.assertNotIn("DO_NOT_PUBLISH", json.dumps(data))


if __name__ == "__main__":
    unittest.main()

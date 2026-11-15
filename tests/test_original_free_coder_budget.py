"""Focused regression for actual original #733 local Free AI budget exhaustion.

No provider, model, container, original mission or paid service is called.
"""
import json
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch

from plenum_ai import openhands_coding_agent as coder


def _authorized_fixture():
    """Real original owner event, public source and ephemeral CI identity."""
    source = Path("src/plenum_ai/public_example.py")
    source.parent.mkdir(parents=True)
    source.write_text("def result():\n    return 1\n", encoding="utf-8")
    event = {"action": "opened", "repository": {"full_name": coder.REPO},
             "issue": {"user": {"login": coder.OWNER}, "number": 123,
                       "title": coder.REPAIR_TITLE,
                       "body": "PLENUM_OPENHANDS_PUBLIC_REPAIR_V1\nfile: src/plenum_ai/public_example.py\nobjective: Correct the public function to return two."}}
    Path("event.json").write_text(json.dumps(event))
    return {"PLENUM_OPENHANDS_MODEL": "openai/glm-4.7-flash",
            "PLENUM_OPENHANDS_BASE_URL": coder.ORIGINAL_FREE_CODING_ENDPOINT,
            "PLENUM_OPENHANDS_API_KEY": "test-ephemeral-oidc-not-a-credential",
            "GITHUB_RUN_ID": "1234", "GITHUB_RUN_ATTEMPT": "1"}


def _sdk_exception_module():
    """Use exact SDK classes when installed; otherwise emulate the optional type boundary.

    Foundation tests deliberately do not install the full model SDK. The
    historical #733 log proves ConversationRunError's direct LLMRateLimitError
    cause. No cloud/SDK conversation is invoked in this offline regression.
    """
    try:
        from openhands.sdk.llm.exceptions import types
        return types
    except ImportError:
        types = ModuleType("openhands.sdk.llm.exceptions.types")
        for name in ("LLMRateLimitError", "LLMTimeoutError", "LLMServiceUnavailableError", "LLMBadRequestError"):
            setattr(types, name, type(name, (Exception,), {"__module__": types.__name__}))
        return types


class OriginalFreeBudgetRecovery(unittest.TestCase):
    def test_gemini_original_wrapped_failure_produces_nonsecret_typed_diagnostic_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            old = Path.cwd()
            try:
                os.chdir(temporary)
                env = {**_authorized_fixture(), "PLENUM_GEMINI_FREE_PROJECT_APPROVAL": coder.GEMINI_FREE_APPROVAL}
                event = json.loads(Path("event.json").read_text())
                types = _sdk_exception_module()
                cloud_error = types.LLMRateLimitError("429 original_daily_ai_budget_exhausted")
                with patch.dict(os.environ, env), patch.dict(sys.modules, {types.__name__: types}):
                    with patch.object(sys, "argv", ["coder", "--execute", "--event", "event.json"]), \
                         patch.object(coder, "execute", side_effect=cloud_error):
                        with self.assertRaises(SystemExit):
                            coder.main()
                    self.assertTrue(coder.reserve_gemini_fallback(event, run_id="1234", run_attempt="1"))
                    provider_error = types.LLMBadRequestError("PRIVATE raw prompt and API key example")
                    provider_error.status_code = 400
                    ConversationRunError = type("ConversationRunError", (RuntimeError,), {})
                    wrapped = ConversationRunError("PRIVATE wrapper text")
                    wrapped.__cause__ = provider_error
                    with patch.object(sys, "argv", ["coder", "--execute", "--gemini-fallback", "--event", "event.json"]), \
                         patch.object(coder, "execute", side_effect=wrapped) as model:
                        with self.assertRaises(SystemExit) as failure:
                            coder.main()
                        self.assertEqual(failure.exception.code, 2)
                        self.assertEqual(model.call_count, 1)
                report = json.loads(Path("reports/openhands-agent-review.json").read_text())
                self.assertEqual(report["failure_category"], "ConversationRunError")
                self.assertEqual(report["diagnostic_category"], "GEMINI_LLM_BAD_REQUEST")
                self.assertEqual(report["exception_chain"], [{"type": "ConversationRunError"}, {"type": "LLMBadRequestError", "http_status": 400}])
                self.assertFalse(report["automatic_retry_authorized"])
                self.assertFalse(report["model_run_completed"])
                self.assertFalse(report["candidate_persisted"])
                self.assertNotIn("PRIVATE", json.dumps(report))
            finally:
                os.chdir(old)

    def test_gemini_diagnostic_unknown_or_cyclic_chain_is_bounded_and_not_retried(self):
        types = _sdk_exception_module()
        fake = RuntimeError("LLMRateLimitError 429 confidential text")
        fake.status_code = "429"
        tail = RuntimeError("confidential tail")
        tail.status_code = True
        fake.__cause__ = tail
        tail.__cause__ = fake
        with patch.dict(sys.modules, {types.__name__: types}):
            proof = coder._gemini_failure_diagnostic(fake)
            self.assertEqual(proof["diagnostic_category"], "GEMINI_UNCLASSIFIED_FAILURE")
            self.assertEqual(proof["exception_chain"], [{"type": "RuntimeError"}, {"type": "RuntimeError"}])
            self.assertFalse(proof["automatic_retry_authorized"])
            self.assertNotIn("confidential", str(proof))
            first = current = RuntimeError("private")
            for _ in range(12):
                current.__cause__ = RuntimeError("private")
                current = current.__cause__
            self.assertLessEqual(len(coder._gemini_failure_diagnostic(first)["exception_chain"]), 6)

    def test_reuse_upstream_retry_config_only_for_exact_free_cloud_route(self):
        self.assertEqual(coder.original_free_retry_options(
            "openai/glm-4.7-flash", coder.ORIGINAL_FREE_CODING_ENDPOINT),
            {"num_retries": 1})
        for model, url in (
            ("ollama/qwen3:1.7b", "http://127.0.0.1:11434"),
            ("openai/glm-4.7-flash", "https://another-provider.example/ai/v1"),
            ("openai/other-model", coder.ORIGINAL_FREE_CODING_ENDPOINT),
        ):
            self.assertEqual(coder.original_free_retry_options(model, url), {})

    def test_true_daily_local_cap_retains_nonsecret_failure_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            old = Path.cwd()
            try:
                os.chdir(temporary)
                env = _authorized_fixture()
                types = _sdk_exception_module()
                # Actual #733 terminal error was directly chained from this
                # exact pinned exception type through ConversationRunError.
                upstream = types.LLMRateLimitError("429 original_daily_ai_budget_exhausted")
                wrapped = RuntimeError("Conversation run failed")
                wrapped.__cause__ = upstream
                with patch.object(sys, "argv", ["coder", "--execute",
                                               "--event", "event.json",
                                               "--out", "reports/free-cap.json"]), \
                     patch.dict(os.environ, env), \
                     patch.dict(sys.modules, {types.__name__: types}), \
                     patch.object(coder, "execute",
                         side_effect=wrapped) as model:
                    with self.assertRaises(SystemExit) as failure:
                        coder.main()
                    self.assertEqual(failure.exception.code, 2)
                    self.assertEqual(model.call_count, 1)
                report = json.loads(Path("reports/free-cap.json").read_text())
                self.assertEqual(report["status"], "BLOCKED_ORIGINAL_DAILY_FREE_AI_CAP")
                self.assertFalse(report["provider_account_quota_verified"])
                self.assertFalse(report["model_run_completed"])
                self.assertFalse(report["candidate_persisted"])
                self.assertFalse(report["retry_same_day_authorized"])
                self.assertEqual(report["origin_issue_number"], 123)
                self.assertEqual(report["origin_run_id"], "1234")
                self.assertEqual(report["origin_run_attempt"], "1")
                self.assertEqual(report["source_file"], "src/plenum_ai/public_example.py")
                self.assertNotIn(env["PLENUM_OPENHANDS_API_KEY"], str(report))
                self.assertNotIn("original_daily_ai_budget_exhausted", str(report))
            finally:
                os.chdir(old)

    def test_unrelated_failure_is_not_silently_relabelled(self):
        with tempfile.TemporaryDirectory() as temporary:
            old = Path.cwd()
            try:
                os.chdir(temporary)
                env = _authorized_fixture()
                types = _sdk_exception_module()
                for message in ("unknown failure", "429 original_daily_ai_budget_exhausted"):
                    with self.subTest(message=message):
                        with patch.object(sys, "argv", ["coder", "--execute", "--event", "event.json",
                                                       "--out", "reports/other.json"]), \
                             patch.dict(os.environ, env), \
                             patch.dict(sys.modules, {types.__name__: types}), \
                             patch.object(coder, "execute", side_effect=RuntimeError(message)):
                            with self.assertRaisesRegex(RuntimeError, message):
                                coder.main()
                        self.assertFalse(Path("reports/other.json").exists())
            finally:
                os.chdir(old)


if __name__ == "__main__":
    unittest.main()



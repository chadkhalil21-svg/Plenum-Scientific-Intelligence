"""Original bounded OpenHands-to-imported-Goldfish reviewer integration contract."""
import hashlib
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from plenum_ai import openhands_goldfish_review as g


class OriginalGoldfishReviewTests(TestCase):
    def _context(self, directory):
        original = b"def skill_match(text):\n    return 'free local' in text\n"
        digest = hashlib.sha256(original).hexdigest()
        issue = 998
        target = "src/plenum_ai/role_skill_router.py"
        objective = "Preserve multiword skill matching without false substring activation"
        event = {"issue": {"number": issue, "title": "[Plenum OpenHands] public repair"}}
        task = {"issue_number": issue, "task": objective,
                "source_file": target, "source_sha256": digest}
        relative = Path(f"reports/openhands-review/issue-{issue}.patch")
        relative.parent.mkdir(parents=True)
        proposed_patch = (
            "--- a/" + target + "\n+++ b/" + target + "\n"
            "@@ -1,2 +1,2 @@\n def skill_match(text):\n"
            "-    return 'free local' in text\n+    return 'free local' in text.split()\n"
        )
        relative.write_text(proposed_patch, encoding="utf-8")
        receipt = {
            "status": "PROPOSAL_AWAITING_REVIEW", "source_file": target,
            "source_sha256": digest,
            "model_run_completed": True, "candidate_persisted": True,
            "candidate_syntax_valid": True, "production_written": False,
            "external_accounts_changed": False, "candidate_artifact": relative.as_posix(),
            "candidate_artifact_sha256": hashlib.sha256(relative.read_bytes()).hexdigest()
        }
        return event, task, original, receipt

    def test_actual_pinned_goldfish_receives_fresh_context_and_flags_semantic_breakage(self):
        original_cwd = Path.cwd()
        try:
            with TemporaryDirectory() as root:
                os.chdir(root)
                event, task, original, coding = self._context(root)
                calls = []
                def mock_provider(request, timeout):
                    calls.append((request, timeout))
                    message = ("BLOCKER: text.split() breaks the existing two-word "
                               "trigger 'free local', so preserve multiword phrase matching.\n"
                               "MAJOR: No test demonstrates punctuation boundaries.")
                    return io.BytesIO(json.dumps({"choices": [{
                        "message": {"role": "assistant", "content": message}
                    }]}).encode())
                with (patch.object(g, "parse_owner_repair_event", return_value=task),
                      patch.object(g, "_public_source", return_value=(original, task["source_sha256"])),
                      patch.dict(os.environ, {"PLENUM_EPHEMERAL_RUNNER": "confirmed",
                                             "PLENUM_OPENHANDS_BASE_URL": g.BASE_URL,
                                             "PLENUM_OPENHANDS_API_KEY": "t" * 600})):
                    result = g.review(event, coding, opener=mock_provider)
                self.assertEqual(len(calls), 1)
                request, timeout = calls[0]
                self.assertEqual(timeout, 55)
                posted = json.loads(request.data)
                self.assertIn("Strict Read-Only Protocol", posted["messages"][0]["content"])
                self.assertIn("Design Critic Goldfish", posted["messages"][0]["content"])
                self.assertNotIn("Elephant", posted["messages"][1]["content"])
                self.assertEqual(posted["model"], "glm-4.7-flash")
                self.assertEqual(result["status"], "ADVISORY_WITH_BLOCKERS")
                self.assertEqual(result["severity_counts"]["BLOCKER"], 1)
                self.assertEqual(result["severity_counts"]["MAJOR"], 1)
                self.assertFalse(result["independent_semantic_verified"])
                self.assertFalse(result["production_written"])
                self.assertFalse(result["auto_merge_authorized"])
        finally:
            os.chdir(original_cwd)

    def test_tampered_or_missing_patch_blocks_before_any_model_call(self):
        original_cwd = Path.cwd()
        try:
            with TemporaryDirectory() as root:
                os.chdir(root)
                event, task, original, coding = self._context(root)
                calls = []
                def must_not_call(*args, **kwargs):
                    calls.append(1)
                    raise AssertionError("Do not call model when original artifact is invalid")
                with (patch.object(g, "parse_owner_repair_event", return_value=task),
                      patch.object(g, "_public_source", return_value=(original, task["source_sha256"]))):
                    broken = {**coding, "candidate_artifact_sha256": "f" * 64}
                    a = g.review(event, broken, opener=must_not_call)
                    self.assertEqual(a["status"], "BLOCKED_PATCH_HASH_MISMATCH")
                    wrong_source = {**coding, "source_sha256": "a" * 64}
                    b = g.review(event, wrong_source, opener=must_not_call)
                    self.assertEqual(b["status"], "BLOCKED_UNVERIFIED_ORIGINAL_CODING_RECEIPT")
                    Path(coding["candidate_artifact"]).unlink()
                    c = g.review(event, coding, opener=must_not_call)
                    self.assertEqual(c["status"], "BLOCKED_UNSAFE_OR_MISSING_SOURCE_PATCH")
                self.assertEqual(calls, [])
        finally:
            os.chdir(original_cwd)

    def test_review_does_not_call_provider_without_original_ephemeral_identity(self):
        original_cwd = Path.cwd()
        try:
            with TemporaryDirectory() as root:
                os.chdir(root)
                event, task, original, coding = self._context(root)
                with (patch.object(g, "parse_owner_repair_event", return_value=task),
                      patch.object(g, "_public_source", return_value=(original, task["source_sha256"])),
                      patch.dict(os.environ, {"PLENUM_EPHEMERAL_RUNNER": "",
                                             "PLENUM_OPENHANDS_BASE_URL": g.BASE_URL,
                                             "PLENUM_OPENHANDS_API_KEY": ""})):
                    result = g.review(event, coding, opener=lambda *a, **k: self.fail("model invoked"))
                self.assertEqual(result["status"], "BLOCKED_ORIGINAL_EPHEMERAL_IDENTITY_MISSING")
        finally:
            os.chdir(original_cwd)

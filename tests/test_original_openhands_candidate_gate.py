"""Only the security invariants of the ORIGINAL offline patch acceptance gate."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.verify_original_openhands_candidate import verify


class OriginalOfflinePatchGateTests(unittest.TestCase):
    def fixture(self, root):
        source = root / "src/plenum_ai/example.py"
        source.parent.mkdir(parents=True)
        original = b"def original():\n    return 1\n"
        source.write_bytes(original)
        candidate = b"def original():\n    return 2\n"
        patch_file = root / "reports/openhands-review/issue-42.patch"
        patch_file.parent.mkdir(parents=True)
        proposal = (
            "--- a/src/plenum_ai/example.py\n"
            "+++ b/src/plenum_ai/example.py\n"
            "@@ -1,2 +1,2 @@\n"
            " def original():\n"
            "-    return 1\n"
            "+    return 2\n"
        ).encode()
        patch_file.write_bytes(proposal)
        record = {
            "status": "PROPOSAL_AWAITING_REVIEW",
            "source_file": "src/plenum_ai/example.py",
            "source_sha256": hashlib.sha256(original).hexdigest(),
            "candidate_artifact": "reports/openhands-review/issue-42.patch",
            "candidate_artifact_sha256": hashlib.sha256(proposal).hexdigest(),
            "candidate_sha256": hashlib.sha256(candidate).hexdigest(),
            "model_run_completed": True,
            "candidate_persisted": True,
            "candidate_syntax_valid": True,
            "production_written": False,
            "external_accounts_changed": False,
        }
        path = root / "reports/original-model.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        return path, record

    def test_forged_patch_hash_rejected_before_untrusted_code_or_sandbox(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            report, content = self.fixture(root)
            content["candidate_artifact_sha256"] = "f" * 64
            report.write_text(json.dumps(content), encoding="utf-8")
            verdict_path = root / "reports/verdict.json"
            with patch("tools.verify_original_openhands_candidate.subprocess.run",
                       side_effect=AssertionError("Untrusted patch must not execute")):
                verdict = verify(report, verdict_path, checkout=root)
            self.assertEqual(verdict["status"], "BLOCKED_UNVERIFIED_CANDIDATE")
            self.assertFalse(verdict["existing_focused_tests_passed"])
            self.assertFalse(verdict["automatically_merged"])
            self.assertEqual(json.loads(verdict_path.read_text()), verdict)

    def test_no_preexisting_source_test_does_not_claim_semantic_review(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            report, _ = self.fixture(root)
            verdict_path = root / "reports/verdict.json"
            with patch("tools.verify_original_openhands_candidate.subprocess.run",
                       side_effect=AssertionError("No source test means no code run")):
                verdict = verify(report, verdict_path, checkout=root)
            self.assertEqual(verdict["status"], "BLOCKED_NO_EXISTING_FOCUSED_TEST")
            self.assertFalse(verdict["independent_semantic_approval"])
            self.assertFalse(verdict["production_written"])


if __name__ == "__main__":
    unittest.main()

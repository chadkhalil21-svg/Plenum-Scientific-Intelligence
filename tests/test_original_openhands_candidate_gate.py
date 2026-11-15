"""Only the security invariants of the ORIGINAL offline patch acceptance gate."""
import hashlib
import json
from contextlib import chdir
from pathlib import Path
import subprocess
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

    def interrupted_fixture(self, root):
        report, content = self.fixture(root)
        content.update(
            schema="plenum-openhands-coding-agent-v1",
            upstream="OpenHands/software-agent-sdk",
            task="Correct the original public source output.",
            status="BLOCKED_INTERRUPTED_WITH_REVIEW_ARTIFACT",
            failure_category="ORIGINAL_ENGINE_TRANSPORT",
            model_run_completed=False,
            generated_code_executed=False,
            verified_independent_quality=False,
            human_review_required=True,
            origin_issue_number=42,
            origin_run_id="12345",
            origin_run_attempt="1",
            retry_same_day_authorized=False,
            no_paid_fallback=True,
        )
        report = report.rename(root / "reports/openhands-agent-review.json")
        report.write_text(json.dumps(content), encoding="utf-8")
        tests = root / "tests"
        tests.mkdir()
        (tests / "test_example.py").write_text("# existing focused contract\n")
        return report, content

    def interrupted_origin_env(self, root, issue=42, run="12345", attempt="1",
                               source="src/plenum_ai/example.py"):
        event_path = root / "original-event.json"
        event_path.write_text(json.dumps({
            "action":"opened", "repository":{"full_name":"chadkhalil21-svg/Plenum-Scientific-Intelligence"},
            "sender":{"login":"chadkhalil21-svg"},
            "issue":{"number":issue,"user":{"login":"chadkhalil21-svg"},
                     "title":"[Plenum OpenHands] public repair",
                     "body":"PLENUM_OPENHANDS_PUBLIC_REPAIR_V1\nfile: " + source
                             + "\nobjective: Correct the original public source output."},
        }), encoding="utf-8")
        return {"PLENUM_REVIEW_INTERRUPTED":"confirmed", "GITHUB_ACTIONS":"true", "GITHUB_EVENT_NAME":"issues",
                "GITHUB_EVENT_PATH":str(event_path), "GITHUB_RUN_ID":run,
                "GITHUB_RUN_ATTEMPT":attempt,
                "GITHUB_REPOSITORY":"chadkhalil21-svg/Plenum-Scientific-Intelligence"}

    def test_bound_interrupted_patch_reaches_existing_sandbox_but_stays_unapproved(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            report, content = self.interrupted_fixture(root)
            original_run = subprocess.run

            def local_git_and_docker_boundary(command, **kwargs):
                if command[0] == "git":
                    return original_run(command, **kwargs)
                self.assertEqual(command[0], "docker")
                self.assertIn("--network=none", command)
                bound = next(x for x in command if x.startswith("type=bind,src="))
                isolated = Path(bound.split(",src=")[1].split(",")[0])
                self.assertEqual((isolated / content["source_file"]).read_bytes(),
                                 b"def original():\n    return 2\n")
                self.assertTrue(bound.endswith(",dst=/work,readonly"))
                return subprocess.CompletedProcess(command, 0)

            with patch.dict("os.environ", self.interrupted_origin_env(root)), chdir(root):
                with patch("tools.verify_original_openhands_candidate.subprocess.run",
                           side_effect=local_git_and_docker_boundary):
                    verdict = verify(report, root / "reports/verdict.json", checkout=root)
            self.assertEqual(verdict["status"], "INTERRUPTED_FOCUSED_TESTS_PASS_REVIEW_STILL_REQUIRED")
            self.assertTrue(verdict["existing_focused_tests_passed"])
            self.assertFalse(verdict["model_run_completed"])
            self.assertFalse(verdict["independent_semantic_approval"])
            self.assertFalse(verdict["automatically_merged"])
            self.assertEqual((root / content["source_file"]).read_bytes(),
                             b"def original():\n    return 1\n")
            self.assertFalse(json.loads(report.read_text())["model_run_completed"])

    def test_interrupted_patch_rejects_missing_or_mismatched_origin_before_sandbox(self):
        for origin in (None, (43, "12345", "1", "src/plenum_ai/example.py"),
                       (42, "12346", "1", "src/plenum_ai/example.py"),
                       (42, "12345", "2", "src/plenum_ai/example.py"),
                       (42, "12345", "1", "src/plenum_ai/other.py")):
            with self.subTest(origin=origin), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                report, _ = self.interrupted_fixture(root)
                env = (self.interrupted_origin_env(root, *origin) if origin else
                       {"PLENUM_REVIEW_INTERRUPTED":""})
                with patch.dict("os.environ", env), chdir(root):
                    with patch("tools.verify_original_openhands_candidate.subprocess.run",
                               side_effect=AssertionError("Unbound patch must not execute")):
                        verdict = verify(report, root / "reports/verdict.json", checkout=root)
                self.assertEqual(verdict["status"], "BLOCKED_UNVERIFIED_CANDIDATE")

    def test_interrupted_patch_keeps_original_digest_and_review_only_flags(self):
        for field, value in (("candidate_artifact_sha256", "f" * 64),
                             ("candidate_artifact", "reports/openhands-review/issue-43.patch"),
                             ("failure_category", "UNCLASSIFIED"),
                             ("model_run_completed", True),
                             ("generated_code_executed", True),
                             ("verified_independent_quality", True),
                             ("retry_same_day_authorized", True)):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                report, record = self.interrupted_fixture(root)
                record[field] = value
                report.write_text(json.dumps(record), encoding="utf-8")
                with patch.dict("os.environ", self.interrupted_origin_env(root)), chdir(root):
                    with patch("tools.verify_original_openhands_candidate.subprocess.run",
                               side_effect=AssertionError("Invalid interrupted artifact must not execute")):
                        verdict = verify(report, root / "reports/verdict.json", checkout=root)
                self.assertEqual(verdict["status"], "BLOCKED_UNVERIFIED_CANDIDATE")


if __name__ == "__main__":
    unittest.main()

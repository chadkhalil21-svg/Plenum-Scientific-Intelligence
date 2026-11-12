"""Pure/offline security checks for original founder Chief single native retry."""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from plenum_ai.chief_retry_gate import eligible_run, inspect_retry
from plenum_ai.mission_checkpoint import artifact_digest, save_checkpoint

REPO = "chadkhalil21-svg/Plenum-Scientific-Intelligence"
OBJECTIVE = "Create a public data validator program and an original SVG illustration"
TEAM = ("public_program", "public_creative")


def event(*, attempt=1, status="completed", conclusion="failure",
          actor="chadkhalil21-svg", kind="issues"):
    return {"workflow_run": {
        "id": 987654321,
        "name": "Plenum Chief | Founder Model-Directed Specialist Command",
        "run_attempt": attempt, "status": status,
        "conclusion": conclusion, "event": kind,
        "actor": {"login": actor}, "repository": {"full_name": REPO},
    }}


def issue(*, author="chadkhalil21-svg", title="[Plenum Chief] public mission",
          objective=OBJECTIVE):
    return {
        "number": 1001, "state": "open",
        "user": {"login": author}, "title": title,
        "body": "PLENUM_CHIEF_PUBLIC_MISSION_V1\nobjective: " + objective,
    }


def stage(root: Path):
    relative = "workers/public_program/issue-1001/code"
    path = root / relative
    path.mkdir(parents=True)
    (path / "public-starter.py").write_text("print('bounded public artifact')\n")
    sha = artifact_digest(root, relative)
    results = {
        "public_program": {
            "attempt": 1, "status": "DRAFT_READY_FOR_FOUNDER",
            "verified": True, "worker": "existing_plenum_program_foundry",
            "verified_scope": "public starter syntax/hash only",
            "output_artifact": "issue-1001/code",
            "artifact_path": relative, "sha256": sha,
        },
        "public_creative": {
            "attempt": 1, "status": "BLOCKED_WORKER_OR_VERIFICATION",
            "verified": False,
            "worker": None, "artifact_path": None, "sha256": None,
        },
    }
    save_checkpoint(root, issue=1001, objective=OBJECTIVE, team=TEAM, results=results)
    (root / "chief-result-1001.json").write_text(json.dumps({
        "issue_number": 1001, "mode": "multi",
        "expected_team": list(TEAM), "status": "BLOCKED_PARTIAL_TEAM",
        "independent_verified": False,
    }))
    return path


class NativeChiefRetryGateTests(TestCase):
    def test_only_first_original_owner_failed_issue_run_qualifies(self):
        self.assertEqual(eligible_run(event()), 987654321)
        for bad in (
            event(attempt=2), event(status="in_progress"),
            event(conclusion="success"), event(kind="pull_request"),
            event(actor="other"), {"workflow_run": {}}, {},
        ):
            self.assertIsNone(eligible_run(bad))

    def test_real_checkpoint_with_original_artifact_allows_single_retry(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            stage(root)
            self.assertEqual(inspect_retry(event(), root, issue())["status"],
                             "ELIGIBLE_NATIVE_RETRY_ONCE")
            self.assertEqual(inspect_retry(event(), root, issue())["saved_verified_workers"], 1)

    def test_tampered_artifact_and_changed_founder_goal_are_rejected(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            path = stage(root)
            self.assertEqual(
                inspect_retry(event(), root, issue(objective="Survey different public science papers"))["status"],
                "BLOCKED_UNRELATED_OR_COMPLETED_WORK",
            )
            (path / "public-starter.py").write_text("tampered")
            self.assertEqual(
                inspect_retry(event(), root, issue())["status"],
                "BLOCKED_UNSAFE_RETRY_HISTORY",
            )

    def test_never_retry_other_authors_closed_issues_or_unrelated_tasks(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            stage(root)
            self.assertEqual(
                inspect_retry(event(), root, issue(author="third-party"))["status"],
                "BLOCKED_NOT_FOUNDER_PUBLIC_MISSION",
            )
            self.assertEqual(
                inspect_retry(event(), root, issue(title="[Plenum Workforce] public research"))["status"],
                "BLOCKED_NOT_FOUNDER_PUBLIC_MISSION",
            )
            closed = issue()
            closed["state"] = "closed"
            self.assertEqual(
                inspect_retry(event(), root, closed)["status"],
                "BLOCKED_NOT_FOUNDER_PUBLIC_MISSION",
            )

    def test_no_repeat_if_sibling_failed_twice_or_many_workers_failed(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            stage(root)
            cp = root / "chief-checkpoint-1001.json"
            data = json.loads(cp.read_text())
            data["results"]["public_creative"]["attempt"] = 2
            cp.write_text(json.dumps(data))
            self.assertEqual(
                inspect_retry(event(), root, issue())["status"],
                "BLOCKED_UNSAFE_RETRY_HISTORY",
            )

    def test_missing_original_checkpoint_fails_closed(self):
        with TemporaryDirectory() as folder:
            self.assertEqual(
                inspect_retry(event(), Path(folder), issue())["status"],
                "BLOCKED_MISSING_OR_UNSAFE_CHECKPOINT",
            )


if __name__ == "__main__":
    import unittest
    unittest.main()

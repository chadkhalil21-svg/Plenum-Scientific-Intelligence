"""A timed-out original specialist must fail closed through its public inbox."""
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from plenum_ai.workforce_public_inbox import MAGIC_V2, OWNER, REPO, TITLE, run_issue


class ReviewedDomainWorkerTimeoutTests(unittest.TestCase):
    def test_validator_timeout_reports_blocked_without_success_manifest(self):
        event = {
            "action": "opened",
            "repository": {"full_name": REPO},
            "issue": {
                "number": 840,
                "user": {"login": OWNER},
                "title": TITLE,
                "body": MAGIC_V2 + "\nkind: public_program\n"
                        "objective: Create a Python validator for NOAA station metadata",
            },
        }
        with TemporaryDirectory() as directory:
            output_dir = Path(directory)
            with patch("plenum_ai.reviewed_domain_workers.subprocess.run",
                       side_effect=subprocess.TimeoutExpired("original-validator", 12)) as command:
                result = run_issue(event, output_dir=output_dir)
            command.assert_called_once()
            self.assertEqual(result["status"], "BLOCKED_WORKER_OR_VERIFICATION")
            self.assertIs(result["verified"], False)
            self.assertIsNone(result["output_artifact"])
            self.assertFalse((output_dir / "issue-840" / "code" / "manifest.json").exists())

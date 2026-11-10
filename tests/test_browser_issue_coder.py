"""Founder browser coding-agent public scope; never calls inference in tests."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from plenum_ai.browser_issue_coder import parse_issue, run, TITLE, MAGIC, REPO, OWNER


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

    def test_preflight_has_no_model_or_external_access(self):
        with tempfile.TemporaryDirectory() as root:
            with patch("plenum_ai.browser_issue_coder._out_dir",
                       return_value=Path(root) / "browser"):
                result = run(fixture(), execute=False)
                self.assertEqual(result["status"], "PREFLIGHT_ONLY")
                self.assertFalse(result["model_executed"])
                self.assertFalse(result["independent_behavior_verified"])
                self.assertTrue((Path(root) / "browser/result.json").is_file())


if __name__ == "__main__":
    unittest.main()

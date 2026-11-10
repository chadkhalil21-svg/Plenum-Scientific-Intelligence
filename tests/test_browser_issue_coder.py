"""Founder browser coding-agent public scope; never calls inference in tests."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from plenum_ai.browser_issue_coder import (
    parse_issue, run, review_candidate_structure, TITLE, MAGIC, REPO, OWNER,
)


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

    def test_real_first_agent_stub_rejected_without_running_model(self):
        # Exact actual failure mode from founder #399, not an artificial demo.
        candidate = (
            "from typing import List, Tuple\n\n"
            "def get_approved_elements() -> List[Tuple[str, str]]:\n"
            "    # Logic to retrieve owner-approved elements\n"
            "    pass\n\n"
            "def rank_elements(elements: List[Tuple[str, str]]) "
            "-> List[Tuple[str, str]]:\n"
            "    # Logic to rank elements based on owner-approved actions\n"
            "    pass\n\n"
            "if __name__ == '__main__':\n"
            "    approved_elements = get_approved_elements()\n"
            "    ranked_elements = rank_elements(approved_elements)\n"
            "    print(ranked_elements)\n"
        ).encode()
        self.assertEqual(len(candidate), 448)
        with self.assertRaisesRegex(ValueError, "no computed function result"):
            review_candidate_structure(candidate)

    def test_generic_ast_structural_gate_is_independent_of_model(self):
        valid = (
            "def rank_elements(elements):\n"
            "    \"\"\"Sort public link records without website side effects.\"\"\"\n"
            "    return sorted(elements, key=lambda element: element[0])\n"
        ).encode()
        self.assertIsNone(review_candidate_structure(valid))
        for candidate in (
            "def rank_elements(elements):\n    pass\n" + "# padding\n" * 12,
            "def rank_elements(elements):\n    ...\n" + "# padding\n" * 12,
            "def rank_elements(elements):\n    raise NotImplementedError()\n"
            + "# padding\n" * 12,
            "def rank_elements(elements):\n    return elements\n    pass\n"
            + "# padding\n" * 12,
            "x = 1\n" + "# padding\n" * 20,
            "def rank_elements(elements):\n    return (\n"
            + "# padding\n" * 12,
        ):
            with self.subTest(candidate=candidate[:45]):
                with self.assertRaises(ValueError):
                    review_candidate_structure(candidate.encode())

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

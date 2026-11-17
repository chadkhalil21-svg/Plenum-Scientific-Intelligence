import json
from pathlib import Path
import sys
import tempfile
import unittest

integration = Path(__file__).resolve().parents[1] / "integrations/upstream/cmbagent-lg-20261116"
if integration.is_dir():
    sys.path.insert(0, str(integration))


class GroundingBoundaryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "evidence").mkdir()
        (self.root / "evidence" / "result.json").write_text(
            json.dumps({"population": 0.125, "time": 450}), encoding="utf-8")

    def test_public_numeric_claims_are_grounded_or_missing_not_semantically_proven(self):
        from audit_claims import audit_claims
        report = audit_claims(self.root, "evidence/result.json",
                              ["Population was 0.125.", "Population was 789.456."])
        self.assertEqual(report["claims"][0]["state"], "grounded")
        self.assertEqual(report["claims"][1]["state"], "ungrounded")
        self.assertTrue(report["complete_within_selected_artifact"])
        self.assertFalse(report["semantic_truth_verified"])

    def test_rejects_outside_evidence_and_symlink(self):
        from audit_claims import audit_claims
        outside = self.root / "outside.json"
        outside.write_text("{}", encoding="utf-8")
        (self.root / "evidence" / "link.json").symlink_to(outside)
        for name in ("outside.json", "evidence/../outside.json", "evidence/link.json"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                audit_claims(self.root, name, ["Value was 1."])


if __name__ == "__main__":
    unittest.main()

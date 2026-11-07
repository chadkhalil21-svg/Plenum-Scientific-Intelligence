"""Check strategic resume state remains evidence-linked and nonconfidential."""
import copy
import json
import tempfile
from pathlib import Path
import unittest
from plenum_ai import continuity_ledger as ledger


def fixture():
    return {
      "schema":ledger.SCHEMA,"last_reviewed_utc":"2026-11-07T03:00:00Z",
      "mission":"Develop independently evaluated general-purpose scientific intelligence while preserving continuity.",
      "confidential_documents_copied":False,
      "AGI_achieved":False,
      "automatic_model_promotion":False,
      "evidence":[{"id":"agi-lab-first-audit","status":"measured_failure",
                   "url":ledger.TRUSTED+"actions/runs/42331449321",
                   "result":{"correct":0,"attempted":6},
                   "AGI_demonstrated":False}],
      "next_actions":[{"priority":1,"action":"Adopt trusted standard benchmark under controlled conditions"}],
      "decisions":[{"decision":"Keep outcome ledger","reason":"Verify progress across sessions"}]
    }


class PublicStrategicContinuityTests(unittest.TestCase):
    def test_valid_immutable_scientific_claims(self):
        s=ledger.validate(fixture())
        text=ledger.brief(s)
        self.assertIn("Verified AGI: NO",text)
        self.assertIn("0/6",text)
        self.assertIn("This file is a checkpoint",text)

    def test_missing_or_changed_evidence_is_rejected(self):
        tests=[("AGI_achieved",True),("confidential_documents_copied",True),
               ("automatic_model_promotion",True)]
        for field,value in tests:
            altered=fixture();altered[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):
                ledger.validate(altered)
        wrong=fixture();wrong["evidence"][0]["result"]["correct"]=7
        with self.assertRaises(ValueError):
            ledger.validate(wrong)
        wrong=fixture();wrong["evidence"][0]["AGI_demonstrated"]=True
        with self.assertRaises(ValueError):
            ledger.validate(wrong)

    def test_non_github_and_duplicate_evidence_are_rejected(self):
        wrong=fixture();wrong["evidence"][0]["url"]="https://example.com/not-verifiable"
        with self.assertRaises(ValueError):
            ledger.validate(wrong)
        wrong=fixture();wrong["evidence"]*=2
        with self.assertRaises(ValueError):
            ledger.validate(wrong)

    def test_next_actions_must_be_prioritized_and_written(self):
        wrong=fixture();wrong["next_actions"][0]["priority"]=9
        with self.assertRaises(ValueError):
            ledger.validate(wrong)
        wrong=fixture();wrong["decisions"]=[]
        with self.assertRaises(ValueError):
            ledger.validate(wrong)

    def test_no_local_private_file_or_oversized_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/"state.json"
            f.write_text(json.dumps(fixture()))
            self.assertEqual(ledger.load(f)["schema"],ledger.SCHEMA)
            f.write_text("a"*50001)
            with self.assertRaises(ValueError):
                ledger.load(f)

    def test_invalid_schema_and_timestamp_rejected(self):
        wrong=fixture();wrong["schema"]="agi-verified"
        with self.assertRaises(ValueError):
            ledger.validate(wrong)
        wrong=fixture();wrong["last_reviewed_utc"]="2026-11-07"
        with self.assertRaises(ValueError):
            ledger.validate(wrong)

if __name__=="__main__":
    unittest.main()

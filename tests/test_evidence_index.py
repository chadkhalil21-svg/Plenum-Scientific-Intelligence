"""Proof the evidence index is bounded, deterministic and doesn't invent AGI."""
import json
from pathlib import Path
import tempfile
import unittest
from plenum_ai import evidence_index as idx


class EvidenceIndexTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)/"evidence"
        (self.root/"chemistry").mkdir(parents=True)
        (self.root/"physics").mkdir()
        (self.root/"chemistry"/"run-2.json").write_text(
            json.dumps({"observations":[1,2],"AGI_demonstrated":True}))
        (self.root/"physics"/"run-1.json").write_text(
            json.dumps({"scientific_claim_verified":True}))

    def test_deterministic_manifest_has_source_hashes_not_promoted_claims(self):
        first=idx.build_index(self.root)
        second=idx.build_index(self.root)
        self.assertEqual(first, second)
        self.assertEqual(first["record_count"], 2)
        self.assertEqual([g["track"] for g in first["groups"]],
                         ["chemistry","physics"])
        self.assertFalse(first["AGI_demonstrated"])
        self.assertFalse(first["scientific_claims_verified_by_index"])
        self.assertFalse(first["automatic_model_promotion"])
        self.assertTrue(first["inventory_complete"])
        self.assertNotIn('"observations"',json.dumps(first))
        self.assertNotIn('"scientific_claim_verified": true',json.dumps(first))

    def test_save_is_idempotent_and_changes_when_source_changes(self):
        output=Path(self.tmp.name)/"state/evidence_index.json"
        first,changed=idx.save_index(self.root,output)
        self.assertTrue(changed)
        same,changed=idx.save_index(self.root,output)
        self.assertFalse(changed)
        self.assertEqual(first,same)
        (self.root/"physics"/"run-1.json").write_text('{"different":true}')
        third,changed=idx.save_index(self.root,output)
        self.assertTrue(changed)
        self.assertNotEqual(first["digest_sha256"],third["digest_sha256"])

    def test_invalid_json_is_reported_as_unindexed_not_silent_success(self):
        (self.root/"physics"/"bad.json").write_text("not JSON")
        report=idx.build_index(self.root)
        self.assertEqual(report["record_count"],2)
        self.assertFalse(report["inventory_complete"])
        self.assertEqual(report["unindexed_records"][0]["reason"],"unreadable_json")

    def test_root_symlink_is_refused(self):
        link=Path(self.tmp.name)/"alias"
        link.symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(ValueError):
            idx.build_index(link)

    def test_refuse_oversized_file_without_exposing_contents(self):
        (self.root/"physics"/"oversized.json").write_text("X"*(idx.MAX_JSON_BYTES+1))
        report=idx.build_index(self.root)
        self.assertFalse(report["inventory_complete"])
        self.assertEqual(report["unindexed_records"][0]["reason"],"oversized")

    def test_unsafe_missing_source_is_rejected(self):
        with self.assertRaises(ValueError):
            idx.build_index(Path(self.tmp.name)/"not-there")


if __name__=="__main__":
    unittest.main()

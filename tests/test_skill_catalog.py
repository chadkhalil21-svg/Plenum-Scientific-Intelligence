"""Validate source pinning, opt-in and no skill code execution."""
import io
import unittest
from plenum_ai.skill_catalog import catalog, retrieve_skill_document, CURATED, REVISION

class FakeResponse(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): self.close()

class CuratedSkillTests(unittest.TestCase):
    def test_pinned_metadata_and_no_execution(self):
        listing = catalog()
        self.assertEqual(len(listing["skills"]), 6)
        self.assertFalse(listing["execution_enabled"])
        self.assertTrue(all(REVISION in s["source"] for s in listing["skills"]))
        self.assertTrue(all(s["installation_status"].startswith("not_installed")
                            for s in listing["skills"]))

    def test_read_only_document_response(self):
        def stub(request, timeout=0):
            self.assertIn(REVISION, request.full_url)
            return FakeResponse(b"---\nname: rdkit\n---\nReference only.")
        doc = retrieve_skill_document("rdkit", opener=stub)
        self.assertFalse(doc["executed"])
        self.assertEqual(len(doc["sha256"]), 64)
        self.assertEqual(doc["status"], "untrusted_document_for_human_review_only")

    def test_refuse_unknown_skill_and_nonmarkdown(self):
        with self.assertRaises(ValueError):
            retrieve_skill_document("dangerous-shell-command")
        with self.assertRaises(ValueError):
            retrieve_skill_document("rdkit", opener=lambda *a, **k: FakeResponse(b"bad input"))

if __name__ == "__main__":
    unittest.main()

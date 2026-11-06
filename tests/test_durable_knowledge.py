"""Test durable graph replay, safe local indexing and licensed full-text parsing."""
import io
import json
import tempfile
import unittest
from pathlib import Path

from plenum_ai.durable_graph import run_persistent, inspect_persistent
from plenum_ai.knowledge_index import (
    upsert_paper, search_index, index_federated,
)
from plenum_ai.open_access import (
    parse_open_article, index_open_article, fulltext_url,
)


class FakeHTTP(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


OPEN_XML = b'''<?xml version="1.0"?>
<article xmlns:xlink="http://www.w3.org/1999/xlink">
<front>
<article-meta>
 <article-id pub-id-type="doi">10.1000/physics-experiment</article-id>
 <title-group><article-title>Reproducible scientific measurements</article-title></title-group>
 <permissions><license xlink:href="https://creativecommons.org/licenses/by/4.0"/></permissions>
 <abstract><p>This paper reports reproducible measurements for controlled scientific experiments in physics.</p></abstract>
</article-meta>
</front>
<body><sec><title>Methods</title>
<p>Independent researchers conducted multiple controlled experimental measurements under established laboratory conditions.</p>
</sec></body>
</article>'''


class DurableGraphTests(unittest.TestCase):
    def test_file_checkpoint_recovers_after_process_scope(self):
        with tempfile.TemporaryDirectory() as folder:
            db = str(Path(folder) / "checkpoints.sqlite")
            first = run_persistent(
                "Test previously verified numerical scientific examples",
                db, "study-0001",
                tool_keys=["scipy.orbit", "scipy.thermal"],
                optimize=True, offline=True,
            )
            self.assertEqual(first["status"], "executed_and_checkpointed")
            self.assertTrue(first["result"]["known_model_integration_passed"])
            recovered = inspect_persistent(db, "study-0001")
            self.assertTrue(recovered["finished"])
            self.assertEqual(recovered["workers_recorded"], 2)
            second = run_persistent(
                "Test previously verified numerical scientific examples",
                db, "study-0001",
                tool_keys=["scipy.orbit", "scipy.thermal"],
                optimize=True, offline=True,
            )
            self.assertEqual(second["status"], "recovered")
            self.assertFalse(second["new_scientific_work_executed"])
            self.assertEqual(second["checkpoint"]["workers_recorded"], 2)
            with self.assertRaises(ValueError):
                run_persistent("Different question", db, "study-0001")

    def test_checkpoint_missing_and_bad_ids(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "missing.sqlite")
            with self.assertRaises(FileNotFoundError):
                inspect_persistent(path, "absent")
            with self.assertRaises(ValueError):
                run_persistent("Valid question", path, "../../unexpected")

class LibraryIndexTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "science.sqlite"

    def tearDown(self):
        self.tmp.cleanup()

    def _metadata(self):
        return {"source":"europepmc", "id":"PMC3258128",
                "title":"Spectroscopy of experimental materials",
                "url":"https://europepmc.org/articles/PMC3258128",
                "doi":"https://doi.org/10.1000/spectral"}

    def test_bibliographic_index_and_reopen(self):
        added = upsert_paper(self.db, self._metadata())
        self.assertFalse(added["fulltext_indexed"])
        found = search_index(self.db, "spectroscopy")
        self.assertEqual(len(found["results"]), 1)
        self.assertEqual(found["results"][0]["title"],
                         "Spectroscopy of experimental materials")
        self.assertFalse(found["results"][0]["citation_verified"])
        with self.assertRaises(ValueError):
            search_index(self.db, "!!!")

    def test_rights_required_for_fulltext(self):
        with self.assertRaises(ValueError):
            upsert_paper(self.db, self._metadata(), fulltext="Full copy")
        doc = {**self._metadata(), "license":"CC-BY-4.0"}
        upsert_paper(self.db, doc, fulltext="Repeated controlled spectroscopy experiments")
        result = search_index(self.db, "repeated")
        self.assertTrue(result["results"][0]["fulltext_available_locally"])
        self.assertEqual(len(result["results"][0]["content_sha256"]), 64)

    def test_public_memory_records_rebuild_index(self):
        from plenum_ai.memory import make_record, save
        from plenum_ai.knowledge_index import import_verified_memory
        root = Path(self.tmp.name) / "prior-memory"
        report = {
            "question": "Spectroscopy of experimental materials",
            "source_status": "retrieved_metadata",
            "literature_and_hypotheses": {"papers": [{
                "id":"https://openalex.org/W1234",
                "title":"Measurements of photon emission",
                "doi":"https://doi.org/10.5555/photons",
                "url":"https://openalex.org/W1234",
                "year":2024,
            }]},
            "numeric_benchmark_verified":False,
        }
        memory=make_record(report, {"candidate":{}}, "test-run", "test-revision")
        save(memory, root)
        index=import_verified_memory(self.db,root)
        self.assertEqual(index["valid_paper_references_indexed"], 1)
        self.assertEqual(index["invalid_or_rejected_records"], 0)
        self.assertEqual(len(search_index(self.db,"photon")["results"]),1)

    def test_federated_ingestion_limited_and_explicit(self):
        payload = {"records":[self._metadata()]}
        r=index_federated(self.db, payload)
        self.assertEqual(r["metadata_records_indexed"], 1)
        self.assertFalse(r["fulltext_added"])

    def test_license_checked_open_access_article_from_fixture(self):
        parsed = parse_open_article("PMC3258128", OPEN_XML)
        self.assertTrue(parsed["license_confirmed_from_article_xml"])
        self.assertEqual(parsed["paper"]["license"], "CC-BY-4.0")
        result=index_open_article(
            self.db, "PMC3258128",
            opener=lambda req, timeout=0: FakeHTTP(OPEN_XML))
        self.assertTrue(result["indexed"])
        self.assertFalse(result["full_article_archived"])
        self.assertEqual(len(search_index(self.db,"reproducible")["results"]), 1)
        self.assertIn("/PMC3258128/fullTextXML", fulltext_url("PMC3258128"))

    def test_unknown_or_restrictive_license_fails_closed(self):
        stripped = OPEN_XML.replace(b'https://creativecommons.org/licenses/by/4.0',
                                    b'https://creativecommons.org/licenses/by-nc/4.0')
        with self.assertRaises(ValueError):
            parse_open_article("PMC3258128", stripped)
        with self.assertRaises(ValueError):
            parse_open_article("PMC3258128", b'<!DOCTYPE article><article/>')
        with self.assertRaises(ValueError):
            fulltext_url("http://external.site/")

if __name__ == "__main__":
    unittest.main()

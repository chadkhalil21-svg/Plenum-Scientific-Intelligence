"""Changes must be compared with previously archived public metadata only."""
import json
import tempfile
import unittest
from pathlib import Path
from plenum_ai.discovery_delta import compare_discovery

def snapshot(records):
    return {"schema":"plenum-cross-domain-research-pulse-v1",
            "observed_at_utc":"2026-11-06T12:00:00+00:00","records":records}

def row(doi,title):
    return {"title":title,"url":"https://doi.org/"+doi,
            "doi":"https://doi.org/"+doi,
            "source":"crossref","tier":"journal_publication_metadata",
            "published":"2026-11-05"}


class NewResearchTests(unittest.TestCase):
    def test_no_prior_record_is_new_to_archive_not_new_to_science(self):
        with tempfile.TemporaryDirectory() as root:
            r=compare_discovery(snapshot([row("10.1/new","New Paper")]),root)
            self.assertEqual(r["new_to_this_archive"],1)
            self.assertFalse(r["novel_to_world_or_independent_science"])
            self.assertFalse(r["new_patentable_discoveries"])

    def test_previous_public_archives_are_deduplicated_by_source_identifier(self):
        with tempfile.TemporaryDirectory() as root:
            original=row("10.1/known","Previously seen paper")
            (Path(root)/"2026-11-05-run-123.json").write_text(json.dumps({
                "schema":"plenum-public-cross-domain-observatory-v1",
                "snapshot":snapshot([original])
            }))
            current=snapshot([original,row("10.1/other","Freshly observed paper")])
            r=compare_discovery(current,root)
            self.assertEqual(r["prior_records_scanned"],1)
            self.assertEqual(r["new_to_this_archive"],1)
            self.assertEqual(r["previously_seen_in_this_archive"],1)
            self.assertEqual(r["items_first_observed_by_plenum"][0]["title"],
                             "Freshly observed paper")

    def test_untrusted_json_and_invalid_archives_are_not_interpreted(self):
        with tempfile.TemporaryDirectory() as root:
            (Path(root)/"bad.json").write_text('{not valid')
            r=compare_discovery(snapshot([row("10.1/new","New")]),root)
            self.assertEqual(r["rejected_or_unreadable_archives"],1)
            self.assertEqual(r["new_to_this_archive"],1)

if __name__=="__main__":
    unittest.main()

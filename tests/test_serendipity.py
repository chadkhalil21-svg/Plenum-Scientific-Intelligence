"""Interdisciplinary question generation must retain original source citations."""
import unittest
from plenum_ai.serendipity import hypotheses_from_sources

class SerendipityTests(unittest.TestCase):
    def test_source_grounded_speculation_not_fabricated_invention(self):
        report={"schema":"plenum-cross-domain-research-pulse-v1",
                "observed_at_utc":"2026-11-06T12:00:00Z",
                "records":[{
                    "title":"Experimental optical interference method",
                    "url":"https://doi.org/10.1111/example",
                    "tier":"journal_publication_metadata"
                },{
                    "title":"Experimental optical interference method",
                    "url":"https://doi.org/10.1111/example",
                    "tier":"journal_publication_metadata"
                },{
                    "title":"Creative biology",
                    "url":"https://doi.org/10.1101/sample",
                    "tier":"preprint_not_peer_reviewed"
                }]}
        out=hypotheses_from_sources(report)
        self.assertEqual(out["idea_count"],2)
        self.assertEqual(out["ideas"][0]["domain_to_explore"],"architecture")
        self.assertEqual(out["ideas"][1]["domain_to_explore"],"music")
        self.assertTrue(out["ideas"][0]["reference_url"].startswith("https://doi.org/"))
        self.assertFalse(out["ideas"][0]["original_paper_read"])
        self.assertFalse(out["breakthrough_verified"])
        self.assertFalse(out["foundation_model_generated_hypotheses"])

    def test_invalid_and_unsupported_text_not_included(self):
        report={"schema":"plenum-cross-domain-research-pulse-v1",
                "records":[{"title":"Bad","url":"http://not-secure",
                            "tier":"journal_publication_metadata"},
                           {"title":"Video","url":"https://youtube.com/video",
                            "tier":"public_video_metadata"}]}
        r=hypotheses_from_sources(report)
        self.assertEqual(r["idea_count"],0)
        with self.assertRaises(ValueError):
            hypotheses_from_sources({"schema":"unrecognized"})

if __name__=="__main__":
    unittest.main()

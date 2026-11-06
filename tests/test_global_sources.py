"""Deterministic tests for all five public scholarly metadata providers."""
import io
import json
import unittest
from urllib.parse import urlsplit
from plenum_ai.global_sources import (
    global_literature, arxiv_query_url, parse_arxiv,
    osti_query_url, parse_osti
)

ARXIV_XML = b'''<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2601.01234v1</id>
    <title>Scientific photon research</title>
    <published>2026-01-05T01:02:03Z</published>
    <arxiv:doi>10.1234/photon</arxiv:doi>
  </entry>
</feed>'''
OSTI_JSON = json.dumps([{
    "osti_id": 12345, "title": "Scientific photon research",
    "publication_date": "2026-02-05", "doi": "10.1234/photon"
}]).encode()

class Response(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *args): self.close()


def bibliographic_source(url):
    host = urlsplit(url).netloc
    if host == "api.openalex.org":
        return {"results":[{
            "id":"https://openalex.org/W1234",
            "title":"Scientific photon research",
            "publication_year":2026,
            "doi":"https://doi.org/10.1234/photon"
        }]}
    if host == "www.ebi.ac.uk":
        return {"resultList":{"result":[{"source":"MED","id":"42",
                        "title":"Other research paper","pubYear":"2025"}]}}
    if host == "api.semanticscholar.org":
        return {"data":[{"paperId":"abc","title":"Third independent paper",
                         "year":2024, "url":"https://www.semanticscholar.org/paper/abc"}]}
    raise ValueError("unexpected provider")


class GlobalLiteratureTests(unittest.TestCase):
    def test_arxiv_api_and_atom_format(self):
        self.assertIn("export.arxiv.org/api/query?",arxiv_query_url("quantum photons"))
        r=parse_arxiv(ARXIV_XML)
        self.assertEqual(len(r),1)
        self.assertEqual(r[0]["source"],"arxiv")
        self.assertEqual(r[0]["doi"],"https://doi.org/10.1234/photon")
        self.assertTrue(r[0]["url"].startswith("https://arxiv.org/abs/"))
        with self.assertRaises(ValueError):
            parse_arxiv(b"<!DOCTYPE x><feed/>")

    def test_osti_search_and_json(self):
        self.assertIn("osti.gov/api/v1/records?",osti_query_url("fusion"))
        r=parse_osti(OSTI_JSON)
        self.assertEqual(r[0]["url"],"https://www.osti.gov/biblio/12345")
        self.assertEqual(r[0]["year"],2026)
        with self.assertRaises(ValueError):
            parse_osti(b'{"unknown": "schema"}')

    def test_five_sources_deduplicate_provenance(self):
        def opener(request, timeout):
            host=urlsplit(request.full_url).netloc
            self.assertEqual(timeout,18)
            if host=="export.arxiv.org":
                return Response(ARXIV_XML)
            if host=="www.osti.gov":
                return Response(OSTI_JSON)
            raise AssertionError("unexpected host")
        r=global_literature("photon research",offline=False,
                            fetcher=bibliographic_source,opener=opener)
        self.assertEqual(len(r["providers"]),5)
        self.assertTrue(r["all_providers_healthy"])
        self.assertEqual(len(r["records"]),3)
        shared=next(x for x in r["records"] if x["doi"]=="https://doi.org/10.1234/photon")
        self.assertEqual(set(shared["also_indexed_by"]),{"openalex","arxiv","osti"})
        self.assertFalse(r["scientific_truth_verified"])
        self.assertEqual(r["materials_project_status"],"not_requested_requires_private_API_key")

    def test_offline_never_calls_providers(self):
        r=global_literature("astronomy",offline=True,
            fetcher=lambda _: 1/0, opener=lambda *a,**k: 1/0)
        self.assertEqual(len(r["records"]),0)
        self.assertTrue(all(x["status"]=="skipped_offline" for x in r["providers"]))

    def test_provider_outage_visible_and_other_sources_preserved(self):
        def opener(request, timeout):
            if "arxiv.org" in request.full_url:
                raise ConnectionError("metadata provider temporarily unavailable")
            return Response(OSTI_JSON)
        r=global_literature("photon research",offline=False,
                            fetcher=bibliographic_source,opener=opener)
        self.assertFalse(r["all_providers_healthy"])
        self.assertEqual(r["providers"][3]["status"],"unavailable")
        self.assertEqual(r["providers"][3]["error_type"],"ConnectionError")
        self.assertGreater(len(r["records"]),0)

if __name__=="__main__":
    unittest.main()

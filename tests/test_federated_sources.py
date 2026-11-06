import unittest
from urllib.parse import urlparse
from plenum_ai.federated_sources import search_federated, _normalize


def fake(url):
    host=urlparse(url).netloc
    if host == "api.openalex.org":
        return {"results":[{"id":"https://openalex.org/W1","title":"Shared source","publication_year":2026,"doi":"https://doi.org/10.1234/example"}]}
    if host == "www.ebi.ac.uk":
        return {"resultList":{"result":[{"source":"MED","id":"42","title":"Shared source","pubYear":"2026","doi":"10.1234/example"}]}}
    if host == "api.semanticscholar.org":
        return {"data":[{"paperId":"x","title":"Independent paper","year":2025,"url":"https://example.org/1"}]}
    raise ValueError("Not an allowed host")


class FederatedTests(unittest.TestCase):
    def test_offline_never_calls_external_network(self):
        report=search_federated("scientific paper",offline=True,fetcher=lambda x:1/0)
        self.assertEqual(len(report["records"]),0)
        self.assertTrue(all(x["status"]=="skipped_offline" for x in report["providers"]))

    def test_three_sources_concurrent_and_deduplicated(self):
        result=search_federated("example research",offline=False,fetcher=fake)
        self.assertTrue(result["all_providers_healthy"])
        self.assertEqual(len(result["providers"]),3)
        self.assertEqual(len(result["records"]),2)
        shared=next(x for x in result["records"] if x["title"]=="Shared source")
        self.assertEqual(set(shared["also_indexed_by"]),{"openalex","europepmc"})
        self.assertFalse(result["scientific_truth_verified"])

    def test_partial_failure_visible_not_silenced(self):
        def unstable(url):
            if "semanticscholar" in url:
                raise ConnectionError("rate limited")
            return fake(url)
        result=search_federated("test",offline=False,fetcher=unstable)
        self.assertFalse(result["all_providers_healthy"])
        self.assertEqual(result["providers"][2]["status"],"unavailable")
        self.assertGreater(len(result["records"]),0)

    def test_bad_provider_input(self):
        with self.assertRaises(ValueError):
            search_federated("")
        with self.assertRaises(ValueError):
            _normalize("unknown",{})

if __name__=="__main__":
    unittest.main()

"""Frozen public acceptance: non-string DOI fields in provider normalization."""
import unittest
from plenum_ai.federated_sources import search_federated

class ProviderNormalization(unittest.TestCase):
    def test_malformed_doi_preserves_valid_provider_neighbors(self):
        def fixture(url):
            if "api.openalex.org" in url:
                return {"results":[]}
            if "europepmc" in url:
                return {"resultList":{"result":[
                    {"id":"e1","title":"Shared study","pubYear":"2020","doi":17},
                    {"id":"e2","title":"Second study","pubYear":"2021","doi":"10.1234/valid"}]}}
            return {"data":[
                {"paperId":"s1","title":"Shared study","year":2020,"externalIds":{"DOI":["bad"]}},
                {"paperId":"s2","title":"Second study","year":2021,"externalIds":{"DOI":"10.1234/valid"}}]}
        result=search_federated("public study",offline=False,fetcher=fixture)
        self.assertTrue(result["all_providers_healthy"])
        self.assertEqual(len(result["records"]),2)
        for record in result["records"]:
            self.assertEqual(set(record["also_indexed_by"]),{"europepmc","semanticscholar"})
        self.assertIsNone(result["records"][0]["doi"])
        self.assertEqual(result["records"][1]["doi"],"https://doi.org/10.1234/valid")
        self.assertFalse(result["scientific_truth_verified"])

    def test_offline_unchanged(self):
        result=search_federated("public study",offline=True,fetcher=lambda _:self.fail("network"))
        self.assertEqual(result["records"],[])
        self.assertTrue(all(p["status"]=="skipped_offline" for p in result["providers"]))

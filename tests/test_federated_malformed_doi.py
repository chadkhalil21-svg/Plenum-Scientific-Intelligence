"""Frozen independent acceptance for malformed bibliographic identifiers."""
import unittest
from plenum_ai.federated_sources import search_federated

def public_fixture(url):
    if "api.openalex.org" in url:
        return {"results":[{"id":"a","title":"Example study","publication_year":2020,"doi":123},
                           {"id":"b","title":"Second study","publication_year":2021,"doi":"https://doi.org/10.1234/example"}]}
    if "europepmc" in url:
        return {"resultList":{"result":[{"id":"c","title":"Example study","pubYear":"2020"},
                                      {"id":"d","title":"Second study","pubYear":"2021","doi":"10.1234/example"}]}}
    return {"data":[]}

class FederatedMalformedDOI(unittest.TestCase):
    def test_nonstr_doi_preserves_records_and_attribution(self):
        result=search_federated("public study",offline=False,fetcher=public_fixture)
        self.assertTrue(result["all_providers_healthy"])
        self.assertEqual(len(result["records"]),2)
        for record in result["records"]:
            self.assertEqual(set(record["also_indexed_by"]),{"openalex","europepmc"})
        self.assertFalse(result["scientific_truth_verified"])

    def test_offline_preserved(self):
        result=search_federated("public study",offline=True,fetcher=lambda _:self.fail("network"))
        self.assertEqual(result["records"],[])
        self.assertTrue(all(p["status"]=="skipped_offline" for p in result["providers"]))

if __name__=="__main__":
    unittest.main()

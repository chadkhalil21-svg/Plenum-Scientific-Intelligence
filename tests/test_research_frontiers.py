"""Contract tests for research-frontier institutional metadata."""
import io
import unittest
from urllib.parse import urlsplit, parse_qs
from plenum_ai.research_frontiers import (
    nsf_url, trials_url, parse_nsf, parse_trials, scan_frontiers,
)

class Reply(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self,*args): self.close()


class FrontierSourceTests(unittest.TestCase):
    def test_queries_bounded_and_official(self):
        self.assertEqual(urlsplit(nsf_url("solar cells")).hostname,"api.nsf.gov")
        self.assertEqual(urlsplit(trials_url("solar cells")).hostname,"clinicaltrials.gov")
        self.assertEqual(parse_qs(urlsplit(trials_url("physics")).query)["sort"],
                         ["LastUpdatePostDate:desc"])
        for bad in ("", "x"*141, 12):
            with self.assertRaises(ValueError):
                nsf_url(bad)

    def test_grants_are_not_scientific_results(self):
        rows=parse_nsf({"response":{"award":[{"id":"1234567","title":"Quantum spectroscopy",
                       "date":"2026-08-01","awardeeName":"Example University"}]}})
        self.assertEqual(rows[0]["tier"],"funded_research_project_metadata")
        self.assertFalse(rows[0]["research_conducted_or_succeeded"])
        self.assertTrue(rows[0]["url"].startswith("https://www.nsf.gov/"))
        with self.assertRaises(ValueError):
            parse_nsf({"response":{"other":[]}})

    def test_trials_are_registered_not_efficacy(self):
        rows=parse_trials({"studies":[{"protocolSection":{
            "identificationModule":{"nctId":"NCT12345678","briefTitle":"Molecular therapy feasibility"},
            "statusModule":{"overallStatus":"RECRUITING",
                            "lastUpdatePostDateStruct":{"date":"2026-09-14"}}
        }}]})
        self.assertEqual(rows[0]["study_id"],"NCT12345678")
        self.assertFalse(rows[0]["clinical_approval_or_treatment_efficacy"])
        self.assertEqual(rows[0]["recruitment_status"],"RECRUITING")
        with self.assertRaises(ValueError):
            parse_trials({"result":[]})

    def test_parallel_fetch_and_outage_isolated(self):
        def opener(req,timeout):
            self.assertEqual(timeout,18)
            url=req.full_url
            if "api.nsf.gov" in url:
                return Reply(b'{"response":{"award":[{"id":"1234567","title":"Photonics sensing project"}]}}')
            if "clinicaltrials.gov" in url:
                return Reply(b'{"studies":[{"protocolSection":{"identificationModule":{"nctId":"NCT12345678","briefTitle":"Photonics clinical imaging"}}}]}')
            raise AssertionError("Unknown destination")
        report=scan_frontiers("photonics", online=True, opener=opener)
        self.assertTrue(report["all_sources_healthy"])
        self.assertEqual(len(report["records"]),2)
        self.assertFalse(report["laboratory_breakthrough_confirmed"])

        def one_down(req,timeout):
            if "clinicaltrials.gov" in req.full_url:
                raise ConnectionError("Temporary clinical API failure")
            return opener(req,timeout)
        report=scan_frontiers("photonics",online=True,opener=one_down)
        self.assertFalse(report["all_sources_healthy"])
        self.assertEqual(report["providers"][1]["error_type"],"ConnectionError")
        self.assertEqual(len(report["records"]),1)

    def test_offline_network_prohibited(self):
        result=scan_frontiers("photonics",online=False,
                              opener=lambda *a,**k: 1/0)
        self.assertEqual(result["records"],[])
        self.assertEqual([p["status"] for p in result["providers"]],
                         ["skipped_offline","skipped_offline"])

if __name__=="__main__":
    unittest.main()

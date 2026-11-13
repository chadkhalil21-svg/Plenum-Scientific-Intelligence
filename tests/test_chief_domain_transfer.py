"""No-model validation for two previously untested types of Chief delegation."""
import json
import math
import unittest
from unittest.mock import patch
from plenum_ai import chief_domain_transfer as x


class Response:
    status = 200
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, n):
        return json.dumps({
            "message": {
                "DOI": x.DOI,
                "title": ["Observation of Gravitational Waves from a Binary Black Hole Merger"],
                "published": {"date-parts": [[2016, 2, 11]]},
                "publisher": "American Physical Society",
            }
        }).encode()


class Client:
    def __init__(self): self.urls = []
    def open(self, req, timeout):
        self.urls.append((req.full_url, req.get_method(), timeout))
        return Response()


class CrossDomainContracts(unittest.TestCase):
    def test_preflight_cannot_claim_model_or_results(self):
        for case in x.CASES:
            p=x.source_preflight(case)
            self.assertEqual(p["status"], "SOURCE_READY_NOT_EXECUTED")
            self.assertFalse(p["model_called"])
            self.assertFalse(p["paid_api_used"])
            self.assertFalse(p["business_account_write"])
            self.assertTrue(p["human_review_for_writes"])

    def test_outside_identifier_is_rejected_before_network(self):
        for d in ("../config", "http://internal", "10.1234/other", x.DOI+"?token=private"):
            with self.subTest(doi=d), self.assertRaises(ValueError):
                x.read_crossref(d, opener=Client())
        with self.assertRaises(ValueError):
            x.source_preflight("engineering-production-deploy")

    def test_crossref_returns_only_proven_identity_metadata(self):
        c=Client()
        e=x.read_crossref(x.DOI, opener=c)
        self.assertEqual(e["year"], 2016)
        self.assertEqual(e["doi"], x.DOI.lower())
        self.assertEqual(e["publisher"], "American Physical Society")
        self.assertTrue(c.urls[0][0].startswith("https://api.crossref.org/works/10.1103%2F"))
        self.assertEqual(c.urls[0][1:], ("GET", 12))
        self.assertEqual(set(e), {"doi", "title", "year", "publisher", "source", "retrieval_kind"})

    def test_untrusted_response_fails_identity_validation(self):
        class Wrong(Response):
            def read(self,n):
                return b'{"message":{"DOI":"10.1234/WRONG","title":["Bad metadata"],"publisher":"Fake Publisher","published":{"date-parts":[[2016]]}}}'
        class Fake(Client):
            def open(self,*args,**kwargs): return Wrong()
        with self.assertRaises(ValueError):
            x.read_crossref(x.DOI, opener=Fake())

    def test_provider_temporarily_unavailable_triggers_bounded_retry(self):
        from urllib.error import URLError
        class Transient(Client):
            def __init__(self): self.calls=0
            def open(self, *args, **kwargs):
                self.calls += 1
                if self.calls==1: raise URLError("temporary")
                return Response()
        client=Transient(); pauses=[]
        self.assertEqual(x.read_crossref(x.DOI,opener=client,sleep_fn=pauses.append)["year"],2016)
        self.assertEqual(client.calls,2)
        self.assertEqual(pauses,[1])

    def test_existing_scientific_engine_with_independent_analytic_readback(self):
        e=x.existing_science_tool("materials")
        self.assertTrue(x.independent_science_readback(e))
        self.assertEqual(e["scientific_discovery"],False)
        bad=dict(e, observed_kelvin=e["observed_kelvin"]+5.0)
        self.assertFalse(x.independent_science_readback(bad))
        with self.assertRaises(ValueError):
            x.existing_science_tool("private")

    def test_runner_gate_before_all_model_imports(self):
        with patch.dict("os.environ", {"PLENUM_EPHEMERAL_RUNNER": ""}, clear=True):
            with self.assertRaisesRegex(RuntimeError,"isolated"):
                x.execute("scholarly")

    def test_one_turn_model_route_is_exact_and_never_invents_tools(self):
        scholarly = '{"role":"scholarly-auditor"}'
        seen = [{"role": "scholarly-auditor", "value": {"doi": x.DOI}}]
        passed = x.grade_single_real_delegate(
            scholarly, seen, "scholarly-auditor")
        self.assertTrue(passed["one_correct_delegation"])
        self.assertEqual(passed["model_route_decisions"], 1)
        self.assertEqual(passed["observed_worker_calls"], 1)
        self.assertFalse(passed["unexpected_or_redundant_specialists"])
        for untrusted in (
            '{"role":"numerical-analyst"}',
            '{"role":"scholarly-auditor","also_run":"numerical-analyst"}',
            'scholarly-auditor',
            '{"role":"unapproved-web-browser"}',
            '{"role":"scholarly-auditor"}\n{"role":"numerical-analyst"}',
        ):
            with self.subTest(raw=untrusted):
                self.assertFalse(x.grade_single_real_delegate(
                    untrusted, seen, "scholarly-auditor")[
                    "one_correct_delegation"])
        duplicate_tool = x.grade_single_real_delegate(
            scholarly, seen + [{"role": "numerical-analyst", "value": {}}],
            "scholarly-auditor")
        self.assertFalse(duplicate_tool["one_correct_delegation"])
        missing_tool = x.grade_single_real_delegate(
            scholarly, [], "scholarly-auditor")
        self.assertFalse(missing_tool["one_correct_delegation"])
        with self.assertRaises(ValueError):
            x.grade_single_real_delegate(scholarly, seen, "unapproved-agent")

    def test_missions_do_not_refer_to_forced_worker_names(self):
        for case in x.CASES:
            m=x.mission(case)
            self.assertNotIn("scholarly-auditor",m)
            self.assertNotIn("numerical-analyst",m)
            self.assertIn("Founder",m)


if __name__ == "__main__":
    unittest.main()

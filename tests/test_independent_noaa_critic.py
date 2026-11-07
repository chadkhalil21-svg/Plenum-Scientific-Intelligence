"""Different-family critic integrity and withheld NOAA observational audit.

All unit-test observations and model responses are synthetic stubs.
Real public NOAA inference is exercised separately by GitHub Actions.
"""
import copy
from datetime import timedelta
import json
import math
import unittest

from plenum_ai import independent_noaa_critic as critic
from plenum_ai import noaa_revision_agent as noaa


def fake_source(station, day, reveal=False):
    if (station, day) not in noaa.CASES:
        raise AssertionError("Unapproved station or historical date")
    start=noaa.cutoff_date(day)-timedelta(days=16)
    size=17*24 if reveal else 16*24
    phase=0.3 if station=="8723214" else 0.08
    obs={start+timedelta(hours=i):
         1.1+0.3*math.cos(math.tau*i/12.4206+phase)
         +0.05*math.sin(math.tau*i/23.9345)
         +0.02*math.cos(math.tau*i/25.8193)
         for i in range(size)}
    return obs,"full-source" if reveal else "development-only-source"


def original_generator(_):
    return json.dumps({
        "alpha":0.6,"gain":1.1,
        "hypothesis":"A blended forecast could predict hourly coastal water levels.",
        "falsifier":"It is rejected when later measured error exceeds a reference."
    })


def critic_generator(_):
    return json.dumps({
        "alpha":0.9,"gain":1.0,
        "hypothesis":"The earlier harmonic weight may be poorly calibrated on development tides.",
        "falsifier":"The change is rejected if later MAE is no better than the original."
    })


def frozen_record():
    previous=noaa.propose("public historical sea level",original_generator,
                         fetcher=fake_source)
    return critic.extract_public_proposals({
        "source_revision":critic.ORIGINAL_REVISION,
        "public_proposal":previous,
        # Deliberately include a disallowed heldout field: extract must drop it.
        "independent_audit":{"withheld_measurements":"must never reach critic"}})


class IndependentScientificCriticTests(unittest.TestCase):
    def test_extract_only_frozen_original_without_hidden_audit(self):
        frozen=frozen_record()
        self.assertEqual(frozen["schema"],critic.FROZEN_SCHEMA)
        self.assertEqual(len(frozen["proposal"]["cases"]),4)
        self.assertNotIn("independent_audit",frozen)
        self.assertFalse(frozen["includes_holdout_measurements"])
        self.assertTrue(frozen["historical_previously_public"])

    def test_different_model_development_only_criticism(self):
        frozen=frozen_record()
        calls=[]
        def guarded(station,day,reveal=False):
            calls.append(reveal)
            if reveal: raise AssertionError("Critic accessed holdout")
            return fake_source(station,day,False)
        prompts=[]
        def generated(prompt):
            prompts.append(prompt)
            return critic_generator(prompt)
        output=critic.critique(frozen,generated,fetcher=guarded)
        self.assertEqual(len(prompts),4)
        self.assertEqual(calls,[False]*4)
        self.assertTrue(all("Qwen" in p for p in prompts))
        self.assertEqual(output["critic_revision"],critic.CRITIC_REVISION)
        self.assertTrue(output["model_family_distinct_from_original"])
        self.assertFalse(output["heldout_observations_seen_by_critic"])
        self.assertFalse(output["autonomous_model_promotion"])

    def test_independent_audit_records_comparison_and_limitations(self):
        frozen=frozen_record()
        proposals=critic.critique(frozen,critic_generator,fetcher=fake_source)
        audit=critic.audit(frozen,proposals,fetcher=fake_source)
        self.assertEqual(audit["total_cases"],4)
        self.assertEqual(audit["valid_counterproposals"],4)
        self.assertEqual(len(audit["cases"]),4)
        self.assertTrue(audit["development_evidence_reproduced"])
        self.assertTrue(audit["historical_public_data_not_prospectively_blind"])
        self.assertFalse(audit["new_scientific_discovery_verified"])
        self.assertFalse(audit["general_intelligence_verified"])
        self.assertFalse(audit["auto_model_promotion"])
        for row in audit["cases"]:
            self.assertIn("critic_alternative_test_mae_m",row)
            self.assertIn("strongest_reference_mae_m",row)

    def test_invalid_counterargument_is_retained_not_fabricated(self):
        frozen=frozen_record()
        bad=critic.critique(frozen,lambda prompt:"the system is AGI",fetcher=fake_source)
        self.assertTrue(all(x["critic_alternative"] is None for x in bad["critiques"]))
        self.assertTrue(all(not x["counterproposal_better_on_development"]
                            for x in bad["critiques"]))
        report=critic.audit(frozen,bad,fetcher=fake_source)
        self.assertEqual(report["valid_counterproposals"],0)
        self.assertEqual(report["actual_holdout_improvements"],0)

    def test_rejects_mutated_frozen_proposal_and_manifest(self):
        original=frozen_record()
        for key,value in [
            ("source_revision","bad"),
            ("proposal_sha256","fake"),
            ("includes_holdout_measurements",True),
        ]:
            p=copy.deepcopy(original)
            p[key]=value
            with self.subTest(field=key),self.assertRaises(ValueError):
                critic.critique(p,critic_generator,fetcher=fake_source)
        p=copy.deepcopy(original)
        p["proposal"]["cases"][0]["selected_candidate"]["alpha"]=0.02
        with self.assertRaises(ValueError):
            critic.critique(p,critic_generator,fetcher=fake_source)

    def test_rejects_changed_noaa_development_measurements(self):
        frozen=frozen_record()
        def altered(station,day,reveal=False):
            obs,source=fake_source(station,day,reveal)
            obs[min(obs)]+=0.25
            return obs,source
        with self.assertRaisesRegex(ValueError,"development measurements differ"):
            critic.critique(frozen,critic_generator,fetcher=altered)

    def test_rejects_tampered_critic_selection_or_scores(self):
        frozen=frozen_record()
        original=critic.critique(frozen,critic_generator,fetcher=fake_source)
        for field,value in [
            ("critic_development_mae_m",0.0),
            ("recommended_candidate",{"alpha":0.99,"gain":1.0}),
            ("counterproposal_better_on_development",True),
            ("holdout_seen",True),
        ]:
            bad=copy.deepcopy(original)
            bad["critiques"][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):
                critic.audit(frozen,bad,fetcher=fake_source)

    def test_rejects_wrong_critic_identity_or_order(self):
        frozen=frozen_record()
        p=critic.critique(frozen,critic_generator,fetcher=fake_source)
        p["critic_revision"]="main"
        with self.assertRaises(ValueError):
            critic.audit(frozen,p,fetcher=fake_source)
        p=critic.critique(frozen,critic_generator,fetcher=fake_source)
        p["critiques"].reverse()
        with self.assertRaises(ValueError):
            critic.audit(frozen,p,fetcher=fake_source)

    def test_critic_model_is_independent_from_proposer(self):
        self.assertNotEqual(critic.CRITIC_MODEL,noaa.MODEL)
        self.assertNotEqual(critic.CRITIC_REVISION,noaa.REVISION)
        self.assertEqual(len(critic.CRITIC_REVISION),40)

    def test_malformed_model_output_not_executable(self):
        for response in ("import os; os.system('echo bad')",
                         '{"alpha":4,"gain":1,"hypothesis":"This appears invalid","falsifier":"Fails a forecast"}',
                         '{"alpha":0.1,"gain":1,"hypothesis":"A possible improved physical forecast","falsifier":"A counterexample could show failure","shell":"echo bad"}'):
            with self.subTest(response=response[:20]):
                self.assertIsNone(noaa.parse_candidate(response)["candidate"])


if __name__=="__main__":
    unittest.main()

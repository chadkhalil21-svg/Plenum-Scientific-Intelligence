"""Offline tests: real NOAA API must only be called in bounded workflow jobs."""
from datetime import timedelta
import copy
import json
import math
import unittest
from unittest.mock import patch
from plenum_ai import noaa_revision_agent as a


def fake_noaa(station, day, reveal_holdout=False):
    """Deterministic hourly synthetic test data, not real NOAA evidence."""
    if (station, day) not in a.CASES:
        raise AssertionError("Unknown NOAA station/day")
    first=a.cutoff_date(day)-timedelta(days=16)
    n=17*24 if reveal_holdout else 16*24
    phase=0.05 if station=="8723214" else 0.25
    obs={first+timedelta(hours=h):
         1.0+0.32*math.cos(math.tau*h/12.4206+phase)
         +0.05*math.sin(math.tau*h/23.9345)
         +0.015*math.sin(math.tau*h/25.8193)
         for h in range(n)}
    return obs, ("full-" if reveal_holdout else "development-")+station+"-"+day


def valid_response(prompt):
    new="Self-critique" in prompt
    return json.dumps({
        "alpha":0.9 if new else 0.4,
        "gain":1.1 if new else 1.0,
        "hypothesis":"Blended harmonic and previous-day reference predictions improve accuracy.",
        "falsifier":"The prediction is not superior when measured holdout MAE is higher."
    })


class NOAAResearchTests(unittest.TestCase):
    def proposal(self, generator=valid_response):
        return a.propose("Public ocean forecasting test",generator,fetcher=fake_noaa)

    def test_multiple_sites_dates_and_rounds(self):
        result=self.proposal()
        self.assertEqual(result["model_calls"],8)
        self.assertEqual(len(result["cases"]),4)
        self.assertFalse(result["heldout_measurements_accessed"])
        for case in result["cases"]:
            self.assertEqual(len(case["attempts"]),2)
            self.assertEqual(case["attempts"][0]["round"],"initial")
            self.assertEqual(case["attempts"][1]["round"],"revision")
            self.assertFalse(case["holdout_seen"])
            self.assertIsNotNone(case["selected_candidate"])
            self.assertTrue(case["development_observations_sha256"])

    def test_proposer_never_fetches_hidden_observations(self):
        accesses=[]
        def guard(station,day,reveal=False):
            accesses.append(reveal)
            if reveal:
                raise AssertionError("Agent attempted to read heldout NOAA data")
            return fake_noaa(station,day,reveal)
        a.propose("Public test",valid_response,fetcher=guard)
        self.assertEqual(accesses,[False]*4)

    def test_independent_audit_scores_realistic_hourly_fixtures(self):
        report=self.proposal()
        audit=a.audit(report,fetcher=fake_noaa)
        self.assertEqual(audit["station_day_cases"],4)
        self.assertEqual(audit["valid_forecasts"],4)
        self.assertTrue(audit["evidence_verified_before_holdout"])
        self.assertTrue(audit["blind_test_evaluated_independently"])
        self.assertFalse(audit["general_intelligence_proven"])
        self.assertFalse(audit["autonomous_model_updates"])
        for row in audit["results"]:
            self.assertGreaterEqual(row["holdout_hours"],20)
            self.assertIn("four_constituents",row["baseline_mae_m"])
            self.assertIn("persistence_24h",row["baseline_mae_m"])

    def test_invalid_response_preserves_failure_without_fabrication(self):
        report=self.proposal(lambda prompt:"I invented a cure, no JSON")
        self.assertTrue(all(x["selected_candidate"] is None for x in report["cases"]))
        final=a.audit(report,fetcher=fake_noaa)
        self.assertEqual(final["valid_forecasts"],0)
        self.assertEqual(final["wins_vs_best_baseline"],0)

    def test_tampered_seal_and_candidates_rejected(self):
        original=self.proposal()
        for key,value in [("selected_round","counterfeit"),
                          ("development_observations_sha256","incorrect"),
                          ("selected_development_mae_m",0),
                          ("holdout_seen",True)]:
            report=copy.deepcopy(original)
            report["cases"][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                a.audit(report,fetcher=fake_noaa)

    def test_independently_changed_noaa_development_data_rejected(self):
        p=self.proposal()
        def altered(station,day,reveal=False):
            data,sha=fake_noaa(station,day,reveal)
            if reveal:
                t=min(data)
                data[t]+=0.3
            return data,sha
        with self.assertRaisesRegex(ValueError,"observations changed"):
            a.audit(p,fetcher=altered)

    def test_holdout_not_sufficient_is_refused(self):
        p=self.proposal()
        def no_test(station,day,reveal=False):
            return fake_noaa(station,day,False)
        with self.assertRaisesRegex(ValueError,"coverage insufficient"):
            a.audit(p,fetcher=no_test)

    def test_invalid_parameter_boundaries_and_untrusted_commands(self):
        base=json.loads(valid_response("test"))
        for changes in ({"alpha":1.5},{"gain":-9},{"alpha":True},
                        {"gain":float("inf")},{"command":"execute shell"}):
            raw={**base,**changes}
            with self.subTest(changes=changes):
                self.assertIsNone(a.parse_candidate(json.dumps(raw))["candidate"])
        self.assertIsNone(a.parse_candidate("import os; os.system('rm -rf /')")["candidate"])

    def test_bad_source_question_and_model_version_rejected(self):
        with self.assertRaises(ValueError):
            a.propose("",valid_response,fetcher=fake_noaa)
        with self.assertRaises(ValueError):
            a.propose("Public test",valid_response,fetcher=fake_noaa,
                      model_id="unreviewed")
        with self.assertRaises(ValueError):
            a.propose("Public test",valid_response,fetcher=fake_noaa,
                      revision="main")

    def test_reference_chronology_and_physical_source(self):
        s,day=a.CASES[0]
        obs,_=fake_noaa(s,day,False)
        fit,dev=a._train_dev(obs,day)
        self.assertTrue(set(fit).isdisjoint(dev))
        self.assertGreaterEqual(len(fit),250)
        self.assertGreaterEqual(len(dev),85)
        self.assertIsInstance(a._metrics(obs,fit,dev),dict)
        # No holdout information exists in proposer source.
        self.assertTrue(all(t<a.cutoff_date(day) for t in obs))


if __name__=="__main__":
    unittest.main()

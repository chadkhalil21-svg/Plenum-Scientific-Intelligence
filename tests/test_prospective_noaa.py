"""Prospective NOAA experiment tests use synthetic observations only.

No tests fetch future public NOAA targets or claim model performance.
"""
import copy
import json
import math
import unittest
from datetime import datetime, timedelta, timezone
from plenum_ai import prospective_noaa as p

ISSUE = datetime(2026,11,10,12,tzinfo=timezone.utc)
AUDIT = datetime(2026,11,16,12,tzinfo=timezone.utc)


def synthetic_source(station,reveal=False):
    if station not in p.STATION_IDS:
        raise AssertionError("Unauthorized experimental station")
    start=p.START
    count=21*24 if reveal else 16*24
    phase=0.4 if station=="8723214" else 0.1
    obs={start+timedelta(hours=i):
         1.25+0.30*math.cos(math.tau*i/12.4206+phase)
             +0.08*math.cos(math.tau*i/12.0)
             +0.04*math.sin(math.tau*i/23.9345)
             +0.03*math.sin(math.tau*i/25.8193)
             +0.02*math.sin(math.tau*i/(24*7))
         for i in range(count)}
    return obs,("future-source-" if reveal else "development-source-")+station


def proposal_model(prompt):
    assert "Nov 12-13" in prompt
    return json.dumps({
        "alpha":0.85,"gain":1.03,
        "hypothesis":"A forecast mixture of hourly phase and harmonics may improve predictions.",
        "falsifier":"The proposal fails if withheld measured mean absolute error is worse."
    })


def independent_model(prompt):
    assert "Qwen" in prompt
    return json.dumps({
        "alpha":0.75,"gain":0.95,
        "hypothesis":"A lower harmonic weight could reduce poor generalization of the original.",
        "falsifier":"A future measured test could show equal or higher prediction error."
    })


def original():
    return p.propose(proposal_model,fetcher=synthetic_source,now=ISSUE)


def criticism(record):
    return p.critique(record,independent_model,fetcher=synthetic_source,now=ISSUE)


def frozen():
    q=original()
    c=criticism(q)
    return {"schema":"plenum-future-noaa-frozen-v1",
            "original":q,"critic":c,
            "original_sha256":p.digest(q),"critic_sha256":p.digest(c),
            "protocol_commit":p.PROTOCOL_COMMIT,
            "frozen_before_future_observations":True}


class ProspectiveNOAATests(unittest.TestCase):
    def test_precommitted_protocol_dates_and_models(self):
        data=p.protocol()
        self.assertEqual(data["protocol_id"],p.PROTOCOL_ID)
        self.assertEqual(list(data["test_days_utc"]),list(p.TEST_DAYS))
        self.assertEqual(len(p.STATION_IDS),2)
        self.assertEqual(len(p.FOLDS),2)
        self.assertEqual(data["selection_rule"][
            "candidate_must_beat_best_baseline_on_each_development_fold_by_at_least_m"],.005)

    def test_only_development_fetched_by_agents(self):
        called=[]
        def guard(station,reveal=False):
            called.append(reveal)
            if reveal: raise AssertionError("Future observations leaked into model job")
            return synthetic_source(station,False)
        q=p.propose(proposal_model,fetcher=guard,now=ISSUE)
        c=p.critique(q,independent_model,fetcher=guard,now=ISSUE)
        self.assertEqual(called,[False]*4)
        self.assertEqual(q["model_calls"],2)
        self.assertEqual(c["model_calls"],2)
        self.assertEqual([x["station"] for x in q["stations"]],list(p.STATION_IDS))
        self.assertTrue(all(not x["future_observations_seen"] for x in c["stations"]))

    def test_time_enforces_prospectivity(self):
        with self.assertRaisesRegex(ValueError,"before future"):
            p.propose(proposal_model,fetcher=synthetic_source,
                      now=datetime(2026,11,12,tzinfo=timezone.utc))
        with self.assertRaises(ValueError):
            p.critique(original(),independent_model,fetcher=synthetic_source,now=AUDIT)
        with self.assertRaisesRegex(ValueError,"before prospective"):
            p.audit(frozen(),fetcher=synthetic_source,now=ISSUE)

    def test_independent_scientific_audit_after_issued_forecasts(self):
        result=p.audit(frozen(),fetcher=synthetic_source,now=AUDIT)
        self.assertEqual(result["station_days"],4)
        self.assertEqual(len(result["results"]),4)
        self.assertTrue(result["prospective_test"])
        self.assertTrue(result["heldout_evaluated_only_in_later_auditor"])
        self.assertFalse(result["scientific_discovery_verified"])
        self.assertFalse(result["general_intelligence_demonstrated"])
        for row in result["results"]:
            self.assertEqual(row["hours"],24)
            self.assertIn(row["selected_method"],("baseline","qwen","critic"))
            self.assertEqual(len(row["baselines_mae_m"]),3)
            self.assertFalse(row["target_data_used_for_selection"])

    def test_audit_fetches_future_only_after_development_checks(self):
        called=[]
        def observer(station,reveal=False):
            called.append(reveal)
            return synthetic_source(station,reveal)
        p.audit(frozen(),fetcher=observer,now=AUDIT)
        self.assertEqual(called,[False,False,True,True])

    def test_model_invalid_output_keeps_conventional_baseline(self):
        q=p.propose(lambda prompt:"not valid JSON",fetcher=synthetic_source,now=ISSUE)
        c=p.critique(q,lambda prompt:"I am AGI",fetcher=synthetic_source,now=ISSUE)
        self.assertTrue(all(r["qwen_candidate"] is None for r in q["stations"]))
        self.assertTrue(all(r["critic_candidate"] is None for r in c["stations"]))
        self.assertTrue(all(r["selected"]["type"]=="baseline" for r in c["stations"]))

    def test_two_folds_prevent_one_period_overfit(self):
        baseline={k:[0.10,0.11] for k in p.BASELINES}
        weak={"alpha":0.8,"gain":1.0}
        selected=p.choose(weak,None,baseline,[0.07,0.12],[None,None])
        self.assertEqual(selected["type"],"baseline")
        selected=p.choose(weak,None,baseline,[0.06,0.08],[None,None])
        self.assertEqual(selected["type"],"qwen")
        strong={"alpha":0.9,"gain":0.9}
        selected=p.choose(weak,strong,baseline,[0.06,0.08],[0.05,0.07])
        self.assertEqual(selected["type"],"critic")

    def test_reject_changed_original_seal(self):
        q=original()
        q["stations"][0]["qwen_candidate"]["gain"]=1.39
        with self.assertRaisesRegex(ValueError,"modified"):
            criticism(q)

    def test_reject_counterproposal_tampering(self):
        packet=frozen()
        packet["critic"]["stations"][0]["selected"]["type"]="fake"
        with self.assertRaises(ValueError):
            p.audit(packet,fetcher=synthetic_source,now=AUDIT)

    def test_reject_resigned_counterproposal_tampering(self):
        packet=frozen()
        packet["critic"]["stations"][0]["selected"]["type"]="critic"
        row=packet["critic"]["stations"][0]
        row["seal_sha256"]=p.digest({k:v for k,v in row.items() if k!="seal_sha256"})
        packet["critic_sha256"]=p.digest(packet["critic"])
        with self.assertRaisesRegex(ValueError,"selection rule"):
            p.audit(packet,fetcher=synthetic_source,now=AUDIT)

    def test_reject_new_development_observations_in_audit(self):
        packet=frozen()
        def changed(station,reveal=False):
            values,sha=synthetic_source(station,reveal)
            values[min(values)]+=0.03
            return values,sha
        with self.assertRaisesRegex(ValueError,"development measurements differ"):
            p.audit(packet,fetcher=changed,now=AUDIT)

    def test_forecasts_do_not_read_future_observed_values(self):
        obs,_=synthetic_source(p.STATION_IDS[0],False)
        fit=sorted(t for t in obs if p.START<=t<p.DEV_END)
        test=[datetime(2026,11,12,hour,tzinfo=timezone.utc) for hour in range(24)]
        pred=p.forecast(obs,fit,test,{"alpha":0.5,"gain":1.1})
        self.assertEqual(len(pred),24)
        self.assertTrue(all(math.isfinite(x) for x in pred))
        self.assertTrue(all(t not in obs for t in test))

    def test_incomplete_real_data_fails_no_fabricated_result(self):
        q=original()
        def missing(station,reveal=False):
            data,sha=synthetic_source(station,reveal)
            if reveal:
                for t in list(data):
                    if t.date().isoformat()=="2026-11-12":
                        del data[t]
            return data,sha
        c=criticism(q)
        packet={"schema":"plenum-future-noaa-frozen-v1",
                "original":q,"critic":c,"original_sha256":p.digest(q),
                "critic_sha256":p.digest(c),"protocol_commit":p.PROTOCOL_COMMIT,
                "frozen_before_future_observations":True}
        with self.assertRaisesRegex(ValueError,"hourly observations missing"):
            p.audit(packet,fetcher=missing,now=AUDIT)


if __name__=="__main__":
    unittest.main()

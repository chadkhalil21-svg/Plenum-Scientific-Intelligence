"""Tests of prospective USGS experiment with simulated, NOT real, river values."""
import copy
import json
import math
import unittest
from datetime import date,datetime,timedelta,timezone
from plenum_ai import prospective_hydrology as agent
from plenum_ai import usgs_hydrology as h

PROPOSE_AT=datetime(2026,11,11,12,tzinfo=timezone.utc)
AUDIT_AT=datetime(2026,11,18,12,tzinfo=timezone.utc)


def synthetic_fetch(site,reveal=False):
    if site not in h.SITES: raise AssertionError("Unexpected USGS gauge")
    n=(h.HOLDOUT_LAST-h.FIRST).days+1 if reveal else (
        h.DEVELOPMENT_LAST-h.FIRST).days+1
    offset=1 if site=="01491000" else 0
    series={h.FIRST+timedelta(days=i):
            800+150*math.sin(i/4+offset)+2*i for i in range(n)}
    return series,{"response_sha256":"synthetic_source_test_only",
                   "statuses":["Provisional"]}


def scientist(prompt):
    assert "USGS" in prompt
    return json.dumps({"alpha":0.8,"beta":0.003,
        "hypothesis":"An adaptive flow mixture predicts future daily river discharge.",
        "falsifier":"An independent future sample can show larger forecast error."})


def critic(prompt):
    assert "Qwen" in prompt
    return json.dumps({"alpha":0.6,"beta":-0.006,
        "hypothesis":"The original streamflow mixture overfits its historical trend.",
        "falsifier":"A future daily discharge sample rejects the claimed improvement."})


def original():
    return agent.propose(scientist,fetcher=synthetic_fetch,now=PROPOSE_AT)


def criticism(q):
    return agent.critique(q,critic,fetcher=synthetic_fetch,now=PROPOSE_AT)


def frozen():
    q=original()
    c=criticism(q)
    return {"schema":agent.FROZEN_SCHEMA,"protocol_commit":agent.PROTOCOL_COMMIT,
        "original":q,"critic":c,"original_sha256":h.canonical_digest(q),
        "critic_sha256":h.canonical_digest(c),"frozen_before_test":True}


class FutureRiverScienceTests(unittest.TestCase):
    def test_precommitted_dates_and_source_names(self):
        p=agent.protocol()
        self.assertEqual(p["protocol_id"],agent.PROTOCOL_ID)
        self.assertEqual(p["selection_rule"][
            "model_must_beat_best_baseline_each_fold_by_relative_margin"],.05)
        self.assertEqual(len(h.SITES),2)
        self.assertEqual(len(h.HOLDOUT_DAYS),2)

    def test_development_only_call_is_enforced(self):
        reads=[]
        def guarded(site,reveal=False):
            reads.append(reveal)
            if reveal: raise AssertionError("Future hydrology observations leaked to model")
            return synthetic_fetch(site,False)
        q=agent.propose(scientist,fetcher=guarded,now=PROPOSE_AT)
        c=agent.critique(q,critic,fetcher=guarded,now=PROPOSE_AT)
        self.assertEqual(reads,[False]*4)
        self.assertEqual(q["model_calls"],2)
        self.assertEqual(c["critic_calls"],2)
        self.assertTrue(all(x["seal_sha256"] for x in q["sites"]+c["sites"]))

    def test_future_time_gates(self):
        with self.assertRaises(ValueError):
            agent.propose(scientist,fetcher=synthetic_fetch,
                now=datetime(2026,11,12,tzinfo=timezone.utc))
        with self.assertRaises(ValueError):
            agent.critique(original(),critic,fetcher=synthetic_fetch,
                           now=AUDIT_AT)
        with self.assertRaises(ValueError):
            agent.audit(frozen(),fetcher=synthetic_fetch,now=PROPOSE_AT)

    def test_independent_future_audit_runs_after_validation(self):
        report=agent.audit(frozen(),fetcher=synthetic_fetch,now=AUDIT_AT)
        self.assertEqual(report["station_days"],4)
        self.assertTrue(report["independent_audit_with_future_data"])
        self.assertTrue(report["prospectively_frozen"])
        self.assertFalse(report["general_intelligence_verified"])
        self.assertFalse(report["automatic_code_or_model_change"])
        for row in report["results"]:
            self.assertIn(row["selected_source"],("qwen","critic","baseline"))
            self.assertEqual(len(row["baseline_relative_errors"]),3)
            self.assertFalse(row["target_day_used_for_model_selection"])

    def test_holdout_is_requested_only_in_separate_auditor(self):
        observations=[]
        def spy(site,reveal=False):
            observations.append(reveal)
            return synthetic_fetch(site,reveal)
        agent.audit(frozen(),fetcher=spy,now=AUDIT_AT)
        self.assertEqual(observations,[False,False,True,True])

    def test_silent_late_or_missing_forecasts_are_rejected(self):
        q=agent.propose(lambda prompt:"no JSON",fetcher=synthetic_fetch,now=PROPOSE_AT)
        c=agent.critique(q,lambda prompt:"I am AGI",fetcher=synthetic_fetch,now=PROPOSE_AT)
        self.assertTrue(all(x["candidate"] is None for x in q["sites"]+c["sites"]))
        self.assertTrue(all(x["selection"]["source"]=="baseline" for x in c["sites"]))

    def test_generated_code_and_wrong_parameters_are_data_only(self):
        for response in ('import os; os.system("echo hello")',
                         '{"alpha":2,"beta":0,"hypothesis":"A river rate model","falsifier":"Future data could refute this model"}',
                         '{"alpha":0.5,"beta":0.2,"hypothesis":"A river rate model","falsifier":"Future data could refute this model"}',
                         '{"alpha":0.5,"beta":0,"hypothesis":"A river rate model","falsifier":"Future data could refute this model","command":"deploy"}'):
            with self.subTest(response=response[:18]):
                self.assertIsNone(agent.parse_response(response)["candidate"])

    def test_mutating_proposal_seal_is_rejected(self):
        q=original()
        q["sites"][0]["candidate"]["alpha"]=0.01
        with self.assertRaisesRegex(ValueError,"changed after sealing"):
            criticism(q)

    def test_mutating_critic_evidence_is_rejected(self):
        p=frozen()
        p["critic"]["sites"][0]["selection"]["source"]="fake"
        with self.assertRaises(ValueError):
            agent.audit(p,fetcher=synthetic_fetch,now=AUDIT_AT)

    def test_resealed_selection_is_still_rejected(self):
        p=frozen()
        item=p["critic"]["sites"][0]
        item["selection"]["source"]="critic" if item["selection"]["source"]!="critic" else "qwen"
        item["seal_sha256"]=h.canonical_digest({
            k:v for k,v in item.items() if k!="seal_sha256"})
        p["critic_sha256"]=h.canonical_digest(p["critic"])
        with self.assertRaisesRegex(ValueError,"selection rule"):
            agent.audit(p,fetcher=synthetic_fetch,now=AUDIT_AT)

    def test_source_revision_prevents_false_science(self):
        p=frozen()
        def revised(site,reveal=False):
            values,meta=synthetic_fetch(site,reveal)
            values[h.FIRST]+=200
            return values,meta
        with self.assertRaisesRegex(ValueError,"development observations changed"):
            agent.audit(p,fetcher=revised,now=AUDIT_AT)

    def test_unavailable_future_values_fail_audit(self):
        p=frozen()
        def missing(site,reveal=False):
            data,meta=synthetic_fetch(site,reveal)
            if reveal:
                data.pop(h.HOLDOUT_DAYS[0],None)
            return data,meta
        with self.assertRaisesRegex(ValueError,"unavailable"):
            agent.audit(p,fetcher=missing,now=AUDIT_AT)

    def test_wrong_model_identity_fails(self):
        with self.assertRaises(ValueError):
            agent.propose(scientist,fetcher=synthetic_fetch,now=PROPOSE_AT,
                          revision="main")
        with self.assertRaises(ValueError):
            agent.critique(original(),critic,fetcher=synthetic_fetch,
                           now=PROPOSE_AT,model_id="Qwen/Qwen3-1.7B")

if __name__=="__main__":
    unittest.main()

"""Offline tests for two-domain scientific model selection and sealed audit.

Synthetic fixtures only. The live source check separately fetches actual
measured molecule data and sklearn's UCI biomedical observations.
"""
import copy
import json
import unittest
import numpy as np
from plenum_ai import cross_domain_lab as m

def fixture(name):
    rng=np.random.default_rng(44 if name=="chemistry" else 45)
    X=rng.normal(size=(135,6))
    X[:,0]=X[:,0]*5+10
    if name=="chemistry":
        y=0.5*X[:,0]+X[:,1]**2+0.06*rng.normal(size=len(X))
    else:
        y=(X[:,0]+2*X[:,1]+rng.normal(size=len(X))>9.8).astype(int)
    if name=="biology":
        # Ensure both classes appear in all splits.
        y=np.tile([0,1],68)[:135].astype(int)
    d=m.Dataset(name,X,np.asarray(y),np.arange(0,85),
                np.arange(85,110),np.arange(110,135),
                "offline-fixture-"+name,tuple("v"+str(i) for i in range(X.shape[1])))
    d.verify()
    return d

def loader(name):return fixture(name)

def generated(prompt):
    return json.dumps({"linear_strength":2.0,"forest_leaf":3,"mix":0.6,
        "hypothesis":"A bounded mixed estimator could improve scientific prediction stability.",
        "falsifier":"Heldout error greater than a strong reference will reject this selection."})

def prepare():return m.prepare(loader)

def qwen(dev=None):
    return m.propose(dev or prepare(),generated,m.QWEN,m.QWEN_SHA,"qwen")

def critic(dev=None,original=None):
    return m.propose(dev or prepare(),generated,m.CRITIC,m.CRITIC_SHA,
                     "critic",original)

class CrossDomainScienceTests(unittest.TestCase):
    def test_protocol_and_pinned_sources(self):
        p=m.protocol()
        self.assertEqual(p["datasets"]["chemistry"]["records"],1128)
        self.assertEqual(p["datasets"]["biology"]["records"],569)
        self.assertEqual(len(m.DOMAINS),2)

    def test_development_baselines_and_split_isolation(self):
        dev=prepare()
        self.assertEqual([x["domain"] for x in dev["domains"]],list(m.DOMAINS))
        self.assertFalse(dev["holdout_labels_exposed_to_models"])
        self.assertTrue(all(x["baseline_dev_errors"]["linear"]>=0 for x in dev["domains"]))

    def test_candidate_schemas_and_arbitrary_generated_code(self):
        examples=[
          'import os; os.system("rm -rf /")',
          '{"linear_strength":100,"forest_leaf":2,"mix":0.5,"hypothesis":"A possible bounded scientific estimate","falsifier":"Future results may invalidate it"}',
          '{"linear_strength":1,"forest_leaf":false,"mix":0.5,"hypothesis":"A possible bounded scientific estimate","falsifier":"Future results may invalidate it"}',
          '{"linear_strength":1,"forest_leaf":2,"mix":0.5,"hypothesis":"A possible bounded scientific estimate","falsifier":"Future results may invalidate it","code":"execute"}'
        ]
        for s in examples:
            with self.subTest(s=s[:18]):
                self.assertIsNone(m.parse(s)["candidate"])
        self.assertIsNotNone(m.parse(generated("public"))["candidate"])

    def test_short_explanation_does_not_discard_independently_testable_numbers(self):
        text=json.dumps({"linear_strength":1.25,"forest_leaf":4,"mix":0.45,
                         "hypothesis":"Weak","falsifier":""})
        parsed=m.parse(text)
        self.assertEqual(parsed["status"],"numeric_only_weak_claim")
        self.assertFalse(parsed["scientific_claim_verified"])
        self.assertEqual(parsed["candidate"]["forest_leaf"],4)
        dev=prepare()
        def poor_draft(_prompt):return text
        q=m.propose(dev,poor_draft,m.QWEN,m.QWEN_SHA,"qwen")
        c=m.propose(dev,poor_draft,m.CRITIC,m.CRITIC_SHA,"critic")
        frozen=m.freeze(dev,q,c,loader)
        self.assertEqual(len(frozen["decisions"]),2)
        a=m.audit(frozen,loader)
        self.assertFalse(a["new_scientific_discovery_verified"])
        self.assertFalse(a["AGI_demonstrated"])

    def test_models_only_receive_development_summaries(self):
        dev=prepare()
        prompts=[]
        def spy(prompt):
            prompts.append(prompt)
            return generated(prompt)
        out=m.propose(dev,spy,m.QWEN,m.QWEN_SHA,"qwen")
        self.assertEqual(len(prompts),2)
        self.assertTrue(all("No held-out labels are provided" in x for x in prompts))
        self.assertTrue(all(x["candidate"] is not None for x in out["records"]))
        self.assertFalse(out["holdout_scored"])

    def test_original_critic_and_sealed_independent_audit(self):
        dev=prepare()
        a=qwen(dev)
        b=critic(dev,a)
        frozen=m.freeze(dev,a,b,loader)
        self.assertEqual(len(frozen["decisions"]),2)
        self.assertFalse(frozen["holdout_used_in_selection"])
        final=m.audit(frozen,loader)
        self.assertEqual(final["tested_domains"],2)
        self.assertEqual(len(final["results"]),2)
        self.assertTrue(final["independent_holdout_audit"])
        self.assertFalse(final["AGI_demonstrated"])
        self.assertFalse(final["clinical_diagnostic_capability_verified"])

    def test_no_automatic_success_when_invalid_model_output(self):
        dev=prepare()
        bad=lambda _: "The universe is solved, I am AGI."
        q=m.propose(dev,bad,m.QWEN,m.QWEN_SHA,"qwen")
        c=m.propose(dev,bad,m.CRITIC,m.CRITIC_SHA,"critic")
        frozen=m.freeze(dev,q,c,loader)
        self.assertTrue(all(x["selection"]["role"]=="baseline"
                            for x in frozen["decisions"]))
        a=m.audit(frozen,loader)
        self.assertEqual(a["tested_domains"],2)

    def test_unreviewed_model_and_wrong_dataset_rejected(self):
        dev=prepare()
        with self.assertRaises(ValueError):
            m.propose(dev,generated,"unreviewed AI",m.QWEN_SHA,"qwen")
        with self.assertRaises(ValueError):
            m.load("unrelated")
        with self.assertRaises(ValueError):
            m.Dataset("chemistry",np.array([[1.]]*135),np.arange(135),
                      np.arange(85),np.arange(80,110),np.arange(110,135),
                      "wrong",("a",)).verify()

    def test_tampered_candidate_or_dev_record_refused(self):
        dev=prepare()
        a=qwen(dev)
        b=critic(dev,a)
        f=m.freeze(dev,a,b,loader)
        broken=copy.deepcopy(f)
        broken["qwen"]["records"][0]["candidate"]["mix"]=0.0
        with self.assertRaises(ValueError):
            m.audit(broken,loader)
        broken=copy.deepcopy(f)
        broken["decisions"][0]["selection"]["score"]=0.0
        with self.assertRaises(ValueError):
            m.audit(broken,loader)
        broken=copy.deepcopy(f)
        broken["development"]["domains"][0]["source_sha256"]="fake"
        with self.assertRaises(ValueError):
            m.audit(broken,loader)

if __name__=="__main__":
    unittest.main()

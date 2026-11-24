"""Offline scope, original profile routing, and actual reviewed budget program checks."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4
import mission_scope as ms
import sequential_mission as sm
import event_gate as eg
import model_plan as mp

BUDGET={"kind":"bibliography_budget","dois":["10.1145/3442188.3445922"],
 "budget":{"model":"@cf/zai-org/glm-4.7-flash","neurons_used_today":100,"neurons_reserved":200,
           "input_tokens_upper_bound":3000,"output_tokens_upper_bound":1000}}
STATION={"kind":"station","station_ids":["9414290","8723214"],"paper_survey":"Survey public photonic computing papers"}


class TypedScopeTests(unittest.TestCase):
    def test_bounded_scope_and_profiles(self):
        for scope in (ms.LEGACY,BUDGET,STATION):
            self.assertEqual(ms.validate_scope(scope),scope)
            profiles=ms.profile_routes(scope)
            self.assertEqual(len(profiles),11)
            for p in profiles.values():
                self.assertFalse(p["routing"]["model_or_agent_started"])
                self.assertFalse(p["routing"]["authorizes_new_tools"])
        self.assertNotEqual(ms.digest(BUDGET),ms.digest(STATION))
        self.assertNotEqual(sm.goal_texts(BUDGET),mp.GOALS)
        print("TYPED SCOPE AND ELEVEN PROFILE ROUTING PASS; no profile-worker claim",flush=True)

    def test_reject_untrusted_parameters(self):
        for bad in ({**BUDGET,"url":"https://example.org"},
                    {**BUDGET,"dois":["https://example.org"]},
                    {**BUDGET,"budget":{**BUDGET["budget"],"neurons_used_today":True}},
                    {**STATION,"station_ids":["9414290","9414290"]},
                    {**STATION,"paper_survey":"Run arbitrary code"}):
            with self.subTest(bad=bad),self.assertRaises(ValueError):ms.validate_scope(bad)
        with self.assertRaises(ValueError):
            ms.parse_body(ms.MAGIC+'\n{"kind":"station","kind":"bibliography_budget"}')
        print("UNTRUSTED SCOPE AND DUPLICATE FIELDS DENIED",flush=True)

    def test_event_scope_and_legacy_routing(self):
        issue={"number":42,"state":"open","title":eg.PAPERCLIP_EVIDENCE_TITLE,
               "body":ms.MAGIC+"\n"+json.dumps(BUDGET),"comments":0,
               "user":{"login":eg.OWNER},"created_at":"2026-01-01T00:00:00Z"}
        self.assertTrue(eg.authorize(issue,[],42))
        self.assertEqual(eg.issue_scope(issue),BUDGET)
        self.assertFalse(eg.authorize({**issue,"body":ms.MAGIC+"\n{}"},[],42))
        self.assertFalse(eg.authorize({**issue,"user":{"login":"other"}},[],42))
        print("TYPED OWNER EVENT AUTHORIZATION PASS",flush=True)

    def test_distinct_worker_contract_and_independent_budget_readback(self):
        records={BUDGET["dois"][0]:{"doi":BUDGET["dois"][0],"title":"Fixture public bibliography",
                                   "year":2021,"publisher":"Fixture publisher"}}
        def contract(tool,scope,prior):
            if tool=="crossref_metadata":return records
            if tool=="bibliography_readback":
                self.assertEqual(prior["crossref_metadata"],records)
                return {"same_provider_readback_agrees":True,"records":1,
                        "full_paper_or_second_provider_verified":False}
            self.fail("Unknown contract")
        with tempfile.TemporaryDirectory() as tmp,patch("plenum_ai.chief_contract_plan.run_contract",side_effect=contract):
            directory=Path(tmp)
            prior={}
            for role in sm.MISSION_ORDER:
                prior[role]=sm.mission_worker(role,prior,directory,BUDGET)
            self.assertTrue(prior["verification"]["result"]["independent_actual_input_test"])
            self.assertFalse(prior["verification"]["result"]["paid_inference"])
            self.assertEqual(prior["engineering"]["result"]["validation"]["estimate_neurons"],53)
            producers={k:v for k,v in prior.items() if k!="verification"}
            self.assertEqual(sm.verify(producers,directory,functional_test=True,scope=BUDGET),prior["verification"]["result"])
            changed=copy.deepcopy(producers)
            changed["engineering"]["result"]["validation"]["estimate_neurons"]=0
            with self.assertRaises(ValueError):sm.verify(changed,directory,functional_test=True,scope=BUDGET)
        print("DISTINCT BUDGET PROGRAM ACTUAL INPUT AND INDEPENDENT READBACK PASS; provider fixture only",flush=True)

if __name__=="__main__":unittest.main(verbosity=2)

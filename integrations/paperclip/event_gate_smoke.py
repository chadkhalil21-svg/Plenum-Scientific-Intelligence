"""Regression for exact owner scope, one durable reservation and legacy routing."""
import copy
from datetime import datetime, timezone
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch
import event_gate as gate
from plenum_ai import public_issue_wake as wake


class EventGateTests(TestCase):
    def setUp(self):
        self.issue={"number":42,"title":gate.TITLE,"body":gate.BODY,"state":"open",
                    "user":{"login":gate.OWNER},"comments":0,
                    "created_at":"2026-01-01T00:00:00Z"}
        self.comments=[]
        self.writes=0

    def reader(self,url,token,*,body=None):
        if body is not None:
            self.assertEqual(url,gate.BASE+"42/comments")
            self.writes+=1
            self.comments.append({"user":{"login":"github-actions[bot]"},"body":body["body"]})
            self.issue["comments"]=len(self.comments)
            return {"html_url":"https://github.com/example"}
        return copy.deepcopy(self.comments if "/comments?" in url else self.issue)

    def test_issue_open_and_dispatch_share_durable_reservation(self):
        self.assertTrue(gate.reserve(42,"fixture",123,1,reader=self.reader)[0])
        self.assertFalse(gate.reserve(42,"fixture",124,1,reader=self.reader)[0])
        self.assertFalse(gate.reserve(42,"fixture",123,2,reader=self.reader)[0])
        self.assertEqual(self.writes,1)
        print("EVENT SINGLE FLIGHT PASS one reservation, duplicate and retry blocked",flush=True)

    def test_wrong_scope_fails_closed(self):
        for changes in ({"state":"closed"},{"body":"different"},{"user":{"login":"other"}},
                        {"title":"legacy"},{"pull_request":{}},{"number":43}):
            with self.subTest(changes=changes):
                self.assertFalse(gate.authorize(dict(self.issue,**changes),[],42))
        with self.assertRaises(ValueError):
            gate.authorize(dict(self.issue,comments=1),[],42)
        print("OWNER AND EXACT PUBLIC SCOPE PASS",flush=True)

    def test_owner_cannot_forge_bot_receipt(self):
        self.issue["comments"]=1
        self.comments=[{"user":{"login":gate.OWNER},"body":"<!-- plenum-public-workforce-run:123:execution-reserved -->"}]
        self.assertTrue(gate.reserve(42,"fixture",123,1,reader=self.reader)[0])
        self.assertEqual(self.writes,1)

    def test_variable_mission_owner_gate_and_one_reservation(self):
        import json
        from mission_scope import MAGIC, parse_body
        from native_variable import fixture
        scope=fixture("engineering")
        self.issue.update(title=gate.PAPERCLIP_EVIDENCE_TITLE,body=MAGIC+"\n"+json.dumps(scope))
        with self.assertRaises(PermissionError):
            parse_body(self.issue["body"])
        self.assertFalse(gate.authorize(dict(self.issue,user={"login":"other"}),[],42))
        self.assertFalse(gate.authorize(dict(self.issue,state="closed"),[],42))
        self.assertFalse(gate.authorize(dict(self.issue,pull_request={}),[],42))
        allowed,_,actual=gate.reserve(42,"fixture",123,1,reader=self.reader)
        self.assertTrue(allowed)
        self.assertEqual(actual,scope)
        self.assertFalse(gate.reserve(42,"fixture",124,1,reader=self.reader)[0])
        self.assertFalse(gate.reserve(42,"fixture",123,2,reader=self.reader)[0])
        self.assertEqual(self.writes,1)

    def test_invalid_variable_scope_is_denied_before_reservation(self):
        import json
        from mission_scope import MAGIC
        from native_variable import fixture
        scope=fixture("science")
        self.issue["title"]=gate.PAPERCLIP_EVIDENCE_TITLE
        for bad in (dict(scope,selection_commitment="missing"),
                    dict(scope,mission=dict(scope["mission"],objective="Retrieve private credentials now.")),
                    dict(scope,mission=dict(scope["mission"],authorized_inputs={"unreviewed":True}))):
            self.issue["body"]=MAGIC+"\n"+json.dumps(bad)
            self.assertFalse(gate.reserve(42,"fixture",123,1,reader=self.reader)[0])
        self.assertEqual(self.writes,0)

    def test_exact_reviewed_rich_scope_only(self):
        import json
        from mission_scope import MAGIC,parse_body
        from reviewed_public_scopes import scopes
        from composition_contract import accept_choice
        from synthesis_contract import accept_choice as accept_synthesis,index,candidates
        approved=scopes()
        arithmetic=approved["terra-timing"]
        accept_choice(arithmetic,{"narration_minutes":"words/words_per_minute","pause_minutes":"film_minutes-narration_minutes"})
        synthesis=approved["terra-release"]
        opts=candidates(index(synthesis["inputs"]["synthesis"]["documents"]))
        accept_synthesis(synthesis,{k:k in ("extract_scene_1","extract_scene_2","extract_science_2") for k in opts})
        for scope in approved.values():
            self.issue.update(title=gate.PAPERCLIP_EVIDENCE_TITLE,body=MAGIC+"\n"+json.dumps(scope))
            self.assertEqual(gate.issue_scope(self.issue),scope)
            self.assertTrue(gate.authorize(self.issue,[],42))
            self.assertFalse(gate.authorize(dict(self.issue,user={"login":"other"}),[],42))
            for changed in (dict(scope,objective="Different unapproved objective."),
                            dict(scope,result_commitment="0"*64)):
                self.issue["body"]=MAGIC+"\n"+json.dumps(changed)
                self.assertFalse(gate.authorize(self.issue,[],42))
            self.issue["body"]=MAGIC+"\n"+json.dumps(scope)
            with patch("reviewed_public_scopes.source",side_effect=ValueError("changed source")):
                self.assertFalse(gate.authorize(self.issue,[],42))
        from synthesis_smoke import scope as unapproved_synthesis
        from composition_smoke import scope as unapproved_composition
        for scope in (unapproved_synthesis(),unapproved_composition("composition-energy")):
            self.issue["body"]=MAGIC+"\n"+json.dumps(scope)
            self.assertFalse(gate.authorize(self.issue,[],42))
        self.issue["body"]=MAGIC+"\n"+json.dumps(arithmetic)
        self.assertTrue(gate.reserve(42,"fixture",123,1,reader=self.reader)[0])
        self.assertFalse(gate.reserve(42,"fixture",124,1,reader=self.reader)[0])
        self.assertEqual(self.writes,1)
        print("EXACT REVIEWED RICH SCOPE PASS source pins, unchanged owner gate, no arbitrary scopes or replay",flush=True)

    def test_legacy_worker_does_not_execute_native_task(self):
        with patch.object(wake,"_read_original_wake_issue",return_value=(self.issue,[])), patch.object(wake,"run_issue",side_effect=AssertionError("duplicate worker")):
            actual=wake.process(42,"fixture",Path("/unused"))
        self.assertEqual(actual["status"],"ROUTED_TO_NATIVE_PAPERCLIP")
        self.assertFalse(actual["worker_reexecuted"])
        print("LEGACY ROUTE ISOLATION PASS no second worker",flush=True)


if __name__=="__main__":main(verbosity=2)

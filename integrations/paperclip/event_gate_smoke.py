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

    def test_legacy_worker_does_not_execute_native_task(self):
        with patch.object(wake,"_read_original_wake_issue",return_value=(self.issue,[])), patch.object(wake,"run_issue",side_effect=AssertionError("duplicate worker")):
            actual=wake.process(42,"fixture",Path("/unused"))
        self.assertEqual(actual["status"],"ROUTED_TO_NATIVE_PAPERCLIP")
        self.assertFalse(actual["worker_reexecuted"])
        print("LEGACY ROUTE ISOLATION PASS no second worker",flush=True)


if __name__=="__main__":main(verbosity=2)

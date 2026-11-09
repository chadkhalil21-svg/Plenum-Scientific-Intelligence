"""Integration contract between existing owner approvals and browser actions.

No outside network, account, cloud resource, model call or repeated upstream
Playwright validation is involved.
"""
import unittest

from services.computer_browser.approved_action_bridge import (
    UnsupportedOwnerAction, compile_exact_steps, authorize_exact_steps,
)
from services.computer_browser.owner_approval import OwnerApprovalGate


class AtomicTestStore:
    def __init__(self):
        self.used = set()

    def claim(self, *, owner_hash, nonce, expiry):
        key = (owner_hash, nonce)
        if key in self.used:
            return False
        self.used.add(key)
        return True


class ExactOwnerActionTests(unittest.TestCase):
    OWNER = "owner-verified-private-identifier"
    SITE = "https://approved.example.org"

    def setUp(self):
        self.store = AtomicTestStore()
        self.gate = OwnerApprovalGate(key=b"approved-owner-grant-key-material" * 2,
                                      nonce_store=self.store)
        self.plan = {
            "origin": self.SITE,
            "operations": [
                {"op": "fill", "selector": "#note", "value": "Approved note"},
                {"op": "select", "selector": "#category", "value": "physics"},
                {"op": "click", "selector": "#preview"},
                {"op": "upload", "selector": "#document", "file_id": "approved.txt"},
            ],
        }

    def _grant(self, plan=None):
        return self.gate.issue(verified_owner_id=self.OWNER,
                               plan=self.plan if plan is None else plan,
                               now=1_700_000_000, ttl_seconds=90)

    def _authorize(self, plan, token):
        return authorize_exact_steps(gate=self.gate, token=token,
                                     verified_owner_id=self.OWNER, plan=plan,
                                     allowed_origins={self.SITE})

    def test_compiles_one_to_one_without_new_executor_or_agent(self):
        result = compile_exact_steps(self.plan, allowed_origins={self.SITE})
        self.assertEqual(result.origin, self.SITE)
        self.assertEqual([s.operation for s in result.steps],
                         ["fill", "select", "click", "upload"])
        self.assertEqual(result.steps[0].value, "Approved note")
        self.assertEqual(result.steps[-1].file_id, "approved.txt")

    def test_exact_original_grant_is_single_use(self):
        token = self._grant()
        # Test time is fixed to prevent expiry in this historical synthetic unit.
        # Authorizing uses current time, so issue a current-time grant for this test.
        token = self.gate.issue(verified_owner_id=self.OWNER, plan=self.plan)
        result = self._authorize(self.plan, token)
        self.assertEqual(len(result.steps), 4)
        with self.assertRaises(PermissionError):
            self._authorize(self.plan, token)
        self.assertEqual(len(self.store.used), 1)

    def test_wrong_owner_or_plan_fails_before_actions(self):
        token = self.gate.issue(verified_owner_id=self.OWNER, plan=self.plan)
        with self.assertRaises(PermissionError):
            authorize_exact_steps(
                gate=self.gate, token=token,
                verified_owner_id="different-private-owner",
                plan=self.plan, allowed_origins={self.SITE})
        with self.assertRaises(UnsupportedOwnerAction):
            self._authorize(dict(self.plan, origin="https://other.example.org"),
                            token)
        self.assertEqual(len(self.store.used), 0)
        self.assertEqual(len(self._authorize(self.plan, token).steps), 4)

    def test_existing_scorer_allows_future_ops_but_adapter_refuses(self):
        for op in ("navigate", "download", "delete", "submit",
                   "check", "uncheck", "press", "snapshot", "javascript"):
            with self.subTest(op=op):
                plan = {"origin": self.SITE,
                        "operations": [{"op": op, "selector": "#button"}]}
                with self.assertRaises(UnsupportedOwnerAction):
                    compile_exact_steps(plan, allowed_origins={self.SITE})

    def test_rejects_unreviewed_fields_and_unsafe_values(self):
        edits = [
            [{"op": "click", "selector": "#save", "value": "hidden"}],
            [{"op": "fill", "selector": "#note", "value": 42}],
            [{"op": "fill", "selector": "#note", "value": "x" * 4001}],
            [{"op": "upload", "selector": "#file", "file_id": "../secret"}],
            [{"op": "upload", "selector": "#file", "file_id": 12}],
            [{"op": "click", "selector": ""}],
            [],
            [{}],
        ]
        for operations in edits:
            with self.subTest(operations=str(operations)[:35]):
                plan = {"origin": self.SITE, "operations": operations}
                with self.assertRaises(UnsupportedOwnerAction):
                    compile_exact_steps(plan, allowed_origins={self.SITE})

    def test_absent_allowlist_and_unlisted_origin_fail_closed(self):
        for allowed in (None, [], {}, {"https://different.example.org"},
                        "https://approved.example.org"):
            with self.subTest(allowed=str(allowed)):
                with self.assertRaises(UnsupportedOwnerAction):
                    compile_exact_steps(self.plan, allowed_origins=allowed)


if __name__ == "__main__":
    unittest.main()

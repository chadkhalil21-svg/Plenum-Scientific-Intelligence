"""Pure-stdlib checks of owner-bound single-use browser action approval policy.

No website, Cloud account, secret, session or deployment is accessed.
"""
import unittest

from services.computer_browser.owner_approval import (
    OwnerApprovalGate, ApprovalRejected, MAX_TTL_SECONDS,
)


class InMemoryAtomicTestStore:
    """Fake persistence: tests only, never use in a production browser."""

    def __init__(self):
        self.used = set()

    def claim(self, *, owner_hash, nonce, expiry):
        key = (owner_hash, nonce)
        if key in self.used:
            return False
        self.used.add(key)
        return True


class BrowserOwnerApprovalTests(unittest.TestCase):
    def setUp(self):
        self.plan = {
            "origin": "https://staging.example.org",
            "operations": [
                {"op": "fill", "selector": "#first-name", "value": "Test"},
                {"op": "submit", "selector": "#save"},
            ],
        }
        self.store = InMemoryAtomicTestStore()
        self.gate = OwnerApprovalGate(key=b"k" * 32, nonce_store=self.store)

    def test_exact_grant_consumed_only_once(self):
        signed = self.gate.issue(
            verified_owner_id="private-owner-identifier", plan=self.plan,
            now=1700000000, ttl_seconds=90,
        )
        self.assertTrue(self.gate.consume(
            token=signed, verified_owner_id="private-owner-identifier",
            plan=self.plan, now=1700000001))
        with self.assertRaises(ApprovalRejected):
            self.gate.consume(
                token=signed, verified_owner_id="private-owner-identifier",
                plan=self.plan, now=1700000002)
        self.assertEqual(len(self.store.used), 1)

    def test_wrong_owner_and_changed_plan_fail_without_burning_grant(self):
        signed = self.gate.issue(
            verified_owner_id="private-owner-identifier", plan=self.plan, now=1700000000)
        for owner, plan in [
            ("another-verified-owner", self.plan),
            ("private-owner-identifier", {
                "origin": self.plan["origin"],
                "operations": [
                    {"op": "fill", "selector": "#first-name", "value": "Altered"},
                    {"op": "submit", "selector": "#save"},
                ],
            }),
            ("private-owner-identifier", {
                "origin": "https://different.example.org",
                "operations": self.plan["operations"],
            }),
        ]:
            with self.subTest(owner=owner, plan=plan):
                with self.assertRaises(ApprovalRejected):
                    self.gate.consume(
                        token=signed, verified_owner_id=owner,
                        plan=plan, now=1700000001)
        self.assertEqual(len(self.store.used), 0)
        self.assertTrue(self.gate.consume(
            token=signed, verified_owner_id="private-owner-identifier",
            plan=self.plan, now=1700000001))

    def test_tampering_expiry_and_future_claims_fail_closed(self):
        token = self.gate.issue(
            verified_owner_id="private-owner-identifier", plan=self.plan,
            now=1700000000, ttl_seconds=30)
        with self.assertRaises(ApprovalRejected):
            self.gate.consume(
                token=token[:-1] + ("A" if token[-1] != "A" else "B"),
                verified_owner_id="private-owner-identifier",
                plan=self.plan, now=1700000001)
        with self.assertRaises(ApprovalRejected):
            self.gate.consume(
                token=token, verified_owner_id="private-owner-identifier",
                plan=self.plan, now=1700000030)
        with self.assertRaises(ApprovalRejected):
            self.gate.consume(
                token=token, verified_owner_id="private-owner-identifier",
                plan=self.plan, now=1699999990)
        self.assertEqual(len(self.store.used), 0)

    def test_bad_origin_and_unsafe_plans_never_issued(self):
        for origin in (
            "http://staging.example.org",
            "https://staging.example.org:8443",
            "https://user:pass@staging.example.org",
            "https://127.0.0.1",
            "https://localhost",
            "https://staging.example.org/private",
            "https://staging.example.org?token=x",
            "https://staging.example.org#top",
            "https://staging.example.org\n",
        ):
            with self.subTest(origin=origin):
                plan = dict(self.plan, origin=origin)
                with self.assertRaises(ApprovalRejected):
                    self.gate.issue(
                        verified_owner_id="private-owner-identifier", plan=plan, now=1700000000)
        for operations in ([], [{"op": "eval_js", "code": "alert(1)"}], [{}]):
            with self.subTest(operations=operations):
                plan = dict(self.plan, operations=operations)
                with self.assertRaises(ApprovalRejected):
                    self.gate.issue(
                        verified_owner_id="private-owner-identifier", plan=plan, now=1700000000)

    def test_hard_max_expiry_and_missing_crypto(self):
        with self.assertRaises(ValueError):
            OwnerApprovalGate(key=b"short", nonce_store=self.store)
        with self.assertRaises(ValueError):
            OwnerApprovalGate(key=b"k" * 32, nonce_store=None)
        for ttl in (0, 601, True, 1.5):
            with self.subTest(ttl=ttl):
                with self.assertRaises(ApprovalRejected):
                    self.gate.issue(
                        verified_owner_id="private-owner-identifier", plan=self.plan,
                        ttl_seconds=ttl, now=1700000000)
        self.assertLessEqual(MAX_TTL_SECONDS, 600)

    def test_unavailable_durable_store_fails_closed(self):
        class UnavailableStore:
            def claim(self, **kwargs):
                return False
        gate = OwnerApprovalGate(key=b"k" * 32, nonce_store=UnavailableStore())
        token = gate.issue(
            verified_owner_id="private-owner-identifier", plan=self.plan, now=1700000000)
        with self.assertRaises(ApprovalRejected):
            gate.consume(
                token=token, verified_owner_id="private-owner-identifier",
                plan=self.plan, now=1700000001)

    def test_json_serialization_order_not_significant_but_values_are(self):
        token = self.gate.issue(
            verified_owner_id="private-owner-identifier", plan=self.plan, now=1700000000)
        reversed_plan = {
            "operations": [
                {"selector": "#first-name", "value": "Test", "op": "fill"},
                {"selector": "#save", "op": "submit"},
            ],
            "origin": self.plan["origin"],
        }
        self.assertTrue(self.gate.consume(
            token=token, verified_owner_id="private-owner-identifier",
            plan=reversed_plan, now=1700000001))


if __name__ == "__main__":
    unittest.main()

"""Offline checks: bounded recovery, double readback, no account mutation."""
import unittest
from plenum_ai.business_public_watch import TARGETS, NoRedirects, inspect_target, run

class BusinessPublicWatchTests(unittest.TestCase):
    def test_targets_are_exact_public_https(self):
        self.assertEqual(len(TARGETS), 3)
        for target in TARGETS:
            self.assertTrue(target.url.startswith("https://american-rider-"))
            self.assertIn(".onrender.com/", target.url)

    def test_two_fresh_reads_required(self):
        calls = []
        def good(target):
            calls.append(target.name)
            return True, "verified_read", 200
        result = inspect_target(TARGETS[0], probe_fn=good, sleep_fn=lambda _: None)
        self.assertEqual(result["status"], "PUBLIC_HTTP_VERIFIED")
        self.assertEqual(calls, ["corporate", "corporate"])
        self.assertEqual(result["independent_gets"], 2)

    def test_transient_failure_retries_once_then_succeeds(self):
        values = iter([(False, "network_unverified", None),
                       (True, "verified_read", 200), (True, "verified_read", 200)])
        pauses = []
        result = inspect_target(TARGETS[0], probe_fn=lambda _: next(values), sleep_fn=pauses.append)
        self.assertEqual(result["status"], "PUBLIC_HTTP_VERIFIED")
        self.assertEqual(result["attempts"], 3)
        self.assertEqual(pauses, [1])

    def test_bounded_failure_never_marks_healthy(self):
        values = []
        def broken(target):
            values.append(target.name)
            return False, "network_unverified", None
        result = inspect_target(TARGETS[1], probe_fn=broken, sleep_fn=lambda _: None)
        self.assertEqual(result["status"], "UNVERIFIED")
        self.assertEqual(result["phase"], "initial")
        self.assertEqual(len(values), 3)
        self.assertFalse(result["external_actions_executed"])

    def test_second_readback_failure_not_misreported(self):
        values = iter([(True, "verified_read", 200)] + [(False, "network_unverified", None)] * 3)
        result = inspect_target(TARGETS[0], probe_fn=lambda _: next(values),
                                sleep_fn=lambda _: None)
        self.assertEqual(result["status"], "UNVERIFIED")
        self.assertEqual(result["phase"], "readback")

    def test_report_does_not_claim_customer_transaction(self):
        result = run(probe_fn=lambda _: (True, "verified_read", 200), sleep_fn=lambda _: None)
        self.assertEqual(result["verified"], 3)
        self.assertEqual(result["total"], 3)
        self.assertFalse(result["asserts_commercial_readiness"])
        self.assertFalse(result["asserts_transaction_success"])
        self.assertFalse(result["requires_production_credentials"])

    def test_redirects_are_not_followed(self):
        self.assertIsNone(NoRedirects().redirect_request(None, None, 302, "", {}, "http://private/"))

if __name__ == "__main__":
    unittest.main()

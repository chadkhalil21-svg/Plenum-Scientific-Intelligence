import unittest
from plenum_ai.business_public_watch import run, TARGETS, Target
class TargetSelection(unittest.TestCase):
    def test_reject_before_any_probe(self):
        for targets in ((), (TARGETS[0], TARGETS[0]), (TARGETS[0], Target("other","https://example.org","html"))):
            with self.subTest(targets=targets):
                calls=[]
                with self.assertRaises(ValueError):
                    run(probe_fn=lambda t: calls.append(t) or (True,"verified_read",200),sleep_fn=lambda _:None,targets=targets)
                self.assertEqual(calls,[])
    def test_valid_subset(self):
        calls=[]
        result=run(probe_fn=lambda t: calls.append(t) or (True,"verified_read",200),sleep_fn=lambda _:None,targets=(TARGETS[1],))
        self.assertEqual(calls,[TARGETS[1],TARGETS[1]])
        self.assertEqual((result["verified"],result["total"]),(1,1))
        self.assertFalse(result["asserts_commercial_readiness"])
    def test_unauthorized_diagnostic_is_bounded(self):
        for invalid in (Target("untrusted\nname","https://example.org","html"), None):
            with self.subTest(invalid=invalid):
                calls=[]
                with self.assertRaisesRegex(ValueError, "^Unauthorized target selection$"):
                    run(probe_fn=lambda t: calls.append(t),sleep_fn=lambda _:None,targets=(TARGETS[0],invalid))
                self.assertEqual(calls,[])

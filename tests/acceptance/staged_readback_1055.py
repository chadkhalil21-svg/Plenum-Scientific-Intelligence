"""Independent held-out acceptance for issue 1055. No real HTTP."""
import unittest
from plenum_ai.business_public_watch import TARGETS, Target, inspect_target

class StagedReadbackAcceptance(unittest.TestCase):
    def test_invalid_bounds_and_target_never_call_callbacks(self):
        calls=[]
        def probe(target):
            calls.append(target)
            return True,"verified_read",200
        for count in (True,False,1.0,2.0,3.0,"2",None,0,4,-1):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):
                    inspect_target(TARGETS[0],probe_fn=probe,sleep_fn=calls.append,max_attempts=count)
        with self.assertRaises(ValueError):
            inspect_target(Target("unknown","https://example.invalid/","html"),probe_fn=probe,sleep_fn=calls.append)
        self.assertEqual(calls,[])
    def test_valid_bounds_preserve_two_fresh_reads_and_retry(self):
        for count in (1,2,3):
            with self.subTest(count=count):
                calls=[]
                def good(target):
                    calls.append(target)
                    return True,"verified_read",200
                result=inspect_target(TARGETS[0],probe_fn=good,sleep_fn=lambda _: self.fail("unexpected retry"),max_attempts=count)
                self.assertEqual(calls,[TARGETS[0],TARGETS[0]])
                self.assertEqual(result["status"],"PUBLIC_HTTP_VERIFIED")
                self.assertEqual(result["independent_gets"],2)
                self.assertEqual(result["attempts"],2)
        calls=[]
        def bad(target):
            calls.append(target)
            return False,"network_unverified",None
        result=inspect_target(TARGETS[1],probe_fn=bad,sleep_fn=lambda _: None,max_attempts=2)
        self.assertEqual(len(calls),2)
        self.assertEqual(result["status"],"UNVERIFIED")

if __name__=="__main__":
    unittest.main()

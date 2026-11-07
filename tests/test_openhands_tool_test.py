"""The normal Plenum test suite must not need optional OpenHands or model calls."""
import unittest
from unittest.mock import patch
from plenum_ai import openhands_tool_test as t

class OpenHandsFunctionalPlan(unittest.TestCase):
    def test_off_by_default(self):
        p=t.plan()
        self.assertEqual(p["sdk_version"],"1.60.1")
        self.assertEqual(p["inference_calls"],0)
        self.assertEqual(p["external_api_calls"],0)
        for field in ("tool_execution_verified","unauthorized_write_blocked",
                      "generated_code_executed","agent_executed",
                      "AGI_demonstrated","private_data_used"):
            self.assertFalse(p[field])

    def test_reviewed_fixture_contains_both_states(self):
        self.assertIn("return x + x",t.START)
        self.assertIn("return x * x",t.FIXED)
        self.assertNotEqual(t.START,t.FIXED)

    def test_altered_version_fails_closed(self):
        with patch("importlib.metadata.version",return_value="wrong"):
            with self.assertRaisesRegex(RuntimeError,"not reviewed"):
                t.run()

    def test_network_disabled(self):
        with self.assertRaisesRegex(RuntimeError,"network forbidden"):
            t._no_network()

if __name__=="__main__":
    unittest.main()

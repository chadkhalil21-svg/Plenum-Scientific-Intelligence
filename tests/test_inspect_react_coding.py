"""Verify reuse of official Inspect ReAct and strict no-inference default."""
import unittest
from types import SimpleNamespace

try:
    from plenum_ai import inspect_react_coding as a
except ModuleNotFoundError:
    a=None


@unittest.skipUnless(a is not None,"Optional upstream Inspect Evals not installed")
class OriginalReactCodingTests(unittest.TestCase):
    def test_public_dataset_scoring_and_bounded_agent(self):
        p=a.plan()
        self.assertEqual(p["upstream_agent"],"Inspect AI react()")
        self.assertIn("inspect_evals/humaneval",p["upstream_scoring"])
        self.assertEqual(p["sample_count"],1)
        self.assertEqual(p["max_messages"],14)
        self.assertEqual(p["max_turns"],6)
        self.assertEqual(p["tool_timeout_seconds"],20)
        self.assertEqual(p["sandbox"],"docker")
        self.assertEqual(p["candidate_revision"],
                         "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e")
        self.assertEqual(p["paid_api_calls"],0)
        for flag in ("inference_executed","official_functional_test_scored",
                     "agent_loop_verified","AGI_demonstrated","automated_deployment"):
            self.assertFalse(p[flag])

    def test_tool_calls_and_returns_are_independently_counted(self):
        msgs=[
            SimpleNamespace(role="user",tool_calls=None),
            SimpleNamespace(role="assistant",tool_calls=["a","b"]),
            SimpleNamespace(role="tool"),
            SimpleNamespace(role="assistant",tool_calls=[]),
        ]
        self.assertEqual(a.count_actual_tools(msgs),(2,1))
        with self.assertRaisesRegex(ValueError,"Unpaired"):
            a.count_actual_tools([SimpleNamespace(role="tool")])

    def test_no_model_or_sandbox_without_explicit_original_log(self):
        with self.assertRaises(ValueError):
            a.audit("other/logs")
            
if __name__=="__main__":
    unittest.main()

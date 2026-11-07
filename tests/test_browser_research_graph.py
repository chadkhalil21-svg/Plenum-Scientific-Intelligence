"""Real graph structure and model authority boundary: no network in unit tests."""
import unittest
from unittest.mock import patch
from plenum_ai.browser_research_graph import (
    URL, build_graph, browser_node, fixed_plan, run_public_graph,
    verify_node, call_real_mcp,
)

GOOD = {"schema":"plenum-playwright-mcp-public-readonly-v1",
        "public_page":"https://example.com/",
        "mcp_protocol_roundtrip_succeeded":True,
        "accessibility_snapshot_has_example_domain":True,
        "site_mutation_performed":False,
        "authenticated_browser_session_used":False,
        "AGI_demonstrated":False}

class BrowserGraphTests(unittest.TestCase):
    def test_fixed_plan_rejects_nonapproved_tasks(self):
        with self.assertRaises(PermissionError):
            fixed_plan({"request":"Log into my email and send a message"})
        with self.assertRaises(PermissionError):
            browser_node({"allowed_url":"https://evil.test/"})

    def test_verifier_rejects_claims_and_failures(self):
        s={"observation":GOOD, "planned_operation":"read-only public MCP navigation+snapshot"}
        self.assertTrue(verify_node(s)["verified"])
        for patch_value in ({"site_mutation_performed":True},
                            {"AGI_demonstrated":True},
                            {"public_page":"https://evil.example"},
                            {"mcp_protocol_roundtrip_succeeded":False}):
            bad={**GOOD,**patch_value}
            with self.assertRaises(RuntimeError):
                verify_node({**s,"observation":bad})

    def test_langgraph_reuses_real_graph_without_browser_in_unit_test(self):
        with patch("plenum_ai.browser_research_graph.call_real_mcp",return_value=GOOD) as invoked:
            result=run_public_graph()
        invoked.assert_called_once_with()
        self.assertTrue(result["fixed_workflow_verified"])
        self.assertFalse(result["model_selected_browser_actions"])
        self.assertFalse(result["AGI_demonstrated"])

    def test_no_arbitrary_credentials_passed_to_child(self):
        from unittest.mock import Mock
        mock=Mock(returncode=0,stdout=__import__("json").dumps(GOOD),stderr="")
        with patch.dict("os.environ",{"PATH":"/usr/bin","HOME":"/tmp",
                                      "KAGGLE_API_TOKEN":"SECRET","STRIPE_SECRET_KEY":"SECRET"},clear=True):
            with patch("plenum_ai.browser_research_graph.subprocess.run",return_value=mock) as call:
                report=call_real_mcp()
        self.assertEqual(report,GOOD)
        args=call.call_args.kwargs
        self.assertNotIn("KAGGLE_API_TOKEN",args["env"])
        self.assertNotIn("STRIPE_SECRET_KEY",args["env"])
        self.assertFalse(args.get("shell",False))

if __name__=="__main__":
    unittest.main()

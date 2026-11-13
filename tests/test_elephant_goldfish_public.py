"""Elephant public durable facts and Goldfish independent fresh-critic boundary."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from plenum_ai import agent_council as c

class ElephantGoldfishTests(TestCase):
    def test_only_reviewed_public_facts_load(self):
        src=c.read_elephant_public()
        self.assertIn("PLENUM",str(c.ELEPHANT_PUBLIC_FILE).upper())
        self.assertIn("VERIFIED_BOUNDED",src)
        self.assertIn("five",src.lower())
        self.assertNotIn("founder email password",src.lower())

    def test_unreviewed_or_private_elephant_facts_rejected(self):
        with TemporaryDirectory() as p:
            f=Path(p)/"bad.json"
            data=json.loads(c.ELEPHANT_PUBLIC_FILE.read_text())
            data["records"][0]["url"]="https://untrusted.example/secret"
            f.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                c.read_elephant_public(f)

    def test_google_actual_upstream_v011_is_pinned_and_not_a_fake_persona(self):
        original = c.read_real_google_egm_design_critic()
        self.assertIn("name: egm-design", original)
        self.assertIn("Design Critic Goldfish", original)
        self.assertIn("Apache-2.0", original)
        self.assertTrue((c.EGM_PERSONA.parent.parent / "LICENSE").is_file())
        self.assertEqual(
            c.EGM_GIT_BLOB_SHA,
            "7f57159d623f898a8e683a5b7f312e8f11f84321",
        )
        with TemporaryDirectory() as folder:
            edited = Path(folder) / "design_critic.md"
            edited.write_text(original + "\nUntrusted additions", encoding="utf-8")
            with self.assertRaises(ValueError):
                c.read_real_google_egm_design_critic(edited)
        # Separate cached persona exists but the FULL 5-stage upstream
        # multi-agent workflow has NOT been activated or claimed.
        self.assertFalse(hasattr(c, "egm_five_stage_pipeline_running"))

    def test_goldfish_does_not_inherit_elephant_as_prior_authority(self):
        event={"action":"opened","repository":{"full_name":c.REPO},"issue":{
            "number":988,"title":c.TITLE,"user":{"login":c.FOUNDER},
            "body":c.MARKER+"\nobjective: Review a public workflow choice with independent experts"}}
        calls=[]
        def fake(system,user):
            calls.append((system,user))
            return "Independent issue evaluation. Compare free alternatives and confirm actual evidence."
        with patch.dict("os.environ",{
            "PLENUM_EPHEMERAL_RUNNER":"confirmed",
            "PLENUM_COUNCIL_MODEL_URL":c.MODEL_URL
        }),patch.object(c,"_ask_local",side_effect=fake):
            report=c.deliberate(event)
        self.assertTrue(report["elephant_public_facts_used"])
        self.assertFalse(report["goldfish_received_elephant_history"])
        self.assertEqual(len(calls),5)
        self.assertTrue(all("DATED PUBLIC ELEPHANT" in x[0] for x in calls[:4]))
        self.assertNotIn("DATED PUBLIC ELEPHANT",calls[4][0])
        self.assertIn("Goldfish Reviewer",calls[4][0])
        self.assertIn("Design Critic Goldfish", calls[4][0])
        self.assertIn("Strict Read-Only Protocol", calls[4][0])
        self.assertIn("Google EGM v0.1.1", calls[4][0])
        self.assertFalse(d["tasks_executed"])

if __name__=="__main__":
    import unittest
    unittest.main()

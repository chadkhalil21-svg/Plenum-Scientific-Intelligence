"""Focus tests: catalog is dormant; council is not a simulated meeting."""
import json
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from plenum_ai import agent_council as c

ROOT=Path(__file__).resolve().parents[1]


def event(objective="Evaluate free AI agent catalog governance", author=c.FOUNDER):
    return {"action":"opened","repository":{"full_name":c.REPO},"issue":{
        "number":984,"title":c.TITLE,"user":{"login":author},
        "body":c.MARKER+"\nobjective: "+objective}}


class CouncilContract(TestCase):
    def test_exact_owner_public_only(self):
        self.assertEqual(c.parse_event(event())["issue"],984)
        for issue in [
            event(author="untrusted"),
            event(objective="Send confidential patent credentials"),
            event(objective="Connect private customer account"),
            event(objective="x"),
            event(objective="Review public research\nhijack"),
        ]:
            with self.assertRaises((ValueError,PermissionError)):
                c.parse_event(issue)

    def test_catalogue_is_full_immutable_idle_inventory(self):
        p=ROOT/"integrations/agent-catalog/agency-agents.index.json"
        d=json.loads(p.read_text())
        self.assertEqual(d["count"],283)
        self.assertEqual(len(d["profiles"]),283)
        self.assertEqual(len({x["path"] for x in d["profiles"]}),283)
        self.assertEqual(len({x["division"] for x in d["profiles"]}),18)
        self.assertEqual(d["source"]["license"],"MIT")
        self.assertEqual(len(d["source"]["commit"]),40)
        self.assertTrue(all(x["status"]=="catalogued_idle" for x in d["profiles"]))
        self.assertTrue(all(x["activation"]=="manual_owner_task_only" for x in d["profiles"]))

    def test_no_real_person_impersonation_and_fresh_critic(self):
        self.assertEqual(len(c.SEATS),4)
        with patch.dict("os.environ",{
            "PLENUM_EPHEMERAL_RUNNER":"confirmed",
            "PLENUM_COUNCIL_MODEL_URL":c.MODEL_URL,
        }):
            calls=[]
            def fake(system,user):
                calls.append((system,user))
                return "Suggested reversible experiment with measurable outcome and uncertain evidence"
            with patch.object(c,"_ask_local",side_effect=fake):
                d=c.deliberate(event())
        self.assertEqual(len(calls),5)
        self.assertEqual(d["seats_completed"],4)
        self.assertTrue(d["review_completed"])
        self.assertFalse(d["next_steps_approved"])
        self.assertFalse(d["sources_independently_checked"])
        self.assertFalse(d["independent_counsel_or_advisors_contacted"])
        self.assertTrue(all("PUBLIC founder agenda" in user for _,user in calls))
        self.assertIn("fresh-context",calls[4][0])
        self.assertEqual(calls[0][1],calls[3][1])
        self.assertGreater(len(calls[4][1]),len(calls[0][1]))

    def test_no_runner_no_paid_remote_model(self):
        with patch.dict("os.environ",{
            "PLENUM_EPHEMERAL_RUNNER":"",
            "PLENUM_COUNCIL_MODEL_URL":"https://some-host.invalid/api/chat",
        }):
            with self.assertRaises(PermissionError):
                c.deliberate(event())
        self.assertEqual(c.MODEL_URL,"http://127.0.0.1:11434/api/chat")


if __name__=="__main__":
    import unittest
    unittest.main()

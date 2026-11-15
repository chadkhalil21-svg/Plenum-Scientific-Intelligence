"""Focused new acceptance for the founder-driven public task bridge; not old model tests."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from plenum_ai import workforce_public_inbox as w

OBJECTIVE="Review free open source AI agents and their security safeguards"

def event(user=w.OWNER, title=w.TITLE, body=None):
    return {
        "action": "opened", "repository": {"full_name":w.REPO},
        "issue":{"number":876,"user":{"login":user},"title":title,
                 "body": body or w.MAGIC+"\nobjective: "+OBJECTIVE}
    }

class FakeRun:
    returncode=0

class IntakeTests(unittest.TestCase):
    def test_real_founder_objective_maps_to_existing_worker(self):
        task=w.parse_public_issue(event())
        self.assertEqual(task["worker"],"existing_plenum_world_horizon")
        self.assertEqual(task["cost_ceiling_usd"],0)

    def test_untrusted_issue_or_private_task_fails_before_execution(self):
        for sample in (
            event(user="malicious-user"), event(title="My private task"),
            event(body=w.MAGIC+"\nobjective: Password file and tokens from inbox"),
            event(body=w.MAGIC+"\nobjective: Too short"),
            {**event(), "action":"edited"},
            {**event(),"repository":{"full_name":"other/repository"}},
        ):
            with self.subTest(sample=sample),self.assertRaises(ValueError):
                w.parse_public_issue(sample)

    def test_reuses_original_worker_and_removes_host_tokens(self):
        calls=[]
        with tempfile.TemporaryDirectory() as folder:
            def fake_runner(cmd, **kw):
                calls.append((cmd,kw))
                assert "GH_TOKEN" not in kw["env"]
                assert not any(k.endswith("_API_KEY") for k in kw["env"])
                Path(cmd[-1]).write_text(json.dumps({
                    "schema":"plenum-public-horizon-snapshot-v1",
                    "topic":OBJECTIVE,
                    "independent_breakthrough_verified":False,
                    "AGI_achieved":False,
                    "records":[{
                        "url":"https://research.example.org/public",
                        "source":"institution",
                        "title":"Public research news"}]
                }),encoding="utf-8")
                return FakeRun()
            with patch.dict("os.environ",{"GH_TOKEN":"private", "THIRD_API_KEY":"private"}):
                result=w.run_issue(event(),output_dir=Path(folder),runner=fake_runner)
            self.assertEqual(result["status"],"DRAFT_READY_FOR_FOUNDER")
            self.assertEqual(result["source_linked_records"],1)
            self.assertFalse(result["individual_papers_independently_validated"])
            self.assertFalse(result["business_accounts_touched"])
            self.assertEqual(calls[0][0][3],"world-horizon")
            self.assertNotIn("shell",calls[0][1])

    def test_actual_grant_request_reuses_original_funding_feed_and_blocks_unrelated_88_lead_result(self):
        objective = "Find current NSF funding leads for photonic concrete infrastructure sensing research"
        owner_event = event(body=w.MAGIC + "\nobjective: " + objective)
        self.assertEqual(w.original_source_category(objective), "funding")
        self.assertEqual(w.original_source_category(OBJECTIVE), "all")
        seen = []
        with tempfile.TemporaryDirectory() as folder:
            def old_broad_result(cmd, **kwargs):
                seen.append(cmd)
                Path(cmd[-1]).write_text(json.dumps({
                    "schema": "plenum-public-horizon-snapshot-v1", "topic": objective,
                    "category": "all", "independent_breakthrough_verified": False,
                    "AGI_achieved": False,
                    "records": [{"url": "https://news.example.org/music",
                                 "category": "music", "source": "institution",
                                 "title": "Unrelated music research"}]
                }), encoding="utf-8")
                return FakeRun()
            wrong = w.run_issue(owner_event, output_dir=Path(folder), runner=old_broad_result)
            self.assertEqual(wrong["status"], "BLOCKED_VERIFICATION")
            self.assertFalse(wrong["verified"])
        self.assertEqual(seen[0][seen[0].index("--category") + 1], "funding")
        with tempfile.TemporaryDirectory() as folder:
            def original_funding_result(cmd, **kwargs):
                Path(cmd[-1]).write_text(json.dumps({
                    "schema": "plenum-public-horizon-snapshot-v1", "topic": objective,
                    "category": "funding", "independent_breakthrough_verified": False,
                    "AGI_achieved": False,
                    "records": [{"url": "https://www.nsf.gov/funding/opportunities/mri-major-research-instrumentation-program/nsf27-500/solicitation",
                                 "category": "funding", "source": "nsf_open_funding",
                                 "title": "Major Research Instrumentation Program"}]
                }), encoding="utf-8")
                return FakeRun()
            actual = w.run_issue(owner_event, output_dir=Path(folder), runner=original_funding_result)
            # Actual original #708 proved a valid NSF funding category does
            # not imply fit with photonic concrete infrastructure sensing.
            self.assertEqual(actual["status"], "REVIEW_REQUIRED_FUNDING_SUBJECT_RELEVANCE")
            self.assertFalse(actual["verified"])
            self.assertEqual(actual["source_linked_records"], 1)
            self.assertEqual(actual["quality"], "FUNDING_CATEGORY_ONLY_SUBJECT_REVIEW_REQUIRED")
            self.assertFalse(actual["funding_subject_relevance_independently_verified"])
            self.assertIn("eligibility remain unverified", actual["reason"])
            self.assertFalse(actual["individual_papers_independently_validated"])
            self.assertFalse(actual["scientific_discovery_verified"])

    def test_fails_closed_if_worker_output_missing_or_wrong(self):
        with tempfile.TemporaryDirectory() as folder:
            result=w.run_issue(event(),output_dir=Path(folder),
                               runner=lambda *args,**kw:FakeRun())
            self.assertEqual(result["status"],"BLOCKED_VERIFICATION")
            self.assertFalse(result["verified"])

    def test_report_schema_cannot_falsely_claim_discovery(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"out.json"
            p.write_text(json.dumps({
                "schema":"plenum-public-horizon-snapshot-v1",
                "topic":OBJECTIVE, "independent_breakthrough_verified":True,
                "AGI_achieved":False,"records":[]
            }))
            with self.assertRaises(ValueError):
                w.validate_original_report(p,OBJECTIVE)

if __name__=="__main__":
    unittest.main()

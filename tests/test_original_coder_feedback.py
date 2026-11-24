"""Exercise trusted feedback reservation and immutable first-attempt retention."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("trusted_coding_verifier", ROOT / "tools/verify_original_openhands_candidate.py")
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
from plenum_ai import openhands_coding_agent as coder

class TrustedRecoveryTests(unittest.TestCase):
    def test_only_original_failed_task_can_receive_one_corrective_attempt(self):
        source = "src/plenum_ai/business_public_watch.py"
        task = next(t for s,t in v.TASK_ACCEPTANCE if s==source)
        original = (ROOT / source).read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            previous = Path.cwd()
            try:
                os.chdir(tmp)
                Path(source).parent.mkdir(parents=True)
                Path(source).write_bytes(original)
                report = Path("reports/openhands-agent-review.json")
                verdict = Path("reports/openhands-sandbox-verdict.json")
                candidate = Path("reports/openhands-review/issue-123.patch")
                candidate.parent.mkdir(parents=True)
                candidate.write_bytes(b"first rejected candidate")
                digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
                event = Path(tmp)/"event.json"
                event.write_text(json.dumps({"action":"opened","repository":{"full_name":coder.REPO},
                    "issue":{"number":123,"user":{"login":coder.OWNER},"title":coder.REPAIR_TITLE,
                    "body":coder.LOCAL_REPAIR_MARKER+"\nfile: "+source+"\nobjective: "+task}}))
                original_report = {**coder.local_plan(task,source_file=source),
                    "status":"PROPOSAL_AWAITING_REVIEW","repair_passes":0,
                    "candidate_artifact":candidate.as_posix(),"candidate_artifact_sha256":digest}
                original_verdict = {"status":"BLOCKED_TASK_ACCEPTANCE","task_acceptance_passed":False,
                    "existing_focused_tests_passed":True,"network_disabled_for_candidate":True,
                    "source_file":source,"task_acceptance_test":"tests/acceptance/"+v.TASK_ACCEPTANCE[(source,task)],
                    "candidate_artifact_sha256":digest}
                report.write_text(json.dumps(original_report))
                verdict.write_text(json.dumps(original_verdict))
                env={"GITHUB_ACTIONS":"true","GITHUB_EVENT_NAME":"issues","GITHUB_REPOSITORY":coder.REPO,
                     "GITHUB_RUN_ATTEMPT":"1","GITHUB_RUN_ID":"123456",
                     "PLENUM_EPHEMERAL_RUNNER":"confirmed","PLENUM_ORIGINAL_CODING_RESERVED":"true",
                     "GITHUB_EVENT_PATH":str(event)}
                def corrected(*args,**kwargs):
                    self.assertTrue(kwargs["behavioral_recovery"])
                    self.assertEqual(args[0],task)
                    self.assertEqual((candidate.parent/"first-attempt"/candidate.name).read_bytes(),b"first rejected candidate")
                    candidate.write_bytes(b"second review-only candidate")
                    return {**original_report,"repair_passes":1}
                with patch.dict(os.environ,env),patch.object(coder,"execute_local",side_effect=corrected) as run,patch.object(v,"verify",return_value={"status":"REVIEW_ONLY_TEST_FIXTURE"}) as verify:
                    with patch.dict(os.environ,{"PLENUM_ORIGINAL_CODING_RESERVED":"false"}):
                        self.assertEqual(v.recover_local_behavior(report,verdict,event),original_verdict)
                        run.assert_not_called()
                    verdict.write_text(json.dumps({**original_verdict,"candidate_artifact_sha256":"0"*64}))
                    v.recover_local_behavior(report,verdict,event)
                    run.assert_not_called()
                    verdict.write_text(json.dumps(original_verdict))
                    result=v.recover_local_behavior(report,verdict,event)
                    self.assertEqual(result["status"],"REVIEW_ONLY_TEST_FIXTURE")
                    self.assertEqual(run.call_count,1)
                    self.assertEqual(verify.call_count,1)
                    saved=candidate.parent/"first-attempt"
                    self.assertEqual(json.loads((saved/verdict.name).read_text()),original_verdict)
                    self.assertEqual(json.loads((saved/report.name).read_text()),original_report)
                    self.assertEqual(json.loads((saved/"reservation.json").read_text())["original_patch_sha256"],digest)
                    verdict.write_text(json.dumps(original_verdict))
                    v.recover_local_behavior(report,verdict,event)
                    self.assertEqual(run.call_count,1)
            finally:
                os.chdir(previous)

if __name__=="__main__":
    unittest.main()

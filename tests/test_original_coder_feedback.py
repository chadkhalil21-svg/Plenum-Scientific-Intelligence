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
        task = next(t for s,t in v.TASK_ACCEPTANCE if s==source and v.TASK_ACCEPTANCE[(s,t)]=="health_body_limit.py")
        self._assert_single_recovery(source, task)

    def test_single_trusted_registry_preserves_recovery_boundaries(self):
        self.assertIs(v.TASK_ACCEPTANCE, coder.TASK_ACCEPTANCE)
        for (source, task), test in v.TASK_ACCEPTANCE.items():
            eligible = task.startswith("Repair function ") and " Then repair function " not in task
            self.assertEqual((source, task) in coder.STRUCTURED_RECOVERY_TASKS, eligible)
            self.assertNotIn((source, task + " Extra."), coder.STRUCTURED_RECOVERY_TASKS)
            self.assertTrue((ROOT / "tests" / "acceptance" / test).is_file())
        self.assertIn("checkpoint_exact_issue_identity.py", coder.STRUCTURED_RECOVERY_TASKS.values())

    def test_registered_structured_task_preserves_first_evidence(self):
        for (source, task), test in coder.STRUCTURED_RECOVERY_TASKS.items():
            with self.subTest(source=source):
                self.assertEqual(v.TASK_ACCEPTANCE[(source, task)], test)
                self._assert_single_recovery(source, task)

    def test_confirmed_regression_preserves_first_evidence(self):
        for source, task in coder.STRUCTURED_RECOVERY_TASKS:
            with self.subTest(source=source):
                self._assert_single_recovery(source, task, regression=True)

    def test_completed_unittest_diagnostic_rejects_infrastructure_failure(self):
        import subprocess
        failure="\nRan 14 tests in 0.120s\n\nFAILED (failures=1, errors=2)\n"
        success="\nRan 14 tests in 0.120s\n\nOK\n"
        self.assertTrue(v.completed_unittest(subprocess.CompletedProcess([],1,stderr=failure),failed=True))
        self.assertTrue(v.completed_unittest(subprocess.CompletedProcess([],0,stderr=success),failed=False))
        for code, stderr in ((125,failure),(137,failure),(1,"Docker unavailable"),
                             (1,"Ran 0 tests in 0.1s\nFAILED (errors=1)\n"),
                             (1,success),(0,failure)):
            self.assertFalse(v.completed_unittest(subprocess.CompletedProcess([],code,stderr=stderr),failed=True))
        self.assertFalse(v.completed_unittest(subprocess.CompletedProcess([],0,stderr="Ran 0 tests in 0.1s\nOK\n"),failed=False))

    def _assert_single_recovery(self, source, task, regression=False):
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
                if regression:
                    original_verdict.update(status="BLOCKED_EXISTING_FOCUSED_TESTS",
                        existing_focused_tests_passed=False, regression_recovery_eligible=True,
                        original_focused_baseline_passed=True,
                        test_file="tests/"+v.FOCUSED_TESTS.get(source,"test_"+Path(source).stem+".py"))
                report.write_text(json.dumps(original_report))
                verdict.write_text(json.dumps(original_verdict))
                env={"GITHUB_ACTIONS":"true","GITHUB_EVENT_NAME":"issues","GITHUB_REPOSITORY":coder.REPO,
                     "GITHUB_RUN_ATTEMPT":"1","GITHUB_RUN_ID":"123456",
                     "PLENUM_EPHEMERAL_RUNNER":"confirmed","PLENUM_ORIGINAL_CODING_RESERVED":"true",
                     "GITHUB_EVENT_PATH":str(event)}
                def corrected(*args,**kwargs):
                    self.assertTrue(kwargs["behavioral_recovery"])
                    self.assertIs(kwargs["regression_recovery"],regression)
                    self.assertEqual(args[0],task)
                    self.assertEqual((candidate.parent/"first-attempt"/candidate.name).read_bytes(),b"first rejected candidate")
                    candidate.write_bytes(b"second review-only candidate")
                    return {**original_report,"repair_passes":1}
                with patch.dict(os.environ,env),patch.object(coder,"execute_local",side_effect=corrected) as run,patch.object(v,"verify",return_value={"status":"REVIEW_ONLY_TEST_FIXTURE"}) as verify:
                    with patch.dict(os.environ,{"PLENUM_ORIGINAL_CODING_RESERVED":"false"}):
                        self.assertEqual(v.recover_local_behavior(report,verdict,event),original_verdict)
                        run.assert_not_called()
                    if regression:
                        for invalid in ({"original_focused_baseline_passed":False},
                                        {"regression_recovery_eligible":False},
                                        {"test_file":"tests/unapproved.py"}):
                            verdict.write_text(json.dumps({**original_verdict,**invalid}))
                            v.recover_local_behavior(report,verdict,event)
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
                    self.assertEqual(json.loads((saved/"reservation.json").read_text())["diagnosis"],"existing_regression" if regression else "task_acceptance")
                    verdict.write_text(json.dumps(original_verdict))
                    v.recover_local_behavior(report,verdict,event)
                    self.assertEqual(run.call_count,1)
            finally:
                os.chdir(previous)

    def test_registered_structured_recovery_is_one_distinct_numbered_edit(self):
        source, task = next(iter(coder.STRUCTURED_RECOVERY_TASKS))
        original = (ROOT / source).read_bytes()
        scope = coder.local_function_scope(task, original)
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "candidate.patch"
            with patch.dict(os.environ, {"PLENUM_EPHEMERAL_RUNNER":"confirmed"}), \
                 patch.object(coder, "_review_output_path", return_value=artifact), \
                 patch.object(coder, "structured_local_edit", return_value=original+b"\n") as edit:
                result = coder.execute_local(task, source_file=source,
                                             candidate_out="unused", behavioral_recovery=True)
                self.assertEqual(result["repair_passes"], 1)
                self.assertEqual(edit.call_count, 1)
                self.assertTrue(edit.call_args.kwargs["numbered"])
                self.assertEqual(edit.call_args.args[1], scope)
                self.assertIn("Independent behavioral acceptance rejected", edit.call_args.args[0])
                self.assertEqual(result["structured_edit_strategies"][0]["behavioral_recovery"], True)
                edit.reset_mock()
                with self.assertRaises(PermissionError):
                    coder.execute_local(task+" Extra.", source_file=source,
                                        candidate_out="unused", behavioral_recovery=True)
                edit.assert_not_called()
                edit.side_effect = coder.StructuredEditFailure("EDIT_VALIDATION")
                with self.assertRaises(coder.StructuredEditFailure):
                    coder.execute_local(task, source_file=source,
                                        candidate_out="unused", behavioral_recovery=True)
                self.assertEqual(edit.call_count, 1)

    def test_function_scoped_edit_keeps_unrelated_bytes_and_signature(self):
        source=b"import math\n\ndef first(x: int) -> int:\n    return x+1\n\ndef second():\n    return 42\n"
        scope=coder.local_function_scope("Repair function first. Correct the result.",source)
        self.assertEqual(scope[1],b"def first(x: int) -> int:\n    return x+1\n")
        changed=scope[1].replace(b"x+1",b"x+2")
        self.assertEqual(coder.restore_function_scope(scope,changed),source.replace(b"x+1",b"x+2"))
        for bad in (changed.replace(b"first",b"other"),changed.replace(b"x: int",b"x: str"),
                    b"import sys\n"+changed, changed+b"\nprint(123)\n"):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                coder.restore_function_scope(scope,bad)
        self.assertIsNone(coder.local_function_scope("Repair this module normally.",source))
        with self.assertRaises(ValueError):
            coder.local_function_scope("Repair function unknown. Fix the issue.",source)


    def test_structured_local_edit_cannot_change_signature_or_ambiguous_anchor(self):
        source=b"import math\n\ndef first(x: int) -> int:\n    y=x+1\n    return y\n\ndef second():\n    return 42\n"
        scope=coder.local_function_scope("Repair function first. Correct result.",source)
        choice={"old":"    y=x+1","new":"    y=x+2"}
        self.assertEqual(coder.apply_structured_edit(scope,choice),source.replace(b"x+1",b"x+2"))
        for bad in ({"old":"missing","new":"x"}, {"old":" ","new":"x"},
                    {"old":"first(x: int)","new":"other(x: int)"},
                    {"old":"    return y","new":"    return y\nprint(2)"},
                    {**choice,"extra":"unapproved"}):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                coder.apply_structured_edit(scope,bad)
        import subprocess
        response={"model":coder.STRUCTURED_EDIT_MODEL,"done":True,"done_reason":"stop",
                  "message":{"content":json.dumps(choice)}}
        with patch.object(coder.subprocess,"run",return_value=subprocess.CompletedProcess([],0,stdout=json.dumps(response).encode())) as run:
            result=coder.structured_local_edit("Repair function first. Correct result.",scope)
            self.assertEqual(result,source.replace(b"x+1",b"x+2"))
            command=run.call_args.args[0]
            self.assertIn("--network=plenum-coding-isolated",command)
            self.assertIn("--read-only",command)
            self.assertNotIn("--mount",command)
            self.assertEqual(json.loads(run.call_args.kwargs["input"])["model"],coder.STRUCTURED_EDIT_MODEL)
            self.assertEqual(set(run.call_args.kwargs["env"]),{"PATH"})



    def test_reject_original_960_pattern_without_another_model_call(self):
        # The preserved original #960 patch read job before its assignment.
        import subprocess
        source = (b"def diagnose(run, jobs):\n"
                  b"    if run.get('conclusion') != 'failure':\n"
                  b"        return False\n"
                  b"    job = jobs[0]\n"
                  b"    return bool(job)\n")
        scope = coder.local_function_scope("Repair function diagnose. Inspect result.", source)
        choice = {"old": "if run.get('conclusion') != 'failure':",
                  "new": "if run.get('conclusion') != 'failure' or job.get('started_at'):"}
        with self.assertRaises(coder.EarlyLocalReadError):
            coder.apply_structured_edit(scope, choice)
        with self.assertRaises(coder.EarlyLocalReadError):
            coder.apply_numbered_edit(scope, {"start":2, "end":2,
                                             "replacement":"    " + choice["new"]})
        response = {"model":coder.STRUCTURED_EDIT_MODEL,"done":True,"done_reason":"stop",
                    "message":{"content":json.dumps(choice)}}
        with patch.object(coder.subprocess, "run", return_value=subprocess.CompletedProcess(
                [],0,stdout=json.dumps(response).encode())) as run:
            with self.assertRaises(coder.StructuredEditFailure) as error:
                coder.structured_local_edit("Repair function diagnose. Inspect result.", scope)
            self.assertEqual(error.exception.stage, "EARLY_LOCAL_READ")
            self.assertEqual(run.call_count, 1)
        # Correctly initialized local reads, parameters and globals remain legal.
        self.assertEqual(coder.apply_structured_edit(scope, {
            "old":"return bool(job)", "new":"return bool(job.get('started_at'))"
        }), source.replace(b"return bool(job)", b"return bool(job.get('started_at'))"))
        # Preserve existing execution behavior; this is not a full dataflow proof.
        self.assertEqual(coder._early_local_reads(b"def f(x):\n    return bool(x)\n"), set())


    def test_two_function_edits_are_atomic_and_preserve_other_bytes(self):
        source=b"def first():\n    return 1\n\ndef second():\n    return 2\n\ndef untouched():\n    return 3\n"
        task="Repair function first. Return four. Then repair function second. Return five."
        requests=coder.local_edit_requests(task,source)
        self.assertEqual(requests,["Repair function first. Return four.","Repair function second. Return five."])
        raw=source
        for clause,old,new in zip(requests,["return 1","return 2"],["return 4","return 5"]):
            raw=coder.apply_structured_edit(coder.local_function_scope(clause,raw),{"old":old,"new":new})
        self.assertEqual(raw,source.replace(b"return 1",b"return 4").replace(b"return 2",b"return 5"))
        for bad in (task+" Then repair function untouched. Return six.",
                    "Repair function first. Return four. Then repair function first. Return five.",
                    "Repair function first. Return four. Then repair function missing. Return five."):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                coder.local_edit_requests(bad,source)


    def test_numbered_edit_preserves_signature_docstring_and_unrelated_source(self):
        source=b'def first(x: int) -> int:\n    """Preserve this."""\n    y=x+1\n    return y\n\ndef second():\n    return 42\n'
        scope=coder.local_function_scope("Repair function first. Correct result.",source)
        self.assertEqual(coder.apply_numbered_edit(scope,{"start":3,"end":3,"replacement":"    y=x+2"}),source.replace(b"x+1",b"x+2"))
        for bad in ({"start":1,"end":1,"replacement":"def first(x):"},
                    {"start":2,"end":2,"replacement":"    pass"},
                    {"start":True,"end":3,"replacement":"    pass"},
                    {"start":3,"end":5,"replacement":"    pass"},
                    {"start":3,"end":3,"replacement":"    y=x+1"},
                    {"start":3,"end":4,"replacement":"    return x\nprint(x)"}):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                coder.apply_numbered_edit(scope,bad)

    def test_numbered_response_uses_host_indices_and_reports_fixed_diagnostics(self):
        import subprocess
        source=b"def first():\n    return 1\n"
        scope=coder.local_function_scope("Repair function first. Correct result.",source)
        response={"model":coder.STRUCTURED_EDIT_MODEL,"done":True,"done_reason":"stop",
                  "message":{"content":json.dumps({"start":2,"end":2,"replacement":"    return 2"})}}
        with patch.object(coder.subprocess,"run",return_value=subprocess.CompletedProcess([],0,stdout=json.dumps(response).encode())) as run:
            self.assertEqual(coder.structured_local_edit("Repair function first. Correct result.",scope,numbered=True),source.replace(b"return 1",b"return 2"))
            payload=json.loads(run.call_args.kwargs["input"])
            self.assertEqual(payload["format"]["required"],["start","end","replacement"])
            self.assertIn("2:     return 1",json.loads(payload["messages"][1]["content"])["numbered_function"])
        for raw,stage in ((b"not json","RESPONSE_SCHEMA"),(json.dumps({**response,"done":False}).encode(),"INCOMPLETE_MODEL_RESPONSE"),
                          (json.dumps({**response,"message":{"content":'{"start":1,"end":1,"replacement":"bad"}'}}).encode(),"EDIT_VALIDATION")):
            with patch.object(coder.subprocess,"run",return_value=subprocess.CompletedProcess([],0,stdout=raw)):
                with self.assertRaises(coder.StructuredEditFailure) as raised:
                    coder.structured_local_edit("Repair function first. Correct result.",scope,numbered=True)
                self.assertEqual(raised.exception.stage,stage)


    def test_general_python_semantics_available_to_both_edit_formats(self):
        import subprocess
        source=b"def first(x):\n    return x\n"
        task="Repair function first. Preserve an ordinary public input contract."
        scope=coder.local_function_scope(task,source)
        for numbered, choice in (
                (False, {"old":"return x","new":"return x+1"}),
                (True, {"start":2,"end":2,"replacement":"    return x+1"})):
            response={"model":coder.STRUCTURED_EDIT_MODEL,"done":True,"done_reason":"stop",
                      "message":{"content":json.dumps(choice)}}
            with self.subTest(numbered=numbered), patch.object(coder.subprocess,"run",
                return_value=subprocess.CompletedProcess([],0,stdout=json.dumps(response).encode())) as run:
                self.assertEqual(coder.structured_local_edit(task,scope,numbered=numbered),
                                 source.replace(b"return x",b"return x+1"))
                self.assertEqual(run.call_count,1)
                payload=json.loads(run.call_args.kwargs["input"])
                system=payload["messages"][0]["content"]
                self.assertIn("bool is a subclass of int",system)
                self.assertIn("preserve subclass acceptance",system)
                self.assertIn("normal and exceptional control flow separately",system)
                self.assertIn("before assignment completes",system)
                self.assertIn("enforce it explicitly",system)
                self.assertEqual(json.loads(payload["messages"][1]["content"])["objective"],task)
                self.assertNotIn("checkpoint_path",system)
                self.assertNotIn("tests/acceptance",system)

    def test_readonly_context_exposes_referenced_declarations_without_editing_them(self):
        source=b"import math\nLIMIT=10\nUNRELATED=99\n\ndef helper(x):\n    return math.floor(x)\n\ndef target(x):\n    return min(LIMIT,helper(x))\n\ndef other():\n    return UNRELATED\n"
        scope=coder.local_function_scope("Repair function target. Correct the result.",source)
        view=coder.readonly_dependency_view(scope)
        self.assertEqual(view,["LIMIT=10","def helper(x):\n    return math.floor(x)"])
        self.assertLessEqual(sum(map(len,view)),2000)
        self.assertNotIn("UNRELATED","".join(view))
        import subprocess
        choice={"old":"min(LIMIT,helper(x))","new":"min(LIMIT,helper(x)+1)"}
        response={"model":coder.STRUCTURED_EDIT_MODEL,"done":True,"done_reason":"stop",
                  "message":{"content":json.dumps(choice)}}
        with patch.object(coder.subprocess,"run",return_value=subprocess.CompletedProcess([],0,stdout=json.dumps(response).encode())) as run:
            actual=coder.structured_local_edit("Repair function target. Correct the result.",scope)
            self.assertEqual(actual,source.replace(b"min(LIMIT,helper(x))",b"min(LIMIT,helper(x)+1)"))
            payload=json.loads(run.call_args.kwargs["input"])
            self.assertEqual(json.loads(payload["messages"][1]["content"])["readonly_dependencies"],view)
        with self.assertRaises(ValueError):
            coder.apply_structured_edit(scope,{"old":"LIMIT=10","new":"LIMIT=100"})



    def test_requested_helper_not_yet_referenced_is_readonly_context(self):
        source=b"from transport import NoRedirects\nLIMIT=10\nUNRELATED=99\n\ndef target(x):\n    return min(LIMIT,x)\n"
        task="Repair function target. Use NoRedirects and preserve the limit."
        scope=coder.local_function_scope(task,source)
        view=coder.readonly_dependency_view(scope,task)
        self.assertEqual(view,["LIMIT=10","from transport import NoRedirects"])
        self.assertNotIn("UNRELATED","".join(view))
        self.assertEqual(coder.readonly_dependency_view(scope, "Use NoRedirectsExtra."),["LIMIT=10"])
        with self.assertRaises(ValueError):
            coder.apply_structured_edit(scope,{"old":"from transport import NoRedirects","new":"import transport"})

    def test_requested_helper_context_preserves_existing_bounds(self):
        source=("LIMIT=10\n" + "\n".join("HELPER_%d=%r"%(i,"x"*350) for i in range(12)) +
                "\n\ndef target(x):\n    return min(LIMIT,x)\n").encode()
        task="Repair function target. Use " + " ".join("HELPER_%d"%i for i in range(12))
        scope=coder.local_function_scope(task,source)
        view=coder.readonly_dependency_view(scope,task)
        self.assertEqual(view[0],"LIMIT=10")
        self.assertLessEqual(len(view),8)
        self.assertLessEqual(sum(map(len,view)),2000)



class ScopedModuleBudgetTests(unittest.TestCase):
    def test_large_original_module_allows_only_small_named_function(self):
        original = b"PAD = " + repr("x" * 13000).encode() + b"\n\ndef target():\n    return 1\n"
        sha = hashlib.sha256(original).hexdigest()
        source = "src/plenum_ai/workforce_team_dispatch.py"
        with patch.object(coder, "_public_source", return_value=(original, sha)):
            result = coder.local_plan("Repair function target. Return two.", source_file=source)
            self.assertEqual(result["authorized_function_edits"], 1)
            self.assertEqual(result["local_model"], coder.STRUCTURED_EDIT_MODEL)
            self.assertEqual(result["source_sha256"], sha)
            self.assertFalse(result["paid_api_authorized"])
            with self.assertRaises(PermissionError):
                coder.local_plan("Change the whole public module.", source_file=source)
            with self.assertRaises(ValueError):
                coder.local_plan("Repair function missing. Return two.", source_file=source)
        scope = coder.local_function_scope("Repair function target. Return two.", original)
        candidate = coder.apply_structured_edit(scope, {"old":"return 1", "new":"return 2"})
        self.assertEqual(candidate, original.replace(b"return 1", b"return 2"))

    def test_large_named_function_remains_blocked(self):
        original = b"def target():\n    return " + repr("x" * 13000).encode() + b"\n"
        with patch.object(coder, "_public_source", return_value=(original, hashlib.sha256(original).hexdigest())):
            with self.assertRaises(PermissionError):
                coder.local_plan("Repair function target. Return two.", source_file="src/plenum_ai/workforce_team_dispatch.py")


if __name__=="__main__":
    unittest.main()

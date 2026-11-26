import copy
import unittest
from unittest.mock import patch
from plenum_ai import engineering_event_controller as c
from plenum_ai import whisper_repair_candidate as repair


class EngineeringGateTests(unittest.TestCase):
    def setUp(self):
        self.n = 925
        branch, workflow, name = c.REGISTERED[self.n]
        self.pr = {"number": self.n, "state": "open", "user": {"login": c.OWNER},
                   "head": {"ref": branch, "sha": "a"*40, "repo": {"full_name": c.REPO}},
                   "base": {"ref": "main", "repo": {"full_name": c.REPO}}}
        self.run = {"id": 100, "name": workflow, "event": "pull_request",
                    "head_branch": branch, "head_sha": "a"*40, "actor": {"login": c.OWNER},
                    "repository": {"full_name": c.REPO}, "head_repository": {"full_name": c.REPO},
                    "run_attempt": 1, "status": "completed", "conclusion": "failure"}
        self.job = {"name": name, "id": 200, "run_id": 100, "head_sha": "a"*40,
                    "conclusion": "failure", "steps": [
                        {"name": "Set up job", "conclusion": "failure"},
                        {"name": "Install dependencies", "conclusion": "skipped"},
                        {"name": "Test", "conclusion": "skipped"}]}

    def test_eligible_first_attempt(self):
        self.assertEqual(c.diagnose(self.pr, self.n, self.run, [self.job]),
                         {"status": "RETRY_UNSTARTED_INFRASTRUCTURE_ONCE", "job_id": 200})

    def test_no_replay_after_start(self):
        self.job["steps"][0]["conclusion"] = "success"
        self.job["steps"][1]["conclusion"] = "failure"
        self.assertEqual(c.diagnose(self.pr, self.n, self.run, [self.job])["status"],
                         "BLOCKED_NEEDS_CORRECTION")

    def test_second_attempt_never_retried(self):
        self.run["run_attempt"] = 2
        self.assertEqual(c.diagnose(self.pr, self.n, self.run, [self.job])["status"],
                         "BLOCKED_NEEDS_CORRECTION")

    def test_stale_head_and_fork(self):
        for key, value in [("head_sha", "b"*40), ("head_repository", {"full_name": "fork/repo"}),
                           ("actor", {"login": "unapproved"}), ("name", "Other")]:
            with self.subTest(key=key):
                run = copy.deepcopy(self.run)
                run[key] = value
                self.assertEqual(c.diagnose(self.pr, self.n, run, [self.job])["status"], "INELIGIBLE")

    def test_success_does_not_authorize_merge(self):
        self.run["conclusion"] = "success"
        self.job["conclusion"] = "success"
        self.job["steps"] = [{"name": "Test", "conclusion": "success"}]
        self.assertEqual(c.diagnose(self.pr, self.n, self.run, [self.job]),
                         {"status": "AWAIT_INDEPENDENT_EVIDENCE"})

    def test_success_requires_exact_approved_job(self):
        self.run["conclusion"] = "success"
        for jobs in ([], [self.job, self.job], [dict(self.job, run_id=101)],
                     [dict(self.job, head_sha="b"*40)], [dict(self.job, steps=[None])]):
            with self.subTest(jobs=jobs):
                self.assertEqual(c.diagnose(self.pr, self.n, self.run, jobs)["status"],
                                 "BLOCKED_JOB_IDENTITY")
        for conclusion in ("skipped", "cancelled", "failure", None):
            with self.subTest(conclusion=conclusion):
                self.assertEqual(c.diagnose(self.pr, self.n, self.run,
                                           [dict(self.job, conclusion=conclusion)])["status"],
                                 "BLOCKED_APPROVED_JOB_NOT_SUCCESS")

    def test_wrong_job_identity(self):
        self.job["run_id"] = 101
        self.assertEqual(c.diagnose(self.pr, self.n, self.run, [self.job])["status"],
                         "BLOCKED_JOB_IDENTITY")

    def test_canonical_ledger_receipt_and_no_duplicate_retry(self):
        self.run["created_at"] = "2026-01-01T00:00:00Z"
        calls = []
        stored = []
        def fake(path, method="GET", payload=None):
            calls.append((path, method))
            if path == "/pulls/925":
                return self.pr
            if path == "/actions/runs/100":
                return self.run
            if path.startswith("/actions/runs?"):
                return {"workflow_runs": [self.run]}
            if path == "/actions/runs/100/attempts/1/jobs?per_page=30":
                return {"jobs": [self.job]}
            if path.startswith("/issues/432/comments?"):
                return stored
            if path == "/issues/432/comments" and method == "POST":
                row = {"user": {"login": "github-actions[bot]"}, "body": payload["body"]}
                stored.append(row)
                return row
            if path == "/actions/jobs/200/rerun" and method == "POST":
                return {}
            self.fail("Unexpected API request: " + path)
        with patch.object(c, "request", side_effect=fake):
            first = c.process(925, 100)
            second = c.process(925, 100)
        self.assertTrue(first["retry_requested"])
        self.assertTrue(second["already_recorded"])
        self.assertEqual(calls.count(("/actions/jobs/200/rerun", "POST")), 1)
        self.assertEqual(calls.count(("/issues/432/comments", "POST")), 1)
        self.assertFalse(any(path.startswith("/issues/925/comments") for path, _ in calls))

    def test_one_exact_speech_repair(self):
        n = 928
        branch, workflow, name = c.REGISTERED[n]
        self.pr["number"] = n
        self.pr["head"].update(ref=branch, sha=c.WHISPER_REPAIR_HEAD)
        self.run.update(id=c.WHISPER_REPAIR_RUN, head_branch=branch,
                        head_sha=c.WHISPER_REPAIR_HEAD, name=workflow)
        self.job.update(id=c.WHISPER_REPAIR_JOB, run_id=c.WHISPER_REPAIR_RUN,
                        head_sha=c.WHISPER_REPAIR_HEAD, name=name, steps=[
            {"name":"Build exact official whisper.cpp release","conclusion":"success"},
            {"name":"Verify official MIT tiny English model and create original synthetic test speech","conclusion":"success"},
            {"name":"Qualify upstream CLI on public synthetic fixture in isolated network namespace","conclusion":"failure"}])
        self.assertEqual(c.diagnose(self.pr,n,self.run,[self.job])["status"],
                         "QUALIFY_PINNED_WHISPER_BASE_CORRECTION_ONCE")
        self.run["run_attempt"] = 2
        self.assertEqual(c.diagnose(self.pr,n,self.run,[self.job])["status"],
                         "BLOCKED_NEEDS_CORRECTION")
        self.run["run_attempt"] = 1
        self.job["steps"][0]["conclusion"] = "skipped"
        self.assertEqual(c.diagnose(self.pr,n,self.run,[self.job])["status"],
                         "BLOCKED_NEEDS_CORRECTION")

    def test_exact_candidate_transform(self):
        original = (b"Verify official MIT tiny English model\n"
                    b"/ggml-tiny.en.bin\n" + repair.OLD_SHA.encode() + b"\n")
        with patch.object(repair, "ORIGINAL_BLOB", repair.git_blob(original)):
            revised = repair.candidate(original)
            self.assertEqual(revised, original.replace(b"tiny English model", b"base English model")
                             .replace(b"/ggml-tiny.en.bin", b"/ggml-base.en.bin")
                             .replace(repair.OLD_SHA.encode(), repair.NEW_SHA.encode()))
            with self.assertRaises(ValueError):
                repair.candidate(original + b"unauthorized change")
        with patch.object(repair, "ORIGINAL_BLOB", repair.git_blob(original + original)):
            with self.assertRaises(ValueError):
                repair.candidate(original + original)

    def test_owner_wake_exact_authorization(self):
        event = {"action":"opened","repository":{"full_name":c.REPO},
                 "sender":{"login":c.OWNER},"issue":{"number":123,"state":"open",
                 "user":{"login":c.OWNER},"title":c.WAKE_TITLE,"body":c.WAKE_BODY}}
        self.assertTrue(c.wake_authorized(event))
        for key,value in [("body","PLENUM_ENGINEERING_WAKE_V1 extra"),
                          ("title","different"),("user",{"login":"stranger"}),
                          ("state","closed"),("pull_request",{})]:
            other = copy.deepcopy(event)
            other["issue"][key] = value
            self.assertFalse(c.wake_authorized(other))
        event["sender"]["login"] = "stranger"
        self.assertFalse(c.wake_authorized(event))

    def test_cloudflare_fallback_fixed_scope(self):
        slot = 1800000000000
        event = {"action":"plenum_engineering_backlog_tick_v1",
                 "repository":{"full_name":c.REPO},
                 "sender":{"login":c.OWNER},"client_payload":{"slot":slot}}
        self.assertTrue(c.fallback_authorized(event, slot+1000))
        self.assertFalse(c.fallback_authorized(event, slot+300000))
        self.assertFalse(c.fallback_authorized(event, slot-1))
        for key,value in [("sender",{"login":"stranger"}),
                          ("action","other"),
                          ("client_payload",{"slot":slot,"task":"unapproved"}),
                          ("client_payload",{"slot":slot+1}),
                          ("client_payload",{"slot":True}),
                          ("repository",{"full_name":"other/repo"})]:
            other=copy.deepcopy(event)
            other[key]=value
            self.assertFalse(c.fallback_authorized(other,slot+1000))

    def test_unregistered_or_closed(self):
        self.assertFalse(c.authorized_pr(self.pr, 926))
        self.pr["state"] = "closed"
        self.assertFalse(c.authorized_pr(self.pr, self.n))


if __name__ == "__main__":
    unittest.main()

class DynamicEngineeringQueueTests(unittest.TestCase):
    def setUp(self):
        self.n=12345
        self.pr={"number":self.n,"state":"open","draft":False,"user":{"login":c.OWNER},
                 "head":{"ref":"prometheus-new-work","sha":"a"*40,"repo":{"full_name":c.REPO}},
                 "base":{"ref":"main","repo":{"full_name":c.REPO}},
                 "body":"<!-- plenum-engineering-observe-v1:"+"a"*40+":New native check:qualification -->"}
    def approval(self):
        return {"body":self.pr["body"],"user":{"login":c.OWNER,"id":251133044},
                "author_association":"OWNER","created_at":"2026-11-26T00:00:00Z","updated_at":"2026-11-26T00:00:00Z"}
    def test_discovery_and_head_bound_revalidation(self):
        with patch.object(c,"DYNAMIC",{}),patch.object(c,"request",side_effect=[[self.pr],[self.approval()]]):
            c.discover()
            self.assertTrue(c.authorized_pr(self.pr,self.n))
            self.assertEqual(c.registry()[self.n],("prometheus-new-work","New native check","qualification"))
            for changed in ("head","body","user","draft"):
                bad=copy.deepcopy(self.pr)
                if changed=="head":bad["head"]["sha"]="b"*40
                elif changed=="body":bad["body"]+="\n"+bad["body"]
                elif changed=="user":bad["user"]["login"]="outsider"
                else:bad["draft"]=True
                self.assertFalse(c.authorized_pr(bad,self.n))
    def test_no_unapproved_or_unbounded_discovery(self):
        with patch.object(c,"DYNAMIC",{}),patch.object(c,"request",return_value=[{}]*100):
            with self.assertRaises(RuntimeError):c.discover()
        with patch.object(c,"DYNAMIC",{}),patch.object(c,"request",side_effect=[[self.pr,self.pr],[self.approval()],[self.approval()]]):
            with self.assertRaises(RuntimeError):c.discover()
        with patch.object(c,"DYNAMIC",{}),patch.object(c,"request",return_value=[dict(self.pr,body="arbitrary instructions")]):
            c.discover()
            self.assertNotIn(self.n,c.registry())

    def test_owner_comment_required_and_unedited(self):
        approval=self.approval()
        for comments in ([],[dict(approval,updated_at="2026-11-26T00:01:00Z")],
                         [dict(approval,user={"login":c.OWNER,"id":999})],
                         [dict(approval,author_association="COLLABORATOR")],[approval,approval]):
            with patch.object(c,"DYNAMIC",{}),patch.object(c,"request",side_effect=[[self.pr],comments]):
                c.discover()
                self.assertNotIn(self.n,c.registry())

class ImmediateApprovalWakeTests(unittest.TestCase):
    def test_owner_event_only_and_exact_shape(self):
        marker="<!-- plenum-engineering-observe-v1:"+"a"*40+":Example check:qualification -->"
        owner={"login":c.OWNER,"id":251133044}
        event={"action":"created","repository":{"full_name":c.REPO},"sender":owner,
               "issue":{"number":12345,"state":"open","pull_request":{},"user":owner},
               "comment":{"user":owner,"body":marker,"author_association":"OWNER",
                          "created_at":"2026-11-26T00:00:00Z","updated_at":"2026-11-26T00:00:00Z"}}
        self.assertEqual(c.approval_event_number(event),12345)
        for path,value in ((("action",),"edited"),(("sender","id"),1),
                           (("comment","user","id"),1),
                           (("comment","body"),marker+"\nextra"),
                           (("comment","author_association"),"COLLABORATOR"),
                           (("comment","updated_at"),"2026-11-26T00:01:00Z"),
                           (("issue","state"),"closed")):
            bad=copy.deepcopy(event)
            target=bad
            for key in path[:-1]:target=target[key]
            target[path[-1]]=value
            self.assertIsNone(c.approval_event_number(bad))
        bad=copy.deepcopy(event)
        del bad["issue"]["pull_request"]
        self.assertIsNone(c.approval_event_number(bad))

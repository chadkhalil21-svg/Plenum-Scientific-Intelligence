import copy
import unittest
from plenum_ai import engineering_event_controller as c


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
        self.assertEqual(c.diagnose(self.pr, self.n, self.run, []),
                         {"status": "AWAIT_INDEPENDENT_EVIDENCE"})

    def test_wrong_job_identity(self):
        self.job["run_id"] = 101
        self.assertEqual(c.diagnose(self.pr, self.n, self.run, [self.job])["status"],
                         "BLOCKED_JOB_IDENTITY")

    def test_unregistered_or_closed(self):
        self.assertFalse(c.authorized_pr(self.pr, 926))
        self.pr["state"] = "closed"
        self.assertFalse(c.authorized_pr(self.pr, self.n))


if __name__ == "__main__":
    unittest.main()

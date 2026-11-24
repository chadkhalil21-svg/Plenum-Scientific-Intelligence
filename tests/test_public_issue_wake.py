"""Focused no-network proof: only original founder issue can wake, exactly once."""
import unittest
from plenum_ai.public_issue_wake import build_original_event, checked_issue_number, one_original_local_repair_warranted

def issue(**kwargs):
    data={
        "number":789, "state":"open", "title":"[Plenum Workforce] public research",
        "body":"PLENUM_PUBLIC_WORKFORCE_V2\nkind: public_research\nobjective: Review source quality for Plenum repository",
        "user":{"login":"chadkhalil21-svg"}
    }
    data.update(kwargs)
    return data

class PublicWakeAcceptance(unittest.TestCase):
    def test_scheduled_wake_completes_original_deterministic_cooling_contract_once(self):
        import json
        import math
        import os
        import subprocess
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from plenum_ai import chief_contract_plan, public_issue_wake as wake
        original = issue(title="[Plenum Chief] public mission", body=(
            "PLENUM_CHIEF_PUBLIC_CONTRACT_MISSION_V1\n"
            "objective: Solve cooling initial 350 K ambient 290 K rate 0.1 time 10"))
        comments = [{"user": {"login": "github-actions[bot]"}, "body":
                     "<!-- plenum-minister-missed-dispatch:789 -->\nScheduled dispatch only"}]
        installs = []
        def api(url, token, *, body=None):
            if url.endswith("/789"):
                return {**original, "comments": len(comments)}
            if url.endswith("comments?per_page=100"):
                return list(comments)
            if url.endswith("/comments"):
                comments.append({"user": {"login": "github-actions[bot]"}, "body": body["body"]})
                return {"html_url": "https://github.com/example/receipt"}
            raise AssertionError(url)
        def install(argv):
            # CI has the real SciPy package installed; substitute only the
            # networked pip operation, not the numerical worker or verifier.
            self.assertEqual(len(comments), 1)
            self.assertEqual(argv[-1], ".[numerical]")
            installs.append(argv[-1])
        prior_directory = Path.cwd()
        with tempfile.TemporaryDirectory() as folder, patch.object(wake, "gh_json", side_effect=api), \
                patch.object(subprocess, "check_call", side_effect=install), \
                patch.object(chief_contract_plan, "model_plan", side_effect=AssertionError("No model needed")), \
                patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "GITHUB_EVENT_NAME": "repository_dispatch",
                                        "GITHUB_REPOSITORY": wake.REPO, "GITHUB_RUN_ID": "123", "GH_TOKEN": "scoped"}):
            try:
                os.chdir(folder)
                wake.main(["--issue-number", "789", "--execute"])
                result = json.loads(Path("reports/public-wake/chief-result-789.json").read_text())
                self.assertEqual(result["status"], "VERIFIED_BOUNDED_CONTRACT_MISSION")
                self.assertTrue(result["independent_verified"])
                self.assertFalse(result["founder_objective_verified"])
                self.assertFalse(result["model_called"])
                self.assertAlmostEqual(result["contract_results"]["cooling_solution"]["observed_kelvin"],
                                       290 + 60 * math.exp(-1), places=6)
                self.assertEqual(len(comments), 3)
                self.assertEqual(installs, [".[numerical]"])
                wake.main(["--issue-number", "789", "--execute"])
                self.assertEqual(len(comments), 3)
                self.assertEqual(installs, [".[numerical]"])
            finally:
                os.chdir(prior_directory)

    def test_scoped_install_rechecks_original_owner_issue_before_reservation(self):
        import subprocess
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from plenum_ai import public_issue_wake as wake
        original = issue(title="[Plenum Chief] public mission", body=(
            "PLENUM_CHIEF_PUBLIC_CONTRACT_MISSION_V1\n"
            "objective: Solve cooling initial 350 K ambient 290 K rate 0.1 time 10"))
        comments = []
        def api(url, token, *, body=None):
            if url.endswith("/789"):
                return {**original, "comments": len(comments)}
            if url.endswith("comments?per_page=100"):
                return list(comments)
            if url.endswith("/comments"):
                comments.append(body)
                return {"html_url": "https://github.com/example/receipt"}
            raise AssertionError(url)
        def install(argv):
            original["body"] = original["body"].replace("350 K", "360 K")
        with tempfile.TemporaryDirectory() as folder, patch.object(wake, "gh_json", side_effect=api), \
                patch.object(subprocess, "check_call", side_effect=install), \
                patch.object(wake, "execute_original_team", return_value={
                    "status": "VERIFIED_BOUNDED_CONTRACT_MISSION", "independent_verified": True}), \
                patch.dict("os.environ", {"GITHUB_RUN_ID": "123"}):
            with self.assertRaisesRegex(PermissionError, "changed"):
                wake.process(789, "scoped", Path(folder))
        self.assertEqual(comments, [])

    def test_legacy_model_data_wake_does_not_reserve_or_execute(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from plenum_ai import public_issue_wake as wake
        original = issue(title="[Plenum Chief] public mission", body=(
            "PLENUM_CHIEF_PUBLIC_DATA_MISSION_V1\n"
            "objective: Review NOAA station metadata 8723214 and run existing validator"))
        def api(url, token, *, body=None):
            self.assertIsNone(body, "Legacy DATA must not consume the execution reservation")
            return original if url.endswith("/789") else []
        with tempfile.TemporaryDirectory() as folder, patch.object(wake, "gh_json", side_effect=api), \
                patch.object(wake, "execute_original_team") as execute:
            with self.assertRaisesRegex(PermissionError, "REQUIRES_ORIGINAL_NATIVE_MODEL_ROUTE"):
                wake.process(789, "scoped", Path(folder))
            execute.assert_not_called()

    def test_existing_public_founder_issue_allowed(self):
        e=build_original_event(issue(),[])
        self.assertEqual(e["issue"]["number"],789)

    def test_native_initial_reservation_prevents_later_wake_and_native_replay(self):
        from unittest.mock import patch
        from plenum_ai import public_issue_wake as wake
        for original in (
            issue(),
            issue(title="[Plenum Chief] public mission", body=(
                "PLENUM_CHIEF_PUBLIC_MISSION_V1\n"
                "objective: Survey public research sources and create a code validator")),
            issue(title="[Plenum Chief] public assignment", body=(
                "PLENUM_CHIEF_PUBLIC_V1\nobjective: Create a public data validator program")),
        ):
            with self.subTest(title=original["title"]):
                # A scheduled dispatch-only reservation is not an execution.
                comments = [{"user": {"login": "github-actions[bot]"},
                             "body": "<!-- plenum-minister-missed-dispatch:789 -->"}]
                event = {"action": "opened", "repository": {"full_name": wake.REPO},
                         "sender": {"login": wake.OWNER}, "issue": original}
                posts = []
                def gh(url, token, *, body=None):
                    if url.endswith("/789"):
                        return original
                    if url.endswith("/comments?per_page=100"):
                        return comments
                    if url.endswith("/comments"):
                        posts.append(body)
                        comments.append({"user": {"login": "github-actions[bot]"},
                                         "body": body["body"]})
                        return {"html_url": "https://github.com/acknowledged"}
                    raise AssertionError(url)
                with patch.object(wake, "gh_json", side_effect=gh):
                    self.assertTrue(wake.reserve_native_issue(event, "scoped", run_id=123, attempt=1))
                    self.assertFalse(wake.reserve_native_issue(event, "scoped", run_id=456, attempt=1))
                    self.assertFalse(wake.reserve_native_issue(event, "scoped", run_id=123, attempt=1))
                self.assertEqual(len(posts), 1)
                if original["title"] != "[Plenum Chief] public assignment":
                    self.assertIsNone(build_original_event(original, comments))

    def test_native_same_run_retry_requires_original_saved_verified_sibling(self):
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from plenum_ai import public_issue_wake as wake, chief_retry_gate as retry
        from plenum_ai.mission_checkpoint import artifact_digest, save_checkpoint
        original = issue(title="[Plenum Chief] public mission", body=(
            "PLENUM_CHIEF_PUBLIC_MISSION_V1\n"
            "objective: Survey public research sources and create a code validator"))
        event = {"action": "opened", "repository": {"full_name": wake.REPO},
                 "sender": {"login": wake.OWNER}, "issue": original}
        comments = [{"user": {"login": "github-actions[bot]"}, "body":
                     "<!-- plenum-public-workforce-run:123:execution-reserved -->"},
                    {"user": {"login": "github-actions[bot]"}, "body":
                     "<!-- plenum-founder-chief-run:123:attempt:1 -->\n**Chief status: BLOCKED_PARTIAL_TEAM**"}]
        prior = {"name": retry.WORKFLOW, "event": "issues", "id": 123,
                 "status": "completed", "conclusion": "failure", "run_attempt": 1,
                 "actor": {"login": wake.OWNER}, "repository": {"full_name": wake.REPO}}
        def gh(url, token, *, body=None):
            if url.endswith("/789"): return original
            if url.endswith("/comments?per_page=100"): return comments
            if url.endswith("/comments"):
                comments.append({"user": {"login": "github-actions[bot]"}, "body": body["body"]})
                return {"html_url": "https://github.com/acknowledged"}
            raise AssertionError(url)
        with tempfile.TemporaryDirectory() as folder, patch.object(wake, "gh_json", side_effect=gh), patch.object(retry, "github_json", return_value=prior):
            root = Path(folder)
            self.assertFalse(wake.reserve_native_issue(event, "scoped", run_id=123, attempt=2, checkpoint=root))
            relative = "workers/public_research/output.txt"
            artifact = root / relative
            artifact.parent.mkdir(parents=True)
            artifact.write_text("verified original public data")
            objective = original["body"].splitlines()[1][11:]
            team = ("public_research", "public_program")
            save_checkpoint(root, issue=789, objective=objective, team=team, results={
                "public_research": {"attempt": 1, "status": "DRAFT_READY_FOR_FOUNDER", "verified": True,
                                    "artifact_path": relative, "sha256": artifact_digest(root, relative)},
                "public_program": {"attempt": 1, "status": "BLOCKED_WORKER_OR_VERIFICATION", "verified": False},
            })
            (root / "chief-result-789.json").write_text(json.dumps({
                "issue_number": 789, "mode": "multi", "expected_team": list(team),
                "status": "BLOCKED_PARTIAL_TEAM", "independent_verified": False,
            }))
            self.assertTrue(wake.reserve_native_issue(event, "scoped", run_id=123, attempt=2, checkpoint=root))
            self.assertFalse(wake.reserve_native_issue(event, "scoped", run_id=123, attempt=2, checkpoint=root))
            self.assertFalse(wake.reserve_native_issue(event, "scoped", run_id=123, attempt=3, checkpoint=root))
            self.assertFalse(wake.reserve_native_issue(event, "scoped", run_id=456, attempt=2, checkpoint=root))

    def test_already_handled_public_issue_is_not_rerun(self):
        comments=[{"user":{"login":"github-actions[bot]"},
                   "body":"<!-- plenum-public-workforce-run:123 -->\nStatus: **DRAFT_READY_FOR_FOUNDER**."}]
        self.assertIsNone(build_original_event(issue(),comments))
        # Third-party comments may never claim GitHub Actions completion.
        comments[0]["user"]["login"]="outsider"
        self.assertIsNotNone(build_original_event(issue(),comments))


    def test_existing_original_chief_multi_specialist_issue_is_allowlisted(self):
        original = issue(
            title="[Plenum Chief] public mission",
            body=("PLENUM_CHIEF_PUBLIC_MISSION_V1\n"
                  "objective: Survey public research sources and create a code validator"),
        )
        event = build_original_event(original, [])
        self.assertEqual(event["issue"]["number"], 789)
        self.assertEqual(event["issue"]["title"], original["title"])
        # A bot result from either original issue workflow OR signed wake
        # must block a repeated execution of the SAME issue.
        for marker in (
            "<!-- plenum-founder-chief-run:123:attempt:1 -->",
            "<!-- plenum-public-workforce-run:456 -->",
        ):
            comment = [{"user": {"login": "github-actions[bot]"}, "body": marker}]
            self.assertIsNone(build_original_event(original, comment))
            # Third-party comments are never trusted completion receipts.
            comment[0]["user"]["login"] = "untrusted-person"
            self.assertIsNotNone(build_original_event(original, comment))
        for bad in (
            issue(title="[Plenum Chief] public mission", body="free text"),
            issue(title="[Plenum Chief] public mission", user={"login": "outsider"},
                  body=original["body"]),
            issue(title="[Plenum Chief] public mission",
                  body=("PLENUM_CHIEF_PUBLIC_MISSION_V1\n"
                        "objective: Sign into a private banking account and send email")),
        ):
            with self.subTest(bad=bad):
                with self.assertRaises((ValueError, PermissionError)):
                    build_original_event(bad, [])

    def test_rewake_uses_exact_existing_chief_team_engine_once(self):
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from plenum_ai import public_issue_wake as wake
        original = issue(
            title="[Plenum Chief] public mission",
            body=("PLENUM_CHIEF_PUBLIC_MISSION_V1\n"
                  "objective: Survey public research sources and create a code validator"),
        )
        completed = {
            "status": "VERIFIED_BOUNDED_TEAM", "issue_number": 789,
            "executed_workers": 2, "independent_verified": True,
        }
        requests = []
        def fake_gh(url, token, *, body=None):
            requests.append((url, body))
            if url.endswith("/789"): return original
            if "comments?per_page" in url: return []
            if url.endswith("/comments"): return {"html_url": "https://github.com/safe#comment"}
            raise AssertionError("Unexpected resource")
        with tempfile.TemporaryDirectory() as folder, patch.object(
            wake, "gh_json", side_effect=fake_gh
        ), patch.object(
            wake, "execute_original_team", return_value=completed
        ) as team, patch.object(
            wake, "run_issue"
        ) as single, patch.dict("os.environ", {"GITHUB_RUN_ID":"123"}):
            result = wake.process(789, "scoped", Path(folder))
            self.assertEqual(result["status"], "VERIFIED_BOUNDED_TEAM")
            self.assertTrue(result["independent_verified"])
            self.assertTrue(result["original_multi_specialist"])
            self.assertTrue((Path(folder)/"chief-result-789.json").is_file())
            self.assertEqual(
                json.loads((Path(folder)/"chief-result-789.json").read_text())["executed_workers"], 2
            )
            self.assertEqual(team.call_count, 1)
            single.assert_not_called()
            self.assertIn("multi-specialist", requests[-1][1]["body"])
            self.assertNotIn("Survey public research", requests[-1][1]["body"])


    def test_original_team_recovers_one_failed_role_without_repeating_good_one(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from plenum_ai import public_issue_wake as wake
        from plenum_ai.mission_checkpoint import artifact_digest, save_checkpoint
        original = issue(title="[Plenum Chief] public mission",
            body=("PLENUM_CHIEF_PUBLIC_MISSION_V1\n"
                  "objective: Survey public research sources and create a code validator"))
        calls = []
        def execute(event, *, output_dir):
            calls.append(event["issue"]["number"])
            if len(calls) == 1:
                relative = "workers/public_research/issue-789/research"
                target = output_dir / relative
                target.mkdir(parents=True)
                (target / "result.txt").write_text("public-source evidence", encoding="utf-8")
                hash_value = artifact_digest(output_dir, relative)
                self.assertTrue(hash_value)
                save_checkpoint(
                    output_dir, issue=789,
                    objective="Survey public research sources and create a code validator",
                    team=("public_research", "public_program"),
                    results={
                        "public_research": {
                            "status": "DRAFT_READY_FOR_FOUNDER",
                            "attempt": 1, "verified": True,
                            "worker": "existing_public_research",
                            "verified_scope": "public-source metadata",
                            "output_artifact": "issue-789/research",
                            "artifact_path": relative,
                            "sha256": hash_value,
                        },
                        "public_program": {
                            "status": "BLOCKED_WORKER_OR_VERIFICATION",
                            "attempt": 1, "verified": False,
                        },
                    },
                )
                return {
                    "issue_number": 789, "status": "BLOCKED_PARTIAL_TEAM",
                    "independent_verified": False,
                }
            return {
                "issue_number": 789, "status": "VERIFIED_BOUNDED_TEAM",
                "independent_verified": True, "reused_prior_verified_workers": 1,
                "executed_workers": 2,
            }
        calls_to_gh = []
        def fake_gh(url, token, *, body=None):
            calls_to_gh.append((url, body))
            if url.endswith("/789"): return original
            if "comments?per_page" in url: return []
            if url.endswith("/comments"): return {"html_url": "https://github.com/example/issue"}
            raise AssertionError("unexpected URL")
        with tempfile.TemporaryDirectory() as folder, patch.object(
            wake, "gh_json", side_effect=fake_gh
        ), patch.object(
            wake, "execute_original_team", side_effect=execute
        ), patch.dict("os.environ", {"GITHUB_RUN_ID": "999"}):
            outcome = wake.process(789, "scoped", Path(folder))
        self.assertEqual(calls, [789, 789])
        self.assertEqual(outcome["status"], "VERIFIED_BOUNDED_TEAM")
        self.assertTrue(outcome["independent_verified"])
        self.assertTrue(outcome["original_multi_specialist"])
        self.assertIn("Status: **VERIFIED_BOUNDED_TEAM**",
                      calls_to_gh[-1][1]["body"])

    def test_wake_recovers_first_contract_failure_without_repeating_completed_work(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from plenum_ai import public_issue_wake as wake
        from plenum_ai import chief_contract_plan as contract
        original = issue(title="[Plenum Chief] public mission",
            body=contract.MAGIC + "\nobjective: Review DOI 10.1038/nature14539 deposited metadata")
        calls = []
        record = {"doi": "10.1038/nature14539", "title": "Public record",
                  "year": 2020, "publisher": "Publisher"}
        def read(doi, **kwargs):
            calls.append(doi)
            if len(calls) == 1:
                raise RuntimeError("temporary interruption")
            return record
        def api(url, token, *, body=None):
            if url.endswith("/789"): return original
            if "/comments?per_page" in url: return []
            if url.endswith("/comments"): return {"html_url": "https://github.com/example/receipt"}
            raise AssertionError(url)
        with tempfile.TemporaryDirectory() as folder, \
                patch.object(wake, "gh_json", side_effect=api), \
                patch.object(contract, "read_crossref", side_effect=read), \
                patch.dict("os.environ", {"GITHUB_RUN_ID": "123"}):
            root = Path(folder)
            result = wake.process(789, "scoped", root)
            self.assertEqual(result["status"], "VERIFIED_BOUNDED_CONTRACT_MISSION")
            self.assertTrue(result["independent_verified"])
            self.assertEqual(len(calls), 3)
            import json
            outcome = json.loads((root / "chief-result-789.json").read_text())
            self.assertTrue(outcome["same_run_bounded_recovery_attempted"])
            self.assertFalse(wake.one_original_local_repair_warranted(
                wake.build_original_event(original, []), root, outcome))

    def test_no_recovery_without_original_checkpoint_or_when_tampered(self):
        import tempfile
        from pathlib import Path
        from plenum_ai import public_issue_wake as wake
        original = issue(title="[Plenum Chief] public mission",
            body=("PLENUM_CHIEF_PUBLIC_MISSION_V1\n"
                  "objective: Survey public research sources and create a code validator"))
        event = wake.build_original_event(original, [])
        with tempfile.TemporaryDirectory() as folder:
            self.assertFalse(one_original_local_repair_warranted(
                event, Path(folder),
                {"status": "BLOCKED_PARTIAL_TEAM", "independent_verified": False},
            ))
            self.assertFalse(one_original_local_repair_warranted(
                event, Path(folder),
                {"status": "VERIFIED_BOUNDED_TEAM", "independent_verified": True},
            ))

    def test_immediate_wake_is_exact_authenticated_original_founder_approval(self):
        from plenum_ai.public_issue_wake import founder_approved_comment_event
        from plenum_ai.minister_missed_public_wake import LEGACY_OWNER_APPROVAL
        owner={"login":"chadkhalil21-svg"}
        payload={
            "action":"edited",
            "issue":{"number":498,"state":"open","user":owner},
            "comment":{"user":owner,"body":LEGACY_OWNER_APPROVAL+"\nExisting original mission only"},
            "sender":owner,
        }
        self.assertTrue(founder_approved_comment_event(payload,498))
        for invalid in (
            {**payload, "sender":{"login":"outsider"}},
            {**payload, "comment":{**payload["comment"],"user":{"login":"outsider"}}},
            {**payload, "action":"deleted"},
            {**payload, "issue":{**payload["issue"],"state":"closed"}},
            {**payload, "comment":{**payload["comment"],"body":"not an approval"}},
        ):
            with self.subTest(invalid=invalid):
                self.assertFalse(founder_approved_comment_event(invalid,498))
        self.assertFalse(founder_approved_comment_event(payload,999))

    def test_same_unexecuted_original_legacy_mission_is_woken_without_a_new_agent(self):
        from plenum_ai import public_issue_wake as wake
        from plenum_ai.minister_missed_public_wake import LEGACY_OWNER_APPROVAL
        from unittest.mock import patch
        from pathlib import Path
        import tempfile
        prior = issue(
            number=498, comments=1, created_at="2026-11-11T20:38:55Z",
            title="[Plenum Chief] public mission",
            body=("PLENUM_CHIEF_PUBLIC_MISSION_V1\n"
                  "objective: Research free documentary sources and original SVG music illustration for Plenum Terra"),
        )
        approved={"user":{"login":"chadkhalil21-svg"},
                  "body":LEGACY_OWNER_APPROVAL+"\nOriginal previously missed public mission"}
        bot = {"status":"VERIFIED_BOUNDED_TEAM", "executed_workers":2,
               "independent_verified":True}
        def api(url,token,*,body=None):
            if url.endswith("/498"):return prior
            if "/comments?per_page" in url:return [approved]
            if url.endswith("/comments"):return {"html_url":"https://github.com/example/receipt"}
            raise AssertionError("unexpected GitHub resource")
        with tempfile.TemporaryDirectory() as folder, \
            patch.object(wake,"gh_json",side_effect=api), \
            patch.object(wake,"execute_original_team",return_value=bot) as execute, \
            patch.dict("os.environ",{"GITHUB_RUN_ID":"321"}):
            result=wake.process(498,"original_ephemeral",Path(folder),
                                require_founder_approval=True)
        self.assertEqual(result["status"],"VERIFIED_BOUNDED_TEAM")
        self.assertTrue(result["original_multi_specialist"])
        execute.assert_called_once()
        with tempfile.TemporaryDirectory() as folder, \
            patch.object(wake,"gh_json",side_effect=lambda url,*args,**kwargs:
                prior if url.endswith("/498") else []):
            with self.assertRaises(PermissionError):
                wake.process(498,"original_ephemeral",Path(folder),
                             require_founder_approval=True)

    def test_owner_direct_wake_reserves_before_worker_and_never_replays(self):
        # Exactly the original Minister's missed-dispatch marker is used.
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from plenum_ai import public_issue_wake as wake
        from plenum_ai.minister_missed_public_wake import (
            LEGACY_OWNER_APPROVAL, RECOVERY_MAGIC,
        )
        original = issue(
            number=498, comments=1, created_at="2026-11-11T20:38:55Z",
            title="[Plenum Chief] public mission",
            body=("PLENUM_CHIEF_PUBLIC_MISSION_V1\n"
                  "objective: Research free documentary sources and original SVG music illustration for Plenum Terra"),
        )
        approval = {"user": {"login": "chadkhalil21-svg"},
                    "body": LEGACY_OWNER_APPROVAL + "\noriginal founder-approved work"}
        reservation = RECOVERY_MAGIC + "498 -->"
        posted = []
        def api(url, token, *, body=None):
            if url.endswith("/498"):
                return original
            if "/comments?per_page" in url:
                return [approval]
            if url.endswith("/comments"):
                posted.append(body["body"])
                return {"html_url": "https://github.com/example/verified-comment"}
            raise AssertionError("Unexpected endpoint")
        def team(event, *, output_dir):
            self.assertEqual(len(posted), 1)
            self.assertIn(reservation, posted[0])
            return {"status": "VERIFIED_BOUNDED_TEAM", "executed_workers": 2,
                    "independent_verified": True}
        with tempfile.TemporaryDirectory() as folder, \
                patch.object(wake, "gh_json", side_effect=api), \
                patch.object(wake, "execute_original_team", side_effect=team) as worker, \
                patch.dict("os.environ", {"GITHUB_RUN_ID": "12345"}):
            result = wake.process(498, "original_ephemeral", Path(folder),
                                  require_founder_approval=True)
        self.assertTrue(result["worker_reexecuted"])
        self.assertEqual(worker.call_count, 1)
        self.assertEqual(len(posted), 2)
        self.assertIn(reservation, posted[0])
        self.assertIn("Status: **VERIFIED_BOUNDED_TEAM**", posted[1])

        original["comments"] = 2
        prior = {"user": {"login": "github-actions[bot]"},
                 "body": posted[0]}
        with tempfile.TemporaryDirectory() as folder, \
                patch.object(wake, "gh_json", side_effect=lambda url, *args, **kwargs:
                    original if url.endswith("/498") else [approval, prior]), \
                patch.object(wake, "execute_original_team") as worker:
            result = wake.process(498, "original_ephemeral", Path(folder),
                                  require_founder_approval=True)
            self.assertEqual(result["status"], "ALREADY_RECORDED")
            self.assertFalse(result["worker_reexecuted"])
            worker.assert_not_called()

    def test_interrupted_wake_cannot_be_replayed_through_dispatch(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from plenum_ai import public_issue_wake as wake
        from plenum_ai.minister_missed_public_wake import LEGACY_OWNER_APPROVAL, RECOVERY_MAGIC
        for direct in (False, True):
            with self.subTest(direct=direct), tempfile.TemporaryDirectory() as folder:
                original = issue(number=498, created_at="2026-11-11T20:38:55Z")
                comments = [{"user": {"login": "chadkhalil21-svg"},
                             "body": LEGACY_OWNER_APPROVAL}]
                if not direct:
                    comments.append({"user": {"login": "github-actions[bot]"},
                                     "body": RECOVERY_MAGIC + "498 -->\nScheduled dispatch only"})
                attempts = []
                def api(url, token, *, body=None):
                    if url.endswith("/498"):
                        return {**original, "comments": len(comments)}
                    if "/comments?per_page" in url:
                        return list(comments)
                    if url.endswith("/comments"):
                        comments.append({"user": {"login": "github-actions[bot]"},
                                         "body": body["body"]})
                        return {"html_url": "https://github.com/example/receipt"}
                    raise AssertionError("unexpected resource")
                def worker(event, *, output_dir):
                    attempts.append(event["issue"]["number"])
                    if len(attempts) == 1:
                        raise RuntimeError("interrupted after invocation")
                    return {"status": "DRAFT_READY_FOR_FOUNDER", "verified": True}
                with patch.object(wake, "gh_json", side_effect=api), \
                     patch.object(wake, "run_issue", side_effect=worker), \
                     patch.dict("os.environ", {"GITHUB_RUN_ID": "1212"}):
                    with self.assertRaisesRegex(RuntimeError, "interrupted after invocation"):
                        wake.process(498, "scoped", Path(folder), require_founder_approval=direct)
                    outcome = wake.process(498, "scoped", Path(folder))
                self.assertEqual(attempts, [498])
                self.assertEqual(outcome["status"], "ALREADY_RECORDED")
                self.assertFalse(outcome["worker_reexecuted"])

    def test_closed_untrusted_or_unbounded_issues_rejected(self):
        for bad in (issue(state="closed"),issue(user={"login":"attacker"}),
                    issue(title="misc"),issue(body="free text"),
                    issue(pull_request={"url":"none"})):
            with self.subTest(bad=bad):
                with self.assertRaises((ValueError,PermissionError)):
                    build_original_event(bad,[])
        with self.assertRaises(ValueError):
            build_original_event(issue(),[{}]*100)
        for value in (-1,0,1000000000,True,"45"):
            with self.assertRaises(ValueError):
                checked_issue_number(value)

if __name__=="__main__":
    unittest.main()

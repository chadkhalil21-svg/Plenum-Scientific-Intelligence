"""Founder-issued real Chief command: isolated nonsecret policy tests only."""
import json
from unittest import TestCase
from unittest.mock import patch

from plenum_ai.chief_workforce_command import (
    CHIEF_MAGIC, CHIEF_TITLE, FORBIDDEN, KIND_TO_AGENT, MODEL_URL,
    execute, independent_expected_kind, parse_founder_chief, preflight,
    worker_event, recover_unexecuted_correct_model_route,
    execute_bounded_single,
)

REPO = "chadkhalil21-svg/Plenum-Scientific-Intelligence"
OWNER = "chadkhalil21-svg"


def event(objective="Create a public data validator for scientific observations",
          actor=OWNER, title=CHIEF_TITLE, body=None, issue_number=902):
    return {
        "action": "opened",
        "repository": {"full_name": REPO},
        "issue": {
            "number": issue_number, "user": {"login": actor},
            "title": title, "body": body if body is not None else
            CHIEF_MAGIC + "\nobjective: " + objective,
        },
    }


class FounderChiefWorkforcePolicy(TestCase):
    def test_real_founder_one_task_without_technical_worker_kind(self):
        e=event()
        x=parse_founder_chief(e)
        self.assertEqual(x["issue_number"],902)
        self.assertEqual(independent_expected_kind(x["objective"]),"public_program")
        self.assertEqual(len(KIND_TO_AGENT),4)
        self.assertEqual(set(KIND_TO_AGENT),{
            "public_research","public_program","public_science","public_creative"})

    def test_bounded_other_three_domains(self):
        for objective, expected in [
            ("Survey public literature on open educational research sources", "public_research"),
            ("Check the thermal cooling numerical model for a known sample", "public_science"),
            ("Draw an original SVG illustration of botanical patterns", "public_creative"),
        ]:
            with self.subTest(objective=objective):
                self.assertEqual(independent_expected_kind(objective),expected)
                self.assertEqual(parse_founder_chief(event(objective))["objective"],objective)

    def test_founder_research_about_software_does_not_misroute_to_coding(self):
        original = "Research free local software and reusable AI agent skills"
        self.assertEqual(independent_expected_kind(original), "public_research")
        self.assertEqual(preflight(event(original))["expected_independent_kind"],
                         "public_research")
        # Creating software remains distinct from merely researching it.
        with self.assertRaises(ValueError):
            independent_expected_kind("Create research software for exploring papers")

    def test_reject_unauthorized_sensitive_and_ambiguous_tasks(self):
        for unauthorized in [
            event(actor="untrusted-user"),
            event(title="untrusted"),
            event(body="PLENUM_CHIEF_PUBLIC_V1\nobjective: too short"),
            event(body="PLENUM_CHIEF_PUBLIC_V1\nobjective: Send email with private customer records"),
            event(body="PLENUM_CHIEF_PUBLIC_V1\nobjective: Review private confidential patent research"),
            event(body="PLENUM_CHIEF_PUBLIC_V1\nobjective: Deploy code to live production platform"),
            event(body="PLENUM_CHIEF_PUBLIC_V1\nobjective: Prepare code\nkind: malicious"),
            event(body="PLENUM_CHIEF_PUBLIC_V1\nobjective: Read  password"),
            event(body=CHIEF_MAGIC+"\nobjective: Build a program with secret login token"),
            event(issue_number=-1),
        ]:
            with self.subTest(body=str(unauthorized)[:60]):
                with self.assertRaises((ValueError,PermissionError)):
                    parse_founder_chief(unauthorized)
        for ambiguous in [
            "Please work on this important interesting business task",
            "Create research software for exploring papers",
            "Invent an autonomous artificial intelligence platform",
        ]:
            with self.assertRaises(ValueError):
                independent_expected_kind(ambiguous)

    def test_existing_worker_exact_type_and_owner_checked_not_new_agents(self):
        for kind in KIND_TO_AGENT:
            with self.subTest(kind=kind):
                rewritten=worker_event(event(),kind)
                self.assertEqual(rewritten["issue"]["user"]["login"],OWNER)
                self.assertTrue(rewritten["issue"]["body"].startswith(
                    "PLENUM_PUBLIC_WORKFORCE_V2\nkind: "+kind))
        self.assertFalse(any("payment" in x for x in KIND_TO_AGENT))

    def test_redundant_model_task_calls_never_claim_another_executed_worker(self):
        from plenum_ai.chief_workforce_command import independently_accept_delegation
        expected="public_program"
        role="coding-specialist"
        once=[{"kind":"public_program","outcome":{"status":"DRAFT_READY_FOR_FOUNDER"}}]
        self.assertTrue(independently_accept_delegation(expected,[role],once,1))
        self.assertTrue(independently_accept_delegation(expected,[role]*5,once,5))
        self.assertFalse(independently_accept_delegation(
            expected,["research-specialist",role],once,2))
        self.assertFalse(independently_accept_delegation(
            expected,[role],[],1))
        self.assertFalse(independently_accept_delegation(
            expected,[role],once*2,1))
        self.assertFalse(independently_accept_delegation(
            expected,[],once,0))
        self.assertFalse(independently_accept_delegation(
            expected,[role],once,2))


    def test_correct_model_route_with_no_tool_execution_has_one_bounded_recovery(self):
        from pathlib import Path
        e=event(issue_number=903)
        calls=[]
        observations=[]
        def worker(original, *, output_dir):
            calls.append((original["issue"]["body"],output_dir))
            return {"status":"DRAFT_READY_FOR_FOUNDER","verified":True,
                    "output_artifact":"issue-903/code","worker":"program_foundry"}
        with patch("plenum_ai.chief_workforce_command.run_issue",side_effect=worker):
            recovered=recover_unexecuted_correct_model_route(
                e, expected="public_program",
                routed_roles=["coding-specialist"], observations=observations,
                output_dir=Path("reports/workforce-chief"))
        self.assertTrue(recovered)
        self.assertEqual(len(calls),1)
        self.assertEqual(len(observations),1)
        self.assertEqual(observations[0]["outcome"]["status"],"DRAFT_READY_FOR_FOUNDER")
        self.assertEqual(observations[0]["kind"],"public_program")

    def test_wrong_route_or_already_called_worker_never_recovers_or_duplicates(self):
        from pathlib import Path
        e=event(issue_number=904)
        for roles, observations in [
            (["research-specialist"],[]),
            ([],[]),
            (["coding-specialist"],[{"kind":"public_program","outcome":{}}]),
        ]:
            with self.subTest(roles=roles):
                with patch("plenum_ai.chief_workforce_command.run_issue",
                           side_effect=AssertionError("must not execute second job")):
                    recovered=recover_unexecuted_correct_model_route(
                        e, expected="public_program", routed_roles=roles,
                        observations=observations, output_dir=Path("reports/workforce-chief"))
                self.assertFalse(recovered)

    def test_bounded_recovery_records_worker_failure_without_claiming_success(self):
        from pathlib import Path
        with patch("plenum_ai.chief_workforce_command.run_issue",
                   side_effect=RuntimeError("original worker failed")):
            obs=[]
            recovered=recover_unexecuted_correct_model_route(
                event(issue_number=905),expected="public_program",
                routed_roles=["coding-specialist"],observations=obs,
                output_dir=Path("reports/workforce-chief"))
        self.assertTrue(recovered)
        self.assertEqual(obs[0]["outcome"]["status"],"BLOCKED_WORKER_OR_VERIFICATION")
        self.assertFalse(obs[0]["outcome"]["verified"])

    def test_direct_known_scope_executes_exact_original_worker_once_without_model(self):
        from pathlib import Path
        e=event(issue_number=911)
        calls=[]
        def worker(item, *, output_dir):
            calls.append(item)
            return {"status":"DRAFT_READY_FOR_FOUNDER",
                    "verified":True,"output_artifact":"issue-911/code",
                    "verified_scope":"public starter syntax/hash"}
        with patch("plenum_ai.chief_workforce_command.run_issue",side_effect=worker):
            item=execute_bounded_single(e,output_dir=Path("reports/workforce-chief"))
        self.assertEqual(len(calls),1)
        self.assertEqual(item["output_artifact"],"workers/public_program/issue-911/code")
        self.assertEqual(item["status"],"VERIFIED_BOUNDED_SINGLE")
        self.assertFalse(item["model_called"])
        self.assertFalse(item["chief_delegated"])
        self.assertTrue(item["specialist_executed"])
        self.assertTrue(item["independent_verified"])
        self.assertFalse(item["general_autonomy_proved"])
        self.assertEqual(item["specialist"],"coding-specialist")

    def test_direct_worker_failure_does_not_claim_autonomy_or_result(self):
        from pathlib import Path
        with patch("plenum_ai.chief_workforce_command.run_issue",
                   side_effect=RuntimeError("unavailable")):
            item=execute_bounded_single(event(issue_number=912),
                                        output_dir=Path("reports/workforce-chief"))
        self.assertEqual(item["status"],"BLOCKED_ORIGINAL_BOUNDED_SPECIALIST")
        self.assertFalse(item["independent_verified"])
        self.assertEqual(item["failure_type"],"RuntimeError")
        self.assertFalse(item["model_called"])

    def test_direct_route_still_rejects_ambiguous_or_private_work(self):
        from pathlib import Path
        with patch("plenum_ai.chief_workforce_command.run_issue",
                   side_effect=AssertionError("unauthorized tool called")):
            with self.assertRaises((PermissionError,ValueError)):
                execute_bounded_single(event("Review confidential private account secrets"),
                    output_dir=Path("reports/workforce-chief"))
            with self.assertRaises((PermissionError,ValueError)):
                execute_bounded_single(event("Create research software for exploring papers"),
                    output_dir=Path("reports/workforce-chief"))

    def test_preflight_no_model_call_no_business_account_access(self):
        x=preflight(event())
        self.assertEqual(x["status"],"SOURCE_READY_NOT_EXECUTED")
        self.assertFalse(x["model_called"])
        self.assertFalse(x["chief_delegated"])
        self.assertFalse(x["private_accounts_accessed"])
        self.assertFalse(x["website_writes_performed"])

    def test_execute_needs_actual_ephemeral_ollama_and_never_uses_public_api_key(self):
        with patch.dict("os.environ", {
            "PLENUM_EPHEMERAL_RUNNER":"", "PLENUM_CHIEF_MODEL_URL":MODEL_URL,
        }):
            with self.assertRaises(PermissionError):
                execute(event(), output_dir=__import__("pathlib").Path("reports/workforce-chief"))
        self.assertEqual(MODEL_URL,"http://127.0.0.1:11434")
        self.assertIn("credential",FORBIDDEN)


if __name__=="__main__":
    import unittest
    unittest.main()

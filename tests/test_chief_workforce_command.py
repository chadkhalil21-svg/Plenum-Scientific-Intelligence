"""Founder-issued real Chief command: isolated nonsecret policy tests only."""
import json
from unittest import TestCase
from unittest.mock import patch

from plenum_ai.chief_workforce_command import (
    CHIEF_MAGIC, CHIEF_TITLE, FORBIDDEN, KIND_TO_AGENT, MODEL_URL,
    execute, independent_expected_kind, parse_founder_chief, preflight,
    worker_event,
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

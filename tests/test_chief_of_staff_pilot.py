"""No-model policy and independent provider readback contract for Chief of Staff."""
import io
import json
import unittest
from unittest.mock import patch

from plenum_ai import chief_of_staff_pilot as chief


class FakeResponse:
    status = 200

    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, size):
        return json.dumps({
            "id": 9082,
            "full_name": "langchain-ai/deepagents",
            "private": False,
            "archived": False,
            "license": {"spdx_id": "MIT"},
        }).encode("utf-8")


class FakeClient:
    def __init__(self):
        self.requests = []
    def open(self, request, timeout):
        self.requests.append((request.full_url, request.get_method(), timeout))
        return FakeResponse()


class ChiefContractTests(unittest.TestCase):
    def test_no_model_preflight_is_source_only(self):
        r = chief.preflight()
        self.assertEqual(r["mode"], "SOURCE_READY_NOT_EXECUTED")
        self.assertFalse(r["model_called"])
        self.assertFalse(r["business_account_action_executed"])
        self.assertFalse(r["paid_api_used"])
        self.assertFalse(r["subagent_delegation_verified"])
        self.assertTrue(r["approval_required_for_external_writes"])

    def test_unapproved_url_or_project_is_rejected(self):
        for bad in (
            "example.org/foo", "chadkhalil21-svg/private",
            "langchain-ai/deepagents?token=stolen",
            "http://169.254.169.254/latest", "../secret"
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    chief.read_public_repo(bad)
                with self.assertRaises(ValueError):
                    chief.preflight(bad)

    def test_fixed_readonly_source_and_minimal_evidence(self):
        client = FakeClient()
        result = chief.read_public_repo("langchain-ai/deepagents", opener=client)
        self.assertEqual(result["license_spdx"], "MIT")
        self.assertEqual(result["repository_id"], 9082)
        self.assertEqual(client.requests, [
            ("https://api.github.com/repos/langchain-ai/deepagents", "GET", 12)
        ])
        self.assertEqual(
            set(result),
            {"repository", "repository_id", "license_spdx", "source", "fetched_over_https"}
        )

    def test_invalid_source_identity_rejected(self):
        class Wrong(FakeResponse):
            def read(self, size):
                return json.dumps({
                    "id": 9082, "full_name": "private/not-deepagents",
                    "private": True, "archived": False,
                    "license": {"spdx_id": "MIT"}
                }).encode()
        class WrongClient(FakeClient):
            def open(self, request, timeout): return Wrong()
        with self.assertRaises(ValueError):
            chief.read_public_repo("langchain-ai/deepagents", opener=WrongClient())

    def test_runtime_requires_isolation_even_with_library_installed(self):
        with patch.dict("os.environ", {"PLENUM_EPHEMERAL_RUNNER": ""},
                        clear=True):
            with self.assertRaisesRegex(RuntimeError, "isolated"):
                chief.run()

    def test_scope_and_approval_rules_are_loaded_from_real_skill(self):
        s = chief.skill_prompt()
        self.assertIn("ALL Plenum programs", s)
        self.assertIn("task tool", s)
        self.assertIn("upstream-auditor", s)
        self.assertIn("$0", s)
        self.assertIn("No spending", s)

    def test_network_redirect_handler_refuses_redirects(self):
        self.assertIsNone(
            chief.NoRedirects().redirect_request(None, None, 302, "", {}, "http://internal/")
        )


if __name__ == "__main__":
    unittest.main()

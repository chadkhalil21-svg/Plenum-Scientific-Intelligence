"""Tiny zero-network contract test: no Browser Use install or model key needed."""
import runpy
import unittest
from pathlib import Path

MODULE = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "tools" / "browser-use" / "public_agent.py"),
    run_name="plenum_browser_use_public_policy",
)


class BrowserUsePolicyTest(unittest.TestCase):
    def test_exact_founder_command_only(self):
        check = MODULE["founder_task_valid"]
        author, title, body = MODULE["OWNER"], MODULE["TITLE"], MODULE["BODY"]
        self.assertTrue(check(author=author, title=title, body=body))
        for a, t, b in [
            ("other", title, body),
            (author, "anything else", body),
            (author, title, body + " run private account"),
            (author, title, "https://bank.example"),
        ]:
            with self.subTest(title=t, body=b):
                self.assertFalse(check(author=a, title=t, body=b))

    def test_upstream_is_optional_and_domain_is_frozen(self):
        s = MODULE["public_agent_settings"]()
        self.assertEqual(s["target"], "https://example.com/")
        self.assertEqual(s["allowed_domains"], ["example.com"])
        self.assertEqual(s["max_steps"], 5)
        self.assertEqual(s["cloud_browser"], False)
        self.assertEqual(s["site_mutations_approved"], False)
        self.assertEqual(s["user_credentials_available"], False)
        self.assertIn("Do not navigate to any other site", s["task"])


if __name__ == "__main__":
    unittest.main()

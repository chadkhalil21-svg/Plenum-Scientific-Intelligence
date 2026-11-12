"""Tiny zero-network contract test: no Browser Use install or model key needed."""
import runpy
import unittest
import os
from unittest.mock import patch
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
        self.assertTrue(check(author=author, title=MODULE["LOCAL_TITLE"], body=MODULE["LOCAL_BODY"]))
        for a, t, b in [
            ("other", title, body),
            (author, "anything else", body),
            (author, title, body + " run private account"),
            (author, title, "https://bank.example"),
        ]:
            with self.subTest(title=t, body=b):
                self.assertFalse(check(author=a, title=t, body=b))

    def test_no_key_never_falls_back_to_paid_model(self):
        fn = MODULE["free_model_config"]
        with patch.dict(os.environ, {"OPENAI_API_KEY": "fake-paid-key"}, clear=True):
            self.assertIsNone(fn())
        with patch.dict(os.environ, {"BROWSER_USE_OPENROUTER_FREE_KEY": "fake-test-key"}, clear=True):
            config = fn()
            self.assertEqual(config["provider"], "openrouter_free")
            self.assertEqual(config["model"], "openrouter/free")
            self.assertEqual(config["base_url"], "https://openrouter.ai/api/v1")

    def test_explicit_local_ollama_needs_no_paid_or_free_api_key(self):
        with patch.dict(os.environ, {
            "PLENUM_BROWSER_FREE_LOCAL": "confirmed",
            "OPENAI_API_KEY": "unrelated-key-ignored",
        }, clear=True):
            config = MODULE["free_model_config"]()
            self.assertEqual(config["provider"], "local_ollama")
            self.assertEqual(config["model"], "qwen3:1.7b")
            self.assertEqual(config["base_url"], "http://127.0.0.1:11434")
            self.assertIsNone(config["key"])
        with patch.dict(os.environ, {"PLENUM_BROWSER_FREE_LOCAL": "no"}, clear=True):
            self.assertIsNone(MODULE["free_model_config"]())

    def test_upstream_is_optional_and_domain_is_frozen(self):
        s = MODULE["public_agent_settings"]()
        self.assertEqual(s["target"], "https://example.com/")
        self.assertEqual(s["allowed_domains"], ["example.com"])
        self.assertEqual(s["max_steps"], 5)
        self.assertEqual(s["ephemeral_ci_launch_args"], [
            "--no-sandbox", "--disable-dev-shm-usage"
        ])
        self.assertEqual(s["cloud_browser"], False)
        self.assertEqual(s["site_mutations_approved"], False)
        self.assertEqual(s["user_credentials_available"], False)
        self.assertIn("Do not navigate to any other site", s["task"])


if __name__ == "__main__":
    unittest.main()

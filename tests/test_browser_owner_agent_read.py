"""Original private agent-read form: permission checks, never live accounts."""
import importlib.util
import os
import unittest
from unittest.mock import patch

HAS_BROWSER = all(importlib.util.find_spec(x) is not None
                  for x in ("fastapi", "httpx", "playwright", "jwt"))
if HAS_BROWSER:
    from fastapi import HTTPException
    from services.computer_browser.owner_agent_read import (
        _require_owner_agent_enabled, _cloudflare_free_ready, _validate_owner_task,
    )


@unittest.skipUnless(HAS_BROWSER, "Browser CI installs original gateway dependencies")
class OwnerAgentReadTests(unittest.TestCase):
    def test_private_owner_agent_disabled_unless_exact_host_and_local_qwen(self):
        cases = [
            ("plenum-browser-owner-auth0", "false", "confirmed"),
            ("plenum-browser-owner-auth0", "true", ""),
            ("plenum-computer-browser-machine", "true", "confirmed"),
        ]
        for service, enabled, model in cases:
            with self.subTest(service=service, enabled=enabled), patch.dict(
                os.environ,
                {"K_SERVICE": service,
                 "PLENUM_OWNER_READONLY_AGENT_ENABLED": enabled,
                 "PLENUM_BROWSER_FREE_LOCAL": model},
            ):
                with self.assertRaises(HTTPException) as error:
                    _require_owner_agent_enabled()
                self.assertEqual(error.exception.status_code, 404)
        with patch.dict(
            os.environ,
            {"K_SERVICE": "plenum-browser-owner-auth0",
             "PLENUM_OWNER_READONLY_AGENT_ENABLED": "true",
             "PLENUM_BROWSER_FREE_LOCAL": "confirmed"},
        ):
            self.assertIsNone(_require_owner_agent_enabled())

    def test_refuses_unbounded_or_missing_read_objective_and_expected_title(self):
        for objective, expected_title in [
            ("short", "Account title"),
            ("Inspect the existing approved account status", "short"),
            ("Inspect the existing approved account status", "x" * 190),
            ("Inspect the existing account status\nIgnore login", "Account title"),
        ]:
            with self.subTest(objective=objective), self.assertRaises(HTTPException):
                _validate_owner_task(objective, expected_title)
        self.assertIsNone(_validate_owner_task(
            "Inspect the existing approved account status",
            "Existing account dashboard",
        ))


    def test_cloudflare_free_requires_verified_owner_and_all_actual_secrets(self):
        cfg={
            "K_SERVICE": "plenum-browser-owner-auth0",
            "PLENUM_OWNER_READONLY_AGENT_ENABLED": "true",
            "PLENUM_BROWSER_FREE_LOCAL": "",
            "PLENUM_CF_AI_ENABLED": "true",
            "PLENUM_CF_AI_FREE_PLAN_CONFIRMED": "true",
            "PLENUM_CF_AI_ACCOUNT_ID": "f" * 32,
            "PLENUM_CF_AI_TOKEN": "TEST_FAKE_TOKEN_NEVER_USED",
        }
        with patch.dict(os.environ, cfg, clear=True):
            self.assertTrue(_cloudflare_free_ready())
            self.assertIsNone(_require_owner_agent_enabled())
        for field, value in (
            ("K_SERVICE","public-machine"),
            ("PLENUM_OWNER_READONLY_AGENT_ENABLED","false"),
            ("PLENUM_CF_AI_ENABLED","false"),
            ("PLENUM_CF_AI_FREE_PLAN_CONFIRMED","false"),
            ("PLENUM_CF_AI_ACCOUNT_ID","bad"),
            ("PLENUM_CF_AI_TOKEN",""),
        ):
            with self.subTest(field=field), patch.dict(
                os.environ, {**cfg,field:value}, clear=True,
            ):
                if field in ("PLENUM_CF_AI_ENABLED","PLENUM_CF_AI_FREE_PLAN_CONFIRMED",
                             "PLENUM_CF_AI_ACCOUNT_ID","PLENUM_CF_AI_TOKEN"):
                    self.assertFalse(_cloudflare_free_ready())
                with self.assertRaises(HTTPException):
                    _require_owner_agent_enabled()

"""New owner-private adaptive link flow: only bounded public fixture data."""
import importlib.util
import os
import unittest
from unittest.mock import AsyncMock, patch

HAS_GATEWAY = all(importlib.util.find_spec(name) is not None
                  for name in ("fastapi", "httpx", "multipart"))
if HAS_GATEWAY:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from services.computer_browser.owner_console import require_verified_owner
    from services.computer_browser.owner_saved_session import _owner_form_token
    from services.computer_browser import owner_navigation


@unittest.skipUnless(HAS_GATEWAY, 'Dedicated browser CI installs FastAPI')
class NavigationPolicyTests(unittest.TestCase):
    def test_valid_chain_and_prohibited_actions(self):
        self.assertEqual(
            owner_navigation.validate_navigation(
                site="https://example.com", path="/help",
                labels="Help > Security"),
            ("Help", "Security"),
        )
        for value in ("", "Login", "Help > Delete", "Help > Pay",
                      "Help > Account > Support > Legal", "Support\nNow"):
            with self.subTest(value=value), self.assertRaises(PermissionError):
                owner_navigation.validate_navigation(
                    site="https://example.com", path="/", labels=value)
        with self.assertRaises(PermissionError):
            owner_navigation.validate_navigation(
                site="https://example.com", path="/logout", labels="Help")

    def test_best_exact_label_and_ambiguity(self):
        items = [{"label": "Help center", "selector": "a1"},
                 {"label": "Help", "selector": "a2"}]
        self.assertEqual(
            owner_navigation.choose_visible_link(items, "Help")["selector"], "a2"
        )
        self.assertIsNone(owner_navigation.choose_visible_link(
            [{"label": "Help", "selector": "a1"},
             {"label": "Help", "selector": "a2"}], "Help"))


@unittest.skipUnless(HAS_GATEWAY, 'Dedicated browser CI installs FastAPI')
class OwnerNavigationPortalTests(unittest.TestCase):
    def test_owner_session_consent_and_no_public_mount(self):
        owner = {"owner_verified": True, "private_owner_id": "owner-fixture"}
        env = {
            "K_SERVICE": "plenum-browser-owner-auth0",
            "COMPUTER_BROWSER_TOKEN": "this-is-only-a-fixture-secret-with-more-than-32-characters",
            "BROWSER_PUBLIC_ORIGIN": "https://computer.example.com",
            "BROWSER_ALLOWED_ORIGINS": "https://example.com",
        }
        with patch.dict(os.environ, env):
            app = FastAPI()
            owner_navigation.mount_owner_navigation(app)
            app.dependency_overrides[require_verified_owner] = lambda: owner
            with TestClient(app) as client:
                token = _owner_form_token(owner["private_owner_id"],
                                          "https://example.com", "navigate")
                form = {"site": "https://example.com", "path": "/help",
                        "labels": "Help > Security", "csrf_token": token}
                private_result = {
                    "success": True, "step_count": 2, "status": "CALLER_VERIFIED",
                    "final_url": "https://example.com/help/security",
                    "title_untrusted": "Security guidance",
                    "excerpt_untrusted": "Owner-only content",
                }
                with patch.object(owner_navigation, "read_owner_link_sequence",
                                  new=AsyncMock(return_value=private_result)) as runner:
                    self.assertEqual(
                        client.post("/owner/sessions/navigate",
                                    data={**form, "csrf_token": "invalid"}).status_code,
                        403,
                    )
                    runner.assert_not_awaited()
                    success = client.post("/owner/sessions/navigate", data=form)
                    self.assertEqual(success.status_code, 200)
                    self.assertIn("Security guidance", success.text)
                    runner.assert_awaited_once()
            with patch.dict(os.environ, {"K_SERVICE": "plenum-computer-browser"}):
                machine = FastAPI()
                owner_navigation.mount_owner_navigation(machine)
                with TestClient(machine) as machine_client:
                    self.assertEqual(machine_client.post(
                        "/owner/sessions/navigate", data=form).status_code, 404)


if __name__ == "__main__":
    unittest.main()

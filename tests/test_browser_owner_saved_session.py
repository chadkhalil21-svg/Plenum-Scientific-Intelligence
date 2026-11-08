"""IAP-only session restore UI tests. No real account, Cloud Run or GCS."""
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from services.computer_browser.owner_console import require_verified_owner
from services.computer_browser import owner_saved_session

app = FastAPI()
owner_saved_session.mount_owner_saved_session(app)
owner = {"owner_verified": True, "private_owner_id": "synthetic-owner-sha"}
client = TestClient(app)


class SavedWebsiteSessionRoutes(unittest.TestCase):
    def setUp(self):
        app.dependency_overrides[require_verified_owner] = lambda: owner
        self.env = patch.dict(os.environ, {
            "BROWSER_PUBLIC_ORIGIN": "https://computer.example.com",
            "BROWSER_ALLOWED_ORIGINS": "https://example.com",
            "BROWSER_PROFILE_BUCKET": "synthetic-private-bucket",
            "BROWSER_SESSION_KEY": "not-a-real-key-never-used",
        })
        self.env.start()

    def tearDown(self):
        self.env.stop()
        app.dependency_overrides.clear()

    @staticmethod
    def _store(exists=True, generation=3):
        store = MagicMock()
        store.status.return_value = {"profile_exists": exists}
        store.current_generation.return_value = generation
        return store

    def test_owner_console_lists_only_metadata_without_cookies(self):
        store = self._store()
        with patch.object(owner_saved_session.BrowserProfileStore,
                          "from_environment", return_value=store):
            response = client.get("/owner/sessions")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Saved encrypted profile exists", response.text)
        self.assertIn("https://example.com", response.text)
        self.assertNotIn("synthetic-secret-cookie", response.text)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertIn("frame-ancestors 'none'",
                      response.headers["content-security-policy"])
        store.status.assert_called_once_with(
            owner=owner["private_owner_id"], origin="https://example.com")

    def test_missing_vault_config_fails_closed(self):
        with patch.dict(os.environ, {"BROWSER_PROFILE_BUCKET": "",
                                     "BROWSER_SESSION_KEY": ""}):
            response = client.get("/owner/sessions")
        self.assertEqual(response.status_code, 200)
        self.assertIn("not yet provisioned", response.text)
        self.assertNotIn("Saved encrypted profile exists", response.text)

    def test_owner_approval_requires_signed_iap_even_if_email_forged(self):
        app.dependency_overrides.clear()
        response = client.get(
            "/owner/sessions", headers={
                "x-goog-authenticated-user-email": "accounts.google.com:owner@example.com"
            },
        )
        self.assertEqual(response.status_code, 401)

    def test_same_origin_and_explicit_revoke_confirmation(self):
        store = self._store()
        with patch.object(owner_saved_session.BrowserProfileStore,
                          "from_environment", return_value=store):
            data = {"site": "https://example.com", "confirmation": "REVOKE"}
            wrong = client.post(
                "/owner/sessions/revoke", data=data,
                headers={"origin": "https://attacker.example.com"})
            self.assertEqual(wrong.status_code, 403)
            missing = client.post(
                "/owner/sessions/revoke",
                data={"site": "https://example.com", "confirmation": "NO"},
                headers={"origin": "https://computer.example.com"})
            self.assertEqual(missing.status_code, 403)
            good = client.post(
                "/owner/sessions/revoke", data=data,
                headers={"origin": "https://computer.example.com"})
        self.assertEqual(good.status_code, 200)
        self.assertIn("revoked", good.text)
        store.revoke.assert_called_once_with(
            owner=owner["private_owner_id"], origin="https://example.com",
            expected_generation=3)

    def test_revoke_already_missing_is_idempotent(self):
        store = self._store(generation=None)
        with patch.object(owner_saved_session.BrowserProfileStore,
                          "from_environment", return_value=store):
            response = client.post(
                "/owner/sessions/revoke",
                data={"site": "https://example.com", "confirmation": "REVOKE"},
                headers={"origin": "https://computer.example.com"})
        self.assertEqual(response.status_code, 200)
        store.revoke.assert_not_called()

    def test_no_unapproved_site_access(self):
        with patch.object(owner_saved_session, "read_saved_site",
                          new_callable=AsyncMock) as run:
            response = client.post(
                "/owner/sessions/preview",
                data={"site": "https://attacker.example.com"},
                headers={"origin": "https://computer.example.com"})
        self.assertEqual(response.status_code, 403)
        run.assert_not_awaited()

    def test_readback_is_only_signed_owner_and_escapes_untrusted_html(self):
        payload = {"site": "https://example.com", "http_status": 200,
                   "title": "<script>bad()</script>",
                   "body": "Synthetic-only private document <img src=x>"}
        with patch.object(owner_saved_session, "read_saved_site",
                          new_callable=AsyncMock, return_value=payload) as run:
            wrong = client.post(
                "/owner/sessions/preview", data={"site": "https://example.com"},
                headers={"origin": "https://different.example.com"})
            self.assertEqual(wrong.status_code, 403)
            right = client.post(
                "/owner/sessions/preview", data={"site": "https://example.com"},
                headers={"origin": "https://computer.example.com"})
        self.assertEqual(right.status_code, 200)
        self.assertIn("&lt;script&gt;", right.text)
        self.assertNotIn("<script>bad()", right.text)
        self.assertNotIn("<img src=x>", right.text)
        run.assert_awaited_once_with(
            site="https://example.com", owner=owner["private_owner_id"])

    def test_unavailable_session_does_not_disclose_cloud_error(self):
        with patch.object(owner_saved_session, "read_saved_site",
                          new_callable=AsyncMock, side_effect=ValueError(
                              "synthetic-secret-cookie-do-not-echo")):
            resp = client.post(
                "/owner/sessions/preview", data={"site": "https://example.com"},
                headers={"origin": "https://computer.example.com"})
        self.assertEqual(resp.status_code, 502)
        self.assertNotIn("synthetic-secret-cookie", resp.text)


if __name__ == "__main__":
    unittest.main()

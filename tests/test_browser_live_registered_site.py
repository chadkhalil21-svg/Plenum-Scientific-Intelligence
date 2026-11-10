"""New owner-granted private sign-in acceptance boundaries (offline only).

Do not turn prior public demo / third-party website fixtures into an
authenticated-success claim. No external account requests occur here.
"""
import importlib.util
import os
import unittest
from unittest.mock import MagicMock, patch

HAS_HTTP = all(importlib.util.find_spec(x) is not None for x in
               ("fastapi", "httpx", "jwt", "cryptography"))

if HAS_HTTP:
    from fastapi.testclient import TestClient
    from services.computer_browser import owner_live_access as live
    from services.computer_browser.runtime_site_grants import OwnerSiteGrantStore
    from services.computer_browser import private_login
    from services.computer_browser.owner_console import require_verified_owner
    from services.computer_browser.api import app

OWNER = "a" * 64
OTHER = "b" * 64
SITE = "https://research.example.org"
ENV = {
    "BROWSER_ALLOWED_ORIGINS": "https://example.com",
    "K_SERVICE": "plenum-browser-owner-auth0",
    "PLENUM_RUNTIME_SITE_GRANTS_ENABLED": "true",
}


@unittest.skipUnless(HAS_HTTP, "Owner browser optional packages not installed")
class RegisteredOwnerLiveTests(unittest.TestCase):
    def test_existing_static_allowlist_retains_original_behavior(self):
        with patch.dict(os.environ, ENV):
            with patch.object(OwnerSiteGrantStore, "from_environment",
                              side_effect=AssertionError("Not needed for static")):
                self.assertEqual(live.owner_live_origin(
                    owner_id=OWNER, site="https://example.com/path"),
                    ("https://example.com", False))

    def test_owner_only_encrypted_registration_unlocks_one_origin(self):
        store = MagicMock()
        store.authorized.side_effect = lambda *, owner, origin: (
            owner == OWNER and origin == SITE)
        with patch.dict(os.environ, ENV):
            with patch.object(OwnerSiteGrantStore, "from_environment",
                              return_value=store):
                self.assertEqual(live.owner_live_origin(
                    owner_id=OWNER, site=SITE + "/signin"),
                    (SITE, True))
                store.authorized.assert_called_with(owner=OWNER, origin=SITE)
                with self.assertRaises(PermissionError):
                    live.owner_live_origin(owner_id=OTHER, site=SITE + "/signin")
                with self.assertRaises(PermissionError):
                    live.owner_live_origin(owner_id=OWNER,
                                           site="https://other.example.net/")

    def test_missing_expired_or_disabled_grant_denies_without_bypass(self):
        store = MagicMock()
        store.authorized.return_value = False
        with patch.dict(os.environ, ENV):
            with patch.object(OwnerSiteGrantStore, "from_environment",
                              return_value=store):
                with self.assertRaises(PermissionError):
                    live.owner_live_origin(owner_id=OWNER, site=SITE)
            with patch.dict(os.environ,
                            {"PLENUM_RUNTIME_SITE_GRANTS_ENABLED": "false"}):
                with self.assertRaises(PermissionError):
                    live.owner_live_origin(owner_id=OWNER, site=SITE)

    def test_unsafe_origin_and_redirect_shapes_denied_before_grant_lookup(self):
        invalid = (
            "http://research.example.org/",
            "https://research.example.org:8443/",
            "https://research.example.org:443/",
            "https://127.0.0.1/",
            "https://169.254.169.254/",
            "https://username:password@research.example.org/",
            "https://research.example.org/#fragment",
            "https://research.example.org.evil.test/",
        )
        store = MagicMock()
        with patch.dict(os.environ, ENV), patch.object(
                OwnerSiteGrantStore, "from_environment",
                return_value=store):
            for url in invalid:
                with self.subTest(url=url), self.assertRaises(PermissionError):
                    live.owner_live_origin(owner_id=OWNER, site=url)
        store.authorized.assert_not_called()

    def test_owner_http_preflight_denies_unapproved_before_websocket(self):
        with patch.dict(os.environ, ENV):
            app.dependency_overrides[require_verified_owner] = (
                lambda: {"private_owner_id": OWNER})
            self.addCleanup(app.dependency_overrides.pop,
                            require_verified_owner, None)
            client = TestClient(app)
            with patch.object(OwnerSiteGrantStore,
                              "from_environment") as store:
                store.return_value.authorized.return_value = False
                denied = client.get("/owner/live-access",
                                    params={"site": SITE + "/"})
                self.assertEqual(denied.status_code, 403)
                store.return_value.authorized.return_value = True
                ok = client.get("/owner/live-access",
                                params={"site": SITE + "/signin"})
                self.assertEqual(ok.status_code, 200)
                self.assertTrue(ok.json()["pinned_single_origin"])
                self.assertFalse(ok.json()["login_restoration_verified"])
                self.assertNotIn(SITE, str(ok.json()))
                self.assertNotIn("password", str(ok.json()))

    def test_registered_site_resource_typo_does_not_masquerade_as_expired_grant(self):
        with patch.dict(os.environ, ENV):
            app.dependency_overrides[require_verified_owner] = (
                lambda: {"private_owner_id": OWNER})
            self.addCleanup(app.dependency_overrides.pop,
                            require_verified_owner, None)
            client = TestClient(app)
            with patch.object(private_login, "owner_live_origin",
                              return_value=(SITE, True)):
                bad = client.get("/owner/live-access", params={
                    "site": SITE, "resource_origins": "https://assets.example.org/",
                    "approve_resources": "1"})
                self.assertEqual(bad.status_code, 403)
                self.assertEqual(bad.json()["detail"], "resource_scope_rejected")
                self.assertNotIn("assets.example.org", str(bad.json()))
                good = client.get("/owner/live-access", params={
                    "site": SITE, "resource_origins": "https://assets.example.org",
                    "approve_resources": "1"})
                self.assertEqual(good.status_code, 200)
                self.assertEqual(good.json()["pinned_exact_origins"], 2)
            with patch.object(private_login, "owner_live_origin",
                              side_effect=PermissionError("unregistered")):
                denied = client.get("/owner/live-access", params={"site": SITE})
                self.assertEqual(denied.status_code, 403)
                self.assertEqual(denied.json()["detail"], "site_authorization_denied")

    def test_mobile_extra_origins_form_is_visible_and_rejection_is_specific(self):
        html = private_login.login_html("safe-test-nonce")
        self.assertIn('<textarea id="resource-origins" rows="3"', html)
        self.assertIn("The grey example is not entered automatically", html)
        self.assertIn('reason==="resource_scope_rejected"', html)
        self.assertIn("This does NOT mean thy main website registration failed", html)
        self.assertIn('u.searchParams.set("resource_origins",resources)', html)
        self.assertIn("autocapitalize=\"off\" spellcheck=\"false\"", html)

    def test_live_html_checks_access_before_websocket_without_leaking_site(self):
        page = private_login.login_html("synthetic-nonce")
        self.assertIn('fetch("/owner/live-access?site="+encodeURIComponent(target)',page)
        self.assertLess(page.index('access=await fetch('),
                        page.index('const connection=new WebSocket(u);'))
        self.assertIn('site_authorization_denied', open(
            "services/computer_browser/private_login.py",
            encoding="utf-8").read())
        self.assertIn('resource_scope_rejected',page)
        self.assertIn('max_lifetime=600', open(
            "services/computer_browser/private_login.py",
            encoding="utf-8").read())
        self.assertNotIn("Google password or other", "placeholder-no-secret")


if __name__ == "__main__":
    unittest.main()

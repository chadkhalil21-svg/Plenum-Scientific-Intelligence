"""Only the separate Auth0 service can use signed owner sessions.

No Auth0 network, credentials, Cloud Run, browser logins or real site writes.
"""
import importlib.util
import os
import time
import unittest
import base64
import json
import sys
import types
from unittest.mock import patch

HAS_WEB_DEPS = all(importlib.util.find_spec(x) is not None
                   for x in ("fastapi", "httpx", "itsdangerous", "authlib"))
if HAS_WEB_DEPS:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from itsdangerous import TimestampSigner
    from services.computer_browser import private_login, owner_auth0, owner_saved_session
    from services.computer_browser.owner_console import mount_owner_console

ISSUER = "https://dev-8sylxsg44yh5kkhh.us.auth0.com/"
SYNTHETIC_ENV = {
    "K_SERVICE": "plenum-browser-owner-auth0",
    "COMPUTER_BROWSER_TOKEN": "Synthetic-only-for-CI-32-byte-secret-unsafe-for-production",
    "COMPUTER_OWNER_EMAIL": "founder@example.org",
    "AUTH0_OWNER_CLIENT_ID": "",
    "AUTH0_OWNER_PUBLIC_ORIGIN": "https://plenum-browser-owner-auth0-98614162800.us-east1.run.app",
}


@unittest.skipUnless(HAS_WEB_DEPS, "Auth0 portal's optional web dependencies are not installed")
class Auth0OwnerTests(unittest.TestCase):
    def test_disabled_in_original_iap_service(self):
        with patch.dict(os.environ, {"K_SERVICE": "plenum-computer-browser"}):
            self.assertFalse(owner_auth0.active())
            with self.assertRaises(PermissionError):
                owner_auth0.verified_session({})
            self.assertRaises(PermissionError, owner_auth0._config)

    def test_only_verified_owner_claims_are_accepted(self):
        with patch.dict(os.environ, SYNTHETIC_ENV, clear=False):
            valid = {
                "sub": "auth0|synthetic-owner-subject",
                "iss": ISSUER,
                "email": "FOUNDER@example.org",
                "email_verified": True,
            }
            who = owner_auth0._verified_owner(valid)
            self.assertTrue(who["owner_verified"])
            self.assertEqual(len(who["private_owner_id"]), 64)
            self.assertNotIn("email", who)
            for bad in [
                dict(valid, email="intruder@example.org"),
                dict(valid, email_verified=False),
                dict(valid, sub="x"),
                dict(valid, iss="https://other.example.org/"),
                dict(valid, email_verified="true"),
                dict(valid, email=None),
            ]:
                with self.subTest(bad=bad), self.assertRaises(PermissionError):
                    owner_auth0._verified_owner(bad)
            with patch.dict(os.environ, {"AUTH0_OWNER_SUB": "auth0|another-identity"}):
                with self.assertRaises(PermissionError):
                    owner_auth0._verified_owner(valid)

    def test_expiring_signed_session_scope(self):
        with patch.dict(os.environ, SYNTHETIC_ENV, clear=False):
            now = int(time.time())
            owner = "a" * 64
            session = {"session": {"plenum_auth0_owner_v1": {
                "owner": owner, "iat": now - 10, "exp": now + 200,
            }}}
            self.assertEqual(owner_auth0.verified_session(session)["private_owner_id"], owner)
            for record in [
                {"owner": owner, "iat": now - 1810, "exp": now + 200},
                {"owner": owner, "iat": now - 100, "exp": now - 1},
                {"owner": "not-digest", "iat": now - 2, "exp": now + 10},
                {"owner": owner, "iat": now + 300, "exp": now + 600},
                {"owner": owner, "iat": True, "exp": now + 100},
            ]:
                with self.subTest(record=record), self.assertRaises(PermissionError):
                    owner_auth0.verified_session({
                        "session": {"plenum_auth0_owner_v1": record}
                    })
            with self.assertRaises(PermissionError):
                owner_auth0.verified_session({"session": {}})

    def test_locked_bootstrap_is_public_only_for_login_prompt(self):
        with patch.dict(os.environ, SYNTHETIC_ENV, clear=False):
            app = FastAPI()
            mount_owner_console(app)
            owner_auth0.mount_auth0_owner(app)
            client = TestClient(app)
            home = client.get("/", follow_redirects=False)
            self.assertEqual(home.status_code, 200)
            self.assertIn("Sign in securely with Auth0", home.text)
            self.assertEqual(client.get("/auth0/login").status_code, 503)
            self.assertEqual(client.get("/owner").status_code, 401)
            self.assertEqual(client.get("/owner", headers={
                "x-goog-iap-jwt-assertion": "synthetic-fake-assertion",
                "x-goog-authenticated-user-email": "founder@example.org",
            }).status_code, 401)

    def test_expired_owner_html_navigation_redirects_only_with_signed_auth_required(self):
        """A human in Edge gets sign-in rather than downloadable JSON; APIs stay 401."""
        with patch.dict(os.environ,SYNTHETIC_ENV,clear=False):
            app=FastAPI()
            mount_owner_console(app)
            private_login.mount_private_login(app)
            owner_saved_session.mount_owner_saved_session(app)
            owner_auth0.mount_auth0_owner(app)
            with TestClient(app,base_url="https://testserver") as client:
                for path in ("/owner","/owner/sign-in","/owner/sessions"):
                    with self.subTest(path=path):
                        nav=client.get(path,headers={"accept":"text/html"},
                                       follow_redirects=False)
                        self.assertEqual(nav.status_code,303)
                        self.assertEqual(nav.headers["location"],"/")
                        self.assertEqual(nav.headers["cache-control"],"no-store")
                        self.assertNotIn("plenum_auth0_owner_v1",nav.text)
                        # HTTP clients still receive normal 401, not a login redirect.
                        api=client.get(path,headers={"accept":"application/json"},
                                       follow_redirects=False)
                        self.assertEqual(api.status_code,401)
                home=client.get("/",headers={"accept":"text/html"})
                self.assertEqual(home.status_code,200)
                self.assertIn("Sign in securely with Auth0",home.text)
                # POST, even with an HTML Accept header, must never redirect.
                posted=client.post("/owner/sessions/preview",data={
                    "site":"https://example.com","csrf_token":"fake"
                },headers={"accept":"text/html"},follow_redirects=False)
                self.assertEqual(posted.status_code,401)
                # No HTML redirects for unrelated URLs or other 401 causes.
                missing=client.get("/nonexistent",headers={"accept":"text/html"},
                                   follow_redirects=False)
                self.assertEqual(missing.status_code,404)

    def test_real_auth0_session_cookie_authorizes_only_bound_websocket(self):
        # Prove the same HTTPS-only, signed owner cookie can authorize the
        # live WebSocket. No external site is contacted, and no Chromium starts.
        with patch.dict(os.environ, {
            **SYNTHETIC_ENV,
            "BROWSER_PUBLIC_ORIGIN": "https://testserver",
            "BROWSER_ALLOWED_ORIGINS": "https://example.com",
        }, clear=False):
            app = FastAPI()
            mount_owner_console(app)
            private_login.mount_private_login(app)
            owner_auth0.mount_auth0_owner(app)
            now = int(time.time())
            record = {"plenum_auth0_owner_v1": {
                "owner": "a" * 64, "iat": now - 5, "exp": now + 120,
            }}
            signed = TimestampSigner(owner_auth0._session_secret()).sign(
                base64.b64encode(json.dumps(record).encode())
            ).decode()
            ws_url = "/owner/live?site=https%3A%2F%2Fexample.com%2F"
            headers = {
                "origin": "https://testserver",
                "cookie": "__Host-plenum_browser_owner=" + signed,
            }
            with TestClient(app, base_url="https://testserver") as client:
                self.assertEqual(client.get("/owner", headers={
                    "cookie": headers["cookie"],
                }).status_code, 200)
                # The test never starts Playwright: DNS rejection is forced
                # before async_playwright() is entered. Stub the optional import
                # rather than downloading Chromium just for an auth-boundary test.
                stub = types.ModuleType("playwright.async_api")
                stub.async_playwright = lambda: None
                with patch.dict(sys.modules, {
                    "playwright": types.ModuleType("playwright"),
                    "playwright.async_api": stub,
                }):
                    with patch.object(private_login, "public_dns_only",
                                      side_effect=PermissionError("synthetic closed DNS")):
                        with client.websocket_connect(ws_url, headers=headers) as ws:
                            self.assertEqual(ws.receive_json()["type"], "status")
                            stopped = ws.receive_json()
                            self.assertTrue(stopped["failure"])
                            self.assertIn("DNS safety checks", stopped["message"])
                # Signed cookie alone cannot permit cross-origin browser use.
                with self.assertRaises(Exception):
                    with client.websocket_connect(ws_url, headers={
                        **headers, "origin": "https://attacker.example",
                    }):
                        pass
                with self.assertRaises(Exception):
                    with client.websocket_connect(ws_url, headers={
                        "origin": "https://testserver",
                    }):
                        pass

    def test_fixed_callback_origin_and_no_open_redirect(self):
        with patch.dict(os.environ, {
            **SYNTHETIC_ENV,
            "AUTH0_OWNER_CLIENT_ID": "TESTonlyClient1234",
        }, clear=False):
            cid, origin = owner_auth0._config()
            self.assertEqual(cid, "TESTonlyClient1234")
            self.assertEqual(
                origin, "https://plenum-browser-owner-auth0-98614162800.us-east1.run.app"
            )
            for dangerous in [
                "http://plenum-browser-owner-auth0-98614162800.us-east1.run.app",
                "https://user@plenum-browser-owner-auth0-98614162800.us-east1.run.app",
                "https://plenum-browser-owner-auth0-98614162800.us-east1.run.app/evil",
                "https://attacker.example.org",
                "https://plenum-browser-owner-auth0-98614162800.us-east1.run.app?x=1",
            ]:
                with self.subTest(dangerous=dangerous), patch.dict(
                    os.environ, {"AUTH0_OWNER_PUBLIC_ORIGIN": dangerous}
                ), self.assertRaises(PermissionError):
                    owner_auth0._config()

    def test_signer_requires_existing_secret(self):
        with patch.dict(os.environ, {"COMPUTER_BROWSER_TOKEN": ""}):
            with self.assertRaises(RuntimeError):
                owner_auth0._session_secret()
        with patch.dict(os.environ, SYNTHETIC_ENV, clear=False):
            secret = owner_auth0._session_secret()
            self.assertEqual(len(secret), 64)
            self.assertNotIn(SYNTHETIC_ENV["COMPUTER_BROWSER_TOKEN"], secret)


if __name__ == "__main__":
    unittest.main()

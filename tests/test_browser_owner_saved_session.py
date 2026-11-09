"""IAP-only session restore UI tests. No real account, Cloud Run or GCS."""
import asyncio
import importlib.util
import os
import re
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

HAS_GATEWAY = all(
    importlib.util.find_spec(name) is not None
    for name in ("fastapi", "httpx", "jwt", "multipart")
)
if HAS_GATEWAY:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from services.computer_browser.owner_console import require_verified_owner
    from services.computer_browser import owner_saved_session
    app = FastAPI()
    owner_saved_session.mount_owner_saved_session(app)
    owner = {"owner_verified": True, "private_owner_id": "synthetic-owner-sha"}
    client = TestClient(app)


@unittest.skipUnless(HAS_GATEWAY, "Browser gateway CI installs IAP and form dependencies")
class SavedWebsiteSessionRoutes(unittest.TestCase):
    def setUp(self):
        app.dependency_overrides[require_verified_owner] = lambda: owner
        self.env = patch.dict(os.environ, {
            "BROWSER_PUBLIC_ORIGIN": "https://computer.example.com",
            "BROWSER_ALLOWED_ORIGINS": "https://example.com",
            "BROWSER_PROFILE_BUCKET": "synthetic-private-bucket",
            "BROWSER_SESSION_KEY": "not-a-real-key-never-used",
            "COMPUTER_BROWSER_TOKEN": "synthetic-ci-only-never-use-in-production-0123456789",
        })
        self.env.start()

    def tearDown(self):
        self.env.stop()
        app.dependency_overrides.clear()

    @staticmethod
    def _form(site,action,**extra):
        return {"site":site,
                "csrf_token":owner_saved_session._owner_form_token(
                    owner["private_owner_id"],site,action),
                **extra}

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

    def test_approved_demo_preview_checks_protected_page(self):
        self.assertEqual(
            owner_saved_session.safe_session_preview_url("https://the-internet.herokuapp.com"),
            "https://the-internet.herokuapp.com/secure")
        self.assertEqual(
            owner_saved_session.safe_session_preview_url("https://example.com"),
            "https://example.com/")

    def test_session_status_does_not_silently_claim_no_profile_on_storage_error(self):
        store=self._store()
        store.status.side_effect=PermissionError("synthetic-cloud-denial-hidden")
        with patch.object(owner_saved_session.BrowserProfileStore,
                          "from_environment",return_value=store):
            resp=client.get("/owner/sessions")
        self.assertEqual(resp.status_code,200)
        self.assertIn("Unable to check saved profile securely",resp.text)
        self.assertNotIn("synthetic-cloud-denial-hidden",resp.text)
        self.assertNotIn("No saved profile",resp.text)
        self.assertNotIn("action='/owner/sessions/preview'",resp.text)

    def test_demo_authenticated_proof_requires_explicit_result(self):
        with patch.dict(os.environ,{
            "BROWSER_ALLOWED_ORIGINS":"https://the-internet.herokuapp.com"
        }):
            with patch.object(owner_saved_session,"read_saved_site",
                              new_callable=AsyncMock,return_value={
                "site":"https://the-internet.herokuapp.com",
                "http_status":200,"title":"Secure Area",
                "body":"Logged in as tomsmith",
                "demo_authenticated_restored":True,
            }):
                resp=client.post("/owner/sessions/preview",
                    data=self._form("https://the-internet.herokuapp.com","preview"),
                    headers={"origin":"https://computer.example.com"})
                self.assertEqual(resp.status_code,200)
                self.assertIn("Demo login restoration verified",resp.text)
                self.assertNotIn("synthetic-secret-cookie",resp.text)


    def test_native_browser_form_origin_respects_referrer_policy(self):
        """Real Chromium regression reproduces the exact 403 header mismatch.

        Fetch standard: ordinary HTML form POST with no-referrer sends
        Origin:null, whereas same-origin sends the valid owner page origin.
        Everything here is intercepted locally, no real website or identity.
        """
        self.assertEqual(owner_saved_session._HEADERS["Referrer-Policy"],
                         "same-origin")
        if importlib.util.find_spec("playwright") is None:
            self.skipTest("Playwright is not installed in this test environment")
        from playwright.sync_api import sync_playwright, Error as PlaywrightError
        origin="https://computer.example.com"
        listing=origin+"/owner/sessions"
        endpoint=origin+"/owner/sessions/preview"
        doc=("<!doctype html><html><body>"
             "<form method='post' action='/owner/sessions/preview'>"
             "<input type='hidden' name='site' value='https://example.com'>"
             "<input type='hidden' name='csrf_token' value='synthetic-ci-only'>"
             "<button type='submit'>Preview saved session (read only)</button>"
             "</form></body></html>")
        with sync_playwright() as p:
            try:
                browser=p.chromium.launch(headless=True)
            except PlaywrightError as exc:
                if "Executable doesn't exist" in str(exc):
                    self.skipTest("Chromium executable not installed in this environment")
                raise
            try:
                def submit_with_policy(policy):
                    context=browser.new_context()
                    try:
                        page=context.new_page()
                        captured=[]
                        def route_handler(route):
                            req=route.request
                            if req.url==listing and req.method=="GET":
                                route.fulfill(status=200,
                                    headers={"content-type":"text/html; charset=utf-8",
                                             "referrer-policy":policy},
                                    body=doc)
                            elif req.url==endpoint and req.method=="POST":
                                captured.append({
                                    "origin":req.headers.get("origin"),
                                    "method":req.method,
                                    "post":req.post_data,
                                })
                                route.fulfill(status=200,content_type="text/plain",
                                              body="Synthetic preview accepted")
                            else:
                                route.abort()
                        page.route("**/*",route_handler)
                        page.goto(listing)
                        page.get_by_role("button",name="Preview saved session (read only)").click()
                        page.wait_for_url(endpoint)
                        self.assertEqual(len(captured),1)
                        self.assertIn("csrf_token=synthetic-ci-only",captured[0]["post"])
                        self.assertEqual(captured[0]["method"],"POST")
                        return captured[0]["origin"]
                    finally:
                        context.close()
                self.assertEqual(submit_with_policy("no-referrer"),"null")
                self.assertEqual(submit_with_policy(
                    owner_saved_session._HEADERS["Referrer-Policy"]),origin)
            finally:
                browser.close()

    def test_mobile_form_without_origin_header_has_signed_csrf(self):
        """Native HTML form in iPad Edge may omit Origin and no-referrer hides Referer."""
        site="https://example.com"
        store=self._store()
        with patch.object(owner_saved_session.BrowserProfileStore,
                          "from_environment",return_value=store):
            html=client.get("/owner/sessions").text
        match=re.search(
            r"action='/owner/sessions/preview'>.*?name='csrf_token' value='([^']+)'",
            html,re.S)
        self.assertIsNotNone(match)
        token=match.group(1)
        # No Origin/Referer/Fetch Metadata header. Owner+signed token required.
        with patch.object(owner_saved_session,"read_saved_site",
                          new_callable=AsyncMock,return_value={
                "site":site,"title":"Synthetic read-only preview",
                "body":"Synthetic body, no credentials","http_status":200
            }) as run:
            response=client.post("/owner/sessions/preview",data={
                "site":site,"csrf_token":token,
            })
        self.assertEqual(response.status_code,200)
        self.assertIn("Synthetic read-only preview",response.text)
        run.assert_awaited_once_with(site=site,owner=owner["private_owner_id"])

    def test_csrf_missing_wrong_site_action_owner_and_foreign_headers_rejected(self):
        site="https://example.com"
        good=self._form(site,"preview")
        attempts=[
            ({"site":site},{}),
            ({"site":site,"csrf_token":"altered.invalid"},{}),
            ({"site":site,"csrf_token":self._form(site,"revoke")["csrf_token"]},{}),
            ({"site":site,"csrf_token":owner_saved_session._owner_form_token(
                "another-test-owner",site,"preview")},{}),
            (good,{"origin":"https://attacker.example.com"}),
            (good,{"origin":"null"}),
            (good,{"referer":"https://attacker.example.com/evil"}),
            (good,{"sec-fetch-site":"cross-site"}),
        ]
        with patch.object(owner_saved_session,"read_saved_site",
                          new_callable=AsyncMock) as read:
            for data,headers in attempts:
                with self.subTest(data=data,headers=headers):
                    response=client.post("/owner/sessions/preview",
                                         data=data,headers=headers)
                    self.assertEqual(response.status_code,403)
            read.assert_not_awaited()

    def test_expired_signed_form_token_is_rejected(self):
        site="https://example.com"
        with patch.object(owner_saved_session.time,"time",return_value=1700000000):
            token=owner_saved_session._owner_form_token(
                owner["private_owner_id"],site,"preview")
        with patch.object(owner_saved_session.time,"time",return_value=1700001801):
            with patch.object(owner_saved_session,"read_saved_site",
                              new_callable=AsyncMock) as read:
                response=client.post("/owner/sessions/preview",
                                     data={"site":site,"csrf_token":token})
        self.assertEqual(response.status_code,403)
        read.assert_not_awaited()

    def test_revoke_requires_distinct_signed_action_even_with_confirmation(self):
        site="https://example.com"
        store=self._store()
        with patch.object(owner_saved_session.BrowserProfileStore,
                          "from_environment",return_value=store):
            cross=client.post("/owner/sessions/revoke",data={
                "site":site,"confirmation":"REVOKE",
                "csrf_token":self._form(site,"preview")["csrf_token"],
            })
            missing=client.post("/owner/sessions/revoke",data={
                "site":site,"confirmation":"REVOKE",
            })
        self.assertEqual(cross.status_code,403)
        self.assertEqual(missing.status_code,403)
        store.revoke.assert_not_called()

    def test_owner_signed_demo_refresh_is_fixed_origin_and_action_scoped(self):
        demo="https://the-internet.herokuapp.com"
        with patch.dict(os.environ,{"BROWSER_ALLOWED_ORIGINS":demo}):
            store=self._store()
            with patch.object(owner_saved_session.BrowserProfileStore,
                              "from_environment",return_value=store):
                html=client.get("/owner/sessions").text
            self.assertIn("Refresh and verify public demo login",html)
            match=re.search(
                r"action='/owner/sessions/demo-refresh'>.*?name='csrf_token' value='([^']+)'",
                html,re.S)
            self.assertIsNotNone(match)
            refresh_token=match.group(1)
            preview_token=self._form(demo,"preview")["csrf_token"]
            with patch.object(owner_saved_session,
                              "_refresh_and_verify_public_demo",
                              new_callable=AsyncMock,return_value="verified") as refresh:
                good=client.post("/owner/sessions/demo-refresh",
                    data={"csrf_token":refresh_token})
                self.assertEqual(good.status_code,200)
                self.assertIn("Demo login restoration verified",good.text)
                refresh.assert_awaited_once_with(owner["private_owner_id"])
                for bad_data,bad_headers in [
                    ({},{}),
                    ({"csrf_token":preview_token},{}),
                    ({"csrf_token":refresh_token},{"origin":"https://attacker.example.com"}),
                    ({"csrf_token":refresh_token},{"sec-fetch-site":"cross-site"}),
                ]:
                    result=client.post("/owner/sessions/demo-refresh",
                                       data=bad_data,headers=bad_headers)
                    self.assertEqual(result.status_code,403)
                self.assertEqual(refresh.await_count,1)

    def test_non_demo_allowlist_never_offers_or_runs_public_demo_refresh(self):
        store=self._store()
        with patch.object(owner_saved_session.BrowserProfileStore,
                          "from_environment",return_value=store):
            html=client.get("/owner/sessions").text
        self.assertNotIn("Refresh and verify public demo login",html)
        with patch.object(owner_saved_session,"_refresh_and_verify_public_demo",
                          new_callable=AsyncMock) as run:
            response=client.post("/owner/sessions/demo-refresh",
                data={"csrf_token":self._form(
                    "https://the-internet.herokuapp.com","demo_refresh")["csrf_token"]})
            self.assertEqual(response.status_code,403)
            run.assert_not_awaited()

    def test_failed_public_demo_refresh_does_not_claim_login_restoration(self):
        demo="https://the-internet.herokuapp.com"
        token=self._form(demo,"demo_refresh")["csrf_token"]
        with patch.dict(os.environ,{"BROWSER_ALLOWED_ORIGINS":demo}):
            with patch.object(owner_saved_session,
                              "_refresh_and_verify_public_demo",
                              new_callable=AsyncMock,return_value="demo_login_not_verified"):
                response=client.post("/owner/sessions/demo-refresh",
                                     data={"csrf_token":token})
            self.assertEqual(response.status_code,200)
            self.assertIn("existing saved profile was not changed",response.text)
            self.assertNotIn("Demo login restoration verified",response.text)
            with patch.object(owner_saved_session,
                              "_refresh_and_verify_public_demo",
                              new_callable=AsyncMock,return_value="saved_but_not_restored"):
                failed=client.post("/owner/sessions/demo-refresh",
                                   data={"csrf_token":token})
            self.assertEqual(failed.status_code,200)
            self.assertIn("saved but not restored",failed.text.lower())
            self.assertNotIn("Demo login restoration verified",failed.text)

    def test_synthetic_public_demo_login_cookie_captured_in_actual_chromium(self):
        """No external website, site account, storage or owner data used."""
        if importlib.util.find_spec("playwright") is None:
            self.skipTest("Playwright is unavailable")
        from playwright.async_api import async_playwright
        demo=owner_saved_session.PUBLIC_DEMO_ORIGIN
        async def exercise():
            async def fixture(route):
                req=route.request
                path=req.url[len(demo):]
                if req.method=="GET" and path=="/login":
                    await route.fulfill(status=200,content_type="text/html",
                        body="<form action='/authenticate' method='POST'>"
                             "<input id='username' name='username'>"
                             "<input id='password' name='password' type='password'>"
                             "<button type='submit'>Login</button></form>")
                elif req.method=="POST" and path=="/authenticate":
                    if ("username=tomsmith" not in (req.post_data or "")
                            or "password=SuperSecretPassword" not in (req.post_data or "")):
                        await route.fulfill(status=403,body="Invalid synthetic request")
                    else:
                        await route.fulfill(status=302,headers={
                            "location":"/secure",
                            "set-cookie":"rack.session=CI_FAKE_COOKIE;"
                                " Path=/; Secure; HttpOnly; SameSite=Lax"
                        },body="")
                elif req.method=="GET" and path=="/secure":
                    if "rack.session=CI_FAKE_COOKIE" not in (await req.all_headers()).get("cookie",""):
                        await route.fulfill(status=302,headers={"location":"/login"},body="")
                    else:
                        await route.fulfill(status=200,content_type="text/html",
                            body="<h3>Secure Area</h3><p>Logged in as tomsmith</p>")
                else:
                    await route.abort()
            async with async_playwright() as pw:
                browser=await pw.chromium.launch(headless=True)
                try:
                    state=await owner_saved_session._public_demo_login_snapshot(
                        browser,fixture_route=fixture)
                finally:
                    await browser.close()
            self.assertIsNotNone(state)
            self.assertEqual([c["name"] for c in state["cookies"]],
                             ["rack.session"])
            self.assertEqual(state["cookies"][0]["domain"],
                             "the-internet.herokuapp.com")
            self.assertEqual(state["origins"],[])
        asyncio.run(exercise())

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
            data = self._form("https://example.com","revoke",confirmation="REVOKE")
            wrong = client.post(
                "/owner/sessions/revoke", data=data,
                headers={"origin": "https://attacker.example.com"})
            self.assertEqual(wrong.status_code, 403)
            missing = client.post(
                "/owner/sessions/revoke",
                data=self._form("https://example.com","revoke",confirmation="NO"),
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
                data=self._form("https://example.com","revoke",confirmation="REVOKE"),
                headers={"origin": "https://computer.example.com"})
        self.assertEqual(response.status_code, 200)
        store.revoke.assert_not_called()

    def test_no_unapproved_site_access(self):
        with patch.object(owner_saved_session, "read_saved_site",
                          new_callable=AsyncMock) as run:
            response = client.post(
                "/owner/sessions/preview",
                data=self._form("https://attacker.example.com","preview"),
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
                "/owner/sessions/preview", data=self._form("https://example.com","preview"),
                headers={"origin": "https://different.example.com"})
            self.assertEqual(wrong.status_code, 403)
            right = client.post(
                "/owner/sessions/preview", data=self._form("https://example.com","preview"),
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
                "/owner/sessions/preview", data=self._form("https://example.com","preview"),
                headers={"origin": "https://computer.example.com"})
        self.assertEqual(resp.status_code, 502)
        self.assertNotIn("synthetic-secret-cookie", resp.text)


if __name__ == "__main__":
    unittest.main()

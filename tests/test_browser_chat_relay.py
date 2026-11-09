"""Offline owner form and signed GitHub workflow relay API acceptance checks."""
import importlib.util
import os
import re
import unittest
from unittest.mock import AsyncMock,patch

HAS_FASTAPI=importlib.util.find_spec("fastapi") is not None
if HAS_FASTAPI:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from services.computer_browser.owner_chat_relay import mount_owner_chat_relay
    from services.computer_browser.owner_console import require_verified_owner
    from services.computer_browser.github_oidc_read_policy import REPOSITORY_ID,ACTOR_ID

OWNER="b"*64
ENV={
    "K_SERVICE":"plenum-browser-owner-auth0",
    "PLENUM_CHAT_RELAY_ENABLED":"true",
    "PLENUM_CHAT_RELAY_REPO_ID":"1447724141",
    "PLENUM_CHAT_RELAY_ACTOR_ID":"251133044",
    "AUTH0_OWNER_PUBLIC_ORIGIN":"https://plenum-browser-owner-auth0-2lak3vl73q-ue.a.run.app",
    "BROWSER_PUBLIC_ORIGIN":"https://plenum-browser-owner-auth0-2lak3vl73q-ue.a.run.app",
    "BROWSER_PROFILE_BUCKET":"synthetic-private-bucket",
    "BROWSER_SESSION_KEY":"synthetic-test-key-not-valid-but-route-does-not-open-gcs",
    "COMPUTER_BROWSER_TOKEN":"synthetic-only-token-more-than-32-bytes-never-prod",
    "BROWSER_ALLOWED_ORIGINS":"https://example.com,https://the-internet.herokuapp.com",
}


@unittest.skipUnless(HAS_FASTAPI,"Web integration requires optional FastAPI")
class OwnerChatRelayApiTests(unittest.TestCase):
    def make_client(self,env=None):
        self.patch_env=patch.dict(os.environ,env or ENV,clear=True)
        self.patch_env.start()
        self.addCleanup(self.patch_env.stop)
        app=FastAPI()
        mount_owner_chat_relay(app)
        app.dependency_overrides[require_verified_owner]=lambda:{"private_owner_id":OWNER}
        return TestClient(app)

    def test_route_absent_in_original_iap_and_if_disabled(self):
        for settings in (
            {**ENV,"K_SERVICE":"plenum-computer-browser"},
            {**ENV,"PLENUM_CHAT_RELAY_ENABLED":"false"},
        ):
            with patch.dict(os.environ,settings,clear=True):
                app=FastAPI()
                mount_owner_chat_relay(app)
                client=TestClient(app)
                self.assertEqual(client.post("/internal/chat-demo-read").status_code,404)
                self.assertEqual(client.get("/owner/chat-demo-approval").status_code,404)

    def test_owner_signed_single_use_approval_form_and_cross_site_rejected(self):
        client=self.make_client()
        from services.computer_browser import owner_chat_relay
        page=client.get("/owner/chat-demo-approval")
        self.assertEqual(page.status_code,200)
        self.assertIn("ONE signed ChatGPT/GitHub workflow",page.text)
        self.assertEqual(page.headers["referrer-policy"],"same-origin")
        match=re.search(r"name='csrf_token' value='([^']+)'",page.text)
        self.assertIsNotNone(match)
        token=match.group(1)
        with patch.object(owner_chat_relay,"approve_one_demo_read",
                          return_value={"approved_once":True}) as consent:
            bad=client.post("/owner/chat-demo-approval",
                data={"csrf_token":token,"confirmation":"APPROVE"},
                headers={"origin":"https://attacker.example"})
            self.assertEqual(bad.status_code,403)
            self.assertFalse(consent.called)
            bad_confirm=client.post("/owner/chat-demo-approval",
                data={"csrf_token":token,"confirmation":"YES"})
            self.assertEqual(bad_confirm.status_code,403)
            self.assertFalse(consent.called)
            approved=client.post("/owner/chat-demo-approval",
                data={"csrf_token":token,"confirmation":"APPROVE"})
            self.assertEqual(approved.status_code,200)
            self.assertIn("One read-only demonstration session check",approved.text)
            consent.assert_called_once_with(OWNER)

    def test_signed_workflow_returns_only_boolean_and_consumes_once(self):
        client=self.make_client()
        from services.computer_browser import owner_chat_relay
        result={
            "site":"https://the-internet.herokuapp.com",
            "http_status":200,
            "demo_authenticated_restored":True,
            "body":"secret-private-cookie-nonreturned",
            "title":"confidential page title",
            "owner":"owner-id-must-not-leak",
        }
        with patch.object(owner_chat_relay.GitHubOIDCTokenVerifier,"verify",
                          return_value={"trusted_github_workflow":True}) as verify,\
             patch.object(owner_chat_relay,"consume_one_demo_read",
                          return_value=OWNER) as consent,\
             patch.object(owner_chat_relay,"read_saved_site",
                          new_callable=AsyncMock,return_value=result) as read:
            resp=client.post("/internal/chat-demo-read",
                             headers={"authorization":"Bearer signed.synthetic.jwt"})
        self.assertEqual(resp.status_code,200)
        self.assertTrue(resp.json()["demo_login_restored"])
        self.assertTrue(resp.json()["approval_consumed"])
        self.assertEqual(resp.headers["cache-control"],"no-store")
        self.assertEqual(resp.json()["private_contents_exposed"],False)
        self.assertEqual(resp.json()["website_modified"],False)
        for secret in ("secret-private-cookie","owner-id-must-not-leak","confidential page title","signed.synthetic.jwt"):
            self.assertNotIn(secret,resp.text)
        verify.assert_called_once_with("signed.synthetic.jwt")
        consent.assert_called_once()
        read.assert_awaited_once_with(site="https://the-internet.herokuapp.com",owner=OWNER)

    def test_unsigned_bad_token_and_unpaired_requests_cannot_read_vault(self):
        client=self.make_client()
        from services.computer_browser import owner_chat_relay
        with patch.object(owner_chat_relay,"consume_one_demo_read") as consume,\
             patch.object(owner_chat_relay,"read_saved_site",
                          new_callable=AsyncMock) as remote:
            missing=client.post("/internal/chat-demo-read")
            self.assertEqual(missing.status_code,401)
            with patch.object(owner_chat_relay.GitHubOIDCTokenVerifier,"verify",
                              side_effect=PermissionError("invalid JWT")):
                bad=client.post("/internal/chat-demo-read",
                                headers={"authorization":"Bearer bad-jwt"})
                self.assertEqual(bad.status_code,401)
            consume.assert_not_called()
            remote.assert_not_awaited()
        with patch.object(owner_chat_relay.GitHubOIDCTokenVerifier,"verify",
                          return_value={"trusted_github_workflow":True}),\
             patch.object(owner_chat_relay,"consume_one_demo_read",
                          side_effect=PermissionError("no owner consent")),\
             patch.object(owner_chat_relay,"read_saved_site",
                          new_callable=AsyncMock) as remote:
            paired=client.post("/internal/chat-demo-read",
                headers={"authorization":"Bearer signed.synthetic.jwt"})
            self.assertEqual(paired.status_code,403)
            remote.assert_not_awaited()

    def test_stale_site_cookie_reports_not_verified_not_browser_content(self):
        client=self.make_client()
        from services.computer_browser import owner_chat_relay
        with patch.object(owner_chat_relay.GitHubOIDCTokenVerifier,"verify",
                          return_value={"trusted_github_workflow":True}),\
             patch.object(owner_chat_relay,"consume_one_demo_read",
                          return_value=OWNER),\
             patch.object(owner_chat_relay,"read_saved_site",
                          new_callable=AsyncMock,return_value={
                              "site":"https://the-internet.herokuapp.com",
                              "http_status":200,
                              "demo_authenticated_restored":False,
                              "body":"login page not sensitive but must not return",
                          }):
            resp=client.post("/internal/chat-demo-read",
                headers={"authorization":"Bearer signed.synthetic.jwt"})
            self.assertEqual(resp.status_code,200)
            self.assertFalse(resp.json()["demo_login_restored"])
            self.assertNotIn("login page",resp.text)


if __name__=="__main__":
    unittest.main()

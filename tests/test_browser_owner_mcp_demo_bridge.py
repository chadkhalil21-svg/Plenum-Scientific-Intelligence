"""No-network security tests for source-only ChatGPT -> saved-demo read adapter."""
import asyncio
import hashlib
import importlib.util
import os
import unittest
from unittest.mock import AsyncMock, patch

from services.computer_browser.oauth_resource_boundary import ResourceConfig
from services.computer_browser.owner_mcp_demo_bridge import (
    DEMO_ORIGIN, FEATURE_FLAG, OWNER_SERVICE, EXPECTED_OWNER_ISSUER,
    derive_vault_owner_id, verified_saved_demo_status,
)

ISSUER=EXPECTED_OWNER_ISSUER
OWNER_SUB="auth0|synthetic-founders-only-identity"
CFG=ResourceConfig(
    issuer=ISSUER,
    jwks_url=ISSUER.rstrip("/")+"/.well-known/jwks.json",
    resource="https://private-browser.example.com/mcp",
    client_id="https://chatgpt.com/oauth/client.json",
    owner_sub=OWNER_SUB,
    machine_url="https://plenum-computer-browser-machine-98614162800.us-east1.run.app",
)
SAFE_ENV={
    "K_SERVICE":OWNER_SERVICE,
    FEATURE_FLAG:"true",
    "BROWSER_ALLOWED_ORIGINS":"https://example.com,"+DEMO_ORIGIN,
    "AUTH0_OWNER_SUB":OWNER_SUB,
    "BROWSER_PROFILE_BUCKET":"synthetic-vault-do-not-use",
    "BROWSER_SESSION_KEY":"synthetic-private-key-never-used",
    "COMPUTER_BROWSER_TOKEN":"s"*48,
    "AUTH0_OWNER_PUBLIC_ORIGIN":
        "https://plenum-browser-owner-auth0-2lak3vl73q-ue.a.run.app",
}


class OwnerMCPDemoBridgeTests(unittest.TestCase):
    def test_bearer_verified_owner_id_matches_existing_auth0_vault_derivation(self):
        expected=hashlib.sha256((ISSUER+OWNER_SUB).encode()).hexdigest()
        self.assertEqual(derive_vault_owner_id(CFG),expected)
        self.assertEqual(len(expected),64)
        from dataclasses import replace
        for issuer,keys in [
            ("https://foreign.us.auth0.com/","https://foreign.us.auth0.com/.well-known/jwks.json"),
            ("https://typo.us.auth0.com/","https://typo.us.auth0.com/.well-known/jwks.json"),
        ]:
            with self.subTest(issuer=issuer),self.assertRaises(PermissionError):
                derive_vault_owner_id(replace(CFG,issuer=issuer,jwks_url=keys))

    @unittest.skipUnless(importlib.util.find_spec("fastapi") is not None,
                         "Browser integration requires optional FastAPI")
    def test_feature_disabled_or_wrong_service_never_reaches_profile(self):
        from services.computer_browser import owner_saved_session
        scenarios=[
            {"K_SERVICE":"plenum-computer-browser"},
            {FEATURE_FLAG:"false"},
            {FEATURE_FLAG:""},
            {"BROWSER_ALLOWED_ORIGINS":"https://example.com"},
            {"BROWSER_ALLOWED_ORIGINS":"https://example.com,"+DEMO_ORIGIN+","+DEMO_ORIGIN},
            {"AUTH0_OWNER_SUB":""},
            {"AUTH0_OWNER_SUB":"auth0|wrong-owner"},
            {"BROWSER_PROFILE_BUCKET":""},
            {"BROWSER_SESSION_KEY":""},
            {"COMPUTER_BROWSER_TOKEN":"too-short"},
            {"AUTH0_OWNER_PUBLIC_ORIGIN":"https://attacker.example"},
        ]
        for update in scenarios:
            with self.subTest(update=update):
                with patch.dict(os.environ,{**SAFE_ENV,**update},clear=True):
                    with patch.object(owner_saved_session,"read_saved_site",
                                      new_callable=AsyncMock) as remote:
                        with self.assertRaises(PermissionError):
                            asyncio.run(verified_saved_demo_status(CFG))
                        remote.assert_not_awaited()

    @unittest.skipUnless(importlib.util.find_spec("fastapi") is not None,
                         "Browser integration requires optional FastAPI")
    def test_protected_demo_read_redacts_body_cookies_and_storage_metadata(self):
        from services.computer_browser import owner_saved_session
        mock_result={
            "site":DEMO_ORIGIN,
            "http_status":200,
            "demo_authenticated_restored":True,
            "title":"Private title SHOULD NOT LEAK",
            "body":"cookie=private-cookie-never-leak and personal page details",
            "headers":{"Authorization":"Bearer bad-secret"},
            "profile":"real-owner-id-should-not-return",
        }
        with patch.dict(os.environ,SAFE_ENV,clear=True):
            with patch.object(owner_saved_session,"read_saved_site",
                              new_callable=AsyncMock,return_value=mock_result) as remote:
                out=asyncio.run(verified_saved_demo_status(CFG))
        self.assertEqual(out["result"],"verified")
        self.assertTrue(out["authenticated_profile_restored"])
        remote.assert_awaited_once_with(
            site=DEMO_ORIGIN,
            owner=hashlib.sha256((ISSUER+OWNER_SUB).encode()).hexdigest())
        raw=str(out)
        for banned in ("cookie","private-cookie","Private title","Bearer","real-owner-id","personal page","Authorization"):
            with self.subTest(banned=banned):
                self.assertNotIn(banned,raw)
        self.assertEqual(out["website_writes_executed"],False)
        self.assertEqual(out["private_page_content_disclosed"],False)

    @unittest.skipUnless(importlib.util.find_spec("fastapi") is not None,
                         "Browser integration requires optional FastAPI")
    def test_stale_cookie_malformed_result_and_vault_error_fail_closed(self):
        from services.computer_browser import owner_saved_session
        results=[
            {"site":DEMO_ORIGIN,"http_status":200,"demo_authenticated_restored":False},
            {"site":DEMO_ORIGIN,"http_status":302,"demo_authenticated_restored":True},
            {"site":"https://attacker.example","http_status":200,"demo_authenticated_restored":True},
            "unexpected",
        ]
        with patch.dict(os.environ,SAFE_ENV,clear=True):
            for result in results:
                with self.subTest(result=result):
                    with patch.object(owner_saved_session,"read_saved_site",
                                      new_callable=AsyncMock,return_value=result):
                        out=asyncio.run(verified_saved_demo_status(CFG))
                    self.assertEqual(out["result"],"not_verified")
                    self.assertFalse(out["authenticated_profile_restored"])
            with patch.object(owner_saved_session,"read_saved_site",
                              new_callable=AsyncMock,side_effect=RuntimeError(
                                  "confidential-storage-metadata-DO-NOT-LOG")):
                out=asyncio.run(verified_saved_demo_status(CFG))
            self.assertEqual(out["result"],"unavailable")
            self.assertFalse(out["authenticated_profile_restored"])
            self.assertNotIn("confidential-storage",str(out))


if __name__=="__main__":
    unittest.main()

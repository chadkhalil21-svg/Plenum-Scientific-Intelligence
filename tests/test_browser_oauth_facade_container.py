"""Offline ASGI / OAuth Cloud Run packaging contract tests."""
import importlib
import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch

HAS_MCP = importlib.util.find_spec('mcp') is not None and importlib.util.find_spec('starlette') is not None
if HAS_MCP:
    from starlette.testclient import TestClient

ROOT=Path(__file__).resolve().parents[1]
FAKE_ENV={
    "PLENUM_MCP_OAUTH_ISSUER":"https://plenum-synthetic.auth0.com/",
    "PLENUM_MCP_RESOURCE_URL":"https://mcp.example.org/mcp",
    "PLENUM_MCP_OAUTH_JWKS_URL":"https://plenum-synthetic.auth0.com/.well-known/jwks.json",
    "PLENUM_MCP_OWNER_SUB":"auth0|synthetic-owner",
    "PLENUM_MCP_ALLOWED_CLIENT_ID":"https://chatgpt.com/oauth/client.json",
    "PLENUM_MCP_MACHINE_URL":"https://plenum-computer-browser-machine-98614162800.us-east1.run.app",
}

class OAuthContainerTests(unittest.TestCase):
    @unittest.skipUnless(HAS_MCP, 'Requires optional browser_mcp dependencies in facade CI')
    def test_inactive_or_missing_provider_fails_process_creation(self):
        from services.computer_browser.mcp_resource_server import create_private_browser_mcp
        with patch.dict(os.environ,{},clear=True),self.assertRaises(ValueError):
            create_private_browser_mcp()

    @unittest.skipUnless(HAS_MCP, 'Optional browser_mcp dependencies are installed in facade CI')
    def test_isolated_asgi_health_and_anonymous_401(self):
        with patch.dict(os.environ,FAKE_ENV,clear=True):
            module=importlib.import_module("services.computer_browser.oauth_asgi")
            with TestClient(module.app) as client:
                health=client.get("/health")
                self.assertEqual(health.status_code,200)
                self.assertEqual(health.json()["private_accounts_enabled"],False)
                self.assertEqual(health.json()["remote_website_writes_enabled"],False)
                self.assertEqual(health.headers["cache-control"],"no-store")
                response=client.post(
                    "/mcp",json={"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}},
                    headers={"Accept":"application/json, text/event-stream"},
                )
                self.assertEqual(response.status_code,401)
                self.assertIn("resource_metadata=",response.headers.get("www-authenticate",""))

    def test_dockerfile_is_separate_nonroot_and_never_starts_owner_browser(self):
        docker=(ROOT/"services/computer_browser/facade.Dockerfile").read_text()
        for item in ("FROM python:3.11-slim-bookworm","browser_mcp",
                     "USER 10001:10001","oauth_asgi:app","$PORT",
                     "COPY services/computer_browser/oauth_resource_boundary.py",
                     "COPY services/computer_browser/mcp_resource_server.py"):
            self.assertIn(item,docker)
        for forbidden in ("playwright install","browser_cloud_storage","BROWSER_SESSION_KEY",
                          "COMPUTER_BROWSER_TOKEN","iap_identity","--allow-unauthenticated",
                          "COPY services/computer_browser ./services/computer_browser",
                          "gcloud ","gh "):
            self.assertNotIn(forbidden,docker)

if __name__=="__main__":
    unittest.main()

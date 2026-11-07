"""Private-browser API, scope, and real local Chromium guardrails."""
import asyncio
import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from services.computer_browser.api import app
from services.computer_browser.engine import (
    _origin_syntax, allowed_origins, safe_url, public_dns_only, local_interaction_smoke,
)

TOKEN="a" * 48
client=TestClient(app)
HEADERS={"Authorization":"Bearer " + TOKEN}

class BrowserGatewayTests(unittest.TestCase):
    def test_no_token_never_authorizes_account_actions(self):
        with patch.dict(os.environ,{"COMPUTER_BROWSER_TOKEN":TOKEN,"BROWSER_ALLOWED_ORIGINS":"https://example.com"}):
            self.assertEqual(client.post("/v1/read",json={"url":"https://example.com/"}).status_code,401)
            self.assertEqual(client.post("/v1/plan",json={"url":"https://example.com/","actions":[]},
                                         headers={"Authorization":"Bearer wrong"}).status_code,401)
            self.assertEqual(client.post("/v1/read",json={"url":"https://example.com/","extra":"x"},
                                         headers=HEADERS).status_code,422)

    def test_missing_server_secret_is_never_open_by_default(self):
        with patch.dict(os.environ,{"COMPUTER_BROWSER_TOKEN":""}):
            r=client.post("/v1/read",json={"url":"https://example.com/"},headers=HEADERS)
            self.assertEqual(r.status_code,401)

    def test_owner_scope_blocks_unsafe_urls_and_ip_targets(self):
        with patch.dict(os.environ,{"BROWSER_ALLOWED_ORIGINS":"https://example.com"}):
            self.assertTrue(safe_url("https://example.com/"))
            for url in ("http://example.com/","https://127.0.0.1/",
                        "https://[::1]/", "https://localhost/",
                        "https://example.com.evil.com/", "https://example.com@evil.com/",
                        "https://example.com:8080/", "https://169.254.169.254/",
                        "file:///etc/passwd", "https://example.com/#secret",
                        "https://example.com/\nInjected:yes"):
                with self.subTest(url=url):
                    self.assertFalse(safe_url(url))
        self.assertFalse(_origin_syntax("https://example.com/private"))
        self.assertFalse(_origin_syntax("http://example.com"))
        self.assertFalse(_origin_syntax("https://localhost"))

    def test_owner_scope_must_be_explicit_and_valid(self):
        with patch.dict(os.environ,{"BROWSER_ALLOWED_ORIGINS":"https://example.com,https://news.mit.edu"}):
            self.assertTrue(safe_url("https://news.mit.edu/2026/research"))
            self.assertFalse(safe_url("https://bad.org/"))
        with patch.dict(os.environ,{"BROWSER_ALLOWED_ORIGINS":"http://example.com"}):
            with self.assertRaises(ValueError):
                allowed_origins()

    def test_planner_stages_click_fill_login_without_running_them(self):
        with patch.dict(os.environ,{"COMPUTER_BROWSER_TOKEN":TOKEN,"BROWSER_ALLOWED_ORIGINS":"https://example.com"}):
            r=client.post("/v1/plan",headers=HEADERS,json={
                "url":"https://example.com/","actions":[{"action":"fill","selector":"#email"},
                                                       {"action":"click","selector":"#submit"}]})
            self.assertEqual(r.status_code,200)
            self.assertFalse(r.json()["allowed_to_run_now"])
            self.assertTrue(r.json()["remote_write_actions_require_owner_review"])
            self.assertFalse(r.json()["account_session_available"])
            self.assertEqual(client.post("/v1/plan",headers=HEADERS,
                json={"url":"https://evil.org","actions":[]}).status_code,403)
            self.assertEqual(client.post("/v1/plan",headers=HEADERS,
                json={"url":"https://example.com/","actions":[{"action":"read"}]}).json()["allowed_to_run_now"],True)

    def test_health_does_not_expose_secret(self):
        with patch.dict(os.environ,{"COMPUTER_BROWSER_TOKEN":TOKEN}):
            r=client.get("/healthz")
            self.assertEqual(r.status_code,200)
            self.assertFalse(r.json()["remote_mutations_enabled"])
            self.assertNotIn(TOKEN,r.text)

    def test_real_local_chromium_interaction(self):
        result=asyncio.run(local_interaction_smoke())
        self.assertTrue(result["actual_chromium_input_and_click_verified"])
        self.assertFalse(result["AGI_demonstrated"])

if __name__=="__main__":unittest.main()

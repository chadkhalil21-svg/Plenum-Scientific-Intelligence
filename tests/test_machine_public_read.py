"""Stateless machine-only browser endpoint: exact public URL, no site sessions."""
import unittest
import os
from unittest.mock import patch,AsyncMock
from fastapi.testclient import TestClient
from services.computer_browser.api import app

CLIENT=TestClient(app)
ENV={"K_SERVICE":"plenum-computer-browser-machine",
     "BROWSER_ALLOWED_ORIGINS":"https://example.com",
     "COMPUTER_BROWSER_TOKEN":"",
     "BROWSER_PROFILE_BUCKET":"",
     "BROWSER_SESSION_KEY":""}


class MachinePublicReadTests(unittest.TestCase):
    def test_exact_public_machine_read_without_credentials(self):
        output={"schema":"plenum-private-browser-read-v1",
                "final_url":"https://example.com/","status":200,
                "title_untrusted":"Example Domain","body_excerpt_untrusted":"Example",
                "external_site_changed":False,"authenticated_site_used":False}
        with patch.dict(os.environ,ENV), patch(
            "services.computer_browser.api.read_public",new_callable=AsyncMock
        ) as reader:
            reader.return_value=output
            res=CLIENT.post("/machine/v1/read",json={"url":"https://example.com/"})
            self.assertEqual(res.status_code,200)
            data=res.json()
            self.assertEqual(data["schema"],"plenum-machine-public-read-v1")
            self.assertTrue(data["machine_private_transport"])
            self.assertFalse(data["remote_mutations_enabled"])
            self.assertFalse(data["authenticated_website_used"])
            self.assertEqual(data["result"],output)
            reader.assert_awaited_once_with("https://example.com/")

    def test_service_identity_missing_or_owner_iap_service_denied(self):
        for val in (None,"plenum-computer-browser","other-service"):
            env={**ENV}
            if val is None:
                env.pop("K_SERVICE")
            else:
                env["K_SERVICE"]=val
            with self.subTest(service=val), patch.dict(os.environ,env,clear=True), patch(
                "services.computer_browser.api.read_public",new_callable=AsyncMock
            ) as reader:
                res=CLIENT.post("/machine/v1/read",json={"url":"https://example.com/"})
                self.assertEqual(res.status_code,404)
                reader.assert_not_called()

    def test_machine_rejects_any_private_session_or_legacy_app_bearer(self):
        for key,val in (("COMPUTER_BROWSER_TOKEN","secret"),
                        ("BROWSER_PROFILE_BUCKET","owner-vault"),
                        ("BROWSER_SESSION_KEY","session"),
                        ("BROWSER_ALLOWED_ORIGINS","https://example.com,https://evil.org")):
            env={**ENV,key:val}
            with self.subTest(key=key), patch.dict(os.environ,env,clear=True), patch(
                "services.computer_browser.api.read_public",new_callable=AsyncMock
            ) as reader:
                self.assertEqual(CLIENT.post("/machine/v1/read",
                    json={"url":"https://example.com/"}).status_code,404)
                reader.assert_not_called()

    def test_machine_blocks_nonexact_urls_and_extra_body_fields(self):
        urls=("https://arxiv.org/","https://example.com/?token=secret",
              "https://example.com/private","http://example.com/",
              "https://example.com@evil.org/","https://example.com/#section",
              "https://127.0.0.1/","file:///etc/passwd")
        with patch.dict(os.environ,ENV), patch(
            "services.computer_browser.api.read_public",new_callable=AsyncMock
        ) as reader:
            for u in urls:
                with self.subTest(url=u):
                    self.assertEqual(CLIENT.post("/machine/v1/read",json={"url":u}).status_code,403)
            self.assertEqual(CLIENT.post("/machine/v1/read",
                json={"url":"https://example.com/","actions":["click"]}).status_code,422)
            reader.assert_not_called()

    def test_machine_cannot_call_legacy_account_endpoints(self):
        with patch.dict(os.environ,ENV,clear=True):
            self.assertEqual(CLIENT.post("/v1/read",json={"url":"https://example.com/"}).status_code,401)
            self.assertEqual(CLIENT.post("/v1/plan",json={
                "url":"https://example.com/","actions":[{"action":"click","selector":"button"}]
            }).status_code,401)
            self.assertEqual(CLIENT.post("/v1/local-smoke").status_code,401)
            self.assertFalse(CLIENT.get("/health").json()["remote_mutations_enabled"])

if __name__=="__main__":
    unittest.main()

"""Machine /v1/public-read is off by default and limited to a harmless fixture.

HTTP tests are application-layer only. Live Cloud Run IAM enforcement must be
verified separately with signed and anonymous identity-token requests.
"""
import importlib.util
import os
import unittest
from unittest.mock import AsyncMock, patch

from services.computer_browser.iam_machine_guard import (
    IMAGE, DEPLOYER, RUNTIME, verify_service, verify_service_iam
)

MACHINE_ENV = {
    "K_SERVICE": "plenum-computer-browser-machine",
    "COMPUTER_BROWSER_TOKEN": "",
    "BROWSER_SESSION_KEY": "",
    "BROWSER_PROFILE_BUCKET": "",
}

WEB_AVAILABLE = importlib.util.find_spec("fastapi") and importlib.util.find_spec("httpx")
if WEB_AVAILABLE:
    from fastapi.testclient import TestClient
    from services.computer_browser.api import app
    client = TestClient(app)


def metadata(enabled=False):
    env = [{"name": "BROWSER_ALLOWED_ORIGINS", "value": "https://example.com"}]
    if enabled:
        env.append({"name": "MACHINE_IAM_PUBLIC_READ", "value": "true"})
    return {
        "metadata": {"name": "plenum-computer-browser-machine",
                     "annotations": {
                       "run.googleapis.com/iap-enabled": "false",
                       "run.googleapis.com/invoker-iam-disabled": "false"}},
        "spec": {"template": {"spec": {
            "serviceAccountName": RUNTIME,
            "containers": [{"image": IMAGE, "env": env}]}}},
        "status": {"url": "https://plenum-computer-browser-machine-98614162800.us-east1.run.app"}
    }


class MachinePublicReadTests(unittest.TestCase):
    @unittest.skipUnless(WEB_AVAILABLE, "HTTP gateway dependencies installed in dedicated CI")
    def test_public_read_is_off_by_default_even_with_cloud_identity(self):
        with patch.dict(os.environ, {**MACHINE_ENV, "MACHINE_IAM_PUBLIC_READ": "false",
                                     "BROWSER_ALLOWED_ORIGINS": "https://example.com"}):
            with patch("services.computer_browser.api.read_public", new_callable=AsyncMock) as mock:
                r = client.post("/machine/v1/public-read",json={"url":"https://example.com/"})
                self.assertEqual(r.status_code,404)
                mock.assert_not_awaited()

    @unittest.skipUnless(WEB_AVAILABLE, "HTTP gateway dependencies installed in dedicated CI")
    def test_public_read_calls_only_fixed_allowed_page_without_session(self):
        fixture={"schema":"plenum-private-browser-read-v1", "final_url":"https://example.com/",
                 "status":200, "title_untrusted":"Example Domain",
                 "external_site_changed":False, "authenticated_site_used":False,
                 "AGI_demonstrated":False}
        with patch.dict(os.environ, {**MACHINE_ENV, "MACHINE_IAM_PUBLIC_READ": "true",
                                     "BROWSER_ALLOWED_ORIGINS": "https://example.com"}):
            with patch("services.computer_browser.api.read_public",new_callable=AsyncMock) as mock:
                mock.return_value=fixture
                r=client.post("/machine/v1/public-read",json={"url":"https://example.com/"})
                self.assertEqual(r.status_code,200)
                self.assertEqual(r.json(),fixture)
                mock.assert_awaited_once_with("https://example.com/")

    @unittest.skipUnless(WEB_AVAILABLE, "HTTP gateway dependencies installed in dedicated CI")
    def test_deny_private_website_paths_queries_and_extra_data_without_browser_launch(self):
        with patch.dict(os.environ, {**MACHINE_ENV, "MACHINE_IAM_PUBLIC_READ":"true",
                                     "BROWSER_ALLOWED_ORIGINS":"https://example.com"}):
            with patch("services.computer_browser.api.read_public", new_callable=AsyncMock) as mock:
                for url in ("https://example.com/login", "https://example.com/?token=x",
                            "https://news.mit.edu/","http://example.com/",
                            "https://example.com.evil.com/","https://127.0.0.1/"):
                    with self.subTest(url=url):
                        r=client.post("/machine/v1/public-read",json={"url":url})
                        self.assertEqual(r.status_code,403)
                r=client.post("/machine/v1/public-read",json={
                    "url":"https://example.com/","password":"secret"})
                self.assertEqual(r.status_code,422)
                self.assertEqual(client.get("/machine/v1/public-read").status_code,405)
                mock.assert_not_awaited()

    @unittest.skipUnless(WEB_AVAILABLE, "HTTP gateway dependencies installed in dedicated CI")
    def test_configuration_cannot_accidentally_enable_broad_origin(self):
        with patch.dict(os.environ, {**MACHINE_ENV, "MACHINE_IAM_PUBLIC_READ":"true",
                                     "BROWSER_ALLOWED_ORIGINS":"https://example.com,https://evil.org"}):
            with patch("services.computer_browser.api.read_public", new_callable=AsyncMock) as mock:
                r=client.post("/machine/v1/public-read",json={"url":"https://example.com/"})
                self.assertEqual(r.status_code,403)
                mock.assert_not_awaited()

    @unittest.skipUnless(WEB_AVAILABLE, "HTTP gateway dependencies installed in dedicated CI")
    def test_wrong_cloud_run_service_or_session_secret_fails_closed(self):
        from fastapi.testclient import TestClient
        with patch("services.computer_browser.api.read_public", new_callable=AsyncMock) as mock:
            for changes in (
                {"K_SERVICE":"plenum-computer-browser"},
                {"K_SERVICE":""},
                {"COMPUTER_BROWSER_TOKEN":"sensitive"},
                {"BROWSER_SESSION_KEY":"sensitive"},
                {"BROWSER_PROFILE_BUCKET":"owner-private-sessions"},
            ):
                env={**MACHINE_ENV,"MACHINE_IAM_PUBLIC_READ":"true",
                     "BROWSER_ALLOWED_ORIGINS":"https://example.com",**changes}
                with self.subTest(changes=changes), patch.dict(os.environ,env,clear=True):
                    r=client.post("/machine/v1/public-read",json={"url":"https://example.com/"})
                    self.assertEqual(r.status_code,404)
            mock.assert_not_awaited()

    def test_machine_metadata_policy_never_accept_unexpected_secrets_or_broad_callers(self):
        verify_service(metadata())
        verify_service(metadata(True),public_read_enabled=True)
        with self.assertRaises(ValueError):
            verify_service(metadata(True))
        with self.assertRaises(ValueError):
            verify_service(metadata(),public_read_enabled=True)
        bad=metadata(True)
        bad["spec"]["template"]["spec"]["containers"][0]["env"].append(
            {"name":"COMPUTER_BROWSER_TOKEN","value":"do-not-store"})
        with self.assertRaises(ValueError):
            verify_service(bad,public_read_enabled=True)
        verify_service_iam({"bindings":[{
            "role":"roles/run.invoker","members":["serviceAccount:"+DEPLOYER]}]})
        with self.assertRaises(ValueError):
            verify_service_iam({"bindings":[{
                "role":"roles/run.invoker","members":["allUsers"]}]})

    def test_owner_gated_release_cannot_enable_arbitrary_browser_control(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        wf=(root/".github/workflows/computer-browser-iam-machine-read-release.yml").read_text()
        for required in (
            "github.event.issue.user.login == 'chadkhalil21-svg'",
            "github.event.issue.body == 'RELEASE_IAM_MACHINE_READ_APPROVED:2026-11-08'",
            "environment: computer-browser-production",
            '--update-env-vars="MACHINE_IAM_PUBLIC_READ=true"',
            "gcloud run services update plenum-computer-browser-machine",
            "gcloud run services get-iam-policy plenum-computer-browser-machine",
            "gcloud builds submit .",
            "gcloud auth print-identity-token",
            "verify_service(read(service),expected_image=image,public_read_enabled=True)",
            "https://example.com/",
            "Anonymous access permitted",
        ):
            self.assertIn(required,wf)
        for forbidden in (
            "gcloud run deploy plenum-computer-browser ",
            "gcloud run services update plenum-computer-browser ",
            "--allow-unauthenticated", "--no-invoker-iam-check",
            "gcloud projects add-iam-policy-binding",
            "gcloud run services add-iam-policy-binding",
            "gcloud iam service-accounts create",
            "--set-secrets", "COMPUTER_BROWSER_TOKEN",
            'set -x',
        ):
            self.assertNotIn(forbidden,wf)


if __name__ == "__main__":
    unittest.main()

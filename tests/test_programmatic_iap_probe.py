"""Offline contract tests for the read-only service-account IAP probe."""
import unittest
from pathlib import Path

from services.computer_browser.programmatic_iap_probe import (
    claims, health_url, verify_health_response,
)

REPO = Path(__file__).resolve().parents[1]
SA = "plenum-browser-deploy@plenum-computer-browser.iam.gserviceaccount.com"
URL = "https://plenum-computer-browser-abc123-ue.a.run.app"


class ProgrammaticIAPProbeTests(unittest.TestCase):
    def test_exact_health_path_and_short_lived_service_claim(self):
        self.assertEqual(health_url(URL), URL + "/healthz")
        d = claims(SA, URL, now=10000)
        self.assertEqual(d, {
            "iss": SA, "sub": SA, "aud": URL + "/healthz",
            "iat": 10000, "exp": 10300,
        })
        self.assertNotIn("/*", d["aud"])

    def test_rejects_redirect_and_unapproved_targets(self):
        rejected = [
            "http://plenum-computer-browser-abc.run.app",
            "https://plenum-computer-browser-abc.run.app/owner",
            "https://plenum-computer-browser-abc.run.app/healthz",
            "https://plenum-computer-browser-abc.run.app/?key=abc",
            "https://plenum-computer-browser-abc.run.app/#fragment",
            "https://plenum-computer-browser-abc.run.app.evil.com",
            "https://plenum-computer-browser-abc.run.app:8443",
            "https://user:pw@plenum-computer-browser-abc.run.app",
            "https://example.com",
            "https://127.0.0.1",
            "file:///etc/passwd",
            None,
        ]
        for url in rejected:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    health_url(url)

    def test_rejects_invalid_service_identity_and_time(self):
        for identity in ("owner@gmail.com", "foo@evil.net", "x;curl attacker",
                         "", None, "A@project.iam.gserviceaccount.com"):
            with self.subTest(identity=identity):
                with self.assertRaises(ValueError):
                    claims(identity, URL, now=10000)
        with self.assertRaises(ValueError):
            claims(SA, URL, now=-10)

    def test_health_response_not_login_or_model_claim(self):
        self.assertTrue(verify_health_response({
            "service": "plenum-computer-browser",
            "ready": True,
            "remote_mutations_enabled": False,
            "browser_profile_persistence": False,
        }))
        self.assertFalse(verify_health_response({"status": "redirect"}))
        self.assertFalse(verify_health_response({"service": "other", "ready": True}))
        self.assertFalse(verify_health_response({
            "service": "plenum-computer-browser", "ready": True,
            "remote_mutations_enabled": True,
        }))

    def test_owner_only_no_deploy_no_token_in_outputs(self):
        wf = (REPO / ".github/workflows/computer-browser-iap-health-probe.yml").read_text()
        required = [
            "github.event.issue.user.login == 'chadkhalil21-svg'",
            "github.event.issue.body == 'VERIFY_IAP_HEALTH_ONLY:2026-11-07'",
            "environment: computer-browser-production",
            "workload_identity_provider:",
            "id-token: write",
            "gcloud iam service-accounts sign-jwt",
            "Proxy-Authorization: Bearer",
            "--health-response",
            "/healthz",
        ]
        for evidence in required:
            self.assertIn(evidence, wf)
        disallowed = [
            "gcloud run deploy", "gcloud run services update",
            "gcloud secrets versions access", "gcloud iap settings set",
            "--allow-unauthenticated", "--no-iap", "token.creator@",
            "curl --location", "set -x",
        ]
        for evidence in disallowed:
            self.assertNotIn(evidence, wf)


if __name__ == "__main__":
    unittest.main()

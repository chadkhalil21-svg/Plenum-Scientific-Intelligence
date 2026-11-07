"""Ensure the identity preflight is explicitly manual and read-only."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BrowserIdentityPreflightPolicyTests(unittest.TestCase):
    def test_workflow_is_manually_triggered_with_short_lived_identity(self):
        flow = (ROOT / ".github/workflows/computer-browser-cloud-identity-preflight.yml").read_text()
        for expected in (
            "workflow_dispatch:", "id-token: write",
            "github.event.issue.user.login == 'chadkhalil21-svg'",
            "github.event.issue.title == 'Computer Browser: verify cloud identity'",
            "environment: computer-browser-production",
            "google-github-actions/auth@v3",
            "secrets.GCP_WIF_PROVIDER",
            "secrets.GCP_BROWSER_DEPLOY_SA",
            "gcloud artifacts repositories describe",
            "gcloud secrets describe",
            "gcloud storage buckets describe",
            "NO DEPLOYMENT, NO BUILD",
        ):
            self.assertIn(expected, flow)
        for forbidden in (
            "gcloud builds submit", "gcloud run deploy",
            "gcloud run services update", "gcloud secrets versions access",
            "gcloud storage cp", "gh secret set", "gh variable set",
            "--allow-unauthenticated",
        ):
            self.assertNotIn(forbidden, flow)
        self.assertNotIn("schedule:", flow)


if __name__ == "__main__":
    unittest.main()

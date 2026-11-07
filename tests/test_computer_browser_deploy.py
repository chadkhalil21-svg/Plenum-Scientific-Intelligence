"""Deployment is always a separate owner-approved, IAM-private action."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class PrivateCloudDeployGuardTests(unittest.TestCase):
    def test_manual_owner_gate_and_no_public_endpoint(self):
        wf=(ROOT/".github/workflows/computer-browser-cloud-run-deploy.yml").read_text()
        for evidence in [
            "workflow_dispatch:", "DEPLOY_APPROVED",
            "environment: computer-browser-production", "id-token: write",
            "workload_identity_provider:", "gcloud artifacts repositories describe",
            "gcloud secrets describe computer-browser-token",
            "--no-allow-unauthenticated", "--min-instances=0",
            "--max-instances=1", "--concurrency=1",
            "--set-secrets COMPUTER_BROWSER_TOKEN=computer-browser-token:latest",
            "plenum-browser-builder@", "--gcs-source-staging-dir",
        ]:
            self.assertIn(evidence,wf)
        self.assertNotIn("--allow-unauthenticated ",wf)
        self.assertNotIn("GOOGLE_APPLICATION_CREDENTIALS=",wf)
    def test_no_credentials_committed(self):
        doc=(ROOT/"docs/COMPUTER_BROWSER_CLOUD_RUN.md").read_text()
        self.assertIn("OAuth 2.1",doc)
        self.assertIn("NOT",doc)
        self.assertIn("Cloud Run",doc)
if __name__=="__main__":
    unittest.main()

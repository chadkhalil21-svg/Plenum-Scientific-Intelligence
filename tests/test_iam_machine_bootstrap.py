"""Static guardrails for owner-gated machine runtime identity bootstrap."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class MachineRuntimeBootstrapTests(unittest.TestCase):
    def test_gate_and_exact_identity(self):
        workflow=(ROOT/".github/workflows/computer-browser-iam-machine-bootstrap.yml").read_text()
        for required in (
            "github.event.issue.user.login == 'chadkhalil21-svg'",
            "github.event.issue.title == 'Computer Browser: bootstrap IAM machine runtime'",
            "github.event.issue.body == 'IAM_MACHINE_RUNTIME_APPROVED:2026-11-07'",
            "environment: computer-browser-production",
            "id-token: write", "issues: write",
            "gcloud iam service-accounts create plenum-browser-machine-runtime",
            "gcloud iam service-accounts add-iam-policy-binding",
            "--role='roles/iam.serviceAccountUser'",
            "--member=\"$MEMBER\"",
            "serviceAccount:$DEPLOY_SA",
            "plenum-browser-deploy@plenum-computer-browser.iam.gserviceaccount.com",
            "No project IAM",
            "No keys",
        ):
            self.assertIn(required,workflow)
        self.assertNotIn("gcloud projects add-iam-policy-binding",workflow)
        self.assertNotIn("gcloud projects set-iam-policy",workflow)
        self.assertNotIn("--role='roles/iam.serviceAccountTokenCreator'",workflow)
        self.assertNotIn("gcloud iam service-accounts keys create",workflow)
        self.assertNotIn("gcloud run deploy",workflow)
        self.assertNotIn("gcloud run services update",workflow)
        self.assertNotIn("--allow-unauthenticated",workflow)
        self.assertNotIn("gcloud secrets",workflow)

    def test_service_account_not_found_must_be_distinguished_from_unauthorized(self):
        wf=(ROOT/".github/workflows/computer-browser-iam-machine-bootstrap.yml").read_text()
        self.assertIn("NOT_FOUND|does not exist|not found",wf)
        self.assertIn("PERMISSION_DENIED|permission",wf)
        self.assertIn("service-accounts get-iam-policy",wf)
        self.assertIn("Exact-resource Service Account User binding",wf)


if __name__=="__main__":
    unittest.main()

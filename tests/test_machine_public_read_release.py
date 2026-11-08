"""Guarantee machine read deployment stays exact, IAM-private and stateless."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT/".github/workflows/computer-browser-iam-machine-read-release.yml"

class MachineReadReleaseTests(unittest.TestCase):
    def test_only_owner_approved_machine_read_release_and_existing_iam(self):
        w=WORKFLOW.read_text()
        required=(
            "github.event.issue.user.login == 'chadkhalil21-svg'",
            "github.event.issue.title == 'Computer Browser: release IAM machine public read'",
            "github.event.issue.body == 'RELEASE_IAM_MACHINE_READ_APPROVED:2026-11-08'",
            "environment: computer-browser-production",
            "gcloud builds submit .",
            "gcloud artifacts docker images describe",
            "gcloud run services update plenum-computer-browser-machine",
            "gcloud run services get-iam-policy plenum-computer-browser-machine",
            "verify_service(m, expected_image=actual)",
            "verify_service_iam(p)",
            "test \"$SIGNED_STATUS\" = \"200\"",
            '"$SERVICE_URL/health"',
            '"$SERVICE_URL/machine/v1/read"',
            '"url":"https://example.com/"',
            "test \"$READ_STATUS\" = \"200\"",
            "machine_private_transport",
            "external_site_changed",
            "authenticated_site_used",
            'int(sys.argv[2]) not in range(200,300)',
        )
        for item in required:
            with self.subTest(required=item):
                self.assertIn(item,w)
        forbidden=(
            "gcloud run deploy plenum-computer-browser ",
            "gcloud run services update plenum-computer-browser ",
            "gcloud projects add-iam-policy-binding",
            "gcloud run services add-iam-policy-binding",
            "--allow-unauthenticated",
            "--no-invoker-iam-check",
            "--no-iap",
            "gcloud iam service-accounts create",
            "--set-secrets",
            "gcloud secrets versions access",
            "BROWSER_PROFILE_BUCKET=",
            "BROWSER_SESSION_KEY=",
            "COMPUTER_BROWSER_TOKEN=",
            "set -x",
        )
        for item in forbidden:
            with self.subTest(forbidden=item):
                self.assertNotIn(item,w)
    def test_cloud_run_runtime_gate_is_exact_machine_and_no_private_secrets(self):
        api=(ROOT/"services/computer_browser/api.py").read_text()
        for item in ('@app.post("/machine/v1/read")',
                     'os.environ.get("K_SERVICE") == "plenum-computer-browser-machine"',
                     'and not os.environ.get("COMPUTER_BROWSER_TOKEN")',
                     'and not os.environ.get("BROWSER_PROFILE_BUCKET")',
                     'and not os.environ.get("BROWSER_SESSION_KEY")',
                     'task.url != "https://example.com/"',
                     'await read_public(task.url)'):
            self.assertIn(item,api)

if __name__=="__main__":
    unittest.main()

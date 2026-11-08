"""Static guarantee: only owner-initiated, private, bounded MCP bootstrap."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]

class BootstrapGuardTests(unittest.TestCase):
    def test_workflow_keeps_endpoint_private_and_zero_secret(self):
        w=(ROOT/".github/workflows/computer-browser-mcp-private-bootstrap.yml").read_text()
        for required in (
            "github.event.issue.user.login == 'chadkhalil21-svg'",
            "github.event.issue.title == 'Computer Browser: bootstrap private MCP address'",
            "github.event.issue.body == 'BOOTSTRAP_PRIVATE_MCP_FACADE:2026-11-08'",
            "environment: computer-browser-production",
            "gcloud builds submit .",
            "facade-bootstrap.cloudbuild.yaml",
            "gcloud run deploy \"$SERVICE\"",
            "--no-allow-unauthenticated",
            "--min-instances=0 --max-instances=1",
            "PENDING_ACTIVATION_NO_OWNER_20261108",
            "gcloud run services get-iam-policy",
            '"allUsers","allAuthenticatedUsers"',
            "test \"$SIGNED\" = \"200\"",
            "MCP_RESOURCE",
            "no owner sessions or website actions",
        ):
            with self.subTest(required=required):
                self.assertIn(required,w)
        for forbidden in (
            "--allow-unauthenticated", "--no-invoker-iam-check",
            "--set-secrets", "gcloud iam service-accounts keys",
            "gcloud run services update plenum-computer-browser ",
            "gcloud run deploy plenum-computer-browser ",
            "gcloud projects add-iam-policy-binding",
            "gcloud run services add-iam-policy-binding",
            "gcloud auth application-default login",
            "BROWSER_PROFILE_BUCKET=", "BROWSER_SESSION_KEY=",
            "COMPUTER_BROWSER_TOKEN=", "set -x",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden,w)
    def test_no_browser_or_private_file_in_facade_build(self):
        docker=(ROOT/"services/computer_browser/facade.Dockerfile").read_text()
        cloudbuild=(ROOT/"services/computer_browser/facade-bootstrap.cloudbuild.yaml").read_text()
        self.assertIn("facade.Dockerfile",cloudbuild)
        self.assertIn("mcp_resource_server.py",docker)
        self.assertIn("USER 10001:10001",docker)
        for path in ("private_login.py","engine.py","session","profiles","storage"):
            self.assertNotIn("COPY services/computer_browser/"+path,docker)
        self.assertNotIn("gcloud run",cloudbuild)

if __name__=="__main__":
    unittest.main()

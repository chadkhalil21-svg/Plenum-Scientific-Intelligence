"""No deployment, IAM grant or private account effects from identity-only staging."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT/".github/workflows/computer-browser-mcp-runtime-identity.yml"

class MCPPermanentRuntimeIdentityGuard(unittest.TestCase):
    def test_exact_founder_trigger_and_unchanged_cloud_run(self):
        text=WORKFLOW.read_text(encoding="utf-8")
        expected=[
            "github.event.issue.user.login == 'chadkhalil21-svg'",
            "github.event.issue.title == 'Computer Browser: prepare keyless MCP identity'",
            "github.event.issue.body == 'PREPARE_MCP_RUNTIME_NO_GRANTS:2026-11-08'",
            "environment: computer-browser-production",
            "verify_service_iam(load(\"worker-iam.json\"))",
            "verify_service_iam(json.load(open(p)))",
            "PLENUM_MCP_OWNER_SUB",
            "auth0|bootstrap-locked-not-a-user",
            "plenum-browser-mcp-runtime",
            "--managed-by=user",
            "gh issue comment",
        ]
        for value in expected:
            with self.subTest(value=value):
                self.assertIn(value,text)
        self.assertLess(text.index("name: Require exact existing private"),
                        text.index("name: Verify existing keyless"))

    def test_no_website_access_or_iam_grants(self):
        text=WORKFLOW.read_text(encoding="utf-8")
        forbidden=[
            "gcloud run deploy ", "gcloud run services update ",
            "gcloud iam service-accounts create",
            "gcloud run services add-iam-policy-binding",
            "gcloud projects add-iam-policy-binding",
            "gcloud iam service-accounts keys create",
            "--allow-unauthenticated", "--no-invoker-iam-check",
            "gcloud builds submit", "gcloud secrets versions access",
            "BROWSER_SESSION_KEY=", "COMPUTER_BROWSER_TOKEN=",
            "--set-env-vars", "--set-secrets",
            "browser.execute_approved", "curl -X POST",
        ]
        for value in forbidden:
            with self.subTest(value=value):
                self.assertNotIn(value,text)

if __name__=="__main__":
    unittest.main()

"""Static policy checks for the owner-only, disabled OAuth facade Cloud Run bootstrap."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT/".github/workflows/computer-browser-auth0-private-facade-bootstrap.yml"
CLOUDBUILD=ROOT/"services/computer_browser/facade.cloudbuild.yaml"

class PrivateOAuthCloudRunBootstrapTests(unittest.TestCase):
    def test_owner_issue_is_exact_and_requires_human_production_environment(self):
        w=WORKFLOW.read_text()
        for phrase in (
            "github.event.issue.user.login == 'chadkhalil21-svg'",
            "github.event.issue.title == 'Computer Browser: bootstrap private Auth0 MCP address'",
            "github.event.issue.body == 'BOOTSTRAP_PRIVATE_AUTH0_MCP_ONLY:2026-11-08'",
            "environment: computer-browser-production",
            "group: plenum-auth0-mcp-bootstrap",
            "github.repository == 'chadkhalil21-svg/Plenum-Scientific-Intelligence'",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase,w)

    def test_domain_discovery_precedes_any_build_or_cloud_access(self):
        w=WORKFLOW.read_text()
        self.assertIn("https://dev-8sylxsg44yh5kkhh.us.auth0.com/.well-known/openid-configuration",w)
        self.assertIn("metadata.get('issuer')==expected",w)
        self.assertIn("parsed.netloc=='dev-8sylxsg44yh5kkhh.us.auth0.com'",w)
        self.assertLess(w.index("name: Verify exact Auth0 tenant OIDC"),w.index("name: Build a separately pinned"))
        self.assertIn("service_account: ${{ secrets.GCP_BROWSER_DEPLOY_SA }}",w)

    def test_created_service_private_without_owner_oauth_or_saved_sessions(self):
        w=WORKFLOW.read_text()
        for word in (
            "gcloud run deploy plenum-computer-browser-mcp",
            "--no-allow-unauthenticated",
            "--min-instances=0 --max-instances=1",
            '--service-account="$RUNTIME_SA"',
            "plenum-browser-machine-runtime@$GCP_PROJECT_ID.iam.gserviceaccount.com",
            "PLENUM_MCP_OWNER_SUB=auth0|bootstrap-locked-not-a-user",
            "PLENUM_MCP_ALLOWED_CLIENT_ID=plenum-bootstrap-locked-not-a-client",
            "PLENUM_MCP_RESOURCE_URL=$SERVICE_URL/mcp",
            "roles/run.invoker",
            'gcloud run services get-iam-policy plenum-computer-browser-mcp',
            "assert 'allUsers' not in members and 'allAuthenticatedUsers' not in members",
            "test \"$MCP_STATUS\" = '401'",
            "test \"$AUTH_STATUS\" = '200'",
            "assert int(sys.argv[2]) not in range(200,300)",
        ):
            with self.subTest(word=word):
                self.assertIn(word,w)
        for forbidden in (
            " --allow-unauthenticated",
            "--no-invoker-iam-check",
            "gcloud run services update plenum-computer-browser-machine ",
            "gcloud run services update plenum-computer-browser ",
            "gcloud run deploy plenum-computer-browser-machine ",
            "gcloud run deploy plenum-computer-browser ",
            "gcloud projects add-iam-policy-binding",
            "gcloud iam service-accounts create",
            "--set-secrets",
            "--set-cloudsql-instances",
            "gcloud secrets versions access",
            "BROWSER_SESSION_KEY=",
            "COMPUTER_BROWSER_TOKEN=",
            "set -x",
            "browser.execute_approved",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden,w)

    def test_image_source_is_minimal_independent_facade(self):
        source=CLOUDBUILD.read_text()
        self.assertIn("services/computer_browser/facade.Dockerfile",source)
        self.assertIn("logging: CLOUD_LOGGING_ONLY",source)
        self.assertNotIn("services/computer_browser/Dockerfile",source)
        self.assertNotIn("--no-cache",source)
        w=WORKFLOW.read_text()
        self.assertIn("gcloud builds submit .",w)
        self.assertIn("gcloud artifacts docker images describe",w)
        self.assertIn('^sha256:[a-f0-9]{64}$',w)
        self.assertIn("--service-account=\"projects/$GCP_PROJECT_ID/serviceAccounts/$BUILD_SA\"",w)
        self.assertIn("us-east1-docker.pkg.dev/plenum-computer-browser/plenum-browser/browser-oauth-mcp@sha256:",w)

if __name__=="__main__":
    unittest.main()

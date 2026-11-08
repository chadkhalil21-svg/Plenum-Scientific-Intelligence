"""Cloud Run reserves some URL paths ending in z: prove with non-reserved GET."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class CloudRunSafeRouteProbeTests(unittest.TestCase):
    def test_cloud_run_safe_health_route_exists(self):
        api=(ROOT/"services/computer_browser/api.py").read_text()
        self.assertIn('@app.get("/health")',api)
        self.assertIn('@app.get("/healthz", include_in_schema=False)',api)
        self.assertIn('"remote_mutations_enabled": False',api)

    def test_workflow_only_reads_private_fallback_and_requires_owner(self):
        w=(ROOT/".github/workflows/computer-browser-iam-machine-route-probe.yml").read_text()
        for word in (
            "github.event.issue.user.login == 'chadkhalil21-svg'",
            "github.event.issue.body == 'VERIFY_MACHINE_ROUTE_ONLY:2026-11-07'",
            "environment: computer-browser-production",
            "services.computer_browser.iam_machine_guard import verify_service,verify_service_iam",
            "--impersonate-service-account=",
            'Authorization: Bearer %s',
            '"$SERVICE_URL/v1/plan"',
            "status!=405", 'body!={"detail":"Method Not Allowed"}',
            "anonymous in range(200,300)",
            "No website action or deployment occurred.",
        ):
            self.assertIn(word,w)
        for unsafe in (
            "gcloud run deploy", "gcloud run services update",
            "gcloud projects add-iam-policy-binding",
            "--allow-unauthenticated", "--no-invoker-iam-check",
            "gcloud iam service-accounts create", "curl --location", "set -x"
        ):
            self.assertNotIn(unsafe,w)

if __name__=="__main__":
    unittest.main()

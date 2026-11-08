"""Offline tests: the 404 diagnosis must be read-only and avoid permission guesses."""
import unittest
from pathlib import Path

from services.computer_browser.route_diagnostic import describe_route

ROOT = Path(__file__).resolve().parents[1]
URL = "https://plenum-computer-browser-abc123-ue.a.run.app"


def sample(ingress="all", ready="True", disabled=None):
    annotations = {"run.googleapis.com/ingress": ingress}
    if disabled is not None:
        annotations["run.googleapis.com/default-url-disabled"] = disabled
    return {
        "metadata": {"name": "plenum-computer-browser", "annotations": annotations},
        "status": {"url": URL, "conditions": [{"type": "Ready", "status": ready}]},
    }


class RouteDiagnosticTests(unittest.TestCase):
    def test_404_is_not_automatically_an_iap_permission_failure(self):
        a = describe_route(sample())
        self.assertEqual(a["possible_cause"], "404_not_explained_by_reported_route_metadata")
        self.assertTrue(a["cloud_run_url_format_expected"])
        self.assertEqual(a["ingress_mode"], "all")
        self.assertFalse(a["iap_permissions_changed"])
        self.assertFalse(a["authenticated_browser_actions_enabled"])

    def test_internal_ingress_blocks_external_runner(self):
        for value in ("internal", "internal-and-cloud-load-balancing",
                      "INGRESS_TRAFFIC_INTERNAL_ONLY"):
            with self.subTest(ingress=value):
                x = describe_route(sample(ingress=value))
                self.assertEqual(x["possible_cause"], "external_github_runner_may_be_blocked_by_ingress")

    def test_disabled_default_url_precedes_other_routing_causes(self):
        x = describe_route(sample(ingress="internal", disabled="true"))
        self.assertEqual(x["possible_cause"], "default_run_app_url_disabled")
        self.assertTrue(x["default_run_app_url_disabled"])

    def test_unready_service_and_strict_name(self):
        self.assertEqual(describe_route(sample(ready="False"))["possible_cause"], "service_not_ready")
        wrong = sample()
        wrong["metadata"]["name"] = "other-service"
        with self.assertRaises(ValueError):
            describe_route(wrong)

    def test_security_controls_not_relaxed_in_workflow(self):
        wf = (ROOT/".github/workflows/computer-browser-iap-health-probe.yml").read_text()
        self.assertIn("services.computer_browser.route_diagnostic", wf)
        self.assertIn("Review the redacted route diagnostic", wf)
        for unsafe in ("gcloud run services update", "gcloud run deploy",
                       "--no-iap", "--allow-unauthenticated", "set -x"):
            self.assertNotIn(unsafe, wf)


if __name__ == "__main__":
    unittest.main()

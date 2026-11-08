"""Verify redacted service-level IAM audit never infers missing inherited access."""
import unittest
from pathlib import Path
from services.computer_browser.iap_policy_audit import summary, policy_grant

ROOT = Path(__file__).resolve().parents[1]
DEPLOYER = "serviceAccount:plenum-browser-deploy@plenum-computer-browser.iam.gserviceaccount.com"
IAP_AGENT = "serviceAccount:service-98614162800@gcp-sa-iap.iam.gserviceaccount.com"

class IAPPolicyAuditTests(unittest.TestCase):
    def test_exact_service_resource_grants(self):
        iap = {"bindings": [{"role": "roles/iap.httpsResourceAccessor",
                              "members": [DEPLOYER, "user:someone@example.com"]}]}
        run = {"bindings": [{"role": "roles/run.invoker", "members": [IAP_AGENT]}]}
        result = summary(iap, run, "98614162800")
        self.assertEqual(result["deployer_iap_access_binding"],
                         "explicit_unconditional_binding")
        self.assertEqual(result["iap_service_agent_run_invoker_binding"],
                         "explicit_unconditional_binding")
        self.assertFalse(result["permission_changes"])
        self.assertNotIn("someone@example.com", str(result))

    def test_no_resource_binding_is_not_proof_of_no_effective_access(self):
        result = summary({"bindings": []}, {"bindings": []}, "98614162800")
        self.assertEqual(result["deployer_iap_access_binding"],
                         "no_explicit_binding")
        self.assertEqual(result["iap_service_agent_run_invoker_binding"],
                         "no_explicit_binding")
        self.assertIn("inherited", result["caution"])

    def test_conditional_binding_is_flagged(self):
        p = {"bindings": [{"role": "roles/run.invoker", "members": [IAP_AGENT],
                            "condition": {"expression": "request.time < timestamp('2027-01-01T00:00:00Z')"}}]}
        self.assertEqual(policy_grant(p, "roles/run.invoker", IAP_AGENT),
                         "explicit_conditional_binding")

    def test_unreadable_resource_policy_has_no_permission_assumption(self):
        s = summary(None, None, "98614162800")
        self.assertFalse(s["iap_policy_read"])
        self.assertEqual(s["deployer_iap_access_binding"], "unavailable")
        self.assertEqual(s["iap_service_agent_run_invoker_binding"], "unavailable")
        for invalid in ("", "x", "98 614", None):
            with self.assertRaises(ValueError):
                summary({}, {}, invalid)

    def test_github_workflow_does_not_change_permissions(self):
        w = (ROOT / ".github/workflows/computer-browser-iap-health-probe.yml").read_text()
        self.assertIn("gcloud iap web get-iam-policy", w)
        self.assertIn("gcloud run services get-iam-policy", w)
        self.assertIn("services.computer_browser.iap_policy_audit", w)
        for forbidden in ("gcloud run services add-iam-policy-binding",
                          "gcloud iap web add-iam-policy-binding",
                          "gcloud iap web set-iam-policy", "gcloud run deploy",
                          "--no-iap", "--allow-unauthenticated"):
            self.assertNotIn(forbidden, w)

if __name__ == "__main__":
    unittest.main()

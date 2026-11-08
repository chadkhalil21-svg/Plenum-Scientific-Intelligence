"""Verify the IAM-only smoke service cannot become a public or credential-bearing browser."""
import unittest
from pathlib import Path
from services.computer_browser.iam_machine_guard import (
    SERVICE, RUNTIME, IMAGE, DEPLOYER, verify_service, verify_service_iam,
    verify_health,
)

ROOT = Path(__file__).resolve().parents[1]
URL = "https://plenum-computer-browser-machine-1234-ue.a.run.app"


def metadata():
    return {
        "metadata": {"name": SERVICE, "annotations": {
            "run.googleapis.com/iap-enabled": "false",
            "run.googleapis.com/invoker-iam-disabled": "false",
        }},
        "spec": {"template": {"spec": {
            "serviceAccountName": RUNTIME,
            "containers": [{"image": IMAGE, "env": [
                {"name": "BROWSER_ALLOWED_ORIGINS", "value": "https://example.com"}]}],
        }}},
        "status": {"url": URL},
    }


def policy(principal="serviceAccount:" + DEPLOYER):
    return {"bindings": [{"role": "roles/run.invoker", "members": [principal]}]}


class IAMMachineHealthTests(unittest.TestCase):
    def test_expected_identity_and_immutable_artifact(self):
        self.assertEqual(verify_service(metadata()), URL)
        self.assertTrue(verify_service_iam(policy()))
        self.assertTrue(verify_health({
            "service": "plenum-computer-browser", "ready": True,
            "remote_mutations_enabled": False
        }))

    def test_fails_closed_on_public_invoker_or_improper_grants(self):
        for member in ("allUsers", "allAuthenticatedUsers",
                       "serviceAccount:other@project.iam.gserviceaccount.com"):
            with self.subTest(member=member):
                with self.assertRaises(ValueError):
                    verify_service_iam(policy(member))
        with self.assertRaises(ValueError):
            verify_service_iam({"bindings": []})
        with self.assertRaises(ValueError):
            verify_service_iam({"bindings": [
                {"role": "roles/run.invoker", "members": ["serviceAccount:" + DEPLOYER],
                 "condition": {"expression": "true"}}]})

    def test_machine_service_forbids_shared_private_secrets_and_public_configs(self):
        for key in ("COMPUTER_BROWSER_TOKEN", "BROWSER_SESSION_KEY",
                    "BROWSER_PROFILE_BUCKET"):
            d=metadata()
            d["spec"]["template"]["spec"]["containers"][0]["env"].append(
                {"name":key,"value":"unexpected"})
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    verify_service(d)
        d=metadata()
        d["spec"]["template"]["spec"]["containers"][0]["env"].append(
            {"name":"SECRET","valueFrom":{"secretKeyRef":{}}})
        with self.assertRaises(ValueError):
            verify_service(d)
        for flag in ("run.googleapis.com/iap-enabled",
                     "run.googleapis.com/invoker-iam-disabled"):
            d=metadata()
            d["metadata"]["annotations"][flag]="true"
            with self.subTest(flag=flag):
                with self.assertRaises(ValueError):
                    verify_service(d)

    def test_wrong_image_runtime_or_service_denied(self):
        for kind in ("image", "serviceAccountName", "service", "url"):
            d=metadata()
            if kind=="image": d["spec"]["template"]["spec"]["containers"][0]["image"]="example:latest"
            if kind=="serviceAccountName": d["spec"]["template"]["spec"]["serviceAccountName"]="default"
            if kind=="service": d["metadata"]["name"]="plenum-computer-browser"
            if kind=="url": d["status"]["url"]="https://example.com"
            with self.subTest(kind=kind):
                with self.assertRaises(ValueError):
                    verify_service(d)

    def test_health_cannot_claim_remote_writes_or_no_ready_status(self):
        self.assertFalse(verify_health({"service": "plenum-computer-browser",
            "ready": True, "remote_mutations_enabled": True}))
        self.assertFalse(verify_health({"service": "plenum-computer-browser",
            "ready": False, "remote_mutations_enabled": False}))

    def test_owner_trigger_immutable_image_and_no_existing_iap_modification(self):
        wf=(ROOT/".github/workflows/computer-browser-iam-machine-health.yml").read_text()
        for item in (
            "github.event.issue.user.login == 'chadkhalil21-svg'",
            "github.event.issue.body == 'IAM_MACHINE_HEALTH_APPROVED:2026-11-07'",
            "environment: computer-browser-production",
            "plenum-browser-machine-runtime@",
            "gcloud run deploy plenum-computer-browser-machine",
            "--no-iap --invoker-iam-check --no-allow-unauthenticated",
            "--min-instances=0 --max-instances=1",
            "serviceAccount:$BROWSER_DEPLOY_SA",
            "--role='roles/run.invoker'",
            "--impersonate-service-account=",
            "gcloud run services get-iam-policy plenum-computer-browser-machine",
            "services.computer_browser.iam_machine_guard",
            "id-token: write", "issues: write",
            IMAGE,
        ):
            self.assertIn(item,wf)
        for forbidden in (
            "gcloud run deploy plenum-computer-browser \\",
            "gcloud run services update plenum-computer-browser \\",
            "--allow-unauthenticated", "--no-invoker-iam-check",
            "gcloud secrets versions access", "gcloud iam service-accounts create",
            "gcloud projects add-iam-policy-binding", "COMPUTER_BROWSER_TOKEN=computer-browser-token"):
            self.assertNotIn(forbidden,wf)

if __name__=="__main__":
    unittest.main()

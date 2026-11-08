"""Guard the isolated immutable IAM machine release before production changes."""
import unittest
from pathlib import Path
from services.computer_browser.iam_machine_guard import IMAGE,verify_service

ROOT=Path(__file__).resolve().parents[1]
PINNED_REPO="us-east1-docker.pkg.dev/plenum-computer-browser/plenum-browser/computer-browser@sha256:"
NEW_IMAGE=PINNED_REPO + "e"*64

def fixture():
    return {
        "metadata": {"name": "plenum-computer-browser-machine",
                     "annotations": {"run.googleapis.com/iap-enabled": "false",
                     "run.googleapis.com/invoker-iam-disabled": "false"}},
        "spec": {"template": {"spec": {
            "serviceAccountName": "plenum-browser-machine-runtime@plenum-computer-browser.iam.gserviceaccount.com",
            "containers": [{"image": IMAGE, "env": [
                {"name": "BROWSER_ALLOWED_ORIGINS", "value": "https://example.com"}]}]}}},
        "status": {"url": "https://plenum-computer-browser-machine-98614162800.us-east1.run.app"}
    }

class IAMMachineHealthReleaseTests(unittest.TestCase):
    def test_original_image_and_new_immutable_image(self):
        sample=fixture()
        verify_service(sample)
        sample["spec"]["template"]["spec"]["containers"][0]["image"]=NEW_IMAGE
        verify_service(sample, expected_image=NEW_IMAGE)
        with self.assertRaises(ValueError):
            verify_service(sample)
    def test_wrong_registry_tag_and_extra_env_rejected(self):
        for ref in ("us-docker.pkg.dev/evil/other@sha256:"+"e"*64,
                    "us-east1-docker.pkg.dev/plenum-computer-browser/plenum-browser/computer-browser:latest",
                    PINNED_REPO+"x"*64):
            sample=fixture()
            sample["spec"]["template"]["spec"]["containers"][0]["image"]=ref
            with self.subTest(image=ref):
                with self.assertRaises(ValueError):
                    verify_service(sample,expected_image=ref)
        for extra in (
          {"name":"BROWSER_SESSION_KEY","value":"not-a-real-key"},
          {"name":"OTHER_CONFIG","value":"not-allowed"},
          {"name":"BROWSER_PROFILE_BUCKET","valueFrom":{"secretKeyRef":{}}},
        ):
            sample=fixture()
            sample["spec"]["template"]["spec"]["containers"][0]["env"].append(extra)
            with self.assertRaises(ValueError):
                verify_service(sample)
    def test_release_changes_only_machine_image_and_never_exposes_browser_credentials(self):
        wf=(ROOT/".github/workflows/computer-browser-iam-machine-health-release.yml").read_text()
        required=(
            "github.event.issue.user.login == 'chadkhalil21-svg'",
            "github.event.issue.body == 'RELEASE_IAM_MACHINE_HEALTH_APPROVED:2026-11-07'",
            "environment: computer-browser-production",
            "gcloud builds submit .",
            "gcloud artifacts docker images describe",
            "gcloud run services update plenum-computer-browser-machine",
            "gcloud run services get-iam-policy plenum-computer-browser-machine",
            "services.computer_browser.iam_machine_guard import verify_service,verify_service_iam",
            '--impersonate-service-account="$BROWSER_DEPLOY_SA"',
            '"$SERVICE_URL/health"',
            '"$SIGNED_STATUS" = "200"',
            '"Anonymous Cloud Run /health: HTTP $ANON_STATUS"',
            'int(anon) not in range(200,300)',
            "gcloud iam service-accounts describe",
            "iam_machine_guard",
        )
        for item in required:
            self.assertIn(item,wf)
        for forbidden in (
            "gcloud run deploy plenum-computer-browser ",
            "gcloud run services update plenum-computer-browser ",
            "gcloud projects add-iam-policy-binding",
            "gcloud run services add-iam-policy-binding",
            "--allow-unauthenticated",
            "--no-invoker-iam-check",
            "gcloud secrets versions access",
            "--set-secrets",
            "gcloud iam service-accounts create",
            'curl --location',
            'set -x',
        ):
            self.assertNotIn(forbidden,wf)

if __name__=="__main__":
    unittest.main()

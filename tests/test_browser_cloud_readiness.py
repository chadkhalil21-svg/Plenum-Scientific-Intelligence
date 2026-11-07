"""The founder can inspect GCP readiness via a free existing GitHub issue."""
from pathlib import Path
import unittest

class BrowserCloudPreflightTests(unittest.TestCase):
    def test_no_cloud_deployment_or_charge(self):
        root=Path(__file__).resolve().parents[1]
        flow=(root/".github/workflows/computer-browser-cloud-readiness.yml").read_text()
        for needle in [
            "types: [opened]","workflow_dispatch:","Computer Browser: check cloud readiness",
            "github.event.issue.user.login == 'chadkhalil21-svg'",
            "environment: computer-browser-production",
            "GCP_PROJECT_ID","GCP_BROWSER_RUNTIME_SA","BROWSER_PROFILE_BUCKET",
            "COMPUTER_OWNER_EMAIL","GCP_WIF_PROVIDER","GCP_BROWSER_DEPLOY_SA",
            "No Google Cloud service has been contacted",
        ]:
            self.assertIn(needle,flow)
        for forbidden in ["gcloud run deploy","gcloud builds submit","--allow-unauthenticated",
                          "gh secret list","echo ${GCP_WIF_PROVIDER}"]:
            self.assertNotIn(forbidden,flow)

if __name__=="__main__":
    unittest.main()

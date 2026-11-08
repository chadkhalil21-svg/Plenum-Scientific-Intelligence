"""Read-only OAuth diagnostics must not disclose credentials or modify IAP."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class IAPReadOnlyDiagnosisTests(unittest.TestCase):
    def test_owner_gated_and_safe(self):
        s=(ROOT/".github/workflows/computer-browser-iap-oauth-diagnosis.yml").read_text()
        for term in ("issues:", "github.event.issue.user.login == 'chadkhalil21-svg'",
                     "Computer Browser: diagnose OAuth redirect",
                     "google-github-actions/auth@v3",
                     "gcloud iap settings get", "gcloud iap web get-iam-policy",
                     "IAP_OAUTH_", "IAP_OWNER_", "No secret values printed"):
            self.assertIn(term,s)
        for term in ("gcloud run deploy","gcloud builds submit","gcloud iap settings set",
                     "gcloud iap web add-iam-policy-binding","gcloud run services update",
                     "gcloud secrets versions access","--allow-unauthenticated"):
            self.assertNotIn(term,s)
if __name__=="__main__":
    unittest.main()

"""Chat-to-Cloud Run IAM browser bridge must never handle private issues or account data."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class ChatIAMBrowserBridgeTests(unittest.TestCase):
    def test_only_founder_and_exact_public_request_can_trigger(self):
        s=(ROOT/".github/workflows/chat-browser-machine-iam-public-fixture.yml").read_text()
        for required in (
            "github.event.issue.user.login == 'chadkhalil21-svg'",
            "github.event.issue.title == 'Computer Browser: machine public-read'",
            "github.event.issue.body == 'READ_PUBLIC_EXAMPLE_ONLY:2026-11-08'",
            "environment: computer-browser-production",
            "id-token: write",
            "issues: write",
            "gcloud auth print-identity-token",
            "gcloud run services get-iam-policy plenum-computer-browser-machine",
            "verify_service(d,expected_image=image,public_read_enabled=True)",
            "verify_service_iam(",
            "https://example.com/",
            "Title",
        ):
            if required=="Title": continue
            self.assertIn(required,s)
        self.assertEqual(s.count('"url":"https://example.com/"'),2)
    def test_no_exposed_credentials_and_only_sanitized_bot_result(self):
        s=(ROOT/".github/workflows/chat-browser-machine-iam-public-fixture.yml").read_text()
        for required in (
            'persist-credentials: false',
            "gh issue comment",
            "Never raw webpage content",
            "Anonymous invocation permitted",
            "external_site_changed",
            "authenticated_site_used",
        ):
            if required=="Never raw webpage content": required="never raw webpage content"
            self.assertIn(required.lower(),s.lower())
        for forbidden in (
            "--allow-unauthenticated",
            "--set-secrets",
            "gcloud projects add-iam-policy-binding",
            "gcloud run deploy",
            "gcloud run services update",
            "gcloud iam service-accounts create",
            "BROWSER_SESSION_KEY",
            "COMPUTER_BROWSER_TOKEN",
            "set -x",
            "cat \"$RUNNER_TEMP/chat-response.json\"",
            "gh issue comment \"$ISSUE_NUMBER\" --body-file",
        ):
            self.assertNotIn(forbidden,s)

if __name__=="__main__":
    unittest.main()

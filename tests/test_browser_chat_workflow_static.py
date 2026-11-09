"""Static least-privilege guardrails for issue-triggered signed browser relay."""
from pathlib import Path
import unittest
from services.computer_browser.github_oidc_read_policy import (
    REPOSITORY, WORKFLOW_REF, AUDIENCE, ACTOR_ID, REPOSITORY_ID,
)

ROOT=Path(__file__).resolve().parents[1]
READ=(ROOT/".github/workflows/chat-browser-owner-read.yml")
ACTIVATE=(ROOT/".github/workflows/chat-browser-owner-read-activate.yml")


class SignedChatWorkflowTests(unittest.TestCase):
    def test_exact_workflow_ref_founder_identity_and_fixed_public_demo_audience(self):
        s=READ.read_text(encoding="utf-8")
        self.assertTrue(WORKFLOW_REF.endswith("/"+READ.name+"@refs/heads/main"))
        self.assertIn("github.event.issue.user.id == "+ACTOR_ID,s)
        self.assertIn("github.repository == '"+REPOSITORY+"'",s)
        self.assertIn("READ_PAIRED_PUBLIC_DEMO:2026-11-08",s)
        self.assertIn("id-token: write",s)
        self.assertIn("environment: computer-browser-production",s)
        self.assertIn("AUDIENCE: "+AUDIENCE,s)
        self.assertIn("github.event.issue.body == 'READ_PAIRED_PUBLIC_DEMO:2026-11-08'",s)
        self.assertIn("set(body)!={'schema','demo_login_restored'",s)
        self.assertIn("GH_REPO: "+REPOSITORY,s)

    def test_no_public_issue_body_or_private_site_data_passed_to_shell(self):
        s=READ.read_text(encoding="utf-8")
        self.assertNotIn("${{ github.event.issue.body }}",s)
        self.assertNotIn("${{ github.event.issue.title }}",s)
        self.assertNotIn("SuperSecretPassword",s)
        self.assertNotIn("BROWSER_SESSION_KEY",s)
        self.assertNotIn("BROWSER_PROFILE_BUCKET",s)
        self.assertNotIn("actions/checkout",s)
        self.assertNotIn("pull_request_target:",s)
        self.assertNotIn("workflow_dispatch:",s)
        self.assertIn("timeout-minutes: 4",s)
        self.assertIn("class NoRedirect(urllib.request.HTTPRedirectHandler):",s)
        self.assertIn("NoRedirect(),urllib.request.ProxyHandler({})",s)
        self.assertNotIn("urllib.request.urlopen(request",s)

    def test_activation_remains_exact_founder_protected_environment_and_rolls_back(self):
        s=ACTIVATE.read_text(encoding="utf-8")
        self.assertIn("github.event.issue.user.id == "+ACTOR_ID,s)
        self.assertIn("environment: computer-browser-production",s)
        self.assertIn("ACTIVATE_SIGNED_DEMO_RELAY:2026-11-08",s)
        self.assertIn("PLENUM_CHAT_RELAY_REPO_ID="+REPOSITORY_ID,s)
        self.assertIn("PLENUM_CHAT_RELAY_ACTOR_ID="+ACTOR_ID,s)
        self.assertIn("id: verify",s)
        self.assertIn("if: failure()",s)
        self.assertIn("PLENUM_CHAT_RELAY_ENABLED=false",s)
        self.assertIn("test \"$owner\" = '401'",s)
        self.assertIn("test \"$signed\" = '401'",s)
        self.assertNotIn("--allow-unauthenticated",s)
        self.assertNotIn("BROWSER_SESSION_KEY=",s)
        self.assertNotIn("gh issue create",s)


if __name__=="__main__":
    unittest.main()

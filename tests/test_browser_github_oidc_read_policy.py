"""Offline GitHub signed-workflow boundary tests, no GitHub API or Cloud Run."""
import importlib.util
import os
import time
import unittest
from unittest.mock import patch

from services.computer_browser.github_oidc_read_policy import (
    AUDIENCE, ENVIRONMENT, GitHubRelayIdentity, GitHubOIDCTokenVerifier,
    ISSUER, JWKS, REPOSITORY, WORKFLOW_REF, enforce_relay_claims,
)
ID=GitHubRelayIdentity(repository_id="98614162",actor_id="32165498")


class GitHubWorkflowPolicyTests(unittest.TestCase):
    def valid(self):
        now=int(time.time())
        return {
            "iss":ISSUER,"aud":AUDIENCE,
            "sub":"repo:chadkhalil21-svg@1/Plenum-Scientific-Intelligence@98614162:environment:computer-browser-production",
            "repository":REPOSITORY,"repository_owner":"chadkhalil21-svg",
            "repository_id":ID.repository_id,
            "actor":"chadkhalil21-svg","actor_id":ID.actor_id,
            "workflow_ref":WORKFLOW_REF,
            "event_name":"issues","ref":"refs/heads/main",
            "ref_type":"branch","environment":ENVIRONMENT,
            "repository_visibility":"public",
            "iat":now-15,"nbf":now-15,"exp":now+120,
            "run_id":"1234567890","jti":"synthetic-jti-1234567890",
        }

    def test_requires_protected_immutable_repo_and_actor_ids(self):
        with patch.dict(os.environ,{},clear=True),self.assertRaises(ValueError):
            GitHubRelayIdentity.from_environment()
        for a,b in [("","3"),("0","3"),("123",""),("test","3"),("123","x")]:
            with self.subTest(ids=(a,b)),self.assertRaises(ValueError):
                GitHubRelayIdentity(repository_id=a,actor_id=b).validate()

    def test_exact_signed_claim_scope_without_trusting_issue_body(self):
        ok=enforce_relay_claims(self.valid(),ID)
        self.assertEqual(ok,{
            "trusted_github_workflow":True,
            "fixed_public_demo_read_only":True,
            "owner_pairing_still_required":True,
        })
        self.assertNotIn("actor_id",str(ok))
        self.assertNotIn("jti",str(ok))

    def test_foreign_repo_actor_workflow_event_audience_or_expiry_denied(self):
        baseline=self.valid()
        variants={
            "iss":"https://attacker.example","aud":"https://other.example",
            "repository":"attacker/fork","repository_id":"99999",
            "repository_owner":"attacker","actor":"attacker","actor_id":"888",
            "workflow_ref":"chadkhalil21-svg/Plenum-Scientific-Intelligence/.github/workflows/evil.yml@refs/heads/main",
            "event_name":"pull_request","ref":"refs/heads/feature",
            "ref_type":"tag","environment":"dev","repository_visibility":"private",
            "sub":"attacker","iat":int(time.time())+1200,
            "nbf":int(time.time())+1200,"exp":int(time.time())+1200,
            "jti":"x","run_id":"1; rm -rf /",
        }
        for k,v in variants.items():
            with self.subTest(claim=k),self.assertRaises(PermissionError):
                enforce_relay_claims({**baseline,k:v},ID)
        with self.assertRaises(PermissionError):
            enforce_relay_claims({**baseline,"iat":baseline["iat"]-900},ID)
        with self.assertRaises(PermissionError):
            enforce_relay_claims({**baseline,"exp":baseline["iat"]},ID)
        with self.assertRaises(PermissionError):
            enforce_relay_claims({},ID)


@unittest.skipUnless(importlib.util.find_spec("jwt") and importlib.util.find_spec("cryptography"),
                     "Signature tests require browser_mcp's optional JWT dependencies")
class SignedGitHubTokenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import jwt
        from cryptography.hazmat.primitives.asymmetric import rsa
        cls.jwt=jwt
        cls.key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        cls.pub=cls.key.public_key()

    def make(self,**changes):
        claims=GitHubWorkflowPolicyTests().valid()
        claims.update(changes)
        return self.jwt.encode(claims,self.key,algorithm="RS256",
                               headers={"kid":"github-synthetic-fixture"})

    def test_signed_jwt_pinned_jwks_and_denied_alternate_issuers(self):
        from types import SimpleNamespace
        public_key=self.pub
        called=[]
        class FakeJWKS:
            def __init__(self,url,**kwargs):
                called.append(url)
            def get_signing_key_from_jwt(self,jwt):
                return SimpleNamespace(key=public_key)
        with patch.object(self.jwt,"PyJWKClient",FakeJWKS):
            verifier=GitHubOIDCTokenVerifier(ID)
            self.assertTrue(verifier.verify(self.make())["trusted_github_workflow"])
            self.assertEqual(called,[JWKS])
            for mutate in (
                {"aud":"https://attacker.example"},
                {"repository_id":"999"},
                {"actor_id":"999"},
                {"exp":int(time.time())+5000},
            ):
                with self.subTest(mutate=mutate),self.assertRaises(PermissionError):
                    verifier.verify(self.make(**mutate))
            from cryptography.hazmat.primitives.asymmetric import rsa
            wrong=rsa.generate_private_key(public_exponent=65537,key_size=2048)
            token=self.jwt.encode(GitHubWorkflowPolicyTests().valid(),wrong,
                                  algorithm="RS256",headers={"kid":"github-synthetic-fixture"})
            with self.assertRaises(PermissionError):
                verifier.verify(token)
            with self.assertRaises(PermissionError):
                verifier.verify("unsigned-invalid")


if __name__=="__main__":
    unittest.main()

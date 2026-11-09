"""Tests of Plenum's OWN confidential ChatGPT browser boundary, no live accounts."""
import base64
import importlib.util
import json
import os
import re
import time
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from services.computer_browser import sealed_chat_read as sealed
from services.computer_browser.github_oidc_read_policy import (
    GitHubRelayIdentity, enforce_relay_claims, AUDIENCE, WORKFLOW_REF,
    SEALED_AUDIENCE, SEALED_WORKFLOW_REF,
)

CRYPTO = importlib.util.find_spec("cryptography") is not None
FASTAPI = importlib.util.find_spec("fastapi") is not None
OWNER = "b" * 64
SITE = "https://the-internet.herokuapp.com"
ENV = {
    "K_SERVICE": "plenum-browser-owner-auth0",
    "PLENUM_CHAT_RELAY_ENABLED": "true",
    sealed.FLAG: "true",
    "AUTH0_OWNER_PUBLIC_ORIGIN":
        "https://plenum-browser-owner-auth0-2lak3vl73q-ue.a.run.app",
    "BROWSER_PUBLIC_ORIGIN":
        "https://plenum-browser-owner-auth0-2lak3vl73q-ue.a.run.app",
    "PLENUM_CHAT_RELAY_REPO_ID": "1447724141",
    "PLENUM_CHAT_RELAY_ACTOR_ID": "251133044",
    "BROWSER_ALLOWED_ORIGINS": SITE + ",https://example.com",
    "BROWSER_PROFILE_BUCKET": "fake-vault",
    "COMPUTER_BROWSER_TOKEN": "synthetic-private-browser-test-token-" * 2,
}
if CRYPTO:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    ENV["BROWSER_SESSION_KEY"] = Fernet.generate_key().decode()


def new_keypair():
    priv = X25519PrivateKey.generate()
    pub = priv.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw)
    return priv, sealed._b64(pub)


class AtomicBlob:
    def __init__(self):
        self.data = None
        self.generation = None
        self.revision = 0

    def exists(self):
        return self.data is not None

    def reload(self):
        if self.data is None:
            raise FileNotFoundError("No pending private approval")

    def upload_from_string(self, data, content_type, if_generation_match):
        if (self.data is not None and self.generation != if_generation_match or
                self.data is None and if_generation_match != 0):
            raise RuntimeError("CAS mismatch")
        self.revision += 1
        self.generation = self.revision
        self.data = data

    def download_as_bytes(self, if_generation_match):
        if self.data is None or self.generation != if_generation_match:
            raise RuntimeError("Stale private consent")
        return self.data

    def delete(self, if_generation_match):
        if self.generation != if_generation_match:
            raise RuntimeError("Cannot double consume")
        self.data = None
        self.generation = None


class FakeStore:
    def __init__(self):
        self.blob_instance = AtomicBlob()
        self.bucket = self

    def blob(self, path):
        if path != sealed.APPROVAL_BLOB:
            raise RuntimeError("Unapproved bucket path")
        return self.blob_instance


@unittest.skipUnless(CRYPTO, "Uses existing cryptography package")
class EncryptedReadTests(unittest.TestCase):
    def setUp(self):
        self.owner_store = FakeStore()
        self.private_profiles = MagicMock()
        self.private_profiles.status.return_value = {"profile_exists": True}
        self.env = patch.dict(os.environ, ENV)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_independent_one_shot_consent_never_reveals_site_or_owner_in_vault_object(self):
        _, public = new_keypair()
        with patch.object(sealed, "_store", return_value=self.owner_store), \
             patch.object(sealed.BrowserProfileStore, "from_environment",
                          return_value=self.private_profiles):
            issued = sealed.approve_read(OWNER, site=SITE, path="/secure",
                                        recipient_public_key=public)
            self.assertEqual(issued["expires_in_seconds"], 600)
            blob = self.owner_store.blob_instance.data
            self.assertNotIn(OWNER.encode(), blob)
            self.assertNotIn(SITE.encode(), blob)
            self.assertNotIn(b"/secure", blob)
            record = sealed.consume_read()
            self.assertEqual(record["owner"], OWNER)
            self.assertEqual(record["site"], SITE)
            self.assertEqual(record["path"], "/secure")
            with self.assertRaises(PermissionError):
                sealed.consume_read()

    def test_consent_requires_valid_owner_saved_profile_and_host_scope(self):
        _, key = new_keypair()
        bad_keys = ["not-key", "A" * 42, "/" * 43, key + "="]
        with patch.object(sealed, "_store", return_value=self.owner_store), \
             patch.object(sealed.BrowserProfileStore, "from_environment",
                          return_value=self.private_profiles):
            for wrong_key in bad_keys:
                with self.subTest(wrong_key=wrong_key[:10]), self.assertRaises(PermissionError):
                    sealed.approve_read(OWNER, site=SITE, path="/secure",
                                        recipient_public_key=wrong_key)
            for bad_site, path in [(SITE, "https://evil.example.org/"),
                                   (SITE, "//evil.example.org"),
                                   (SITE, "/page#fragment"),
                                   ("https://evil.example.org", "/secure")]:
                with self.subTest(bad_site=bad_site,path=path),self.assertRaises(PermissionError):
                    sealed.approve_read(OWNER, site=bad_site, path=path,
                                        recipient_public_key=key)
            self.private_profiles.status.return_value = {"profile_exists": False}
            with self.assertRaises(PermissionError):
                sealed.approve_read(OWNER, site=SITE, path="/secure",
                                    recipient_public_key=key)
            self.assertIsNone(self.owner_store.blob_instance.data)

    def test_expiry_and_vault_cas_reject_old_consent(self):
        _, pub = new_keypair()
        now = int(time.time())
        with patch.object(sealed, "_store", return_value=self.owner_store), \
             patch.object(sealed.BrowserProfileStore, "from_environment",
                          return_value=self.private_profiles):
            sealed.approve_read(OWNER, site=SITE, path="/secure",
                                recipient_public_key=pub, now=now - 650)
            with self.assertRaises(PermissionError):
                sealed.consume_read(now=now)
            sealed.approve_read(OWNER, site=SITE, path="/secure",
                                recipient_public_key=pub, now=now)
            self.assertEqual(sealed.consume_read(now=now)["owner"], OWNER)

    def test_aead_roundtrip_wrong_key_and_tamper_fail_and_public_envelope_redacts_page(self):
        priv, pub = new_keypair()
        other, _ = new_keypair()
        record = {"site": SITE, "path": "/secure", "recipient_public_key": pub}
        result = {"site":SITE, "http_status":200,
                  "title":"Private synthetic title",
                  "body":"PRIVATE PAGE TEXT: confidential test result"}
        encrypted = sealed.seal_result(record, result)
        self.assertEqual(encrypted["plaintext_in_github"], False)
        self.assertNotIn(result["body"], json.dumps(encrypted))
        self.assertNotIn(record["site"], json.dumps(encrypted))
        self.assertLess(len(json.dumps(encrypted)), 8100)
        def open_with(key, envelope):
            b64 = lambda s: base64.urlsafe_b64decode(s+"="*(-len(s)%4))
            from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
            peer = X25519PublicKey.from_public_bytes(b64(envelope["ephemeral_public_key"]))
            derived = HKDF(algorithm=hashes.SHA256(), length=32,
                           salt=b64(envelope["salt"]),
                           info=sealed.HKDF_INFO).derive(key.exchange(peer))
            return json.loads(AESGCM(derived).decrypt(
                b64(envelope["nonce"]), b64(envelope["ciphertext"]), sealed.AAD))
        plaintext = open_with(priv, encrypted)
        self.assertEqual(plaintext["body"], result["body"])
        self.assertEqual(plaintext["path"], "/secure")
        with self.assertRaises(Exception):
            open_with(other, encrypted)
        altered = dict(encrypted)
        content = bytearray(base64.urlsafe_b64decode(encrypted["ciphertext"]+"="*(-len(encrypted["ciphertext"])%4)))
        content[-1] ^= 1
        altered["ciphertext"] = sealed._b64(bytes(content))
        with self.assertRaises(Exception):
            open_with(priv, altered)

    def test_cipher_never_serializes_arbitrary_browser_object_fields(self):
        _, pub = new_keypair()
        record = {"site": SITE, "path": "/secure", "recipient_public_key": pub}
        data = {"site": SITE, "http_status":200,
                "title":"Private", "body":"Authorized page",
                "cookie":"NEVER-ECHO", "session_state":{"password":"secret"}}
        result=sealed.seal_result(record, data)
        self.assertNotIn("NEVER-ECHO",json.dumps(result))
        self.assertNotIn("password",json.dumps(result))
        for bad in [
            {**data,"http_status":401},
            {**data,"site":"https://evil.example.org"},
            {**data,"body":"X"*1201},
        ]:
            with self.assertRaises(PermissionError):
                sealed.seal_result(record,bad)

    def test_disabled_service_is_denied_without_vault_access(self):
        for change in [{sealed.FLAG:"false"},
                       {"K_SERVICE":"plenum-computer-browser"},
                       {"PLENUM_CHAT_RELAY_ENABLED":"false"}]:
            with patch.dict(os.environ, change), self.assertRaises(PermissionError):
                sealed.require_enabled()


@unittest.skipUnless(CRYPTO and FASTAPI, "FastAPI and crypto required")
class AuthenticatedOwnerHttpTests(unittest.TestCase):
    def setUp(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from services.computer_browser.owner_sealed_relay import mount_owner_sealed_relay
        from services.computer_browser.owner_console import require_verified_owner
        self.env = patch.dict(os.environ, ENV)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.app=FastAPI()
        mount_owner_sealed_relay(self.app)
        self.owner_dep=require_verified_owner
        self.app.dependency_overrides[self.owner_dep]=lambda:{"private_owner_id":OWNER}
        self.client=TestClient(self.app)

    def test_owner_approval_exact_path_and_separately_signed_csrf(self):
        from services.computer_browser import owner_sealed_relay
        from services.computer_browser.owner_saved_session import _owner_form_token
        store=MagicMock()
        store.status.return_value={"profile_exists":True}
        with patch.object(owner_sealed_relay.BrowserProfileStore,"from_environment",
                          return_value=store):
            response=self.client.get("/owner/chat-sealed-approval")
        self.assertEqual(response.status_code,200)
        self.assertIn("Approve one encrypted page read",response.text)
        token=_owner_form_token(OWNER,SITE,"sealed_read")
        _,pub=new_keypair()
        params={"site":SITE,"path":"/secure",
                "recipient_public_key":pub,"confirmation":"APPROVE",
                "csrf_token":token}
        with patch.object(owner_sealed_relay,"approve_read",
                          return_value={"expires_in_seconds":600}) as issued:
            evil=self.client.post("/owner/chat-sealed-approval",data=params,
                headers={"origin":"https://attacker.example.org"})
            self.assertEqual(evil.status_code,403)
            self.assertFalse(issued.called)
            wrong=self.client.post("/owner/chat-sealed-approval",
                data={**params,"confirmation":"YES"})
            self.assertEqual(wrong.status_code,403)
            self.assertFalse(issued.called)
            valid=self.client.post("/owner/chat-sealed-approval",data=params)
        self.assertEqual(valid.status_code,200)
        self.assertIn("One sealed private page read authorized",valid.text)
        issued.assert_called_once_with(OWNER,site=SITE,path="/secure",
                                       recipient_public_key=pub)

    def test_github_workflow_requires_signed_identity_and_atomic_consent(self):
        from services.computer_browser import owner_sealed_relay
        from services.computer_browser.github_oidc_read_policy import GitHubOIDCTokenVerifier
        result={"site":SITE,"http_status":200,"title":"Private Title",
                "body":"SENSITIVE CONTENT MUST BE SEALED"}
        priv,pub=new_keypair()
        record={"site":SITE,"path":"/secure","owner":OWNER,
                "recipient_public_key":pub}
        with patch.object(GitHubOIDCTokenVerifier,"verify",
                          return_value={"trusted_github_workflow":True}) as verify, \
             patch.object(owner_sealed_relay,"consume_read",return_value=record) as consume, \
             patch.object(owner_sealed_relay,"read_saved_site",
                          new_callable=AsyncMock,return_value=result) as browser:
            without=self.client.post("/internal/chat-sealed-read")
            self.assertEqual(without.status_code,401)
            consume.assert_not_called()
            done=self.client.post("/internal/chat-sealed-read",
                headers={"authorization":"Bearer synthetic.signed.workflow"})
        self.assertEqual(done.status_code,200)
        self.assertTrue(done.json()["plaintext_in_github"] is False)
        self.assertNotIn(result["body"],done.text)
        self.assertEqual(done.headers["cache-control"],"no-store")
        self.assertEqual(consume.call_count,1)
        browser.assert_awaited_once_with(site=SITE, owner=OWNER,path="/secure")
        verify.assert_called_once_with("synthetic.signed.workflow")

    def test_no_owner_approval_does_not_run_browser(self):
        from services.computer_browser import owner_sealed_relay
        from services.computer_browser.github_oidc_read_policy import GitHubOIDCTokenVerifier
        with patch.object(GitHubOIDCTokenVerifier,"verify",
                          return_value={"trusted_github_workflow":True}), \
             patch.object(owner_sealed_relay,"consume_read",
                          side_effect=PermissionError("Missing consent")), \
             patch.object(owner_sealed_relay,"read_saved_site",
                          new_callable=AsyncMock) as reader:
            response=self.client.post("/internal/chat-sealed-read",
                headers={"authorization":"Bearer synthetic.signed.workflow"})
        self.assertEqual(response.status_code,403)
        reader.assert_not_awaited()


class SignedWorkflowSeparationTests(unittest.TestCase):
    def test_public_demo_and_private_sealed_read_have_distinct_pinned_claims(self):
        self.assertNotEqual(AUDIENCE,SEALED_AUDIENCE)
        self.assertNotEqual(WORKFLOW_REF,SEALED_WORKFLOW_REF)
        now=int(time.time())
        claims={
            "iat":now,"nbf":now,"exp":now+120,
            "iss":"https://token.actions.githubusercontent.com",
            "aud":SEALED_AUDIENCE,
            "repository":"chadkhalil21-svg/Plenum-Scientific-Intelligence",
            "repository_id":"1447724141",
            "repository_owner":"chadkhalil21-svg",
            "actor":"chadkhalil21-svg",
            "actor_id":"251133044",
            "event_name":"issues","ref":"refs/heads/main",
            "ref_type":"branch","workflow_ref":SEALED_WORKFLOW_REF,
            "environment":"computer-browser-production",
            "repository_visibility":"public",
            "sub":"repo:chadkhalil21-svg@251133044/Plenum-Scientific-Intelligence@1447724141:environment:computer-browser-production",
            "repository_owner_id":"251133044",
            "runner_environment":"github-hosted",
            "jti":"synthetic-unique-jti-00001","run_id":"42584878685",
        }
        identity=GitHubRelayIdentity("1447724141","251133044")
        self.assertTrue(enforce_relay_claims(
            claims,identity,now=now,
            expected_audience=SEALED_AUDIENCE,
            expected_workflow_ref=SEALED_WORKFLOW_REF)["trusted_github_workflow"])
        with self.assertRaises(PermissionError):
            enforce_relay_claims(claims,identity,now=now)
        with self.assertRaises(PermissionError):
            enforce_relay_claims({**claims,"actor_id":"9999"},identity,now=now,
                expected_audience=SEALED_AUDIENCE,
                expected_workflow_ref=SEALED_WORKFLOW_REF)


if __name__ == "__main__":
    unittest.main()

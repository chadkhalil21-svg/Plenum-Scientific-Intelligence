"""New Plenum-specific adaptive owner browser contract, no live accounts."""
import base64
import importlib.util
import json
import os
import re
import time
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from services.computer_browser import sealed_chat_read as sealed
from services.computer_browser import owner_adaptive_session as adaptive

CRYPTO = importlib.util.find_spec("cryptography") is not None
FASTAPI = importlib.util.find_spec("fastapi") is not None
OWNER = "b" * 64
SITE = "https://the-internet.herokuapp.com"
ENV = {
    "K_SERVICE": "plenum-browser-owner-auth0",
    "PLENUM_CHAT_RELAY_ENABLED": "true",
    "PLENUM_ADAPTIVE_OWNER_READ_ENABLED": "true",
    sealed.FLAG: "true",
    "AUTH0_OWNER_PUBLIC_ORIGIN":
        "https://plenum-browser-owner-auth0-2lak3vl73q-ue.a.run.app",
    "BROWSER_PUBLIC_ORIGIN":
        "https://plenum-browser-owner-auth0-2lak3vl73q-ue.a.run.app",
    "BROWSER_ALLOWED_ORIGINS": SITE + ",https://example.com",
    "BROWSER_PROFILE_BUCKET": "fake-private-owner-bucket",
    "COMPUTER_BROWSER_TOKEN": "synthetic-private-owner-test-token-" * 2,
    "PLENUM_CHAT_RELAY_REPO_ID": "1447724141",
    "PLENUM_CHAT_RELAY_ACTOR_ID": "251133044",
}
if CRYPTO:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    ENV["BROWSER_SESSION_KEY"] = Fernet.generate_key().decode()


class AtomicBlob:
    def __init__(self):
        self.data = None
        self.generation = None
        self.revision = 0

    def exists(self):
        return self.data is not None

    def reload(self):
        if self.data is None:
            raise FileNotFoundError("No encrypted owner approval")

    def upload_from_string(self, value, *, content_type, if_generation_match):
        if ((self.data is None and if_generation_match != 0)
                or (self.data is not None and self.generation != if_generation_match)):
            raise RuntimeError("GCS compare-and-swap prevented stale write")
        self.revision += 1
        self.generation = self.revision
        self.data = value

    def download_as_bytes(self, *, if_generation_match):
        if self.data is None or self.generation != if_generation_match:
            raise RuntimeError("Missing or stale owner approval")
        return self.data

    def delete(self, *, if_generation_match):
        if self.data is None or self.generation != if_generation_match:
            raise RuntimeError("Owner approval already revoked")
        self.data = None
        self.generation = None


class Store:
    def __init__(self):
        self.objects = {}
        self.bucket = self

    def blob(self, name):
        if name not in (sealed.APPROVAL_BLOB, adaptive.CURSOR_BLOB):
            raise RuntimeError("Undeclared private vault location")
        if name not in self.objects:
            self.objects[name] = AtomicBlob()
        return self.objects[name]


def new_keys():
    key = X25519PrivateKey.generate()
    pub = key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw)
    return key, sealed._b64(pub)


@unittest.skipUnless(CRYPTO, "Original X25519/AES-GCM dependency required")
class AdaptiveOwnerContract(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, ENV)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.store = Store()
        self.store_patch = patch.object(sealed, "_store", return_value=self.store)
        self.store_patch.start()
        self.addCleanup(self.store_patch.stop)
        profile = MagicMock()
        profile.status.return_value = {"profile_exists": True}
        self.profile_patch = patch.object(
            sealed.BrowserProfileStore, "from_environment", return_value=profile)
        self.profile_patch.start()
        self.addCleanup(self.profile_patch.stop)

    def approve(self, *, now=None):
        _, public = new_keys()
        sealed.approve_read(OWNER, site=SITE, path="/secure",
                            recipient_public_key=public, adaptive=True, now=now)
        return sealed.consume_read(now=now)

    def page(self, path="/secure", links=None):
        return {
            "site": SITE, "final_url": SITE+path, "http_status": 200,
            "title": "Authorized private page", "body": "NO PRIVATE DATA IN GITHUB",
            "demo_authenticated_restored": path == "/secure",
            "links_untrusted": links if links is not None else [
                {"label_untrusted": "Research", "path": "/research"},
                {"label_untrusted": "Delete", "path": "/delete/all"},
                {"label_untrusted": "Reports", "path": "/reports"},
                {"label_untrusted": "Cross", "path": "//evil.example/"},
            ],
        }

    def test_owner_consent_one_time_secure_and_batch_exclusive(self):
        _, key = new_keys()
        with self.assertRaises(PermissionError):
            sealed.approve_read(
                OWNER, site=SITE, path="/secure", recipient_public_key=key,
                additional_paths="/research", adaptive=True)
        record = self.approve()
        self.assertEqual(record["schema"], "plenum-sealed-owner-adaptive-consent-v1")
        self.assertRegex(record["adaptive_session_id"], r"^[0-9a-f]{32}$")
        self.assertNotIn(SITE.encode(), self.store.blob(
            sealed.APPROVAL_BLOB).data or b"")
        with self.assertRaises(PermissionError):
            sealed.consume_read()
        self.assertFalse(adaptive.require_enabled() is False)

    def test_read_only_adaptation_with_one_approval_and_owner_revocation(self):
        consent = self.approve()
        raw = self.page()
        screened = {**raw, "links_untrusted": adaptive._safe_links(
            SITE, "/secure", raw)}
        encrypted = sealed.seal_result(consent, screened)
        self.assertNotIn("NO PRIVATE DATA IN GITHUB", json.dumps(encrypted))
        info = adaptive.begin_session(consent, self.page())
        sid = info["session_id"]
        self.assertEqual(info["remaining"], 3)
        self.assertEqual([v["path"] for v in info["links_untrusted"]],
                         ["/research", "/reports"])
        # Opaque link number only, never a public GitHub URL or private data.
        with self.assertRaises(PermissionError):
            adaptive.consume_follow("f" * 32, 1)
        cursor = adaptive.consume_follow(sid, 1)
        self.assertEqual(cursor["path"], "/research")
        with self.assertRaises(PermissionError):
            adaptive.consume_follow(sid, 1)  # In-flight lease stops replay
        adaptive.save_follow(cursor, self.page(
            "/research", [{"label_untrusted": "Reports", "path": "/reports"}]))
        follow = adaptive.consume_follow(sid, 1)
        self.assertEqual(follow["path"], "/reports")
        self.assertTrue(adaptive.revoke_session())
        with self.assertRaises(PermissionError):
            adaptive.save_follow(follow, self.page("/reports", []))
        with self.assertRaises(PermissionError):
            adaptive.consume_follow(sid, 1)

    def test_follow_replay_expiry_and_path_scope_rejected(self):
        t = int(time.time())
        consent = self.approve(now=t)
        info = adaptive.begin_session(consent, self.page(), now=t)
        sid = info["session_id"]
        for bad in ["", "A" * 32, "x" * 32]:
            with self.assertRaises(PermissionError):
                adaptive.consume_follow(bad, 1, now=t)
        for index in [0, -1, 7, True]:
            with self.assertRaises(PermissionError):
                adaptive.consume_follow(sid, index, now=t)
        with self.assertRaises(PermissionError):
            adaptive.consume_follow(sid, 1, now=t+601)
        with self.assertRaises(PermissionError):
            adaptive.begin_session(consent, self.page(), now=t+601)
        with patch.dict(os.environ, {adaptive.FLAG: "false"}):
            with self.assertRaises(PermissionError):
                adaptive.consume_follow(sid, 1, now=t)

    def test_revocation_also_cancels_pending_owner_approval_before_first_read(self):
        _, public = new_keys()
        sealed.approve_read(OWNER, site=SITE, path="/secure",
                            recipient_public_key=public, adaptive=True)
        self.assertNotIn(SITE.encode(), self.store.blob(
            sealed.APPROVAL_BLOB).data)
        with self.assertRaises(PermissionError):
            adaptive.revoke_session(owner="c" * 64)
        self.assertTrue(adaptive.revoke_session(owner=OWNER))
        with self.assertRaises(PermissionError):
            sealed.consume_read()
        self.assertFalse(adaptive.revoke_session(owner=OWNER))

    def test_sealed_result_metadata_stays_recipient_only(self):
        consent = self.approve()
        result = self.page()
        result["links_untrusted"] = adaptive._safe_links(
            SITE, "/secure", result)
        envelope = sealed.seal_result(consent, result)
        serialized = json.dumps(envelope)
        self.assertNotIn(consent["adaptive_session_id"], serialized)
        self.assertNotIn("/research", serialized)
        self.assertFalse(envelope["plaintext_in_github"])
        # Published envelope retains the original expected cryptographic type.
        self.assertEqual(envelope["encoding"], "x25519-hkdf-sha256-aes256gcm")
        from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
        from cryptography.hazmat.primitives import hashes
        # The original recipient's private key is the ONLY decryption key;
        # a separate key here MUST NOT decrypt the confidential result.
        other, _ = new_keys()
        b64 = lambda v: base64.urlsafe_b64decode(v+"="*(-len(v)%4))
        peer = X25519PublicKey.from_public_bytes(b64(envelope["ephemeral_public_key"]))
        derived = HKDF(algorithm=hashes.SHA256(), length=32,
                       salt=b64(envelope["salt"]),
                       info=sealed.HKDF_INFO).derive(other.exchange(peer))
        with self.assertRaises(Exception):
            AESGCM(derived).decrypt(
                b64(envelope["nonce"]), b64(envelope["ciphertext"]), sealed.AAD)


@unittest.skipUnless(CRYPTO and FASTAPI, "Authenticated owner HTTP test dependencies")
class AdaptiveOwnerHttpContract(unittest.TestCase):
    def setUp(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from services.computer_browser.owner_sealed_relay import mount_owner_sealed_relay
        from services.computer_browser.owner_console import require_verified_owner
        from services.computer_browser import owner_sealed_relay as relay
        self.env = patch.dict(os.environ, ENV)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.app = FastAPI()
        mount_owner_sealed_relay(self.app)
        self.app.dependency_overrides[require_verified_owner] = lambda: {
            "private_owner_id": OWNER}
        self.client = TestClient(self.app)
        self.relay = relay

    def test_owner_ui_requires_exact_csrf_for_approval_and_revocation(self):
        from services.computer_browser.owner_saved_session import _owner_form_token
        profile = MagicMock()
        profile.status.return_value = {"profile_exists": True}
        with patch.object(self.relay.BrowserProfileStore, "from_environment",
                          return_value=profile):
            page = self.client.get("/owner/chat-sealed-approval")
        self.assertEqual(page.status_code, 200)
        self.assertIn("name='adaptive'", page.text)
        self.assertIn("Revoke adaptive browser session", page.text)
        _, public = new_keys()
        payload = {
            "site": SITE, "path": "/secure", "recipient_public_key": public,
            "adaptive": "read_only", "confirmation": "APPROVE",
            "csrf_token": _owner_form_token(OWNER, SITE, "sealed_read"),
        }
        with patch.object(self.relay, "approve_read",
                          return_value={"expires_in_seconds": 600}) as approve:
            bad = self.client.post("/owner/chat-sealed-approval",
                                   data=payload,
                                   headers={"origin":"https://attacker.invalid"})
            self.assertEqual(bad.status_code, 403)
            self.assertFalse(approve.called)
            good = self.client.post("/owner/chat-sealed-approval",data=payload)
        self.assertEqual(good.status_code, 200)
        approve.assert_called_once_with(
            OWNER, site=SITE, path="/secure", recipient_public_key=public,
            adaptive=True)
        revoke = {
            "csrf_token": _owner_form_token(
                OWNER, "https://example.com", "adaptive_revoke"),
            "confirmation": "REVOKE",
        }
        with patch.object(self.relay, "revoke_session",return_value=True) as revoked:
            wrong = self.client.post("/owner/chat-adaptive-revoke",
                                     data={**revoke,"confirmation":"NO"})
            self.assertEqual(wrong.status_code, 403)
            self.assertFalse(revoked.called)
            okay = self.client.post("/owner/chat-adaptive-revoke",data=revoke)
        self.assertEqual(okay.status_code, 200)
        revoked.assert_called_once_with(owner=OWNER)

    def test_signed_follow_only_and_no_generic_private_write(self):
        from services.computer_browser.github_oidc_read_policy import GitHubOIDCTokenVerifier
        _, public = new_keys()
        cursor = {
            "site": SITE, "owner": OWNER, "path": "/research",
            "recipient_public_key": public,
            "session_id": "a" * 32, "remaining": 2, "lease": "c" * 32,
        }
        result = {
            "site": SITE, "final_url": SITE+"/research", "http_status": 200,
            "title": "Private research", "body": "NO PUBLIC CONTENT",
            "links_untrusted": [{"label_untrusted":"Reports","path":"/reports"}],
        }
        with patch.object(GitHubOIDCTokenVerifier,"verify",
                          return_value={"trusted_github_workflow":True}), \
             patch.object(self.relay,"consume_follow",return_value=cursor) as consume, \
             patch.object(self.relay,"read_hardened_saved_site",
                          new_callable=AsyncMock,return_value=result) as browser, \
             patch.object(self.relay,"save_follow",return_value={"remaining":2}) as save:
            denied=self.client.post("/internal/chat-sealed-read",
                headers={"x-plenum-navigation":"a"*32+":1"})
            self.assertEqual(denied.status_code,401)
            consume.assert_not_called()
            okay=self.client.post("/internal/chat-sealed-read",
                headers={"authorization":"Bearer signed.synthetic.oidc",
                         "x-plenum-navigation":"a"*32+":1"})
        self.assertEqual(okay.status_code,200)
        self.assertFalse(okay.json()["plaintext_in_github"])
        self.assertNotIn("NO PUBLIC CONTENT", okay.text)
        browser.assert_awaited_once_with(site=SITE,owner=OWNER,path="/research")
        save.assert_called_once()
        # No site URL, write plan, JavaScript command or account credential
        # is accepted from the public GitHub issue or HTTP client.


if __name__ == "__main__":
    unittest.main()

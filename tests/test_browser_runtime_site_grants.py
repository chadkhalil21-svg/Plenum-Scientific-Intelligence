"""Original Plenum integration tests for universal owner website registration.

Synthetic owner, GCS and website DNS only; no private pages or real logins.
"""
import importlib.util
import os
import unittest
from unittest.mock import patch, MagicMock

FASTAPI = importlib.util.find_spec("fastapi") is not None
CRYPTO = importlib.util.find_spec("cryptography") is not None
# The scientific foundation intentionally installs neither HTTP gateway
# nor browser crypto extras; keep the optional Plenum browser tests skipped.
if FASTAPI and CRYPTO:
    from services.computer_browser import runtime_site_grants as grants
else:
    grants = None

if CRYPTO:
    from cryptography.fernet import Fernet

OWNER = "a" * 64
OTHER_OWNER = "b" * 64
SITE = "https://example.org"
ANOTHER = "https://another-example.net"
ENV = {
    "K_SERVICE": "plenum-browser-owner-auth0",
    "PLENUM_RUNTIME_SITE_GRANTS_ENABLED": "true",
    "BROWSER_PUBLIC_ORIGIN": "https://computer.example.com",
    "COMPUTER_BROWSER_TOKEN": "private-runtime-site-csrf-" * 3,
    "BROWSER_ALLOWED_ORIGINS": "https://example.com",
}


class FakeBlob:
    def __init__(self):
        self.value = None
        self.generation = None
        self.rev = 0

    def exists(self):
        return self.value is not None

    def reload(self):
        if self.value is None:
            raise FileNotFoundError("No registry")

    def download_as_bytes(self, if_generation_match):
        if if_generation_match != self.generation:
            raise RuntimeError("Conflicting generation")
        return self.value

    def upload_from_string(self, data, *, content_type, if_generation_match):
        if content_type != "application/octet-stream":
            raise AssertionError("Registration must be private binary")
        if if_generation_match != (self.generation if self.value else 0):
            raise RuntimeError("Stale update rejected")
        self.rev += 1
        self.value = data
        self.generation = self.rev


class FakeBucket:
    def __init__(self):
        self.blobs = {}

    def blob(self, name):
        if not name.startswith("browser-owner-site-grants/v1/"):
            raise RuntimeError("Invalid private registry object prefix")
        return self.blobs.setdefault(name, FakeBlob())


@unittest.skipUnless(CRYPTO, "Original encrypted grant tests need cryptography")
class RuntimeSiteGrantTests(unittest.TestCase):
    def setUp(self):
        self.key = Fernet.generate_key()
        self.bucket = FakeBucket()
        self.store = grants.OwnerSiteGrantStore(bucket=self.bucket, key=self.key)

    def test_owner_can_register_any_public_https_origin_without_code_change(self):
        a = self.store.register(owner=OWNER, origin=SITE, now=10000)
        b = self.store.register(owner=OWNER, origin=ANOTHER, now=10001)
        self.assertTrue(a["registered"])
        self.assertFalse(a["browser_navigation_enabled"])
        self.assertEqual(b["site"], ANOTHER)
        self.assertTrue(self.store.authorized(owner=OWNER, origin=SITE, now=10002))
        self.assertFalse(self.store.authorized(owner=OTHER_OWNER, origin=SITE, now=10002))
        self.assertEqual([x["origin"] for x in self.store.list_active(owner=OWNER, now=10003)],
                         [ANOTHER, SITE])
        self.assertEqual(len(self.bucket.blobs), 2)  # One owner-scoped index each.
        for blob in self.bucket.blobs.values():
            if blob.value:
                self.assertNotIn(SITE.encode(), blob.value)
                self.assertNotIn(OWNER.encode(), blob.value)
                self.assertNotIn(ANOTHER.encode(), blob.value)

    def test_expiry_revocation_and_second_registration_are_cas_bound(self):
        self.store.register(owner=OWNER, origin=SITE, now=10000)
        blob = self.store._blob(OWNER)
        original_cipher = blob.value
        self.assertTrue(self.store.authorized(owner=OWNER, origin=SITE, now=10001))
        self.assertFalse(self.store.authorized(owner=OWNER, origin=SITE,
                                                now=10000 + grants.TTL_SECONDS))
        self.store.register(owner=OWNER, origin=SITE, now=10020)
        self.assertNotEqual(original_cipher, blob.value)
        self.assertTrue(self.store.revoke(owner=OWNER, origin=SITE, now=10021)["revoked"])
        self.assertFalse(self.store.authorized(owner=OWNER, origin=SITE, now=10022))
        self.assertFalse(self.store.revoke(owner=OWNER, origin=SITE, now=10023)["revoked"])
        # A stale two-client writer cannot overwrite a newer grant snapshot.
        with self.assertRaises(RuntimeError):
            blob.upload_from_string(b"tampered", content_type="application/octet-stream",
                                    if_generation_match=1)

    def test_confidentiality_integrity_and_wrong_owner_are_fail_closed(self):
        self.store.register(owner=OWNER, origin=SITE, now=10000)
        blob = self.store._blob(OWNER)
        blob.value = blob.value[:-1] + b"A"
        with self.assertRaises(PermissionError):
            self.store.list_active(owner=OWNER, now=10001)
        self.assertEqual(self.store.list_active(owner=OTHER_OWNER, now=10001), [])

    def test_normalize_origin_rejects_credential_hosts_private_ip_and_url_paths(self):
        denied = (
            "http://example.org", "https://example.org/path",
            "https://example.org/", "https://example.org?secret=1",
            "https://alice:pass@example.org", "https://127.0.0.1",
            "https://localhost", "https://internal.local", "https://host.internal",
            "https://evil.example.org#fragment", "https://example.org:8080",
            "https://example.org:443", "https://example.org@other.example",
            "https://EXAMPLE.ORG", "ftp://example.org",
        )
        for bad in denied:
            with self.subTest(origin=bad), self.assertRaises(PermissionError):
                grants.normalize_origin(bad)
        self.assertEqual(grants.normalize_origin("https://research.example.org"),
                         "https://research.example.org")

    def test_registration_not_enabled_on_other_cloud_run_services(self):
        for vals in [
            {"K_SERVICE": "plenum-computer-browser-machine"},
            {"PLENUM_RUNTIME_SITE_GRANTS_ENABLED": "false"},
        ]:
            with patch.dict(os.environ, {**ENV, **vals}):
                self.assertFalse(grants.enabled())
        with patch.dict(os.environ, ENV):
            self.assertTrue(grants.enabled())


@unittest.skipUnless(CRYPTO and FASTAPI, "Owner FastAPI and crypto tests")
class OwnerSiteRegistrationHttpTests(unittest.TestCase):
    def setUp(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from services.computer_browser.owner_console import require_verified_owner
        from services.computer_browser.owner_saved_session import _owner_form_token

        self.env = patch.dict(os.environ, ENV)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.key = Fernet.generate_key()
        self.store = grants.OwnerSiteGrantStore(bucket=FakeBucket(), key=self.key)
        self.app = FastAPI()
        grants.mount_runtime_site_grants(self.app)
        self.client = TestClient(self.app)
        self.app.dependency_overrides[require_verified_owner] = lambda: {
            "private_owner_id": OWNER}
        self.form_token = _owner_form_token
        self.store_patch = patch.object(grants.OwnerSiteGrantStore,
                                        "from_environment", return_value=self.store)
        self.store_patch.start()
        self.addCleanup(self.store_patch.stop)

    def _approval(self, site=SITE, action="site_register"):
        scope = grants.REGISTRY_SCOPE if action == "site_register" else site
        return self.form_token(OWNER, scope, action)

    def test_owner_only_ui_and_exact_site_confirmation(self):
        page = self.client.get("/owner/sites")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Registration alone does NOT activate browser navigation", page.text)
        self.assertIn("Register owner-approved website", page.text)
        self.assertEqual(page.headers.get("cache-control"), "no-store")
        with patch.object(grants, "public_dns_only", return_value=None) as dns:
            result = self.client.post("/owner/sites/authorize", data={
                "site": SITE,
                "confirmation": "AUTHORIZE",
                "csrf_token": self._approval()
            })
        self.assertEqual(result.status_code, 200)
        dns.assert_called_once_with(SITE)
        self.assertTrue(self.store.authorized(owner=OWNER, origin=SITE))
        self.assertIn("does NOT activate browser navigation", page.text)
        self.assertNotIn("browser_navigation_enabled", result.text)
        self.assertIn(SITE, self.client.get("/owner/sites").text)

    def test_external_origin_wrong_action_bad_confirmation_denied_no_mutation(self):
        good = {"site": SITE, "confirmation": "AUTHORIZE",
                "csrf_token": self._approval()}
        cases = [
            ({**good, "confirmation": "YES"}, {}),
            ({**good, "csrf_token": ""}, {}),
            ({**good, "csrf_token": self._approval(action="site_revoke")}, {}),
            (good, {"origin": "https://attacker.example.net"}),
            (good, {"sec-fetch-site": "cross-site"}),
            ({**good, "site": "http://example.org"}, {}),
        ]
        with patch.object(grants, "public_dns_only", return_value=None) as dns:
            for data, headers in cases:
                with self.subTest(data=data, headers=headers):
                    denied = self.client.post("/owner/sites/authorize",
                                              data=data, headers=headers)
                    self.assertEqual(denied.status_code, 403)
            dns.assert_not_called()
        self.assertEqual(self.store.list_active(owner=OWNER), [])

    def test_dns_reject_and_registry_revocation(self):
        with patch.object(grants, "public_dns_only", side_effect=PermissionError):
            response = self.client.post("/owner/sites/authorize",
                data={"site": SITE, "confirmation": "AUTHORIZE",
                      "csrf_token": self._approval()})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.store.list_active(owner=OWNER), [])
        with patch.object(grants, "public_dns_only", return_value=None):
            self.assertEqual(self.client.post("/owner/sites/authorize",
                data={"site": SITE, "confirmation": "AUTHORIZE",
                      "csrf_token": self._approval()}).status_code, 200)
        wrong = self.client.post("/owner/sites/revoke", data={
            "site": SITE, "confirmation": "REVOKE",
            "csrf_token": self._approval()})
        self.assertEqual(wrong.status_code, 403)
        right = self.client.post("/owner/sites/revoke", data={
            "site": SITE, "confirmation": "REVOKE",
            "csrf_token": self._approval(action="site_revoke")})
        self.assertEqual(right.status_code, 200)
        self.assertFalse(self.store.authorized(owner=OWNER, origin=SITE))
        self.assertIn("separately preconfigured", right.text)

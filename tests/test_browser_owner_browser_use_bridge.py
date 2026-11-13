"""Original encrypted owner session -> pinned upstream Browser Use; no live account use."""
import unittest
import importlib.util
from unittest.mock import patch

from services.computer_browser.owner_browser_use_bridge import build_private_browser_use

ORIGIN = "https://github.com"
BINARY = "/ms-playwright/chromium-1165/chrome-linux/chrome"


class FakeStore:
    def __init__(self, state, generation=2):
        self.state, self.generation = state, generation
        self.requested = None

    def load_for_trusted_worker(self, *, owner, origin):
        self.requested = (owner, origin)
        return self.state, self.generation


def state():
    return {
        "cookies": [
            {"domain": ".github.com", "name": "owner", "value": "PRIVATE_COOKIE"},
            {"domain": ".elsewhere.test", "name": "other", "value": "MUST_NOT_TRANSFER"}
        ],
        "origins": [
            {"origin": ORIGIN, "localStorage": [{"name": "credential", "value": "PRIVATE_STATE"}]},
            {"origin": "https://elsewhere.test", "localStorage": [{"name": "other", "value": "MUST_NOT_TRANSFER"}]}
        ]
    }


@unittest.skipUnless(importlib.util.find_spec('fastapi') is not None,
                     'Private browser CI installs FastAPI; science core does not')
class OwnerBrowserUseBridgeTests(unittest.TestCase):
    def build(self, **options):
        observed = {}
        def capture(**kwargs):
            observed.update(kwargs)
            return observed
        default = dict(
            verified_owner={"private_owner_id": "founder-private-owner"},
            website_origin=ORIGIN,
            owner_proxy_url="http://127.0.0.1:24517",
            existing_chromium_executable=BINARY,
            store=FakeStore(state()),
            browser_factory=capture,
        )
        default.update(options)
        with patch("services.computer_browser.owner_browser_use_bridge.owner_live_origin",
                   return_value=(ORIGIN, True)):
            result = build_private_browser_use(**default)
        return result

    def test_reuses_original_browser_binary_vault_and_pinned_proxy(self):
        result = self.build()
        self.assertEqual(result["executable_path"], BINARY)
        self.assertEqual(result["allowed_domains"], [ORIGIN])
        self.assertEqual(result["proxy"], {"server": "http://127.0.0.1:24517"})
        self.assertFalse(result["use_cloud"])
        self.assertTrue(result["is_local"])
        self.assertIsNone(result["cdp_url"])
        self.assertIsNone(result["user_data_dir"])
        self.assertFalse(result["enable_default_extensions"])
        self.assertTrue(result["block_ip_addresses"])
        self.assertFalse(result["keep_alive"])
        self.assertEqual(len(result["storage_state"]["cookies"]), 1)
        self.assertEqual(result["storage_state"]["cookies"][0]["value"], "PRIVATE_COOKIE")
        self.assertEqual(len(result["storage_state"]["origins"]), 1)
        self.assertEqual(result["storage_state"]["origins"][0]["origin"], ORIGIN)
        self.assertNotIn("MUST_NOT_TRANSFER", str(result))

    def test_rejects_missing_or_unverified_session(self):
        for value in [None, {}, {"private_owner_id": ""}]:
            with self.subTest(value=value), self.assertRaises(PermissionError):
                self.build(verified_owner=value)
        with self.assertRaises(PermissionError):
            self.build(store=FakeStore({"cookies": [], "origins": []}))

    def test_rejects_unsafe_proxy_or_foreign_executable(self):
        for proxy in ["https://127.0.0.1:24517", "http://0.0.0.0:24517",
                      "http://127.0.0.1:0", "http://127.0.0.1:24517/secret"]:
            with self.subTest(proxy=proxy), self.assertRaises(PermissionError):
                self.build(owner_proxy_url=proxy)
        for binary in ["/usr/bin/google-chrome", "/ms-playwright/../malicious",
                       "https://example.com/browser"]:
            with self.subTest(binary=binary), self.assertRaises(PermissionError):
                self.build(existing_chromium_executable=binary)

    def test_rejects_foreign_origin_and_revoked_owner_grant(self):
        for origin in ["https://github.com/private", "https://github.com:443",
                       "http://github.com", "https://evil.test"]:
            with self.subTest(origin=origin), self.assertRaises(PermissionError):
                self.build(website_origin=origin)
        with patch("services.computer_browser.owner_browser_use_bridge.owner_live_origin",
                   return_value=(ORIGIN, False)):
            with self.assertRaises(PermissionError):
                build_private_browser_use(
                    verified_owner={"private_owner_id": "founder-private-owner"},
                    website_origin=ORIGIN,
                    owner_proxy_url="http://127.0.0.1:24517",
                    existing_chromium_executable=BINARY,
                    store=FakeStore(state()),
                    browser_factory=lambda **kw: kw)

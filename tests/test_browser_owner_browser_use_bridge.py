"""Original encrypted owner session -> pinned upstream Browser Use; no live account use."""
import unittest
import asyncio
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock
import importlib.util
from unittest.mock import patch

from services.computer_browser.owner_browser_use_bridge import (build_private_browser_use, _owner_readonly_tools, run_owner_readonly_browser_task)

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
        self.assertTrue(result["browser_profile"]["block_ip_addresses"])
        self.assertNotIn("block_ip_addresses", result)
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


@unittest.skipUnless(importlib.util.find_spec('fastapi') is not None,
                     'Private browser CI installs original owner FastAPI')
class OwnerReadOnlyAgentContractTests(unittest.TestCase):
    def test_only_read_only_upstream_actions_survive(self):
        class FakeTools:
            def __init__(self):
                acts={n:object() for n in (
                    "done","navigate","scroll","find_elements","go_back",
                    "click","input","upload_file","evaluate","send_keys",
                    "write_file","search","save_as_pdf","screenshot")}
                self.registry=SimpleNamespace(registry=SimpleNamespace(actions=acts))
            def exclude_action(self,name):
                del self.registry.registry.actions[name]
        t=_owner_readonly_tools(tools_factory=FakeTools)
        actions=set(t.registry.registry.actions)
        self.assertIn("done", actions)
        self.assertIn("navigate", actions)
        for name in ("click","input","upload_file","evaluate","send_keys",
                     "write_file","search","save_as_pdf","screenshot"):
            self.assertNotIn(name, actions)

    def test_missing_upstream_done_fails_closed(self):
        class BrokenTools:
            def __init__(self):
                self.registry=SimpleNamespace(
                    registry=SimpleNamespace(actions={"click":object()}))
            def exclude_action(self,name):
                del self.registry.registry.actions[name]
        with self.assertRaises(PermissionError):
            _owner_readonly_tools(tools_factory=BrokenTools)

    def test_trusted_owner_read_mission_requires_verifier_and_never_returns_secrets(self):
        seen={}
        class FakeTools:
            def __init__(self):
                self.registry=SimpleNamespace(registry=SimpleNamespace(
                    actions={"navigate":1, "done":1, "find_elements":1, "click":1}))
            def exclude_action(self,name):
                del self.registry.registry.actions[name]
        class FakeBrowser:
            def __init__(self,**kwargs):
                seen["browser_settings"]=kwargs
                self.stop=AsyncMock()
        class FakeHistory:
            def is_done(self): return True
            def is_successful(self): return True
        class FakeAgent:
            def __init__(self, **kwargs):
                self.tools=kwargs["tools"]
                seen["task"]=kwargs["task"]
                seen["max_failures"]=kwargs["max_failures"]
            async def run(self, max_steps):
                seen["steps"]=max_steps
                return FakeHistory()
        async def approved(owner,origin,objective):
            seen["owner_approval"]=(owner,origin,objective)
            return True
        async def verify(history,browser):
            self.assertIsInstance(history, FakeHistory)
            seen["independent_verifier_called"]=True
            return True

        async def execute(verify_result=True):
            def custom_verify(history,browser):
                return verify(history,browser) if verify_result else False
            with patch.dict("os.environ",{
                "PLENUM_OWNER_READONLY_AGENT_ENABLED":"true",
                "PLENUM_BROWSER_FREE_LOCAL":"confirmed",
                "ANONYMIZED_TELEMETRY":"false",
                "BROWSER_USE_SETUP_LOGGING":"false",
            }), patch("services.computer_browser.owner_browser_use_bridge.owner_live_origin",
                      return_value=(ORIGIN,True)):
                result=await run_owner_readonly_browser_task(
                    verified_owner={"private_owner_id":"founder-private-owner"},
                    website_origin=ORIGIN,
                    objective="Inspect the account-specific existing issue status",
                    owner_proxy_url="http://127.0.0.1:24517",
                    existing_chromium_executable=BINARY,
                    store=FakeStore(state()),
                    browser_factory=FakeBrowser,
                    tools_factory=FakeTools, model_factory=lambda: object(),
                    agent_factory=FakeAgent,
                    independent_verify=custom_verify,
                    approval_callback=approved,
                    approval_expires_at=time.time()+200,
                )
                return result
        result=asyncio.run(execute())
        self.assertEqual(result["status"],"INDEPENDENTLY_VERIFIED_BY_TRUSTED_CALLER")
        self.assertTrue(seen["independent_verifier_called"])
        self.assertEqual(seen["steps"],6)
        self.assertEqual(seen["max_failures"],1)
        self.assertEqual(seen["owner_approval"][1],ORIGIN)
        self.assertNotIn("PRIVATE_COOKIE",str(result))
        self.assertNotIn("PRIVATE_STATE",str(result))
        blocked=asyncio.run(execute(False))
        self.assertEqual(blocked["status"],"BLOCKED_NOT_INDEPENDENTLY_VERIFIED")

    def test_disabled_and_expired_grants_never_open_browser(self):
        kwargs=dict(
            verified_owner={"private_owner_id":"founder-private-owner"},
            website_origin=ORIGIN,
            objective="Inspect the account-specific existing issue status",
            owner_proxy_url="http://127.0.0.1:24517",
            existing_chromium_executable=BINARY,
            store=FakeStore(state()),
            browser_factory=lambda **k: self.fail("Browser must remain closed"),
            model_factory=lambda: self.fail("Model must remain closed"),
            tools_factory=lambda: self.fail("Tools must remain closed"),
            agent_factory=lambda **k: self.fail("Agent must remain closed"),
            independent_verify=lambda h,b: True,
            approval_callback=lambda *args: True,
            approval_expires_at=time.time()+200,
        )
        with patch.dict("os.environ",{"PLENUM_OWNER_READONLY_AGENT_ENABLED":"false"}):
            with self.assertRaises(PermissionError):
                asyncio.run(run_owner_readonly_browser_task(**kwargs))
        kwargs["approval_expires_at"]=time.time()-1
        with patch.dict("os.environ",{"PLENUM_OWNER_READONLY_AGENT_ENABLED":"true"}):
            with self.assertRaises(PermissionError):
                asyncio.run(run_owner_readonly_browser_task(**kwargs))


    def test_cloudflare_private_page_inference_fails_closed_without_token_or_free_plan(self):
        kwargs = dict(
            verified_owner={"private_owner_id":"founder-private-owner"},
            website_origin=ORIGIN,
            objective="Inspect the account-specific existing issue status",
            owner_proxy_url="http://127.0.0.1:24517",
            existing_chromium_executable=BINARY,
            store=FakeStore(state()),
            browser_factory=lambda **k: self.fail("Browser should not open"),
            tools_factory=lambda: self.fail("Browser tools should not open"),
            agent_factory=lambda **k: self.fail("Agent should not open"),
            independent_verify=lambda h,b: True,
            approval_callback=lambda *args: True,
            approval_expires_at=time.time()+200,
            external_inference_consent=True,
        )
        cfg={
            "PLENUM_OWNER_READONLY_AGENT_ENABLED":"true",
            "PLENUM_BROWSER_FREE_LOCAL":"",
            "PLENUM_CF_AI_ENABLED":"true",
            "PLENUM_CF_AI_FREE_PLAN_CONFIRMED":"true",
            "PLENUM_CF_AI_ACCOUNT_ID":"f"*32,
            "PLENUM_CF_AI_TOKEN":"TEST_ONLY_NO_NETWORK",
        }
        for field, value in (
            ("PLENUM_CF_AI_ENABLED","false"),
            ("PLENUM_CF_AI_FREE_PLAN_CONFIRMED","false"),
            ("PLENUM_CF_AI_ACCOUNT_ID","invalid"),
            ("PLENUM_CF_AI_TOKEN",""),
        ):
            with self.subTest(field=field), patch.dict(
                "os.environ",{**cfg,field:value},clear=True,
            ):
                with self.assertRaises(PermissionError):
                    asyncio.run(run_owner_readonly_browser_task(**kwargs))
        # A model factory (possibly agent/page-supplied) cannot substitute
        # a trusted Cloudflare model or its required owner privacy permission.
        with patch.dict("os.environ",cfg,clear=True):
            with self.assertRaises(PermissionError):
                asyncio.run(run_owner_readonly_browser_task(
                    **{**kwargs,"model_factory":lambda: object()}
                ))

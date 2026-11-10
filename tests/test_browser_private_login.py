"""Signed-owner live browser WebSocket and per-domain cookie scoping."""
import importlib.util
import os
import unittest
from unittest.mock import patch, AsyncMock

HAS_TEST=all(importlib.util.find_spec(x) is not None
             for x in ("playwright","fastapi","httpx","jwt","cryptography"))
if HAS_TEST:
    from fastapi.testclient import TestClient
    from starlette.websockets import WebSocketDisconnect
    from services.computer_browser.api import app
    from services.computer_browser import private_login
    client=TestClient(app)


@unittest.skipUnless(HAS_TEST,"Dedicated browser CI installs optional Playwright and IAP SDK")
class PrivateLoginTests(unittest.TestCase):
    def test_separate_website_cookie_isolation(self):
        state={"cookies":[
            {"domain":".kaggle.com","name":"site","value":"synthetic"},
            {"domain":"accounts.google.com","name":"google","value":"other"},
            {"domain":".example.org","name":"other","value":"unused"},
        ],"origins":[
            {"origin":"https://www.kaggle.com","localStorage":[]},
            {"origin":"https://accounts.google.com","localStorage":[]},
        ]}
        result=private_login.filter_site_storage(state,"https://www.kaggle.com")
        self.assertEqual([c["name"] for c in result["cookies"]],["site"])
        self.assertEqual([x["origin"] for x in result["origins"]],["https://www.kaggle.com"])

    def test_https_origin_isolation_covers_indexeddb_and_other_port(self):
        sample={"cookies":[
            {"domain":".kaggle.com","name":"site","value":"synthetic"},
            {"domain":"accounts.google.com","name":"idp","value":"not-owner-site"},
        ],"origins":[
            {"origin":"https://www.kaggle.com","localStorage":[],
             "indexedDB":[{"name":"synthetic-auth","stores":[]}]},
            {"origin":"http://www.kaggle.com","localStorage":[{"name":"insecure","value":"x"}]},
            {"origin":"https://www.kaggle.com:8443","localStorage":[{"name":"other-port","value":"x"}]},
            {"origin":"https://accounts.google.com","localStorage":[],
             "indexedDB":[{"name":"google-identity","stores":[]}]},
        ]}
        result=private_login.filter_site_storage(sample,"https://www.kaggle.com")
        self.assertEqual([c["name"] for c in result["cookies"]],["site"])
        self.assertEqual(len(result["origins"]),1)
        self.assertEqual(result["origins"][0]["origin"],"https://www.kaggle.com")
        self.assertEqual(result["origins"][0]["indexedDB"][0]["name"],"synthetic-auth")
        for invalid in ("http://www.kaggle.com","https://www.kaggle.com/path",
                        "https://www.kaggle.com?token=x","https://www.kaggle.com#x"):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                private_login.filter_site_storage(sample,invalid)

    def test_real_offline_chromium_indexeddb_capture_and_restore(self):
        """First-use interface acceptance only: no external OAuth/network."""
        from playwright.sync_api import sync_playwright

        def create_state(page, label):
            page.evaluate("""async (label) => {
                await new Promise((resolve, reject) => {
                    const req = indexedDB.open("synthetic-session", 1);
                    req.onupgradeneeded = () => req.result.createObjectStore("tokens");
                    req.onerror = () => reject(req.error);
                    req.onsuccess = () => {
                        const tx = req.result.transaction("tokens", "readwrite");
                        tx.objectStore("tokens").put(label, "session");
                        tx.oncomplete = () => { req.result.close(); resolve(); };
                        tx.onerror = () => reject(tx.error);
                    };
                });
            }""", label)

        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            try:
                ctx=browser.new_context(service_workers="block",accept_downloads=False)
                ctx.route("**/*",lambda route:route.fulfill(
                    status=200,content_type="text/html",body="<html><body>Offline only</body></html>"))
                page=ctx.new_page()
                page.goto("https://www.kaggle.com/synthetic")
                create_state(page,"SITE_SYNTHETIC")
                page.goto("https://accounts.google.com/synthetic")
                create_state(page,"IDP_MUST_NOT_SAVE")
                state=ctx.storage_state(indexed_db=True)
                selected=private_login.filter_site_storage(state,"https://www.kaggle.com")
                self.assertEqual([x["origin"] for x in selected["origins"]],
                                 ["https://www.kaggle.com"])
                self.assertIn("indexedDB",selected["origins"][0])
                restored=browser.new_context(storage_state=selected,
                                            service_workers="block",accept_downloads=False)
                try:
                    restored.route("**/*",lambda route:route.fulfill(
                        status=200,content_type="text/html",body="<html><body>Restored offline</body></html>"))
                    second=restored.new_page()
                    second.goto("https://www.kaggle.com/synthetic")
                    value=second.evaluate("""async () => {
                        return await new Promise((resolve, reject) => {
                            const req=indexedDB.open("synthetic-session");
                            req.onerror=()=>reject(req.error);
                            req.onsuccess=()=>{
                                const tx=req.result.transaction("tokens","readonly");
                                const get=tx.objectStore("tokens").get("session");
                                get.onerror=()=>reject(get.error);
                                get.onsuccess=()=>resolve(get.result);
                            };
                        });
                    }""")
                    self.assertEqual(value,"SITE_SYNTHETIC")
                finally:
                    restored.close()
                ctx.close()
            finally:
                browser.close()

    def test_session_writer_uses_owner_origin_and_generation_cas(self):
        from unittest.mock import MagicMock
        fake=MagicMock()
        data={"cookies":[{"name":"synthetic","value":"CI_ONLY"}],"origins":[]}
        origin="https://example.com"
        fake.current_generation.return_value=None
        with patch.object(private_login.BrowserProfileStore,"from_environment",
                          return_value=fake):
            private_login._persist_encrypted_site_profile(
                owner_id="test-owner",origin=origin,state=data)
        fake.save_new.assert_called_once_with(
            owner="test-owner",origin=origin,state=data,ttl_seconds=86400)
        fake.replace_if_current.assert_not_called()
        fake.reset_mock()
        fake.current_generation.return_value=42
        with patch.object(private_login.BrowserProfileStore,"from_environment",
                          return_value=fake):
            private_login._persist_encrypted_site_profile(
                owner_id="test-owner",origin=origin,state=data)
        fake.replace_if_current.assert_called_once_with(
            owner="test-owner",origin=origin,state=data,
            expected_generation=42,ttl_seconds=86400)

    def test_session_writer_propagates_storage_failure_without_disclosing_data(self):
        with patch.object(private_login.BrowserProfileStore,"from_environment",
                          side_effect=PermissionError("synthetic storage permission error")):
            with self.assertRaises(PermissionError):
                private_login._persist_encrypted_site_profile(
                    owner_id="test-owner",origin="https://example.com",
                    state={"cookies":[],"origins":[]})

    def test_browser_rejects_anonymous_websocket(self):
        with patch.dict(os.environ,{"BROWSER_PUBLIC_ORIGIN":"http://testserver",
                                   "COMPUTER_BROWSER_CI_ONLY":"true"}):
            with self.assertRaises(WebSocketDisconnect):
                with client.websocket_connect(
                    "/owner/live?site=https%3A%2F%2Fexample.com%2F&demo=1",
                    headers={"origin":"http://testserver"}):
                    pass

    def test_actual_chromium_websocket_typing_and_click_without_network(self):
        with patch.dict(os.environ,{"BROWSER_PUBLIC_ORIGIN":"http://testserver",
                                   "COMPUTER_BROWSER_CI_ONLY":"true",
                                   "BROWSER_ALLOWED_ORIGINS":"https://example.com"}):
            with patch.object(private_login,"verify_owner_token",
                              return_value={"owner_verified":True,
                                            "private_owner_id":"test-owner"}):
                with client.websocket_connect(
                    "/owner/live?site=https%3A%2F%2Fexample.com%2F&demo=1",
                    headers={"origin":"http://testserver",
                             "x-goog-iap-jwt-assertion":"STAGING-SIGNED-ONLY"}) as ws:
                    first=ws.receive_json()
                    self.assertEqual(first["type"],"status")
                    image=ws.receive_json()
                    self.assertEqual(image["type"],"frame")
                    self.assertGreater(len(image["image"]),100)
                    initial_health=ws.receive_json()
                    self.assertEqual(initial_health["type"],"page_health")
                    self.assertFalse(initial_health["blank"])
                    ws.send_json({"type":"click","x":140,"y":18})
                    selected=ws.receive_json()
                    self.assertEqual(selected,{"type":"ack","action":"click","field":"text"})
                    before=ws.receive_json()
                    self.assertEqual(before["type"],"frame")
                    self.assertEqual(ws.receive_json()["type"],"page_health")
                    ws.send_json({"type":"type","value":"Synthetic no-secret"})
                    self.assertEqual(ws.receive_json(),
                                     {"type":"ack","action":"type","ok":True})
                    after=ws.receive_json()
                    self.assertEqual(after["type"],"frame")
                    self.assertEqual(ws.receive_json()["type"],"page_health")
                    self.assertNotEqual(before["image"],after["image"])
                    ws.send_json({"type":"key","key":"Tab"})
                    self.assertEqual(ws.receive_json()["type"],"frame")
                    self.assertEqual(ws.receive_json()["type"],"page_health")
                    ws.send_json({"type":"type","value":"Must-not-be-entered"})
                    self.assertEqual(ws.receive_json(),
                                     {"type":"ack","action":"type","ok":False})
                    ws.send_json({"type":"save"})
                    response=ws.receive_json()
                    self.assertEqual(response["type"],"save_result")
                    self.assertFalse(response["ok"])
                    self.assertIn("Offline test",response["message"])
                    ws.send_json({"type":"close"})

    def test_mobile_touch_and_confirmation_ui_in_real_offline_chromium(self):
        """Verify rendered portal sends touch coordinates and preserves text
        until an actual server acknowledgment, without any network."""
        from playwright.sync_api import sync_playwright
        from urllib.parse import quote
        fixture=private_login.login_html("test-nonce")
        self.assertIn("Continue with Google",fixture)
        self.assertIn("LIVE browser picture",fixture)
        self.assertIn('id="url" type="url" placeholder=',fixture)
        self.assertNotIn('value="https://the-internet.herokuapp.com/login"',fixture)
        self.assertIn("Save this website login",fixture)
        injected="""(() => {
          class TestWebSocket {
            static OPEN=1;
            constructor(url){
              this.url=url;this.readyState=1;this.commands=[];
              window.__owner_ws=this;
              setTimeout(()=>{if(this.onopen)this.onopen();},0);
            }
            send(raw){this.commands.push(JSON.parse(raw));}
            close(){this.readyState=3;}
          }
          // Owner permission preflight is an existing authenticated HTTP
          // gate; the synthetic UI test injects its successful response.
          window.fetch=async()=>({ok:true,status:200});
          window.WebSocket=TestWebSocket;
        })();"""
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            try:
                page=browser.new_page(viewport={"width":1180,"height":850},
                                      is_mobile=True,has_touch=True)
                page.add_init_script(injected)
                page.route("**/*",lambda route: (
                    route.fulfill(status=200,content_type="text/html",body=fixture)
                    if route.request.url=="https://owner.test/owner/sign-in"
                    else route.abort()))
                page.goto("https://owner.test/owner/sign-in")
                page.locator("#open").click()
                page.wait_for_function("Boolean(window.__owner_ws && window.__owner_ws.onmessage)")
                page.evaluate("""() => window.__owner_ws.onmessage({
                  data: JSON.stringify({type:"frame",image:""})
                })""")
                page.wait_for_function("document.getElementById('status').textContent.includes('Browser stream connected')")
                page.evaluate("""() => window.__owner_ws.onmessage({
                  data: JSON.stringify({type:"page_health",blank:false,
                                        blocked_cross_origin:0})
                })""")
                self.assertIn("login is not yet verified",page.locator("#status").inner_text())
                box=page.locator("#display").bounding_box()
                self.assertIsNotNone(box)
                page.dispatch_event("#display","pointerup",{
                    "clientX":box["x"]+box["width"]*.15,
                    "clientY":box["y"]+box["height"]*.25,
                    "pointerType":"touch",
                })
                sent=page.evaluate("window.__owner_ws.commands")
                self.assertEqual(len(sent),1)
                self.assertEqual(sent[0]["type"],"click")
                self.assertEqual(sent[0]["x"],153)
                self.assertEqual(sent[0]["y"],180)
                page.evaluate("""() => window.__owner_ws.onmessage({
                  data: JSON.stringify({type:"ack",action:"click",field:"text"})
                })""")
                self.assertFalse(page.locator("#type").is_disabled())
                page.locator("#text").fill("synthetic-only-no-secret")
                page.locator("#type").click()
                self.assertEqual(page.locator("#text").input_value(),
                                 "synthetic-only-no-secret")
                self.assertEqual(page.evaluate("window.__owner_ws.commands.at(-1).type"),"type")
                page.evaluate("""() => window.__owner_ws.onmessage({
                  data: JSON.stringify({type:"ack",action:"type",ok:true})
                })""")
                self.assertEqual(page.locator("#text").input_value(),"")
                page.locator("#text").fill("must-preserve-on-failure")
                page.evaluate("""() => window.__owner_ws.onmessage({
                  data: JSON.stringify({type:"ack",action:"click",field:"password"})
                })""")
                page.locator("#type").click()
                page.evaluate("""() => window.__owner_ws.onmessage({
                  data: JSON.stringify({type:"ack",action:"type",ok:false})
                })""")
                self.assertEqual(page.locator("#text").input_value(),
                                 "must-preserve-on-failure")
                self.assertIn("NOT entered",page.locator("#field-status").inner_text())
                # Redacted rendering diagnostics must not leak a website URL,
                # cross-origin hostname or account secret. Blank is NOT ready.
                page.evaluate("""() => window.__owner_ws.onmessage({
                  data: JSON.stringify({type:"page_health",blank:true,
                                        blocked_cross_origin:3})
                })""")
                self.assertIn("appears blank",page.locator("#status").inner_text())
                self.assertIn("cross-origin resources",page.locator("#status").inner_text())
                self.assertTrue(page.locator("#save").is_disabled())
                page.evaluate("""() => window.__owner_ws.onmessage({
                  data: JSON.stringify({type:"page_health",blank:false,
                                        blocked_cross_origin:0})
                })""")
                self.assertFalse(page.locator("#save").is_disabled())
                # Save controls remain usable once the page is not blank;
                # no secret is persisted by this synthetic browser.
                page.locator("#save").click()
                self.assertIn("Saving encrypted website session",
                              page.locator("#status").inner_text())
                self.assertTrue(page.locator("#save").is_disabled())
                page.evaluate("""() => window.__owner_ws.onmessage({
                  data: JSON.stringify({
                    type:"save_result",ok:false,
                    message:"Encrypted session storage unavailable. Browser remains open."
                  })
                })""")
                self.assertFalse(page.locator("#save").is_disabled())
                self.assertIn("Browser remains open",page.locator("#status").inner_text())
                self.assertIn("not assume this login is stored",
                              page.locator("#field-status").inner_text())
                self.assertEqual(page.locator("#text").input_value(),
                                 "must-preserve-on-failure")
                # Model a mobile-network or Cloud Run WebSocket disconnect.
                # A dead screenshot must not look interactive, and the
                # diagnostics should report duration/code without secrets.
                page.evaluate("""() => {
                  window.__owner_ws.readyState=3;
                  window.__owner_ws.onclose({code:1006});
                }""")
                self.assertTrue(page.locator("#enter").is_disabled())
                self.assertTrue(page.locator("#type").is_disabled())
                self.assertTrue(page.locator("#save").is_disabled())
                self.assertIn("1006",page.locator("#status").inner_text())
                self.assertIn("previous browser image has been cleared",
                              page.locator("#field-status").inner_text())
                self.assertEqual(page.locator("#text").input_value(),
                                 "must-preserve-on-failure")
                commands_before=page.evaluate("window.__owner_ws.commands.length")
                page.locator("#display").click(force=True)
                self.assertEqual(page.evaluate("window.__owner_ws.commands.length"),
                                 commands_before)
                self.assertIn("disconnected",
                              page.locator("#status").inner_text().lower())
                self.assertIn("previous browser image has been cleared",
                              page.locator("#field-status").inner_text().lower())
            finally:
                browser.close()

    def test_auth0_release_bounded_websocket_timeout_and_no_public_bypass(self):
        from pathlib import Path
        wf=(Path(__file__).resolve().parents[1]/
            ".github/workflows/browser-auth0-owner-websocket-release.yml").read_text()
        self.assertIn("--timeout=900s",wf)
        self.assertIn('int(spec.get("timeoutSeconds",0))==900',wf)
        self.assertIn("github.event.issue.user.login == 'chadkhalil21-svg'",wf)
        self.assertIn("environment: computer-browser-production",wf)
        self.assertNotIn("--allow-unauthenticated",wf)

    def test_config_only_timeout_restoration_remains_exact_owner_and_immutable_image(self):
        from pathlib import Path
        wf=(Path(__file__).resolve().parents[1]/
            ".github/workflows/browser-auth0-restore-original-timeout.yml").read_text()
        self.assertIn("github.event.issue.user.login == 'chadkhalil21-svg'",wf)
        self.assertIn("github.event.issue.body == 'RESTORE_AUTH0_ORIGINAL_TIMEOUT:2026-11-08'",wf)
        self.assertIn("environment: computer-browser-production",wf)
        self.assertIn("--timeout=900s",wf)
        self.assertIn('int(new["timeoutSeconds"])==900',wf)
        self.assertIn('old["containers"][0]["image"]==new["containers"][0]["image"]',wf)
        self.assertIn('old["containers"][0]["env"]==new["containers"][0]["env"]',wf)
        self.assertIn("Do not print URLs",wf)
        self.assertNotIn("gcloud builds submit",wf)
        self.assertNotIn("--allow-unauthenticated",wf)

    def test_ci_demo_does_not_enable_without_flag(self):
        with patch.dict(os.environ,{"BROWSER_PUBLIC_ORIGIN":"https://example.com",
                                   "COMPUTER_BROWSER_CI_ONLY":"false"}):
            with patch.object(private_login,"verify_owner_token",
                              return_value={"private_owner_id":"test-owner"}):
                with self.assertRaises(WebSocketDisconnect):
                    with client.websocket_connect(
                        "/owner/live?site=https%3A%2F%2Fexample.com%2F&demo=1",
                        headers={"origin":"https://example.com"}):
                        pass

@unittest.skipUnless(HAS_TEST,"Browser owner diagnostic needs async gateway deps")
class OwnerBlankPageDiagnostics(unittest.IsolatedAsyncioTestCase):
    def test_owner_stream_repaints_after_delayed_javascript_first_paint(self):
        import inspect
        code=inspect.getsource(private_login.mount_private_login)
        self.assertIn("refresh_task=asyncio.create_task(refresh_picture())",code)
        self.assertIn("await asyncio.sleep(3)",code)
        self.assertIn("for tick in range(200):",code)
        self.assertIn("frame_lock=asyncio.Lock()",code)
        self.assertIn("await show_picture()",code)
        self.assertIn("refresh_task.cancel()",code)
        self.assertIn("owner_live_origin,",code)

    async def test_health_has_only_aggregates_without_page_content_or_urls(self):
        page=unittest.mock.Mock()
        page.evaluate=AsyncMock(return_value=False)
        ws=unittest.mock.Mock()
        ws.send_json=AsyncMock()
        await private_login._page_render_health(ws,page,{"cross_origin":6})
        report=ws.send_json.await_args.args[0]
        self.assertEqual(report,{"type":"page_health",
                                 "blank":True,"blocked_cross_origin":6})
        self.assertNotIn("https",str(report))
        self.assertNotIn("cookie",str(report))
        self.assertNotIn("account",str(report))

        page.evaluate=AsyncMock(return_value=True)
        await private_login._page_render_health(ws,page,{"cross_origin":200})
        self.assertEqual(ws.send_json.await_args.args[0],
                         {"type":"page_health",
                          "blank":False,"blocked_cross_origin":99})

    async def test_unavailable_js_does_not_claim_blank(self):
        page=unittest.mock.Mock()
        page.evaluate=AsyncMock(side_effect=RuntimeError("secret example HTML"))
        ws=unittest.mock.Mock()
        ws.send_json=AsyncMock()
        await private_login._page_render_health(ws,page,{"cross_origin":0})
        self.assertEqual(ws.send_json.await_args.args[0],
                         {"type":"page_health","blank":False,
                          "render_unverified":True,
                          "blocked_cross_origin":0})
        self.assertNotIn("secret",str(ws.send_json.await_args.args[0]))



@unittest.skipUnless(HAS_TEST, "Owner-only Apple scope needs original gateway")
class AppleAuthenticationOptInPolicy(unittest.TestCase):
    def test_apple_dependencies_require_exact_site_private_owner_and_opt_in(self):
        primary = "https://appstoreconnect.apple.com"
        base = private_login._approved_live_origins(
            primary, dynamic=True, apple_auth="0")
        self.assertEqual(base, frozenset({primary}))
        approved = private_login._approved_live_origins(
            primary, dynamic=True, apple_auth="1")
        self.assertEqual(len(approved), 5)
        self.assertIn("https://idmsa.apple.com", approved)
        self.assertIn("https://appleid.cdn-apple.com", approved)
        self.assertIn("https://account.apple.com", approved)
        self.assertIn("https://gsa.apple.com", approved)
        for site, dynamic, flag in (
            ("https://unrelated.example", True, "1"),
            (primary, False, "1"),
            (primary, True, "true"),
            (primary, True, "2"),
        ):
            with self.subTest(site=site, dynamic=dynamic, flag=flag):
                with self.assertRaises(PermissionError):
                    private_login._approved_live_origins(
                        site, dynamic=dynamic, apple_auth=flag)
        self.assertEqual(private_login._approved_live_origins(
            "https://unrelated.example", dynamic=True, apple_auth="0"),
            frozenset({"https://unrelated.example"}))

    def test_owner_canvas_requires_explicit_session_only_checkbox(self):
        page = private_login.login_html("synthetic-nonce")
        self.assertIn('id="apple-auth" type="checkbox"', page)
        self.assertNotIn('id="apple-auth" type="checkbox" checked', page)
        self.assertIn('"&apple_auth="+appleAuth', page)
        self.assertIn('u.searchParams.set("apple_auth",appleAuth)', page)
        code = __import__("inspect").getsource(private_login.mount_private_login)
        self.assertIn("approved_origins=_approved_live_origins(", code)
        self.assertIn("additional_origins=approved_origins-{origin}", code)
        self.assertIn("safe_url(req.url,origins=approved_origins)", code)
        self.assertIn("safe_url(page.url,origins={origin})", code)


if __name__=="__main__":
    unittest.main()

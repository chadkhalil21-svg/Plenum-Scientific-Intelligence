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
    def test_github_quick_open_does_not_require_manual_url_entry(self):
        html = private_login.login_html("ci-nonce", "ci-register-token")
        self.assertIn('document.getElementById("url").value="https://github.com";', html)
        self.assertIn("https://github.githubassets.com,https://avatars.githubusercontent.com", html)

    def test_owner_navigation_is_explicit_bounded_and_origin_scoped(self):
        # Tests the ORIGINAL owner-only Chromium handler without an actual
        # login, live website, secret, new browser or external account call.
        import asyncio
        from types import SimpleNamespace
        from unittest.mock import AsyncMock
        page=SimpleNamespace(
            url="https://github.com/settings",
            mouse=SimpleNamespace(wheel=AsyncMock()),
            go_back=AsyncMock(),
            go_forward=AsyncMock(),
        )
        async def verify():
            await private_login._owner_safe_navigation(
                page,kind="scroll",direction="down",
                approved_origins={"https://github.com"})
            page.mouse.wheel.assert_awaited_once_with(0,640)
            await private_login._owner_safe_navigation(
                page,kind="scroll",direction="up",
                approved_origins={"https://github.com"})
            page.mouse.wheel.assert_awaited_with(0,-640)
            await private_login._owner_safe_navigation(
                page,kind="back",
                approved_origins={"https://github.com"})
            page.go_back.assert_awaited_once()
            await private_login._owner_safe_navigation(
                page,kind="forward",
                approved_origins={"https://github.com"})
            page.go_forward.assert_awaited_once()
            before=page.mouse.wheel.await_count
            for bad in ("sideways","../../private",""):
                with self.assertRaises(PermissionError):
                    await private_login._owner_safe_navigation(
                        page,kind="scroll",direction=bad,
                        approved_origins={"https://github.com"})
            self.assertEqual(page.mouse.wheel.await_count,before)
            page.url="https://untrusted.example/"
            with self.assertRaises(PermissionError):
                await private_login._owner_safe_navigation(
                    page,kind="back",approved_origins={"https://github.com"})
            self.assertEqual(page.go_back.await_count,1)
            page.url="https://github.com/"
            async def redirect_off_site(**kwargs):
                page.url="https://untrusted.example/"
            page.go_back.side_effect=redirect_off_site
            with self.assertRaises(PermissionError):
                await private_login._owner_safe_navigation(
                    page,kind="back",approved_origins={"https://github.com"})
        asyncio.run(verify())

    def test_owner_chromium_controls_only_use_websocket_with_session(self):
        html=private_login.login_html("ci-nonce","ci-register-token")
        for label in ("back","forward","scroll-up","scroll-down"):
            self.assertIn('id="'+label+'" disabled',html)
        self.assertIn('send({type:"scroll",direction:"down"})',html)
        self.assertIn('send({type:"back"})',html)
        self.assertNotIn('new EventSource(',html)

    def test_trusted_owner_saved_login_reused_without_cross_site_secrets(self):
        from unittest.mock import MagicMock
        site="https://github.com"
        private_id="owner-fixture"
        vault=MagicMock()
        vault.status.return_value={"profile_exists":False}
        with patch.object(private_login.BrowserProfileStore,"from_environment",
                          return_value=vault):
            self.assertIsNone(private_login._load_existing_owner_state(
                owner_id=private_id,origin=site))
        vault.load_for_trusted_worker.assert_not_called()
        vault.status.return_value={"profile_exists":True}
        vault.load_for_trusted_worker.return_value=({
            "cookies":[
                {"domain":".github.com","name":"owner-cookie","value":"confidential"},
                {"domain":"accounts.example.org","name":"other","value":"deny"},
            ],
            "origins":[
                {"origin":site,"localStorage":[{"name":"auth","value":"private"}]},
                {"origin":"https://accounts.example.org","localStorage":[]},
            ],
        },42)
        with patch.object(private_login.BrowserProfileStore,"from_environment",
                          return_value=vault):
            state=private_login._load_existing_owner_state(
                owner_id=private_id,origin=site)
        self.assertEqual([x["name"] for x in state["cookies"]],["owner-cookie"])
        self.assertEqual([x["origin"] for x in state["origins"]],[site])
        vault.status.assert_called_with(owner=private_id,origin=site)
        vault.load_for_trusted_worker.assert_called_once_with(
            owner=private_id,origin=site)

    def test_corrupt_saved_site_state_fails_closed_not_credentials_disclosed(self):
        from unittest.mock import MagicMock
        vault=MagicMock()
        vault.status.return_value={"profile_exists":True}
        vault.load_for_trusted_worker.return_value=({"cookies":[],"origins":[]},4)
        with patch.object(private_login.BrowserProfileStore,"from_environment",
                          return_value=vault):
            with self.assertRaises(PermissionError):
                private_login._load_existing_owner_state(
                    owner_id="owner",origin="https://example.com")

    def test_click_to_approve_github_assets_and_resume_are_owner_only(self):
        html=private_login.login_html("fixture-nonce")
        self.assertIn('id="github-quick-open"',html)
        self.assertIn('site.origin!=="https://github.com"',html)
        self.assertIn('"https://github.githubassets.com,https://avatars.githubusercontent.com"',html)
        self.assertIn('document.getElementById("approve-resources").checked=true',html)
        self.assertIn('document.getElementById("open").click()',html)
        self.assertIn('id="resume-saved" type="checkbox" checked',html)
        self.assertIn('u.searchParams.set("resume_saved",resumeSaved)',html)
        import inspect
        route=inspect.getsource(private_login.mount_private_login)
        self.assertIn('resume_saved not in ("0", "1")',route)
        self.assertIn('owner_id=owner["private_owner_id"], origin=origin',route)
        self.assertIn('**({"storage_state": saved_state} if saved_state is not None else {})',route)
        self.assertIn('Website login validity is not yet verified.',route)

    def test_registered_site_may_approve_exact_static_resource_origins(self):
        main="https://github.com"
        resource="https://github.githubassets.com"
        avatar="https://avatars.githubusercontent.com"
        denied=private_login._approved_live_origins(
            main,dynamic=True,apple_auth="0")
        self.assertEqual(denied,frozenset({main}))
        allowed=private_login._approved_live_origins(
            main,dynamic=True,apple_auth="0",
            resource_origins=resource+","+avatar,
            approve_resources="1")
        self.assertEqual(allowed,frozenset({main,resource,avatar}))
        allow=private_login._allow_live_request
        self.assertTrue(allow(
            url=main+"/login",method="POST",resource_type="document",
            primary=main,approved=allowed))
        self.assertTrue(allow(
            url=resource+"/assets/app.js",method="GET",resource_type="script",
            primary=main,approved=allowed))
        self.assertTrue(allow(
            url=resource+"/assets/style.css",method="GET",
            resource_type="stylesheet",primary=main,approved=allowed))
        self.assertTrue(allow(
            url=avatar+"/u/1",method="GET",resource_type="image",
            primary=main,approved=allowed))
        for url,method,kind in (
            (resource+"/login","GET","document"),
            (resource+"/submit","POST","script"),
            (resource+"/f","GET","fetch"),
            ("https://other.example.org/a.js","GET","script"),
            ("http://github.githubassets.com/a.js","GET","script"),
            ("https://localhost/a.js","GET","script"),
        ):
            with self.subTest(url=url,method=method,kind=kind):
                self.assertFalse(allow(
                    url=url,method=method,resource_type=kind,
                    primary=main,approved=allowed))
        self.assertTrue(allow(
            url="https://idmsa.apple.com/auth",
            method="POST",resource_type="document",
            primary="https://appstoreconnect.apple.com",
            approved=frozenset({
                "https://appstoreconnect.apple.com","https://idmsa.apple.com"}),
            allow_apple_auth=True))

    def test_unapproved_extra_resources_rejected_before_connect(self):
        site="https://github.com"
        extra="https://github.githubassets.com"
        for resource,approved,dynamic in (
            (extra,"0",True), (extra,"1",False),
            (extra+"/assets","1",True),
            ("http://github.githubassets.com","1",True),
            ("https://127.0.0.1","1",True),
            (extra+","+extra,"1",True),
            (site,"1",True),
            ("https://a.example,https://b.example,https://c.example,"
             "https://d.example,https://e.example,https://f.example","1",True),
        ):
            with self.subTest(resource=resource),self.assertRaises(PermissionError):
                private_login._approved_live_origins(
                    site,dynamic=dynamic,apple_auth="0",
                    resource_origins=resource,approve_resources=approved)
        for apple in ("0","1"):
            with self.subTest(apple=apple), self.assertRaises(PermissionError):
                private_login._approved_live_origins(
                    "https://appstoreconnect.apple.com",dynamic=True,
                    apple_auth=apple,resource_origins=extra,
                    approve_resources="0" if apple=="0" else "1")
        with self.assertRaises(PermissionError):
            private_login._approved_live_origins(
                site,dynamic=True,apple_auth="0",
                resource_origins="",approve_resources="1")
        self.assertIn('id="resource-origins"',private_login.login_html("safe-nonce"))
        self.assertIn('id="approve-resources"',private_login.login_html("safe-nonce"))
        self.assertIn('u.searchParams.set("resource_origins",resources)',
                      private_login.login_html("safe-nonce"))

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


    def test_cloudflare_challenge_returns_boolean_for_exact_host_only(self):
        from unittest.mock import AsyncMock, MagicMock
        import asyncio
        page=MagicMock()
        page.url="https://dash.cloudflare.com/"
        page.evaluate=AsyncMock(return_value=True)
        self.assertTrue(asyncio.run(private_login._unsupported_cloudflare_challenge(page)))
        self.assertIn("incompatible browser extension",page.evaluate.call_args.args[0])
        page.url="https://github.com/"
        page.evaluate.reset_mock()
        self.assertFalse(asyncio.run(private_login._unsupported_cloudflare_challenge(page)))
        page.evaluate.assert_not_called()
        page.url="https://dash.cloudflare.com/"
        page.evaluate=AsyncMock(return_value=False)
        self.assertFalse(asyncio.run(private_login._unsupported_cloudflare_challenge(page)))

    def test_known_cloudflare_challenge_disables_save_without_leaking_page(self):
        html=private_login.login_html("test-nonce")
        self.assertIn("m.unsupported_cloudflare_challenge===true",html)
        self.assertIn("!ready||saveInFlight||pageBlank||challengeBlocked",html)
        self.assertIn("Cloudflare security verification is incompatible",html)
        self.assertIn("if(saveInFlight||!ready||pageBlank||challengeBlocked)return;",html)

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
                page.evaluate("""() => window.__owner_ws.onmessage({
                  data: JSON.stringify({type:"status",code:"picture_timeout",
                                        message:"Picture timed out"})
                })""")
                self.assertTrue(page.locator("#enter").is_disabled())
                self.assertIn("fields remain open",page.locator("#field-status").inner_text())
                page.evaluate("""() => window.__owner_ws.onmessage({
                  data: JSON.stringify({type:"frame",image:""})
                })""")
                self.assertFalse(page.locator("#enter").is_disabled())
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
                                 "blank":True,"blocked_cross_origin":6,
                                 "unsupported_cloudflare_challenge":False})
        self.assertNotIn("https",str(report))
        self.assertNotIn("cookie",str(report))
        self.assertNotIn("account",str(report))

        page.evaluate=AsyncMock(return_value=True)
        await private_login._page_render_health(ws,page,{"cross_origin":200})
        self.assertEqual(ws.send_json.await_args.args[0],
                         {"type":"page_health","blank":False,
                          "blocked_cross_origin":99,
                          "unsupported_cloudflare_challenge":False})

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
        self.assertIn("_allow_live_request(", code)
        self.assertIn('allow_apple_auth=apple_auth=="1"', code)
        self.assertIn("primary=origin,approved=approved_origins", code)
        self.assertIn("safe_url(page.url,origins={origin})", code)


@unittest.skipUnless(HAS_TEST,"Owner stream recovery needs browser gateway dependencies")
class OwnerStreamTimeoutRecovery(unittest.IsolatedAsyncioTestCase):
    async def test_picture_timeout_reports_recoverable_without_leaking_exception(self):
        from types import SimpleNamespace
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError
        page=SimpleNamespace(screenshot=AsyncMock(side_effect=[
            PlaywrightTimeoutError("PRIVATE synthetic content must never escape"),
            b"synthetic-jpeg"]))
        ws=SimpleNamespace(send_json=AsyncMock())
        self.assertFalse(await private_login._frame(ws,page))
        report=ws.send_json.await_args.args[0]
        self.assertEqual(report["code"],"picture_timeout")
        self.assertNotIn("failure",report)
        self.assertNotIn("PRIVATE",str(report))
        self.assertTrue(await private_login._frame(ws,page))
        self.assertEqual(ws.send_json.await_args.args[0]["type"],"frame")

    async def test_action_timeout_keeps_browser_for_next_command_without_replay(self):
        from types import SimpleNamespace
        from fastapi import FastAPI
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError
        page=SimpleNamespace(
            url="https://example.com/",
            set_content=AsyncMock(),screenshot=AsyncMock(return_value=b"jpeg"),
            evaluate=AsyncMock(return_value=True),
            mouse=SimpleNamespace(click=AsyncMock(side_effect=PlaywrightTimeoutError("PRIVATE"))),
            keyboard=SimpleNamespace(press=AsyncMock()))
        context=SimpleNamespace(route=AsyncMock(),new_page=AsyncMock(return_value=page))
        browser=SimpleNamespace(new_context=AsyncMock(return_value=context),close=AsyncMock())
        manager=AsyncMock()
        manager.__aenter__.return_value=SimpleNamespace(
            chromium=SimpleNamespace(launch=AsyncMock(return_value=browser)))
        ws=SimpleNamespace(scope={},headers={"origin":"http://owner.test"},
            accept=AsyncMock(),close=AsyncMock(),send_json=AsyncMock(),
            receive_json=AsyncMock(side_effect=[
                {"type":"click","x":20,"y":20},
                {"type":"key","key":"Tab"},{"type":"close"}]))
        original=FastAPI()
        private_login.mount_private_login(original)
        endpoint=next(r.endpoint for r in original.routes if r.path=="/owner/live")
        with patch.dict(os.environ,{"BROWSER_PUBLIC_ORIGIN":"http://owner.test",
                                    "COMPUTER_BROWSER_CI_ONLY":"true"}), \
             patch.object(private_login,"auth0_active",return_value=False), \
             patch.object(private_login,"verify_owner_token",return_value={"private_owner_id":"fixture"}), \
             patch.object(private_login,"owner_live_origin",return_value=("https://example.com",False)), \
             patch("playwright.async_api.async_playwright",return_value=manager):
            await endpoint(ws,site="https://example.com/",demo="1",apple_auth="0",
                           resource_origins="",approve_resources="0",resume_saved="0")
        reports=[call.args[0] for call in ws.send_json.await_args_list]
        self.assertTrue(any(r.get("code")=="action_timeout" for r in reports))
        self.assertFalse(any(r.get("failure") for r in reports))
        self.assertNotIn("PRIVATE",str(reports))
        self.assertEqual(page.mouse.click.await_count,1)
        page.keyboard.press.assert_awaited_once_with("Tab")
        self.assertEqual(ws.receive_json.await_count,3)


if __name__=="__main__":
    unittest.main()

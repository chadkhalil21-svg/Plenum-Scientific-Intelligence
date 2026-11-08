"""Signed-owner live browser WebSocket and per-domain cookie scoping."""
import importlib.util
import os
import unittest
from unittest.mock import patch

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
                    ws.send_json({"type":"click","x":140,"y":18})
                    selected=ws.receive_json()
                    self.assertEqual(selected,{"type":"ack","action":"click","field":"text"})
                    before=ws.receive_json()
                    self.assertEqual(before["type"],"frame")
                    ws.send_json({"type":"type","value":"Synthetic no-secret"})
                    self.assertEqual(ws.receive_json(),
                                     {"type":"ack","action":"type","ok":True})
                    after=ws.receive_json()
                    self.assertEqual(after["type"],"frame")
                    self.assertNotEqual(before["image"],after["image"])
                    ws.send_json({"type":"key","key":"Tab"})
                    self.assertEqual(ws.receive_json()["type"],"frame")
                    ws.send_json({"type":"type","value":"Must-not-be-entered"})
                    self.assertEqual(ws.receive_json(),
                                     {"type":"ack","action":"type","ok":False})
                    ws.send_json({"type":"save"})
                    response=ws.receive_json()
                    self.assertIn("Offline test",response["message"])
                    ws.send_json({"type":"close"})

    def test_mobile_touch_and_confirmation_ui_in_real_offline_chromium(self):
        """Verify rendered portal sends touch coordinates and preserves text
        until an actual server acknowledgment, without any network."""
        from playwright.sync_api import sync_playwright
        from urllib.parse import quote
        fixture=private_login.login_html("test-nonce")
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
                page.wait_for_function("document.getElementById('status').textContent.includes('Browser ready')")
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
                self.assertIn("not connected",
                              page.locator("#field-status").inner_text().lower())
            finally:
                browser.close()

    def test_auth0_release_bounded_websocket_timeout_and_no_public_bypass(self):
        from pathlib import Path
        wf=(Path(__file__).resolve().parents[1]/
            ".github/workflows/browser-auth0-owner-websocket-release.yml").read_text()
        self.assertIn("--timeout=600s",wf)
        self.assertIn('int(spec.get("timeoutSeconds",0))==600',wf)
        self.assertIn("github.event.issue.user.login == 'chadkhalil21-svg'",wf)
        self.assertIn("environment: computer-browser-production",wf)
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

if __name__=="__main__":
    unittest.main()

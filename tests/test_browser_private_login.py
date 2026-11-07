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
                    self.assertEqual(ws.receive_json()["type"],"frame")
                    ws.send_json({"type":"type","value":"Synthetic no-secret"})
                    self.assertEqual(ws.receive_json()["type"],"frame")
                    ws.send_json({"type":"key","key":"Tab"})
                    self.assertEqual(ws.receive_json()["type"],"frame")
                    ws.send_json({"type":"save"})
                    response=ws.receive_json()
                    self.assertIn("Offline test",response["message"])
                    ws.send_json({"type":"close"})

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

"""Owner console uses real ES256 JWT claims, not forged unsigned identity headers."""
import importlib.util
import os
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

AVAILABLE=all(importlib.util.find_spec(x) is not None for x in ("jwt","fastapi","httpx","cryptography"))
if AVAILABLE:
    import jwt
    from cryptography.hazmat.primitives.asymmetric import ec
    from fastapi.testclient import TestClient
    from services.computer_browser.api import app
    from services.computer_browser import iap_identity
    client=TestClient(app)

AUDIENCE="/projects/123456789/locations/us-east1/services/plenum-computer-browser"
ENV={"COMPUTER_IAP_AUDIENCE":AUDIENCE,"COMPUTER_OWNER_EMAIL":"browser-owner@example.com"}


@unittest.skipUnless(AVAILABLE,"Browser-only CI includes JWT, FastAPI and cryptography")
class OwnerConsoleTests(unittest.TestCase):
    def setUp(self):
        self.private=ec.generate_private_key(ec.SECP256R1())
        self.public=self.private.public_key()
        self.env=patch.dict(os.environ,ENV)
        self.env.start()
        self.key=patch.object(iap_identity,"_signing_key",return_value=self.public)
        self.key.start()

    def tearDown(self):
        self.key.stop()
        self.env.stop()

    def token(self,**changes):
        now=int(time.time())
        payload={"aud":AUDIENCE,"iss":"https://cloud.google.com/iap",
                 "iat":now,"exp":now+550,"sub":"identity-987654321",
                 "email":"browser-owner@example.com"}
        payload.update(changes)
        return jwt.encode(payload,self.private,algorithm="ES256",headers={"kid":"synthetic"})

    def test_missing_jwt_and_forged_plaintext_header_are_rejected(self):
        x=client.get("/owner",headers={"x-goog-authenticated-user-email":"accounts.google.com:browser-owner@example.com"})
        self.assertEqual(x.status_code,401)
        self.assertEqual(client.get("/owner").status_code,401)

    def test_real_signed_owner_token_opens_private_console(self):
        r=client.get("/owner",headers={"x-goog-iap-jwt-assertion":self.token()})
        self.assertEqual(r.status_code,200)
        self.assertIn("Connected as verified owner",r.text)
        self.assertIn("no-store",r.headers.get("cache-control",""))
        self.assertIn("frame-ancestors 'none'",r.headers.get("content-security-policy",""))
        self.assertNotIn("browser-owner@example.com",r.text)

    def test_wrong_owner_and_bad_signature_are_denied(self):
        for jwt_token in [self.token(email="intruder@example.com"),
                          self.token(aud="/projects/123/locations/us-east1/services/other"),
                          self.token(iss="https://other.example.com"),
                          self.token(exp=int(time.time())-90),
                          self.token(iat=int(time.time())-1100,exp=int(time.time())+400)]:
            with self.subTest(jwt_token=jwt_token[:12]):
                self.assertEqual(client.get("/owner",headers={"x-goog-iap-jwt-assertion":jwt_token}).status_code,401)
        other=ec.generate_private_key(ec.SECP256R1())
        forged=jwt.encode({"aud":AUDIENCE,"iss":"https://cloud.google.com/iap",
                           "iat":int(time.time()),"exp":int(time.time())+500,
                           "sub":"attacker-12345","email":"browser-owner@example.com"},
                          other,algorithm="ES256")
        self.assertEqual(client.get("/owner",headers={"x-goog-iap-jwt-assertion":forged}).status_code,401)

    def test_no_owner_environment_fails_closed(self):
        with patch.dict(os.environ,{"COMPUTER_OWNER_EMAIL":"","COMPUTER_IAP_AUDIENCE":""}):
            self.assertEqual(client.get("/owner",headers={"x-goog-iap-jwt-assertion":self.token()}).status_code,401)

    def test_preview_requires_identity_and_blocks_foreign_websites(self):
        u="/owner/public-preview?url=https://example.com/"
        self.assertEqual(client.get(u).status_code,401)
        r=client.get("/owner/public-preview?url=https://evil.example.com/",
                     headers={"x-goog-iap-jwt-assertion":self.token()})
        self.assertEqual(r.status_code,403)

    def test_untrusted_web_content_is_html_escaped(self):
        async def mock_public_read(url):
            return {"title_untrusted":"<script>alert(1)</script>",
                    "body_excerpt_untrusted":"<img src=x onerror=alert(1)>",
                    "final_url":url}
        with patch("services.computer_browser.owner_console.read_public",new=mock_public_read):
            r=client.get("/owner/public-preview?url=https://example.com/",
                         headers={"x-goog-iap-jwt-assertion":self.token()})
        self.assertEqual(r.status_code,200)
        self.assertIn("&lt;script&gt;",r.text)
        self.assertNotIn("<script>",r.text)
        self.assertNotIn("<img",r.text)

if __name__=="__main__":
    unittest.main()

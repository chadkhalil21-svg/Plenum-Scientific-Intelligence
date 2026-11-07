"""Session cryptography and actual Chromium synthetic account isolation."""
import asyncio
import importlib.util
import unittest
from unittest.mock import patch

ENABLED=bool(importlib.util.find_spec("cryptography") and
             importlib.util.find_spec("playwright"))

@unittest.skipUnless(ENABLED, "Dedicated browser CI installs optional cryptography and Playwright")
class SessionContractTests(unittest.TestCase):
    def setUp(self):
        from cryptography.fernet import Fernet
        from services.computer_browser.session_crypto import PrivateSessionVault
        self.vault=PrivateSessionVault(Fernet.generate_key())
        self.state={"cookies":[{"name":"synthetic","value":"example"}],"origins":[]}

    def test_encrypted_state_is_owner_and_origin_bound(self):
        token=self.vault.encrypt(self.state,"computer","https://example.com",ttl_seconds=60,now=1000)
        self.assertNotIn(b"example",token)
        self.assertEqual(self.vault.decrypt(token,"computer","https://example.com",now=1002),self.state)
        for owner,site in [("prometheus","https://example.com"),("computer","https://other.org")]:
            with self.assertRaises(PermissionError):
                self.vault.decrypt(token,owner,site,now=1002)
        with self.assertRaises(PermissionError):
            self.vault.decrypt(token,"computer","https://example.com",now=1060)
        with self.assertRaises(PermissionError):
            self.vault.decrypt(token+b"x","computer","https://example.com",now=1002)

    def test_strict_state_format_and_envelope_lifetime(self):
        with self.assertRaises(ValueError):
            self.vault.encrypt({}, "computer","https://example.com")
        with self.assertRaises(ValueError):
            self.vault.encrypt(self.state,"computer","http://example.com")
        with self.assertRaises(ValueError):
            self.vault.encrypt(self.state,"computer","https://example.com",ttl_seconds=999999)
        with self.assertRaises(ValueError):
            self.vault.encrypt(self.state,"account/other","https://example.com")

    def test_real_chromium_encrypt_and_restore_synthetic_cookie(self):
        from services.computer_browser.session_crypto import local_encrypted_context_roundtrip
        result=asyncio.run(local_encrypted_context_roundtrip())
        self.assertTrue(result["actual_chromium_state_restored"])
        self.assertFalse(result["external_website_login_verified"])
        self.assertFalse(result["AGI_demonstrated"])

if __name__=="__main__":unittest.main()

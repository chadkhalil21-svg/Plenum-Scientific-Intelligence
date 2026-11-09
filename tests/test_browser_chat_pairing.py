"""No-network GCS CAS/cryptography contract for one-time owner chat approval."""
import importlib.util
import os
import time
import unittest
from unittest.mock import patch

from services.computer_browser import owner_chat_pairing as pairing

OWNER="b"*64
SAFE={
    "K_SERVICE":"plenum-browser-owner-auth0",
    pairing.FLAG:"true",
    "AUTH0_OWNER_PUBLIC_ORIGIN":
        "https://plenum-browser-owner-auth0-2lak3vl73q-ue.a.run.app",
    "BROWSER_PROFILE_BUCKET":"fake-private-bucket",
    "BROWSER_ALLOWED_ORIGINS":
        "https://example.com,https://the-internet.herokuapp.com",
    "BROWSER_SESSION_KEY":"",
    "COMPUTER_BROWSER_TOKEN":"test-only-bridge-token"*3,
}


class AtomicBlob:
    def __init__(self):
        self.generation=None
        self.data=None
        self._generation_counter=0
    def exists(self):
        return self.data is not None
    def reload(self):
        if self.data is None:
            raise FileNotFoundError("No consent")
    def upload_from_string(self,data,content_type,if_generation_match):
        if (if_generation_match!=0 and if_generation_match!=self.generation) or (
                if_generation_match==0 and self.data is not None):
            raise RuntimeError("CAS mismatch")
        self._generation_counter+=1
        self.generation=self._generation_counter
        self.data=data
    def download_as_bytes(self,if_generation_match):
        if self.data is None or self.generation!=if_generation_match:
            raise RuntimeError("CAS stale")
        return self.data
    def delete(self,if_generation_match):
        if self.generation!=if_generation_match or self.data is None:
            raise RuntimeError("CAS stale delete")
        self.data=None
        self.generation=None


class FakeBucket:
    def __init__(self):
        self.blob_calls=[]
        self.object=AtomicBlob()
    def blob(self,path):
        self.blob_calls.append(path)
        if path!=pairing.APPROVAL_BLOB:
            raise AssertionError("Unexpected object name")
        return self.object


class FakeStore:
    def __init__(self):
        self.bucket=FakeBucket()
        self.checked=0
    def _require_private_bucket(self):
        self.checked+=1


class ConsentTests(unittest.TestCase):
    def test_off_and_cross_service_fail_closed_before_storage(self):
        for update in [
            {pairing.FLAG:"false"},
            {"K_SERVICE":"plenum-computer-browser"},
            {"BROWSER_PROFILE_BUCKET":""},
            {"BROWSER_SESSION_KEY":""},
            {"BROWSER_ALLOWED_ORIGINS":"https://example.com"},
            {"AUTH0_OWNER_PUBLIC_ORIGIN":"https://attacker.invalid"},
        ]:
            with self.subTest(update=update),patch.dict(os.environ,{**SAFE,**update}):
                with self.assertRaises(PermissionError):
                    pairing.require_enabled()

    def test_invalid_opaque_owner_is_rejected(self):
        for owner in ("",None,"someone@gmail.com","0"*63,"/"*64,"A"*64):
            with self.subTest(owner=owner),self.assertRaises(PermissionError):
                pairing._owner(owner)

    @unittest.skipUnless(importlib.util.find_spec("cryptography") is not None,
                         "Real Fernet requires optional browser crypto library")
    def test_encrypted_one_use_consumed_atomically_and_never_returns_credential(self):
        from cryptography.fernet import Fernet
        store=FakeStore()
        env={**SAFE,"BROWSER_SESSION_KEY":Fernet.generate_key().decode()}
        with patch.dict(os.environ,env),patch(
                "services.computer_browser.private_profiles.BrowserProfileStore.from_environment",
                return_value=store):
            approval=pairing.approve_one_demo_read(OWNER)
            self.assertEqual(approval["ttl_seconds"],600)
            sealed=store.bucket.object.data
            self.assertNotIn(OWNER.encode(),sealed)
            self.assertNotIn(b"browser.session",sealed)
            approved_owner=pairing.consume_one_demo_read()
            self.assertEqual(approved_owner,OWNER)
            self.assertIsNone(store.bucket.object.data)
            with self.assertRaises(PermissionError):
                pairing.consume_one_demo_read()
        self.assertGreaterEqual(store.checked,3)
        self.assertEqual(store.bucket.blob_calls,[pairing.APPROVAL_BLOB]*3)

    @unittest.skipUnless(importlib.util.find_spec("cryptography") is not None,
                         "Real Fernet requires optional browser crypto library")
    def test_expired_approval_denied_and_generation_guarded(self):
        from cryptography.fernet import Fernet
        store=FakeStore()
        env={**SAFE,"BROWSER_SESSION_KEY":Fernet.generate_key().decode()}
        now=int(time.time())
        with patch.dict(os.environ,env),patch(
                "services.computer_browser.private_profiles.BrowserProfileStore.from_environment",
                return_value=store):
            pairing.approve_one_demo_read(OWNER,now=now-700)
            with self.assertRaises(PermissionError):
                pairing.consume_one_demo_read(now=now)
            # Owner may replace a pending expired approval, preserving CAS.
            pairing.approve_one_demo_read(OWNER,now=now)
            self.assertEqual(pairing.consume_one_demo_read(now=now),OWNER)


if __name__=="__main__":
    unittest.main()

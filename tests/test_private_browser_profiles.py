"""Offline tests for encrypted GCS-backed browser session isolation."""
import base64
import os
import unittest
from cryptography.fernet import Fernet
from services.computer_browser.private_profiles import BrowserProfileStore


class FakeBlob:
    def __init__(self):
        self.generation=None
        self.saved=None
    def upload_from_string(self,data,content_type,if_generation_match):
        assert content_type=="application/octet-stream"
        if if_generation_match==0 and self.saved is not None:
            raise ValueError("Already exists")
        if if_generation_match and self.generation!=if_generation_match:
            raise ValueError("Generation changed")
        self.saved=data
        self.generation=(self.generation or 0)+1
    def reload(self):
        if self.saved is None:
            raise FileNotFoundError()
    def download_as_bytes(self,if_generation_match):
        assert self.generation==if_generation_match
        return self.saved
    def exists(self):
        return self.saved is not None
    def delete(self,if_generation_match):
        if if_generation_match != self.generation:
            raise ValueError("Concurrent write")
        self.saved=None

class FakeBucket:
    def __init__(self):
        self.blobs={}
    def blob(self,name):
        if name not in self.blobs:
            self.blobs[name]=FakeBlob()
        return self.blobs[name]

class FakeClient:
    def __init__(self):
        self.bucket_obj=FakeBucket()
    def bucket(self,name):
        return self.bucket_obj

class SessionCloudStoreTests(unittest.TestCase):
    def setUp(self):
        self.key=Fernet.generate_key()
        self.client=FakeClient()
        self.store=BrowserProfileStore(bucket_name="private-browser-test",fernet_key=self.key,client=self.client)
        self.state={"cookies":[{"name":"fake-token","value":"SYNTHETIC-COOKIE-NOT-REAL"}],"origins":[]}

    def test_encrypt_store_restore_no_exposed_tokens(self):
        self.assertFalse(self.store.status(owner="computer",origin="https://example.com")["profile_exists"])
        stored=self.store.save_new(owner="computer",origin="https://example.com",state=self.state)
        self.assertTrue(stored["stored"])
        self.assertNotIn("cookies",stored)
        blob=next(iter(self.client.bucket_obj.blobs.values()))
        self.assertIsInstance(blob.saved,bytes)
        self.assertNotIn(b"SYNTHETIC-COOKIE-NOT-REAL",blob.saved)
        recovered,gen=self.store.load_for_trusted_worker(owner="computer",origin="https://example.com")
        self.assertEqual(recovered,self.state)
        self.assertEqual(gen,1)

    def test_owner_and_site_separation(self):
        self.store.save_new(owner="computer",origin="https://example.com",state=self.state)
        self.assertFalse(self.store.status(owner="prometheus",origin="https://example.com")["profile_exists"])
        self.assertFalse(self.store.status(owner="computer",origin="https://news.mit.edu")["profile_exists"])
        keys=list(self.client.bucket_obj.blobs)
        self.assertNotIn("computer"," ".join(keys))
        self.assertNotIn("example.com"," ".join(keys))

    def test_no_overwrite_without_generation_and_revoke(self):
        self.store.save_new(owner="computer",origin="https://example.com",state=self.state)
        with self.assertRaises(ValueError):
            self.store.save_new(owner="computer",origin="https://example.com",state=self.state)
        with self.assertRaises(ValueError):
            self.store.replace_if_current(owner="computer",origin="https://example.com",
                                           state=self.state,expected_generation=2)
        self.store.replace_if_current(owner="computer",origin="https://example.com",
                                      state=self.state,expected_generation=1)
        with self.assertRaises(ValueError):
            self.store.revoke(owner="computer",origin="https://example.com",expected_generation=1)
        self.assertTrue(self.store.revoke(owner="computer",origin="https://example.com",expected_generation=2)["revoked"])

    def test_no_arbitrary_cloud_bucket_or_internal_site(self):
        for origin in ("http://example.com","https://127.0.0.1","https://example.com/private",
                       "https://metadata.google.internal","https://localhost"):
            with self.subTest(origin=origin):
                with self.assertRaises(PermissionError):
                    self.store.status(owner="computer",origin=origin)
        with self.assertRaises(PermissionError):
            self.store.status(owner="other/owner",origin="https://example.com")

    def test_unconfigured_service_is_fail_closed(self):
        with unittest.mock.patch.dict(os.environ,{"BROWSER_SESSION_KEY":"","BROWSER_PROFILE_BUCKET":""}):
            with self.assertRaises(RuntimeError):
                BrowserProfileStore.from_environment()

if __name__=="__main__":
    unittest.main()

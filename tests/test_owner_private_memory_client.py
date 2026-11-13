"""Original owner HMAC memory client's isolated offline tests (never sends data)."""
import hashlib
import hmac
import json
import os
import unittest
from unittest.mock import patch

from plenum_ai.owner_private_memory_client import (
    PrivateMemoryClient, PrivateMemoryUnavailable, ENDPOINT,
)


class Response:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False
    def read(self, n): return b'{"status":"STORED","revision":1}'


class PrivateMemoryClientTests(unittest.TestCase):
    def test_signed_request_exact_original_worker_endpoint(self):
        captures = []
        def sender(req, timeout):
            captures.append((req, timeout))
            return Response()
        with patch.dict(os.environ, {"GITHUB_ACTIONS":"false"}, clear=False):
            client=PrivateMemoryClient(secret="X"*40, sender=sender)
            result=client.put(
                key="american-rider:app-review",
                summary="Source-linked reviewer state is pending a decision.",
                source="https://github.com/chadkhalil21-svg/American-Rider-Commercial/issues/451",
                observed_at="2026-11-12T20:09:00-05:00",
                level="VERIFIED",expected_revision=0,
            )
        self.assertEqual(result["revision"],1)
        req, timeout = captures[0]
        self.assertEqual(req.full_url, ENDPOINT+"/memory")
        self.assertEqual(timeout,8)
        timestamp=req.get_header("X-plenum-memory-time")
        content=req.data.decode()
        signature=req.get_header("X-plenum-memory-signature")
        expected=hmac.new(b"X"*40,
            ("\n".join(["POST","/memory",timestamp,content])).encode(),
            hashlib.sha256).hexdigest()
        self.assertEqual(signature,"sha256="+expected)
        self.assertEqual(json.loads(content)["level"],"VERIFIED")

    def test_public_ci_cannot_access_owner_data(self):
        with patch.dict(os.environ,{"GITHUB_ACTIONS":"true","PLENUM_PRIVATE_MEMORY_HMAC_SECRET":"Y"*48}):
            with self.assertRaises(PrivateMemoryUnavailable):
                PrivateMemoryClient()
    def test_no_secret_fails_closed(self):
        with patch.dict(os.environ,{"GITHUB_ACTIONS":"false","PLENUM_PRIVATE_MEMORY_HMAC_SECRET":""}):
            with self.assertRaises(PrivateMemoryUnavailable):
                PrivateMemoryClient()
    def test_invalid_key_no_network(self):
        def sender(*args,**kwargs): raise AssertionError("Unexpected network")
        with patch.dict(os.environ,{"GITHUB_ACTIONS":"false"}):
            client=PrivateMemoryClient(secret="Z"*40,sender=sender)
            with self.assertRaises(ValueError):
                client.get("../private")
    def test_private_get_uses_signed_path(self):
        seen=[]
        def sender(req, timeout):seen.append(req.full_url);return Response()
        with patch.dict(os.environ,{"GITHUB_ACTIONS":"false"}):
            client=PrivateMemoryClient(secret="Z"*40,sender=sender)
            client.get("american-rider:review")
        self.assertEqual(seen,[ENDPOINT+"/memory/american-rider:review"])


if __name__=="__main__":
    unittest.main()

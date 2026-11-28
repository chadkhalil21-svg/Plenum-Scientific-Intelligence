"""Independent prospective transfer acceptance; no network or candidate code."""
import unittest
from plenum_ai.business_public_watch import TARGETS, probe

class Response:
    def __init__(self, url, status=200):
        self.url, self.status = url, status
        self.headers = {"Content-Type": "application/json"}
        self.reads = 0
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def geturl(self): return self.url
    def read(self, size):
        self.reads += 1
        return b'{"service":"american-rider-server"}'

class Client:
    def __init__(self, response): self.response = response
    def open(self, request, timeout):
        return self.response

class BusinessResponseBoundaryTransfer(unittest.TestCase):
    def test_mismatched_response_is_not_verified_or_read(self):
        target = TARGETS[2]
        for url in ("https://example.invalid/health", target.url + "?other=1"):
            with self.subTest(url=url):
                response = Response(url)
                result = probe(target, opener=Client(response))
                self.assertFalse(result[0])
                self.assertEqual(response.reads, 0)

    def test_expected_response_preserves_valid_health_read(self):
        target = TARGETS[2]
        response = Response(target.url)
        self.assertEqual(probe(target, opener=Client(response)), (True, "verified_read", 200))
        self.assertEqual(response.reads, 1)

    def test_non_200_preserves_no_read(self):
        target = TARGETS[2]
        response = Response(target.url, 503)
        self.assertFalse(probe(target, opener=Client(response))[0])
        self.assertEqual(response.reads, 0)

if __name__ == "__main__":
    unittest.main()

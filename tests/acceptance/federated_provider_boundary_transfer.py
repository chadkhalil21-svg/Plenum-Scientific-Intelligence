"""Frozen independent acceptance for distinct scientific retrieval boundary."""
import unittest
from plenum_ai.federated_sources import _read_json, MAX_BODY

URL = "https://api.openalex.org/works?search=concrete"
class Response:
    def __init__(self, destination=URL, status=200, data=b'{"results": []}'):
        self.destination, self.status, self.data = destination, status, data
        self.reads = 0
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def geturl(self): return self.destination
    def read(self, size):
        self.reads += 1
        return self.data[:size]

class FederatedBoundary(unittest.TestCase):
    def test_wrong_destination_or_status_before_read(self):
        for destination, status in ((URL+"x",200),("https://example.invalid/",200),(URL,203)):
            with self.subTest(destination=destination,status=status):
                response=Response(destination,status)
                with self.assertRaises(ValueError):
                    _read_json(URL, opener=lambda *a, **k: response)
                self.assertEqual(response.reads,0)

    def test_valid_and_legacy_injected_response(self):
        response=Response()
        self.assertEqual(_read_json(URL,opener=lambda *a,**k:response),{"results":[]})
        self.assertEqual(response.reads,1)
        class Legacy:
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def read(self,size): return b'{"results":[]}'
        self.assertEqual(_read_json(URL,opener=lambda *a,**k:Legacy()),{"results":[]})

    def test_byte_limit_retained(self):
        with self.assertRaises(ValueError):
            _read_json(URL, opener=lambda *a,**k:Response(data=b"x"*(MAX_BODY+1)))

if __name__=="__main__":
    unittest.main()

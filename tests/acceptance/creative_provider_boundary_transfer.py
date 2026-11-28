"""Frozen independent cross-domain public creative provider boundary."""
import unittest
from unittest.mock import patch
from urllib.request import HTTPRedirectHandler, OpenerDirector
from plenum_ai.creative_sources import _get, MAX_BYTES

URL = "https://api.openverse.org/v1/images/?q=sky"
class Response:
    def __init__(self, status=200, url=URL, data=b'{"results":[]}'):
        self.status, self.url, self.data = status, url, data
        self.reads=0
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def geturl(self): return self.url
    def read(self,size):
        self.reads+=1
        return self.data[:size]

class CreativeBoundary(unittest.TestCase):
    def test_non200_and_destination_mismatch_no_read(self):
        for r in (Response(201), Response(url=URL+"&other=1"), Response(url="https://example.invalid")):
            with self.subTest(status=r.status,url=r.url):
                with self.assertRaises(ValueError): _get(URL,opener=lambda *a,**k:r)
                self.assertEqual(r.reads,0)

    def test_conflicting_destination_metadata_no_read(self):
        r=Response(url="https://example.invalid")
        r.geturl=lambda:URL
        with self.assertRaises(ValueError): _get(URL,opener=lambda *a,**k:r)
        self.assertEqual(r.reads,0)

    def test_default_refuses_redirect(self):
        def offline_open(client,request,*a,**k):
            handler=next(h for h in client.handlers if isinstance(h,HTTPRedirectHandler))
            self.assertIsNone(handler.redirect_request(request,None,302,"Found",{},URL+"x"))
            return Response()
        with patch.object(OpenerDirector,"open",offline_open):
            self.assertEqual(_get(URL),{"results":[]})

    def test_valid_injected_legacy_and_bound(self):
        r=Response()
        self.assertEqual(_get(URL,opener=lambda *a,**k:r),{"results":[]})
        self.assertEqual(r.reads,1)
        class Legacy:
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def read(self,size): return b'{"results":[]}'
        self.assertEqual(_get(URL,opener=lambda *a,**k:Legacy()),{"results":[]})
        with self.assertRaises(ValueError):
            _get(URL,opener=lambda *a,**k:Response(data=b"x"*(MAX_BYTES+1)))

if __name__=="__main__":
    unittest.main()

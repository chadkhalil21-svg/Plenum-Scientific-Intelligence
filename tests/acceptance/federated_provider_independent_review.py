"""Supplemental independent review, frozen before prospective candidate readback."""
import unittest
from unittest.mock import patch
from urllib.request import HTTPRedirectHandler
from plenum_ai.federated_sources import _read_json

URL = "https://api.openalex.org/works?search=concrete"
class BaseResponse:
    status=200
    def __init__(self): self.reads=0
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self,size):
        self.reads+=1
        return b'{"results":[]}'

class FederatedIndependentReview(unittest.TestCase):
    def test_url_only_wrong_destination_and_conflicting_metadata(self):
        class URLOnly(BaseResponse):
            url=URL+"x"
        class Conflict(URLOnly):
            def geturl(self): return URL
        for response in (URLOnly(),Conflict()):
            with self.subTest(response=type(response).__name__):
                with self.assertRaises(ValueError):
                    _read_json(URL,opener=lambda *a,**k:response)
                self.assertEqual(response.reads,0)

    def test_default_redirect_handler_refuses_redirect_before_network(self):
        # Patch the standard builder's actual opener execution, not the
        # injected-client path. Inspect the redirect handler installed.
        from urllib.request import OpenerDirector
        def offline_open(client,request,*a,**k):
            handler=next(h for h in client.handlers if isinstance(h,HTTPRedirectHandler))
            self.assertIsNone(handler.redirect_request(request,None,302,"Found",{},URL+"x"))
            response=BaseResponse()
            response.url=URL
            response.geturl=lambda: URL
            return response
        with patch.object(OpenerDirector,"open",offline_open):
            self.assertEqual(_read_json(URL),{"results":[]})

if __name__=="__main__":
    unittest.main()

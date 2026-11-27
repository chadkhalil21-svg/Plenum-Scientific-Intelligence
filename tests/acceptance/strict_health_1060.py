"""Independent acceptance for #1060; no network."""
import unittest
from plenum_ai.business_public_watch import TARGETS, probe

class Response:
    status=200
    headers={"Content-Type":"application/json"}
    def __init__(self,raw): self.raw=raw
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self,n): return self.raw[:n]
class Opener:
    def __init__(self,raw): self.raw=raw; self.calls=0
    def open(self,req,timeout):
        self.calls+=1
        return Response(self.raw)

class StrictHealth(unittest.TestCase):
    def test_reject_nonstandard_json(self):
        for raw in (
            b'{"service":"wrong","service":"american-rider-server"}',
            b'{"service":"american-rider-server","details":{"x":1,"x":2}}',
            b'{"service":"american-rider-server","items":[{"x":1,"x":2}]}',
            b'{"service":"american-rider-server","x":NaN}',
            b'{"service":"american-rider-server","x":[Infinity]}',
            b'{"service":"american-rider-server","x":{"y":-Infinity}}',
        ):
            with self.subTest(raw=raw):
                opener=Opener(raw)
                result=probe(TARGETS[2],opener=opener)
                self.assertEqual(result[:2],(False,"unexpected_content"))
                self.assertEqual(opener.calls,1)
    def test_valid_and_wrong_service(self):
        for raw in (
            b'{"service":"american-rider-server","x":{"a":1},"y":{"a":2}}',
            b'{"service":"american-rider-server","x":[1,2.5,-3,true,null,"NaN"]}',
        ):
            with self.subTest(raw=raw):
                self.assertEqual(probe(TARGETS[2],opener=Opener(raw)),(True,"verified_read",200))
        self.assertEqual(probe(TARGETS[2],opener=Opener(b'{"service":"wrong"}')),(False,"unexpected_service",200))

if __name__=="__main__":
    unittest.main()

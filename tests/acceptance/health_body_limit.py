"""Independently authored acceptance for the specific public monitor repair.
Executed only against a candidate by the existing networkless review gate.
"""
import io
import json
import unittest
from plenum_ai.business_public_watch import TARGETS, probe

class Response(io.BytesIO):
    status=200
    headers={"Content-Type":"application/json"}

class Client:
    def __init__(self, raw):
        self.raw=raw
    def open(self, request, timeout):
        return Response(self.raw)

class HealthBodyAcceptance(unittest.TestCase):
    def test_exact_byte_limit_and_oversize_valid_json_prefix(self):
        original=json.dumps({"service":"american-rider-server"}).encode()
        for size, expected in ((65535,True),(65536,True),(65537,False),(70000,False)):
            raw=original+b" "*(size-len(original))
            with self.subTest(size=size):
                result=probe(TARGETS[2],opener=Client(raw))
                self.assertIs(result[0],expected)
                if expected:
                    self.assertEqual(result,(True,"verified_read",200))
    def test_wrong_service_and_invalid_json_remain_failed(self):
        for raw in (b'{"service":"other"}', b'{"broken":'):
            self.assertFalse(probe(TARGETS[2],opener=Client(raw))[0])

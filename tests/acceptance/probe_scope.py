"""Frozen independent acceptance for the original probe scope defect."""
import unittest
import io
from plenum_ai.business_public_watch import Target, TARGETS, probe

class Reply(io.BytesIO):
    status=200
    headers={"Content-Type":"text/html"}

class Client:
    def __init__(self):
        self.calls=[]
    def open(self, request, timeout):
        self.calls.append(request.full_url)
        return Reply(b"<html>ok</html>")

class ProbeScopeAcceptance(unittest.TestCase):
    def test_unapproved_target_never_reaches_http(self):
        for target in (Target("corporate","https://example.org/","html"),
                       Target("unknown",TARGETS[0].url,"html"),
                       Target("corporate",TARGETS[0].url,"health")):
            with self.subTest(target=target):
                client=Client()
                result=probe(target,opener=client)
                self.assertIs(result[0],False)
                self.assertIsNone(result[2])
                self.assertTrue(result[1])
                self.assertEqual(client.calls,[])
    def test_approved_target_preserves_http_and_result(self):
        client=Client()
        self.assertEqual(probe(TARGETS[0],opener=client),(True,"verified_read",200))
        self.assertEqual(client.calls,[TARGETS[0].url])

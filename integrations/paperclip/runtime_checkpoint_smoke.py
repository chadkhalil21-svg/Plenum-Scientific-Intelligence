"""Strict transport contract; isolated fixture only, no production secrets/network."""
import hashlib
import hmac
import json
import os
import unittest
from io import BytesIO
from unittest.mock import Mock,patch
from urllib.error import HTTPError
from uuid import uuid4
from runtime_checkpoint import RuntimeCheckpoint,CheckpointRejected

class Response(BytesIO):
    status=200

class Tests(unittest.TestCase):
    def setUp(self):
        self.c,self.m,self.i=[str(uuid4()) for _ in range(3)]
        self.secret="isolated-test-secret-not-production-0123456789"
        self.env=patch.dict(os.environ,{"GITHUB_ACTIONS":"false"})
        self.env.start();self.addCleanup(self.env.stop)
        self.row={"issue":self.i,"state":"reserved","attempt":1,"sha256":None,"revision":1}
    def client(self,sender):
        return RuntimeCheckpoint(self.c,self.m,"engineering",self.i,secret=self.secret,scope=self.c+"/"+self.m,sender=sender)
    def response(self,row,status=200):
        res=Response(json.dumps(row).encode());res.status=status;return res
    def missing(self):
        return HTTPError("https://fixture.invalid",404,"missing",{},BytesIO(b'{"error":"not_found"}'))
    def test_exact_transitions_and_signed_body(self):
        row=None;calls=[]
        def sender(req,timeout):
            nonlocal row
            raw=req.data.decode() if req.data else ""
            stamp=req.get_header("X-plenum-memory-time")
            sig=hmac.new(self.secret.encode(),"\n".join((req.method,req.selector,stamp,raw)).encode(),hashlib.sha256).hexdigest()
            self.assertEqual(req.get_header("X-plenum-memory-signature"),"sha256="+sig)
            calls.append(req.method)
            if req.method=="GET":
                if row is None:raise self.missing()
                return self.response(row)
            b=json.loads(raw)
            self.assertEqual(b["expected_revision"],0 if row is None else row["revision"])
            row={k:b[k] for k in ("issue","state","attempt","sha256")}
            row["revision"]=b["expected_revision"]+1
            return self.response(row)
        c=self.client(sender)
        c.reserve(1);c.reserve(2);c.complete("a"*64);c.complete("a"*64)
        self.assertEqual(calls,["GET","POST","GET","POST","GET","POST","GET"])
        self.assertEqual(row,{"issue":self.i,"state":"completed","attempt":2,"sha256":"a"*64,"revision":3})
        with self.assertRaises(ValueError):c.complete("b"*64)
        self.assertEqual(calls[-1],"GET")
    def test_wrong_valid_post_ack_blocks_reservation(self):
        for row in ({**self.row,"attempt":2,"revision":2},{**self.row,"state":"completed","sha256":"a"*64,"revision":2}):
            sender=Mock(side_effect=[self.missing(),self.response(row)])
            with self.assertRaisesRegex(ValueError,"acknowledgment"):
                self.client(sender).reserve(1)
            self.assertEqual(sender.call_count,2)
    def test_wrong_valid_completion_ack_blocks(self):
        row={**self.row,"state":"completed","sha256":"b"*64,"revision":2}
        sender=Mock(side_effect=[self.response(self.row),self.response(row)])
        with self.assertRaisesRegex(ValueError,"acknowledgment"):
            self.client(sender).complete("a"*64)
    def test_malformed_success_receipts_denied(self):
        for row in ({**self.row,"revision":2},{**self.row,"attempt":True},{**self.row,"sha256":"a"*64},
                    {**self.row,"unexpected":"x"},{**self.row,"state":"completed","revision":2,"sha256":"x"}):
            with self.assertRaises(ValueError):self.client(lambda *a,**k:self.response(row)).request("GET")
        for raw in (b'{"issue":"a","issue":"b"}',b'{"x":NaN}',b' '*4097):
            with self.assertRaises(RuntimeError):self.client(lambda *a,**k:Response(raw)).request("GET")
        with self.assertRaises(RuntimeError):self.client(lambda *a,**k:self.response(self.row,201)).request("GET")
    def test_replay_conflict_and_invalid_inputs_never_continue(self):
        denied=HTTPError("https://fixture.invalid",409,"conflict",{},BytesIO(b'{"error":"stale_revision","current_revision":1}'))
        sender=Mock(side_effect=[self.missing(),denied]);c=self.client(sender)
        with self.assertRaises(CheckpointRejected) as exc:c.reserve(1)
        self.assertEqual(exc.exception.status,409);self.assertEqual(exc.exception.code,"stale_revision")
        self.assertEqual(sender.call_count,2)
        with self.assertRaises(ValueError):c.reserve(True)
        with self.assertRaises(ValueError):c.complete("not-a-digest")
        self.assertEqual(sender.call_count,2)

if __name__=="__main__":unittest.main(verbosity=2)

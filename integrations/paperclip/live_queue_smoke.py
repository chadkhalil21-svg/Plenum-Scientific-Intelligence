"""Offline signed-response fixtures, queue identity, and fail-closed regression."""
import hashlib,hmac,json,os,tempfile,unittest
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError
from uuid import uuid4
from unittest.mock import patch,Mock
from checkpoint_store import exclusive
from model_plan import digest
from runtime_checkpoint import RuntimeCheckpoint
from live_verify import remote_receipt,local_receipt,ROLES,REQUIRED
from mission_queue import validate_queue,queue_run
from mission_scope import digest as scope_digest
from production_wiring import prepared

class Response(BytesIO):
    status = 200

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.c,self.m,self.leader,self.qid=(str(uuid4()) for _ in range(4))
        self.d=self.root/self.c/self.m;self.d.mkdir(parents=True)
        self.scope={"kind":"coastal"};self.secret="s"*32
        self.tasks={r:str(uuid4()) for r in ROLES}
        self.roster={"minister":self.leader,**{r:str(uuid4()) for r in ROLES}}
        evidence={}
        for r,issue in self.tasks.items():
            result={"value":r};h=digest(result)
            exclusive(self.d/(r+".json"),{"company":self.c,"role":r,"issue":issue,"result":result,"sha256":h})
            evidence[r]={"issue":issue,"sha256":h}
        self.q={"company":self.c,"parent":self.m,"minister":self.leader,"scope_sha256":scope_digest(self.scope),
                **REQUIRED,"model_receipt_sha256":"a"*64,"persistent_roster":self.roster,
                "profile_receipt_sha256":{str(i):"b"*64 for i in range(11)},"evidence":evidence}
        prepared(self.d,self.c,self.m,self.q["scope_sha256"],"remote","local")
        exclusive(self.d/"activation.json",{"company":self.c,"mission":self.m,"minister":self.leader,"scope_sha256":self.q["scope_sha256"],"model_mode":"local","remote_checkpoint_preflight":True})
        exclusive(self.d/"minister-plan.json",{"company":self.c,"parent":self.m,"minister":self.leader,"tasks":self.tasks})
        exclusive(self.d/"qualification.json",self.q)
        exclusive(self.d/"event-timing.json",{"parent":self.m,"qualification_sha256":digest(self.q),"paid_inference":False,"model_executed":True,"verified_divisions":5})
    def sender(self,req,timeout):
        path=req.selector
        stamp=req.get_header("X-plenum-memory-time")
        actual=req.get_header("X-plenum-memory-signature")
        self.assertEqual(actual,"sha256="+hmac.new(self.secret.encode(),("\n".join(("GET",path,stamp,""))).encode(),hashlib.sha256).hexdigest())
        self.assertEqual(req.method,"GET")
        if not path.startswith("/paperclip-checkpoints/"+self.c+"/"+self.m+"/"):
            raise HTTPError(req.full_url,403,"denied",{},BytesIO(b'{"error":"checkpoint_scope_unavailable"}'))
        r=path.rsplit("/",1)[1]
        return Response(json.dumps({**self.q["evidence"][r],"state":"completed","attempt":1,"revision":2}).encode())
    def remote(self,sender):
        def client(*args,**kwargs):return RuntimeCheckpoint(*args,**kwargs,sender=sender)
        with patch.dict(os.environ,{"PLENUM_PERSISTENT_BOARD":"confirmed","GITHUB_ACTIONS":"false"}),patch("live_verify.grant",return_value=self.secret),patch("live_verify.RuntimeCheckpoint",side_effect=client):
            return remote_receipt(self.root,self.c,self.m,lambda *args:self.q)
    def test_live_five_signed_gets_and_wrong_scope(self):
        sender=Mock(side_effect=self.sender)
        row=self.remote(sender)
        self.assertEqual(sender.call_count,6)
        self.assertEqual(row["remote_checkpoint_count"],5)
        self.assertEqual(row["wrong_scope_http_status"],403)
        self.assertIsNone(row["restart_readback_receipt_sha256"])
        self.assertFalse(row["container_restart_performed_by_verifier"])
        self.assertFalse(row["wake_verified"])
    def test_live_bad_digest_or_wrong_status_rejected(self):
        def bad_digest(req,timeout):
            with self.sender(req,timeout) as stream:row=json.load(stream)
            row["sha256"]="0"*64;return Response(json.dumps(row).encode())
        with self.assertRaises(ValueError):self.remote(bad_digest)
        def bad_scope(req,timeout):
            try:return self.sender(req,timeout)
            except HTTPError:raise HTTPError(req.full_url,403,"denied",{},BytesIO(b'{"error":"unauthorized_or_stale"}'))
        with self.assertRaises(ValueError):self.remote(bad_scope)
        with patch.dict(os.environ,{"GITHUB_ACTIONS":"true","PLENUM_PERSISTENT_BOARD":"confirmed"}):
            with self.assertRaises(PermissionError):remote_receipt(self.root,self.c,self.m,Mock())
    def test_local_tamper(self):
        (self.d/"engineering.json").write_text("{}")
        with patch.dict(os.environ,{"PLENUM_PERSISTENT_BOARD":"confirmed"}):
            with self.assertRaises(ValueError):local_receipt(self.root,self.c,self.m,lambda *args:self.q)
    def test_queue_validation(self):
        second={"kind":"public_dataset","subject":"Novel samples","dois":["10.1145/3442188.3445922"],"values":[1,9],"operations":["mean"]}
        self.assertEqual(validate_queue([self.scope,second]),[self.scope,second])
        for bad in ([self.scope,self.scope],[self.scope],[self.scope,{"kind":"shell"}],[second]*6):
            with self.assertRaises(ValueError):validate_queue(bad)
    def test_local_chain_immutable_and_no_replay(self):
        second={"kind":"public_dataset","subject":"Novel samples","dois":["10.1145/3442188.3445922"],"values":[1,9],"operations":["mean"]}
        scopes=[self.scope,second];calls=[];last=None
        def qualify(action):
            nonlocal last
            calls.append(action)
            if action=="prepare":
                scope=json.loads(os.environ["PLENUM_MISSION_SCOPE"]);last=str(uuid4())
                directory=self.root/self.c/last;directory.mkdir()
                return prepared(directory,self.c,last,scope_digest(scope),"local","local")
            directory=self.root/self.c/last
            exclusive(directory/"qualification.json",{"fixture":True})
        def local(root,cid,mid,readback):
            row={"persistent_roster":self.roster,"parent":mid}
            return None,row,None,None,None
        env={"PLENUM_PERSISTENT_BOARD":"confirmed","PLENUM_PAPERCLIP_MODEL":"local","PLENUM_PERSISTENT_CHECKPOINT_MODE":"local","PLENUM_PAPERCLIP_COMPANY_UUID":self.c,"PLENUM_PAPERCLIP_QUEUE_UUID":self.qid,"PLENUM_MISSION_QUEUE":json.dumps(scopes)}
        with patch.dict(os.environ,env),patch("mission_queue.local_receipt",side_effect=local):
            api=lambda path:[{"id":self.c}]
            first=queue_run(api,self.root,qualify,Mock())
            again=queue_run(api,self.root,qualify,Mock())
            self.assertEqual(first,again)
            self.assertEqual(calls,["prepare","activate","prepare","activate"])
            os.environ["PLENUM_MISSION_QUEUE"]=json.dumps(scopes[::-1])
            with self.assertRaises(ValueError):queue_run(api,self.root,qualify,Mock())
    def test_remote_queue_pauses_before_assignment(self):
        second={"kind":"public_dataset","subject":"Novel samples","dois":["10.1145/3442188.3445922"],"values":[1,9],"operations":["mean"]}
        calls=[]
        def qualify(action):
            calls.append(action)
            scope=json.loads(os.environ["PLENUM_MISSION_SCOPE"]);mid=str(uuid4())
            d=self.root/self.c/mid;d.mkdir()
            return prepared(d,self.c,mid,scope_digest(scope),"remote","local")
        env={"GITHUB_ACTIONS":"false","PLENUM_PERSISTENT_BOARD":"confirmed","PLENUM_PAPERCLIP_MODEL":"local","PLENUM_PERSISTENT_CHECKPOINT_MODE":"remote","PLENUM_PAPERCLIP_COMPANY_UUID":self.c,"PLENUM_PAPERCLIP_QUEUE_UUID":self.qid,"PLENUM_MISSION_QUEUE":json.dumps([self.scope,second])}
        with patch.dict(os.environ,env):
            r=queue_run(lambda path:[{"id":self.c}],self.root,qualify,Mock())
        self.assertEqual(r["state"],"awaiting_exact_grant")
        self.assertEqual(calls,["prepare"])
        self.assertEqual(r["checkpoint_scope"],self.c+"/"+r["mission"])
if __name__=="__main__":unittest.main(verbosity=2)

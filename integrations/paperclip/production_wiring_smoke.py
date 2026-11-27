"""No external access: exact grant, preflight ordering and deny-before-assignment."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch,Mock
from uuid import uuid4
from urllib.error import HTTPError
from io import BytesIO
import production_wiring as w
from runtime_checkpoint import RuntimeCheckpoint

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.c,self.m,self.leader=(str(uuid4()) for _ in range(3))
        self.binding={"scope_sha256":"a"*64,"parent_title":"title","parent_description":"description"}
        self.task={"id":self.m,"companyId":self.c,"parentId":None,"status":"todo","assigneeAgentId":None,
                   "title":"title","description":"description"}
    def test_prepare_and_fail_closed(self):
        w.prepared(self.root,self.c,self.m,"a"*64,"remote")
        api=Mock(return_value=self.task)
        with patch.object(w,"preflight",side_effect=PermissionError("no grant")):
            with self.assertRaises(PermissionError):w.authorize_activation(api,self.root,self.c,self.m,self.leader,self.binding)
        self.assertEqual(api.call_count,1)
        self.assertFalse((self.root/"activation.json").exists())
        with patch.object(w,"preflight",return_value=True):
            self.assertTrue(w.authorize_activation(api,self.root,self.c,self.m,self.leader,self.binding))
            self.assertEqual(api.call_args.args,("/api/issues/"+self.m,"PATCH",{"assigneeAgentId":self.leader}))
            with self.assertRaises(FileExistsError):w.authorize_activation(api,self.root,self.c,self.m,self.leader,self.binding)
    def test_local_and_exact_grant(self):
        w.prepared(self.root,self.c,self.m,"a"*64,"local")
        self.assertFalse(w.preflight(self.root,self.c,self.m))
        p=self.root/(self.m+".json")
        p.write_text(json.dumps({"scope":self.c+"/"+self.m,"secret":"x"*32}))
        p.chmod(0o600)
        with patch.dict(os.environ,{"GITHUB_ACTIONS":"false"}):
            self.assertEqual(w.grant(self.c,self.m,root=self.root),"x"*32)
            p.chmod(0o644)
            with self.assertRaises(PermissionError):w.grant(self.c,self.m,root=self.root)
            p.chmod(0o700)
            with self.assertRaises(PermissionError):w.grant(self.c,self.m,root=self.root)
            p.chmod(0o600)
            self.root.chmod(0o755)
            try:
                with self.assertRaises(PermissionError):w.grant(self.c,self.m,root=self.root)
            finally:self.root.chmod(0o700)
            with patch.object(w,"GRANT_DIR",self.root):
                with self.assertRaises(PermissionError):w.grant(self.c,self.m)
            with self.assertRaises(PermissionError):w.grant(str(uuid4()),self.m,root=self.root)
        with patch.dict(os.environ,{"GITHUB_ACTIONS":"true"}):
            with self.assertRaises(PermissionError):w.grant(self.c,self.m,root=self.root)
    def test_generic_404_not_valid_preflight(self):
        def sender(body):
            def fail(*args,**kwargs):raise HTTPError("https://fixture.invalid",404,"missing",{},BytesIO(json.dumps(body).encode()))
            return fail
        with patch.dict(os.environ,{"GITHUB_ACTIONS":"false"}):
            for value,ok in (({"error":"not_found"},True),({"error":"route_not_found"},False)):
                client=RuntimeCheckpoint(self.c,self.m,"intelligence",self.m,secret="x"*32,scope=self.c+"/"+self.m,sender=sender(value))
                if ok:self.assertIsNone(client.request("GET"))
                else:
                    with self.assertRaises(RuntimeError):client.request("GET")
    def test_company_submission_lock(self):
        with w.company_lock(self.root,self.c):
            with self.assertRaises(BlockingIOError):
                with w.company_lock(self.root,self.c):pass

    def test_magentic_activation_checks_selected_model_and_denies_unapproved_scope(self):
        import sys
        from types import SimpleNamespace
        from native_variable import magentic_fixture
        from mission_scope import digest as scope_digest
        scope=magentic_fixture()
        tag=scope_digest(scope)
        binding={**self.binding,"scope":scope,"scope_sha256":tag}
        w.prepared(self.root,self.c,self.m,tag,"local","local")
        api=Mock(return_value=self.task)
        checker=Mock(return_value="56671c2ab938"+"a"*52)
        planner=SimpleNamespace(strict=Mock(),model_digest=checker)
        with patch.dict(sys.modules,{"planner":planner}),patch("model_plan.check_local_model") as old:
            with patch.dict(os.environ,{"GITHUB_ACTIONS":"true","PLENUM_CI_MAGENTIC_NATIVE":"off"}):
                with self.assertRaises(PermissionError):
                    w.authorize_activation(api,self.root,self.c,self.m,self.leader,binding)
            self.assertFalse((self.root/"activation.json").exists())
            checker.assert_not_called()
            with patch.dict(os.environ,{"GITHUB_ACTIONS":"true","PLENUM_CI_MAGENTIC_NATIVE":"confirmed"}):
                checker.side_effect=ValueError("Wrong model")
                with self.assertRaises(ValueError):
                    w.authorize_activation(api,self.root,self.c,self.m,self.leader,binding)
                self.assertFalse((self.root/"activation.json").exists())
                checker.side_effect=None
                self.assertFalse(w.authorize_activation(api,self.root,self.c,self.m,self.leader,binding))
                self.assertEqual(api.call_args.args,("/api/issues/"+self.m,"PATCH",{"assigneeAgentId":self.leader}))
            self.assertEqual(checker.call_count,2)
            old.assert_not_called()
    def test_original_activation_preserves_4b_check(self):
        with patch("model_plan.check_local_model",return_value="original") as checker:
            self.assertEqual(w.check_activation_model({"checkpoint_mode":"local"},self.binding),"original")
            checker.assert_called_once_with()

if __name__=="__main__":unittest.main(verbosity=2)

"""Offline fixtures for owner preflight, scope probe and private mount."""
import os,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
from types import SimpleNamespace
from uuid import uuid4
from io import BytesIO
from urllib.error import HTTPError
import live_preflight as lp
import production_wiring as w
from runtime_checkpoint import RuntimeCheckpoint

class Tests(unittest.TestCase):
    def test_directory_mode_and_readonly(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);p.chmod(0o700)
            with patch("live_preflight.os.statvfs",return_value=SimpleNamespace(f_flag=os.ST_RDONLY)):
                self.assertTrue(lp.grant_directory(p))
                p.chmod(0o755)
                with self.assertRaises(PermissionError):lp.grant_directory(p)
                p.chmod(0o700)
                link=p/"link";link.symlink_to(p)
                with self.assertRaises(PermissionError):lp.grant_directory(link)
            with patch("live_preflight.os.statvfs",return_value=SimpleNamespace(f_flag=0)):
                with self.assertRaises(PermissionError):lp.grant_directory(p)
    def test_live_preflight_no_scope_and_wrong_worker(self):
        env={"GITHUB_ACTIONS":"false","PLENUM_PERSISTENT_BOARD":"confirmed","PLENUM_PAPERCLIP_MODEL":"local","PLENUM_PAPERCLIP_MISSION_UUID":""}
        with patch.dict(os.environ,env),patch.object(lp,"local_checks",return_value={"model_digest":"fixture"}),patch.object(lp,"grant_directory"),patch.object(lp,"health_json",return_value={"state":"REACHABLE_NOT_A_RUNNING_AGENT","no_model":True}) as health:
            row=lp.preflight_live(Mock(),Path("/unused"))
            self.assertIsNone(row["scoped_remote_preflight"]);self.assertFalse(row["billing_plan_verified"])
            health.return_value={"state":"other","no_model":True}
            with self.assertRaises(ValueError):lp.preflight_live(Mock(),Path("/unused"))
            os.environ["GITHUB_ACTIONS"]="true"
            with self.assertRaises(PermissionError):lp.preflight_live(Mock(),Path("/unused"))
    def test_local_configuration_and_model(self):
        env={"HOST":"127.0.0.1","PAPERCLIP_BIND":"loopback","PAPERCLIP_DEPLOYMENT_MODE":"local_trusted","PAPERCLIP_DEPLOYMENT_EXPOSURE":"private","PAPERCLIP_API_URL":"http://127.0.0.1:3100"}
        with patch.dict(os.environ,env),patch.object(lp,"health_json",return_value={"ok":True}),patch.object(lp,"check_local_model",return_value="fixture") as model:
            self.assertEqual(lp.local_checks(lambda path:[],Path("/unused"))["model_digest"],"fixture")
            model.side_effect=ValueError("wrong model")
            with self.assertRaises(ValueError):lp.local_checks(lambda path:[],Path("/unused"))
            os.environ["HOST"]="0.0.0.0"
            with self.assertRaises(PermissionError):lp.local_checks(lambda path:[],Path("/unused"))
    def test_all_slots_empty_and_exact_wrong_scope(self):
        c,m=str(uuid4()),str(uuid4())
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);w.prepared(d,c,m,"a"*64,"remote","local")
            calls=[]
            def sender(req,timeout):
                calls.append(req.selector)
                if "/"+m+"/" in req.selector:
                    raise HTTPError(req.full_url,404,"missing",{},BytesIO(b'{"error":"not_found"}'))
                raise HTTPError(req.full_url,403,"denied",{},BytesIO(b'{"error":"checkpoint_scope_unavailable"}'))
            def client(*args,**kw):return RuntimeCheckpoint(*args,**kw,sender=sender)
            with patch.dict(os.environ,{"GITHUB_ACTIONS":"false"}),patch.object(w,"grant",return_value="x"*32),patch("runtime_checkpoint.RuntimeCheckpoint",side_effect=client):
                self.assertTrue(w.preflight(d,c,m));self.assertEqual(len(calls),6)
                self.assertEqual({x.rsplit("/",1)[1] for x in calls[:5]},{"intelligence","research","engineering","commercial","verification"})
            def bad(*args,**kw):
                client=Mock();client.request.return_value={"state":"reserved"}
                return client
            with patch.object(w,"grant",return_value="x"*32),patch("runtime_checkpoint.RuntimeCheckpoint",side_effect=bad):
                with self.assertRaises(ValueError):w.preflight(d,c,m)
if __name__=="__main__":unittest.main(verbosity=2)

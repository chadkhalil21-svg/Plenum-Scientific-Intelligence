"""Source policy and failure-closed fresh-runner checkpoint tests."""
import json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch,Mock
import event_native as e
import fresh_runner_acceptance as f
from uuid import uuid4

class Tests(unittest.TestCase):
    def test_event_native_objective_selects_staged_path(self):
        c,m=str(uuid4()),str(uuid4())
        scope={"kind":"public_objective","objective":"Compare synthetic numerical sample values","dois":["10.1145/3442188.3445922"],"inputs":{"samples":[1,2]},"operations":["mean"]}
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{"PLENUM_PAPERCLIP_MODEL":"local"},clear=False),patch.object(e.native,"ROOT",Path(tmp)),patch.object(e.native,"active_scope",return_value=scope),patch.object(e.native,"api",side_effect=[[],{"id":c}]),patch.object(e.native,"qualify",side_effect=[{"mission":m},{"accepted":True}]) as qualify:
            self.assertEqual(e.execute(),{"accepted":True})
            self.assertEqual([x.args for x in qualify.call_args_list],[("prepare",),("activate",)])
            self.assertEqual(json.loads((Path(tmp)/e.MARKER).read_text())["mission"],m)
    def test_event_coastal_reuses_original(self):
        with patch.object(e.native,"active_scope",return_value={"kind":"coastal"}),patch.object(e.native,"qualify",return_value={"ok":True}) as q:
            self.assertEqual(e.execute(),{"ok":True});q.assert_called_once_with()
    def test_fresh_runner_rejects_symlink_and_wrong_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"ci-diagnostic.json").write_text(json.dumps({"run_id":"wrong"}))
            with self.assertRaises(ValueError):f.accept(root,"original","sha")
            (root/"alias").symlink_to(root/"ci-diagnostic.json")
            with self.assertRaises(ValueError):f.safe_tree(root)
    def test_fresh_runner_requires_exact_archive_set(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{"EVENT":"pull_request","GITHUB_RUN_ID":"1","GITHUB_SHA":"sha"}),patch.object(f.sys,"argv",["program",tmp,tmp+"/output.json"]):
            with self.assertRaises(ValueError):f.main()
if __name__=="__main__":unittest.main(verbosity=2)

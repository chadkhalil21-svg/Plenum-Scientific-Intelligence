"""Frozen independent behavioral acceptance for actual mission #1048."""
import os
import tempfile
import unittest
from pathlib import Path
from plenum_ai import mission_checkpoint as c

ARGS = dict(issue=1048, objective="Checkpoint hard-link isolation", team=("research",))
RESULTS = {"research":{"attempt":1}}

class HardLinkAcceptance(unittest.TestCase):
    def test_ordinary_checkpoint_and_worker_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"mission"
            c.save_checkpoint(root,**ARGS,results=RESULTS)
            self.assertEqual(c.load_checkpoint(root,**ARGS),RESULTS)
            c.save_checkpoint(root,**ARGS,results={})
            self.assertEqual(c.load_checkpoint(root,**ARGS),{})
            item=root/"workers/research/output.txt"
            item.parent.mkdir(parents=True)
            item.write_text("ordinary public evidence",encoding="utf-8")
            digest=c.artifact_digest(root,"workers/research/output.txt")
            self.assertIsNotNone(digest)
            self.assertIsNotNone(c.artifact_digest(root,"workers/research"))
            entry={"status":"DRAFT_READY_FOR_FOUNDER","verified":True,"attempt":1,
                   "artifact_path":"workers/research/output.txt","sha256":digest}
            self.assertIsNotNone(c.verified_previous_result(root,"research",entry))

    def test_checkpoint_alias_rejected_before_replacement(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp); root=base/"mission"
            c.save_checkpoint(root,**ARGS,results=RESULTS)
            path=c.checkpoint_path(root,1048)
            outside=base/"outside.json"
            os.link(path,outside)
            before=outside.read_bytes()
            with self.assertRaises(ValueError):
                c.load_checkpoint(root,**ARGS)
            with self.assertRaises(ValueError):
                c.save_checkpoint(root,**ARGS,results={})
            self.assertTrue(os.path.samefile(path,outside))
            self.assertEqual(outside.read_bytes(),before)
            outside.unlink()
            self.assertEqual(c.load_checkpoint(root,**ARGS),RESULTS)
            c.save_checkpoint(root,**ARGS,results={})
            self.assertEqual(c.load_checkpoint(root,**ARGS),{})

    def test_worker_file_and_nested_aliases_are_not_resume_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp); root=base/"mission"
            item=root/"workers/research/sub/output.txt"
            item.parent.mkdir(parents=True)
            item.write_text("public evidence",encoding="utf-8")
            name="workers/research/sub/output.txt"
            digest=c.artifact_digest(root,name)
            self.assertIsNotNone(digest)
            entry={"status":"DRAFT_READY_FOR_FOUNDER","verified":True,"attempt":1,
                   "artifact_path":name,"sha256":digest}
            outside=base/"outside.txt"
            os.link(item,outside)
            self.assertIsNone(c.artifact_digest(root,name))
            self.assertIsNone(c.artifact_digest(root,"workers/research"))
            self.assertIsNone(c.verified_previous_result(root,"research",entry))
            outside.unlink()
            self.assertEqual(c.artifact_digest(root,name),digest)
            sibling=item.parent/"alias.txt"
            os.link(item,sibling)
            self.assertIsNone(c.artifact_digest(root,name))
            self.assertIsNone(c.artifact_digest(root,"workers/research"))
            sibling.unlink()
            self.assertIsNotNone(c.artifact_digest(root,"workers/research"))

if __name__=="__main__":unittest.main()

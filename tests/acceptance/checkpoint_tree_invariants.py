"""Independent acceptance of malformed saved attempts and nonregular artifact entries."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from plenum_ai import mission_checkpoint as m

class CheckpointTreeAcceptance(unittest.TestCase):
    def test_all_saved_attempts_are_valid_before_any_worker_is_resumed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            args={"issue":42,"objective":"Public task","team":("program","research")}
            valid={"program":{"attempt":1,"status":"RUNNING","verified":False},
                   "research":{"attempt":2,"status":"DRAFT_READY_FOR_FOUNDER","verified":True}}
            m.save_checkpoint(root,**args,results=valid)
            self.assertEqual(m.load_checkpoint(root,**args),valid)
            m.save_checkpoint(root,**args,results={})
            self.assertEqual(m.load_checkpoint(root,**args),{})
            for bad in (None,[],42,{},{"attempt":True},{"attempt":False},{"attempt":0},
                        {"attempt":3},{"attempt":-1},{"attempt":1.0},{"attempt":"1"}):
                with self.subTest(entry=bad):
                    path=m.checkpoint_path(root,42)
                    m.save_checkpoint(root,**args,results=valid)
                    before=path.read_bytes()
                    with self.assertRaises(ValueError):
                        m.save_checkpoint(root,**args,results={**valid,"research":bad})
                    self.assertEqual(path.read_bytes(),before)
                    # Simulate corruption from outside the validated writer.
                    corrupted=json.loads(before)
                    corrupted["results"]["research"]=bad
                    path.write_text(json.dumps(corrupted))
                    with self.assertRaises(ValueError):
                        m.load_checkpoint(root,**args)

    def test_nested_regular_tree_is_accepted_but_fifo_is_not_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            name="workers/program/result"
            artifact=root/name
            nested=artifact/"nested"
            nested.mkdir(parents=True)
            (nested/"output.txt").write_text("completed")
            digest=m.artifact_digest(root,name)
            self.assertIsNotNone(digest)
            fifo=artifact/"untrusted-pipe"
            os.mkfifo(fifo)
            self.assertIsNone(m.artifact_digest(root,name))
            fifo.unlink()
            self.assertEqual(m.artifact_digest(root,name),digest)

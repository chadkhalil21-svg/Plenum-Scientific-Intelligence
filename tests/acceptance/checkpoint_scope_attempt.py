"""Independent pre-inference acceptance of checkpoint scope and attempt invariants."""
import hashlib
import json
import tempfile
from pathlib import Path
import unittest
from plenum_ai import mission_checkpoint as m

class CheckpointQualification(unittest.TestCase):
    def test_load_requires_explicit_true_scope(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            args={"issue":42,"objective":"Public task","team":("program",)}
            m.save_checkpoint(root,**args,results={})
            path=m.checkpoint_path(root,42)
            valid=json.loads(path.read_text())
            self.assertEqual(m.load_checkpoint(root,**args),{})
            for value in (False,None,1,"true"):
                with self.subTest(value=value):
                    path.write_text(json.dumps({**valid,"only_original_public_workers":value}))
                    with self.assertRaises(ValueError):
                        m.load_checkpoint(root,**args)
            del valid["only_original_public_workers"]
            path.write_text(json.dumps(valid))
            with self.assertRaises(ValueError):
                m.load_checkpoint(root,**args)
    def test_receipt_requires_exact_attempt_integer(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            name="workers/program/output.txt"
            path=root/name
            path.parent.mkdir(parents=True)
            path.write_text("Completed work")
            entry={"status":"DRAFT_READY_FOR_FOUNDER","verified":True,
                   "worker":"coding-specialist","artifact_path":name,"output_artifact":name,
                   "sha256":m.artifact_digest(root,name)}
            for attempt in (1,2):
                self.assertIsNotNone(m.verified_previous_result(root,"program",{**entry,"attempt":attempt}))
            for attempt in (0,3,-1,True,False,1.0,"1",None):
                with self.subTest(attempt=attempt):
                    self.assertIsNone(m.verified_previous_result(root,"program",{**entry,"attempt":attempt}))
            self.assertIsNone(m.verified_previous_result(root,"program",entry))

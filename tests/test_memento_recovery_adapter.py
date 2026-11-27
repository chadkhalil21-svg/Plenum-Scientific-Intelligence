import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from memento_recovery_adapter import NativeRecovery
from miniswe_staged_interface import StagedInterface

class MementoRecoveryTests(unittest.TestCase):
    def test_upstream_repeated_failure_detection(self):
        r=NativeRecovery()
        hits=[]
        for turn in range(1,7):
            result,cats=r.observe({"command":'{"op":"replace","old":"x","new":"y"}'},
                {"returncode":1,"output":"No such file FileNotFoundError"},0,turn)
            hits.extend(cats)
        self.assertIn("file_not_found",hits)
        self.assertIn("infinite_retry_loop",hits)
        self.assertIn("observation_chain",hits)
        self.assertNotIn("list_dir",result["output"])
        self.assertNotIn("Install",result["output"])
    def test_productive_effects_not_a_research_loop(self):
        r=NativeRecovery()
        for turn in range(1,8):
            _,cats=r.observe({"command":json.dumps({"op":"replace","old":str(turn),"new":str(turn+1)})},
                             {"returncode":0,"output":"passed"},turn,turn)
            self.assertEqual(cats,[])
    def test_actual_staged_denials_feed_upstream_recovery(self):
        class NoShell:
            def execute(self,action):
                raise AssertionError("Unexpected shell action")
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"actions.jsonl"
            gate=StagedInterface(NoShell(),"src/plenum_ai/example.py","test_example.py",b"x=1",p)
            for _ in range(6):
                result=gate.execute({"command":"ls -la"})
            rows=[json.loads(line) for line in p.with_name("memento-recovery.jsonl").read_text().splitlines()]
            self.assertTrue(any("infinite_retry_loop" in row["diagnostics"] for row in rows))
            self.assertTrue(all(row["upstream"]=="Memento-Skills v0.4.0" for row in rows))
            self.assertEqual(gate.edits,0)

if __name__=="__main__":
    unittest.main()

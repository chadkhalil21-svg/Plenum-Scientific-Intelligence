"""Offline state-machine tests; no model, network, or hidden grader output."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from miniswe_staged_interface import StagedInterface

class Environment:
    def __init__(self):
        self.calls=[]
    def execute(self, action):
        self.calls.append(action["command"])
        return {"returncode":0,"output":"OK","exception_info":""}

class Grader:
    def __init__(self):
        self.calls=0
        self.last_was_cached=False
    def __call__(self, env):
        self.calls+=1
        self.last_was_cached=self.calls==2
        return self.calls>=3

class CandidateCycleTest(unittest.TestCase):
    def test_feedback_before_submission_and_no_repeat_grade(self):
        with tempfile.TemporaryDirectory() as folder:
            env=Environment()
            grader=Grader()
            worker=StagedInterface(env,"src/plenum_ai/example.py","test_example.py",
                                   b"x=1",Path(folder)/"actions.jsonl",grader)
            def run(op, **values):
                return worker.execute({"command":json.dumps({"op":op,**values})})
            failed=run("replace",old="x=1",new="x=2")
            self.assertEqual(failed["returncode"],1)
            self.assertIn("Independent objective acceptance failed",failed["output"])
            self.assertTrue(worker.passed)
            self.assertEqual(grader.calls,1)
            self.assertEqual(run("submit")["returncode"],1)
            self.assertEqual(grader.calls,1)
            repeated=run("replace",old="x=2",new="x=1")
            self.assertIn("Previously rejected candidate state revisited",repeated["output"])
            self.assertEqual(grader.calls,2)
            passed=run("replace",old="x=1",new="x=3")
            self.assertEqual(passed["returncode"],0)
            self.assertIn("Independent objective acceptance passed",passed["output"])
            self.assertEqual(run("submit")["returncode"],0)
            self.assertEqual(grader.calls,3)
            self.assertEqual(env.calls[-1],"echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT")

if __name__=="__main__":
    unittest.main()

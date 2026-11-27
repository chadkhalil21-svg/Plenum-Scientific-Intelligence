import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from miniswe_staged_interface import StagedInterface, EDIT_SCRIPT, staged_task

class Stub:
    def __init__(self):
        self.calls=[]
        self.regression=0
    def execute(self,action):
        command=action["command"]
        self.calls.append(command)
        code=self.regression if command.startswith("printf") else 0
        return {"returncode":code,"output":"fixed fixture","exception_info":""}

class StagedTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.env=Stub()
        self.receipt=Path(self.tmp.name)/"actions.jsonl"
        self.gate=StagedInterface(self.env,"src/plenum_ai/sample.py","test_sample.py",b"x=1\n",self.receipt)
    def action(self,**data):
        return self.gate.execute({"command":json.dumps(data)})
    def test_views_bounded_and_shell_rejected(self):
        self.assertEqual(self.gate.execute({"command":"ls -al"})["returncode"],1)
        for _ in range(2):
            self.assertEqual(self.action(op="view",start=1,end=2)["returncode"],0)
        self.assertEqual(self.action(op="view",start=1,end=2)["returncode"],1)
        self.assertEqual(len(self.env.calls),2)
    def test_submission_requires_changed_source_and_passing_regression(self):
        self.assertEqual(self.action(op="submit")["returncode"],1)
        self.env.regression=1
        self.assertEqual(self.action(op="replace",old="x=1",new="x=2")["returncode"],1)
        self.assertEqual(self.action(op="submit")["returncode"],1)
        self.env.regression=0
        self.assertEqual(self.action(op="replace",old="x=2",new="x=3")["returncode"],0)
        self.assertEqual(self.action(op="submit")["returncode"],0)
        self.assertEqual(self.env.calls[-1],"echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT")
        rows=[json.loads(line) for line in self.receipt.read_text().splitlines()]
        self.assertEqual(rows[-1]["edits"],2)
        self.assertTrue(rows[-1]["regression_passed"])
        self.assertEqual(rows[-1]["action"],"submit")
    def test_fixed_edit_script_on_trusted_fixture(self):
        p=Path(self.tmp.name)/"sample.py"
        p.write_text("x=1\nx=1\n")
        def edit(old,new):
            return subprocess.run([sys.executable,"-B","-c",EDIT_SCRIPT,str(p),json.dumps({"old":old,"new":new})],capture_output=True,timeout=5)
        self.assertNotEqual(edit("x=1","x=2").returncode,0)
        self.assertEqual(p.read_text(),"x=1\nx=1\n")
        p.write_text("x=1\n")
        self.assertNotEqual(edit("x=1","x=").returncode,0)
        self.assertEqual(p.read_text(),"x=1\n")
        self.assertEqual(edit("x=1","x=2").returncode,0)
        self.assertEqual(p.read_text(),"x=2\n")
    def test_prompt_contains_valid_json_example(self):
        self.assertIn('{"op":"submit"}',staged_task("Fix fixture",b"x=1"))
    def test_action_limit(self):
        for _ in range(12):
            self.action(op="invalid")
        self.assertEqual(self.action(op="replace",old="x=1",new="x=2")["returncode"],1)
        self.assertEqual(self.env.calls,[])

if __name__=="__main__":
    unittest.main()

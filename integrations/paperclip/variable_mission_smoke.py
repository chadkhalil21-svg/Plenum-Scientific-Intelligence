"""Offline reservation, scope and hidden-commitment checks for the variable graph."""
import json, os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import variable_mission as vm
from model_plan import MODEL, MODEL_DIGEST, digest

class TestGraph(unittest.TestCase):
    def test_variable_graph_and_no_hidden_answer_in_request(self):
        for case,chosen,count in (("science",["bibliography","stations"],5),("engineering",["thermal"],3),("commercial",["commercial"],3)):
            m=vm.fixture(case)
            select={k:k in chosen for k in m["authorized_inputs"]}
            scope,nodes=vm.graph(m,select)
            self.assertEqual(len(nodes),count)
            self.assertEqual(nodes[-1]["id"],"evidence_report")
            self.assertNotIn(digest(sorted(chosen)),json.dumps(vm.request(m)))
            self.assertEqual(set(nodes[-1]["depends_on"]),{x["id"] for x in nodes[:-1]})

    def test_unaccepted_selection_no_worker_no_replay(self):
        m=vm.fixture("engineering")
        chosen={k:k=="commercial" for k in m["authorized_inputs"]}
        reply={"model":MODEL,"done":True,"message":{"content":json.dumps(chosen)},"eval_count":45,"prompt_eval_count":200}
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ,{"GITHUB_ACTIONS":"true","PLENUM_EPHEMERAL_RUNNER":"confirmed"}):
            root=Path(tmp)
            with patch.object(vm,"check_local_model",return_value=MODEL_DIGEST+"a"*52), patch.object(vm,"read_json",return_value=reply) as model, patch.object(vm,"run_contract",side_effect=AssertionError("No unauthorized work")):
                for _ in range(2):
                    with self.assertRaisesRegex(ValueError,"commitment mismatch"):
                        vm.execute(m,root,digest(["thermal"]))
                self.assertEqual(model.call_count,1)
                self.assertFalse(list(root.glob("*.reserved.json")))

    def test_scope_rejects_private_or_unapproved(self):
        with self.assertRaises(PermissionError):
            vm.validate({"objective":"Read the private credentials now","authorized_inputs":{"commercial":True}})
        with self.assertRaises(ValueError):
            vm.validate({"objective":"Review public service status","authorized_inputs":{"shell":True}})
if __name__=="__main__":unittest.main(verbosity=2)

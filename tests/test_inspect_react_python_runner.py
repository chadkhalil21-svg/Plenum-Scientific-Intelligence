"""No-model regression: Inspect receives one typed native chat-template string."""
import unittest
from plenum_ai import inspect_react_python_runner as r
from plenum_ai.qwen3_chat_template import PATCH


class OriginalPythonInspectModelArgs(unittest.TestCase):
    def setUp(self):
        self.template="prefix"*21+PATCH+"suffix"*10
        self.path="hf/snapshots/"+r.REVISION

    def test_patched_template_is_a_single_string_not_yaml_split_list(self):
        options=r.model_args(self.path,self.template)
        self.assertIs(type(options["chat_template"]),str)
        self.assertEqual(options["chat_template"],self.template)
        self.assertIn(",",options["chat_template"])
        self.assertEqual(options["device"],"cpu")
        self.assertIs(options["enable_thinking"],False)

    def test_real_upstream_api_receives_typed_dictionary_and_hard_bounds(self):
        observed={}
        def fake_eval(task,**kwargs):
            observed["task"]=task;observed["kwargs"]=kwargs
            return [object()]
        self.assertEqual(len(r.arguments(fake_eval,self.path,self.template)),1)
        self.assertEqual(observed["task"],r.TASK)
        cfg=observed["kwargs"]["model_args"]
        self.assertIsInstance(cfg["chat_template"],str)
        self.assertEqual(observed["kwargs"]["turn_limit"],6)
        self.assertEqual(observed["kwargs"]["message_limit"],14)
        self.assertEqual(observed["kwargs"]["max_tokens"],256)
        self.assertEqual(observed["kwargs"]["max_sandboxes"],1)
        self.assertEqual(observed["kwargs"]["limit"],1)
        self.assertEqual(observed["kwargs"]["model"],"hf/local")

    def test_invalid_model_or_serialization_rejected(self):
        for source in ("","../../../private","HF/Other/model","Qwen3-1.7B"):
            with self.subTest(source=source),self.assertRaises(ValueError):
                r.model_args(source,self.template)
        with self.assertRaises(ValueError):
            r.model_args(self.path,[self.template])
        with self.assertRaises(ValueError):
            r.model_args(self.path,"raw template"*30)

    def test_plan_cannot_claim_inference_or_agi(self):
        p=r.plan()
        self.assertFalse(p["actual_model_inference_executed"])
        self.assertFalse(p["original_functional_grade_verified"])
        self.assertFalse(p["AGI_demonstrated"])
        self.assertEqual(p["model_calls"],0)
        self.assertEqual(p["paid_api_calls"],0)


if __name__=="__main__":
    unittest.main()

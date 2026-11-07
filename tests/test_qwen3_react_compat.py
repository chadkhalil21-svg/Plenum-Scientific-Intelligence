"""No model inference: patch only exact Qwen tool-call bug, reject drift."""
import unittest
from plenum_ai import qwen3_chat_template as t,react_original_failure as r

ORIGIN="""
{%- for tool_call in message.tool_calls %}
<tool_call>
{%- if tool_call.function %}
{%- set tool_call = tool_call.function %}
{%- endif %}
{{ tool_call.name }}
{{ tool_call.arguments | tojson }}
</tool_call>
{%- endfor %}
""" + "pad"*30

class OriginalAgentCompatibilityTests(unittest.TestCase):
    def test_patches_exact_one_original_branch_without_changing_other_text(self):
        patched=t.patch_template(ORIGIN)
        self.assertIn("tool_call.function is string",patched)
        self.assertIn("tool_call.function is mapping",patched)
        self.assertIn("<tool_call>",patched)
        self.assertNotEqual(patched,ORIGIN)
        self.assertEqual(patched.count("tool_call.function is string"),1)
    def test_real_flat_and_nested_function_shape_renders(self):
        try:
            from jinja2 import Environment
        except ModuleNotFoundError:
            self.skipTest('Jinja2 optional; real original tokenizer CI validates both tool shapes')
        patch=t.patch_template(ORIGIN)
        for function,arguments in [
                ("python",{"code":"print(2+2)"}),
                ({"name":"python","arguments":{"code":"print(2+2)"}},None)]:
            item={"function":function}
            if arguments:item["arguments"]=arguments
            rendered=Environment().from_string(patch).render(message={"tool_calls":[item]})
            self.assertIn("python",rendered)
            self.assertIn("print(2+2)",rendered)
            self.assertNotIn("Undefined",rendered)
    def test_malformed_or_drifting_template_fails(self):
        with self.assertRaises(ValueError):t.patch_template("too small")
        with self.assertRaisesRegex(ValueError,"exactly once"):
            t.patch_template(ORIGIN+ORIGIN)
        with self.assertRaisesRegex(ValueError,"Unrecognized"):
            t.patch_template(ORIGIN.replace("<tool_call>","<other-tag>"))
    def test_safe_plans_have_zero_calls_and_no_agi(self):
        self.assertEqual(t.plan()["local_model_calls"],0)
        self.assertFalse(t.plan()["AGI_demonstrated"])
        self.assertFalse(r.plan()["original_log_reviewed"])
        self.assertFalse(r.plan()["independent_functional_grade_available"])
    def test_source_audit_fails_before_reading_unreviewed_runtime(self):
        from unittest.mock import patch
        with patch("importlib.metadata.version",return_value="fake"):
            with self.assertRaisesRegex(RuntimeError,"Unreviewed"):
                r.audit("reports/inspect-react-failed-original")


if __name__=="__main__":
    unittest.main()

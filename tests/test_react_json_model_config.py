"""No-model regression for JSON config preserving complete Jinja as one scalar."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from plenum_ai import react_json_model_config as cfg
from plenum_ai import qwen3_chat_template as templ


SOURCE="""{%- for tool_call in message.tool_calls %}
<tool_call>
{%- if tool_call.function %}
{%- set tool_call = tool_call.function %}
{%- endif %}
{{ tool_call.name }}
{{ tool_call.arguments | tojson }}
</tool_call>
{%- endfor %}
"""+"pad"*45


class QwenNativeModelConfigTests(unittest.TestCase):
    def test_exact_template_remains_single_json_string_with_commas(self):
        corrected=templ.patch_template(SOURCE)
        self.assertIn("arguments",corrected)
        self.assertIn("'",corrected)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            frozen=root/cfg.REVISION
            frozen.mkdir()
            out=root/"model.json"
            with patch.object(cfg,"CONFIG_NAME",str(out)):
                record=cfg.make(str(frozen),SOURCE,corrected,str(out))
            read=json.loads(out.read_text())
            self.assertIs(type(read["chat_template"]),str)
            self.assertEqual(read["chat_template"],corrected)
            self.assertEqual(set(read),{"model_path","device","do_sample",
                                        "enable_thinking","chat_template"})
            self.assertFalse(read["do_sample"])
            self.assertFalse(read["enable_thinking"])
            self.assertEqual(record["model_inference_calls"],0)
            self.assertEqual(record["external_paid_model_apis"],0)
            self.assertFalse(record["AGI_demonstrated"])

    def test_misidentified_checkpoint_and_other_template_rejected(self):
        corrected=templ.patch_template(SOURCE)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            frozen=root/cfg.REVISION
            frozen.mkdir()
            bad=root/"unknown"
            bad.mkdir()
            with self.assertRaisesRegex(ValueError,"Frozen"):
                cfg.checked_config(str(bad),SOURCE,corrected)
            with self.assertRaisesRegex(ValueError,"does not exactly match"):
                cfg.checked_config(str(frozen),SOURCE,corrected+"changed")
            with self.assertRaisesRegex(ValueError,"reviewed"):
                cfg.make(str(frozen),SOURCE,corrected,str(root/"wrong.json"))


if __name__=="__main__":
    unittest.main()

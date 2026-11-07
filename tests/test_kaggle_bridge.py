"""Offline verification; no Kaggle auth or network used."""
import importlib.util
import io
import json
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
import unittest
from unittest.mock import patch

BASE=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("kaggle_bridge",BASE/"scripts/kaggle_bridge.py")
bridge=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bridge)

class KaggleBridgeTests(unittest.TestCase):
    def test_safe_source_and_private_metadata(self):
        notebook=bridge.safe_notebook()
        self.assertEqual(notebook["nbformat"],4)
        meta=bridge.metadata("someowner/plenum-prometheus-qwen-trial")
        self.assertTrue(meta["is_private"])
        self.assertTrue(meta["enable_gpu"])
        self.assertEqual(meta["machine_shape"],"NvidiaTeslaT4")
        self.assertEqual(meta["code_file"],"prometheus_kaggle_qwen36_27b.ipynb")

    def test_guards_against_unrelated_notebook_writes(self):
        for value in ["alice/another-notebook","https://kaggle.com/code/test",
                      "../../anything","alice/my notebook","alice/abc;rm -rf /"]:
            with self.assertRaises((ValueError,PermissionError)):
                bridge.check_ref(value,for_write=True)

    def test_no_auth_fails_closed(self):
        with patch.dict("os.environ",{},clear=True):
            with self.assertRaises(PermissionError):
                bridge.sdk(["kernels","list","-m"])
        with self.assertRaises(ValueError):
            bridge.sdk(["datasets","delete","example"])

    def test_offline_only_checks_format(self):
        result=io.StringIO()
        with patch.object(bridge,"sdk",side_effect=AssertionError("Called live CLI")):
            with redirect_stdout(result):
                bridge.run("offline")
        self.assertIn("no Kaggle network",result.getvalue())

    def test_auth_call_not_logged_or_shell_executed(self):
        from unittest.mock import Mock
        mock=Mock(returncode=0,stdout="SENSITIVE PRIVATE KERNEL NAME",stderr="")
        with patch.dict("os.environ",{"KAGGLE_API_TOKEN":"do-not-print"},clear=True):
            with patch.object(bridge.subprocess,"run",return_value=mock) as spawned:
                buf=io.StringIO()
                with redirect_stdout(buf):
                    bridge.run("list")
        self.assertNotIn("SENSITIVE",buf.getvalue())
        self.assertNotIn("do-not-print",buf.getvalue())
        kwargs=spawned.call_args.kwargs
        self.assertFalse(kwargs.get("shell",False))

    def test_push_uses_no_run_and_fixed_slug(self):
        calls=[]
        def fake_kaggle(args):
            calls.append(args)
            return ""
        with patch.object(bridge,"sdk",side_effect=fake_kaggle):
            bridge.run("write-draft","owner/plenum-prometheus-qwen-trial")
        self.assertEqual(calls[0][:2],["kernels","push"])
        self.assertIn("--no-run",calls[0])

if __name__=="__main__":unittest.main()

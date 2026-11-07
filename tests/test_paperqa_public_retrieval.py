"""Offline PaperQA2 pilot: no proprietary inputs, providers or source rewriting."""
import unittest
from unittest.mock import patch
from plenum_ai import paperqa_public_retrieval as p

class PublicPaperQAPilotTests(unittest.TestCase):
    def test_plan_is_read_only_and_limited(self):
        x=p.plan()
        self.assertEqual(x["model_calls"],0)
        self.assertEqual(x["paid_api_calls"],0)
        self.assertFalse(x["private_documents"])
        self.assertFalse(x["AGI_demonstrated"])
        self.assertFalse(x["inference_executed"])
        self.assertEqual(len(x["documents"]),2)
        self.assertEqual(len(x["queries"]),2)
    def test_only_preexisting_public_documents(self):
        for name,path,citation in p.DOCUMENTS:
            self.assertTrue(path.startswith("docs/"))
            self.assertIn("public",citation)
            self.assertTrue((p.ROOT/path).is_file())
    def test_original_source_is_never_an_inference_prompt(self):
        with patch("importlib.metadata.version",side_effect=AssertionError("Unexpected dependency access")):
            self.assertFalse(p.plan()["retrieval_verified"])
    def test_unreviewed_paperqa_fails_closed(self):
        with patch("importlib.metadata.version",return_value="bad"):
            with self.assertRaisesRegex(RuntimeError,"Unreviewed"):
                p.run()
    def test_network_is_prohibited(self):
        with self.assertRaisesRegex(RuntimeError,"Network access forbidden"):
            p._blocked_connect()

if __name__=="__main__":
    unittest.main()

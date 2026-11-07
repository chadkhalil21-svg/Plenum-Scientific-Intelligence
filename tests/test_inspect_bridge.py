"""No external dependency, network, LLM or secrets required for default tests."""
import unittest
from unittest.mock import patch
from plenum_ai import inspect_bridge as b

class UpstreamInspectReuse(unittest.TestCase):
    def test_default_is_nonexecuting(self):
        p=b.plan()
        self.assertFalse(p["execution_authorized"])
        self.assertEqual(p["model_calls"],0)
        self.assertEqual(p["external_api_calls"],0)
        self.assertFalse(p["AGI_demonstrated"])

    def test_samples_include_real_positive_and_negative(self):
        self.assertEqual(len(b.ROWS),2)
        self.assertEqual(len({x["id"] for x in b.ROWS}),2)
        self.assertEqual(sum(x["reply"]==x["target"] for x in b.ROWS),1)

    def test_unknown_inspect_version_refused_before_imports(self):
        with patch("importlib.metadata.version",return_value="unreviewed"):
            with self.assertRaisesRegex(RuntimeError,"Unreviewed"):
                b.smoke()

if __name__=="__main__":
    unittest.main()

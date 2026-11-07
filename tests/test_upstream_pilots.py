"""Guard opt-in SDK checks from surprise model, API or workspace execution."""
import unittest
from unittest.mock import patch
from plenum_ai import upstream_pilots as u

class ReuseFirstTests(unittest.TestCase):
    def test_plan_nonexecuting_for_every_sdk(self):
        for name in u.VERSIONS:
            with self.subTest(name=name):
                p=u.plan(name)
                self.assertEqual(p["model_calls"],0)
                self.assertEqual(p["external_api_calls"],0)
                for field in ("api_import_verified","agent_executed",
                              "documents_indexed","deployment","AGI_demonstrated"):
                    self.assertFalse(p[field])

    def test_unsupported_upstream_rejected(self):
        for name in ("../bad","other","", "local-shell"):
            with self.assertRaises(ValueError):
                u.plan(name)

    def test_modified_version_refused_before_import(self):
        with patch("importlib.metadata.version",return_value="different"):
            for name in u.VERSIONS:
                with self.subTest(name=name),self.assertRaisesRegex(RuntimeError,"Unreviewed"):
                    u.inspect_upstream(name)

    def test_plan_does_not_load_third_party_dependencies(self):
        with patch("importlib.metadata.version",side_effect=AssertionError("Unexpected SDK import")):
            for name in u.VERSIONS:
                self.assertFalse(u.plan(name)["api_import_verified"])

if __name__=="__main__":
    unittest.main()

import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / (
    "integrations/upstream/fermilink-maxwelllink/run_tls.py"
)

class FermiLinkBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), "guarded TLS adapter missing")
        spec = importlib.util.spec_from_file_location("fermilink_tls", SCRIPT)
        self.adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.adapter)

    def test_unapproved_source_never_executes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            marker = root / "executed"
            (root / "em.py").write_text("from pathlib import Path\nPath(" + repr(str(marker)) + ").touch()\n")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                self.adapter.validated_inputs(root)
            self.assertFalse(marker.exists())

    def test_symlink_input_denied(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "elsewhere").write_text("anything")
            (root / "em.py").symlink_to(root / "elsewhere")
            with self.assertRaisesRegex(ValueError, "symlink"):
                self.adapter.validated_inputs(root)

if __name__ == "__main__":
    unittest.main()

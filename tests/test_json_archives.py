"""Independent guard against accidental invalid literal backslash-n in JSON artifacts."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
class JsonArchiveTests(unittest.TestCase):
    def test_json_artifact_writes_use_real_newline(self):
        broken='+"' + '\\'*2 + 'n")'
        valid='+"' + '\\' + 'n")'
        for path in ('.github/workflows/world-horizon.yml',
                     '.github/workflows/pyscf-reference.yml'):
            with self.subTest(path=path):
                s=(ROOT/path).read_text()
                self.assertNotIn(broken,s)
                self.assertIn(valid,s)
                self.assertIn("json.loads(",s)

if __name__=="__main__":
    unittest.main()

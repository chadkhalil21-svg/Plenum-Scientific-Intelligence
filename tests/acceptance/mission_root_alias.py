"""Independent acceptance of original owner mission 1040; never mounted in agent workspace."""
import tempfile
import unittest
from pathlib import Path

from plenum_ai import mission_checkpoint as c

ARGS = dict(issue=1040, objective="Public source repair", team=("research",))
RESULTS = {"research": {"attempt": 1}}

class MissionRootAcceptance(unittest.TestCase):
    def test_valid_nested_root_and_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "new" / "mission"
            self.assertEqual(c.load_checkpoint(root, **ARGS), {})
            c.save_checkpoint(root, **ARGS, results=RESULTS)
            self.assertEqual(c.load_checkpoint(root, **ARGS), RESULTS)
            item = root / "workers/research/output.txt"
            item.parent.mkdir(parents=True)
            item.write_text("public result", encoding="utf-8")
            self.assertIsNotNone(c.artifact_digest(root, "workers/research/output.txt"))
            self.assertIsNotNone(c.artifact_digest(root, "workers/research"))
            self.assertEqual(c.checkpoint_path(root, 1040).name, "chief-checkpoint-1040.json")

    def test_aliases_rejected_without_reading_or_writing_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            real = base / "actual"
            root = real / "mission"
            c.save_checkpoint(root, **ARGS, results=RESULTS)
            item = root / "workers/research/output.txt"
            item.parent.mkdir(parents=True)
            item.write_text("valid public result", encoding="utf-8")
            original = c.checkpoint_path(root, 1040).read_bytes()
            direct = base / "alias-root"
            direct.symlink_to(root, target_is_directory=True)
            ancestor = base / "alias-parent"
            ancestor.symlink_to(real, target_is_directory=True)
            dangling = base / "dangling"
            dangling.symlink_to(base / "absent", target_is_directory=True)
            for alias in (direct, ancestor / "mission", ancestor / "new", dangling, dangling / "child"):
                with self.subTest(alias=alias):
                    with self.assertRaises(ValueError):
                        c.load_checkpoint(alias, **ARGS)
                    with self.assertRaises(ValueError):
                        c.save_checkpoint(alias, **ARGS, results={})
                    self.assertIsNone(c.artifact_digest(alias, "workers/research/output.txt"))
                    self.assertEqual(c.checkpoint_path(root, 1040).read_bytes(), original)
            self.assertFalse((real / "new").exists())
            self.assertFalse((base / "absent").exists())
            self.assertEqual(c.load_checkpoint(root, **ARGS), RESULTS)

if __name__ == "__main__":
    unittest.main()

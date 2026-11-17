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

    def test_robin_pair_schedule_is_reproducible_unique_and_bounded(self):
        import random
        before = random.getstate()
        p = u.robin_pair_schedule(4, 6)
        self.assertEqual(set(map(tuple, p["pairs"])), {(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)})
        self.assertEqual(p, u.robin_pair_schedule(4, 6))
        self.assertEqual(random.getstate(), before)
        self.assertEqual(p["model_calls"], 0)
        self.assertFalse(p["agent_executed"])
        for n, games in ((1, 1), (33, 1), (2, 0), (2, 2), (True, 1)):
            with self.subTest(n=n, games=games), self.assertRaises(ValueError):
                u.robin_pair_schedule(n, games)

    def test_scienceclaw_sequence_rejects_untrusted_input_before_import(self):
        for sequence in ("", "../secret", "ACGTN", "ACGT" * 2501, 2):
            with self.subTest(sequence=str(sequence)[:10]), self.assertRaises(ValueError):
                u.scienceclaw_dna_statistics(sequence)

    def test_scienceclaw_statistic_from_optional_upstream(self):
        import importlib.util
        if importlib.util.find_spec("Bio") is None:
            self.skipTest("optional Biopython integration not installed")
        p = u.scienceclaw_dna_statistics("ACGCGTAA")
        self.assertEqual(p["statistics"]["composition"], {"A": 3, "T": 1, "C": 2, "G": 2})
        self.assertEqual(p["statistics"]["gc_content"], 50.0)
        self.assertEqual(p["statistics"]["length"], 8)
        self.assertEqual(p["model_calls"], 0)
        self.assertFalse(p["agent_executed"])
        self.assertFalse(p["scientific_discovery_verified"])

    def test_report_cli_refuses_symlink_escape_and_does_not_mutate_hardlinks(self):
        import os
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as work, tempfile.TemporaryDirectory() as external:
            original_cwd = os.getcwd()
            try:
                os.chdir(work)
                outside = Path(external) / "untouched.json"
                outside.write_text("private sentinel", encoding="utf-8")
                def run(path):
                    args = ["upstream_pilots", "--provider", "robin",
                            "--hypotheses", "4", "--games", "6", "--out", path]
                    with patch("sys.argv", args):
                        u.main()

                Path("reports").symlink_to(external, target_is_directory=True)
                with self.assertRaises((ValueError, OSError)):
                    run("reports/untouched.json")
                self.assertEqual(outside.read_text(encoding="utf-8"), "private sentinel")
                Path("reports").unlink()
                Path("reports").mkdir()

                Path("reports/nested").symlink_to(external, target_is_directory=True)
                with self.assertRaises((ValueError, OSError)):
                    run("reports/nested/untouched.json")
                Path("reports/leaf.json").symlink_to(outside)
                with self.assertRaises((ValueError, OSError)):
                    run("reports/leaf.json")
                self.assertEqual(outside.read_text(encoding="utf-8"), "private sentinel")

                os.link(outside, "reports/hard.json")
                run("reports/hard.json")
                self.assertEqual(outside.read_text(encoding="utf-8"), "private sentinel")
                self.assertTrue(Path("reports/hard.json").is_file())
                run("reports/new/nested.json")
                run("reports/new/nested.json")
                self.assertTrue(Path("reports/new/nested.json").is_file())
            finally:
                os.chdir(original_cwd)

if __name__=="__main__":
    unittest.main()

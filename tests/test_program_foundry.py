"""Program foundry must emit reviewable, syntactically valid working starters."""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

from plenum_ai.program_foundry import KINDS, generate_program

class ProgramFoundryTests(unittest.TestCase):
    def test_all_programs_have_working_tests_but_no_deployment(self):
        for kind in KINDS:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as root:
                folder=pathlib.Path(root)/kind
                result=generate_program(kind,"Public scientific creativity",folder)
                self.assertTrue(result["generated_program_has_not_been_deployed"])
                self.assertFalse(result["model_weights_self_modified"])
                self.assertTrue(result["human_code_review_required"])
                self.assertEqual(result["file_count"],3)
                for name in ("main.py","README.md","test_generated.py","manifest.json"):
                    self.assertTrue((folder/name).is_file())
                done=subprocess.run(
                    [sys.executable,"-m","unittest","discover","-s",".",
                     "-p","test_generated.py","-v"],
                    cwd=folder,capture_output=True,text=True,timeout=8,
                )
                self.assertEqual(done.returncode,0,done.stderr[-1200:])

    def test_path_and_topics_are_restricted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)
            with self.assertRaises(ValueError):
                generate_program("unknown","public design",root/"x")
            with self.assertRaises(ValueError):
                generate_program("research_cli","x; rm -rf /",root/"y")
            generate_program("research_cli","Public research",root/"z")
            with self.assertRaises(FileExistsError):
                generate_program("research_cli","Public research",root/"z")

if __name__=="__main__":
    unittest.main()

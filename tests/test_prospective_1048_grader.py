"""Offline regression for the original #1048 independent grader, no inference."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from verify_original_openhands_candidate import completed_task_acceptance

class FrozenAcceptanceTests(unittest.TestCase):
    def test_exact_completed_suite(self):
        cases = [
            (3,0,"OK","checkpoint_hardlink_1048.py",True),
            (2,0,"OK","checkpoint_hardlink_1048.py",False),
            (3,0,"OK (skipped=1)","checkpoint_hardlink_1048.py",False),
            (3,1,"FAILED (failures=1)","checkpoint_hardlink_1048.py",False),
            (2,0,"OK","previous.py",True),
            (3,0,"OK","previous.py",False),
            (3,0,"not completed","checkpoint_hardlink_1048.py",False),
        ]
        for n,rc,tail,case,want in cases:
            with self.subTest(n=n,rc=rc,tail=tail,case=case):
                result=SimpleNamespace(returncode=rc,stderr=f"Ran {n} tests in 0.001s\n\n{tail}\n")
                self.assertEqual(completed_task_acceptance(result,case),want)

if __name__ == "__main__":
    unittest.main()

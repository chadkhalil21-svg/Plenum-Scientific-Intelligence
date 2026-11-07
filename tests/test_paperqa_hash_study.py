"""Fixed exploratory PaperQA source-retrieval comparisons are not AGI."""
import unittest
from unittest.mock import patch
from plenum_ai import paperqa_hash_study as s

class SparseDimensionStudyTests(unittest.TestCase):
    def test_offline_plan(self):
        d=s.plan()
        self.assertEqual(d["dimensions"],[256,4096])
        self.assertEqual(d["source_questions"],8)
        self.assertEqual(d["model_calls"],0)
        self.assertEqual(d["paid_api_calls"],0)
        self.assertFalse(d["results_measured"])
        self.assertFalse(d["AGI_demonstrated"])

    def test_balanced_predeclared_questions(self):
        self.assertEqual(sum(k=="battery" for _,k in s.QUESTIONS),4)
        self.assertEqual(sum(k=="noaa" for _,k in s.QUESTIONS),4)
        self.assertEqual(len({q for q,_ in s.QUESTIONS}),8)

    def test_version_drift_fails_closed(self):
        with patch("importlib.metadata.version",return_value="wrong"):
            with self.assertRaisesRegex(RuntimeError,"Unreviewed"):
                s.run()

if __name__=="__main__":
    unittest.main()

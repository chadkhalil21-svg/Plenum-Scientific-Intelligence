"""Offline tests for Qwen3-1.7B math length confound."""
import unittest
from unittest.mock import patch

from plenum_ai import qwen17_math_budget as b


class Qwen17MathTokenBudgetTests(unittest.TestCase):
    def test_pinned_model_and_no_inference_default(self):
        p=b.plan()
        self.assertEqual(p["model"],"Qwen/Qwen3-1.7B")
        self.assertEqual(p["question_count"],12)
        self.assertEqual(p["original_max_tokens"],128)
        self.assertEqual(p["retest_max_tokens"],256)
        self.assertEqual(p["paid_api_calls"],0)
        self.assertEqual(p["local_generation_calls"],0)
        self.assertFalse(p["inference_executed"])
        self.assertFalse(p["automatic_model_promotion"])
        self.assertFalse(p["AGI_demonstrated"])

    def test_original_source_is_exact_and_public(self):
        a,z=b.original_paths("ledger/evidence/paired-qwen")
        self.assertEqual(a.name,"run-42342242561.json")
        self.assertEqual(z.name,"run-42342242561-raw.zip")
        for path in ("../private","/tmp/test","a/../secret"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                b.original_paths(path)

    def test_missing_original_archive_fails_closed(self):
        with self.assertRaises(FileNotFoundError):
            b.verify_original("missing/evidence/paired-qwen")

    def test_unreviewed_inspect_fails_before_scoring(self):
        with patch("importlib.metadata.version",return_value="unreviewed"):
            with self.assertRaisesRegex(RuntimeError,"Unreviewed"):
                b.audit("reports/inspect-qwen17-math-budget-logs",
                        "ledger/evidence/paired-qwen")

    def test_reused_paired_scorer_accepts_twelve_matching_original_ids(self):
        from plenum_ai.gsm8k_token_budget import compare
        old={f"gsm8k-{i}":i==0 for i in range(12)}
        new=old.copy()
        new["gsm8k-0"]=False
        new["gsm8k-1"]=True
        prior={k:128 if k!="gsm8k-3" and k!="gsm8k-4" else 50 for k in old}
        current={k:200 for k in old}
        result=compare(old,new,prior,current,count=12)
        self.assertEqual(result["question_count"],12)
        self.assertEqual(result["baseline_correct"],1)
        self.assertEqual(result["candidate_correct"],1)
        self.assertEqual(result["improved_count"],1)
        self.assertEqual(result["regressed_count"],1)
        self.assertEqual(result["baseline_at_token_cap_count"],10)

    def test_nonbinary_or_mismatched_ids_are_rejected(self):
        from plenum_ai.gsm8k_token_budget import compare
        old={f"k{i}":True for i in range(12)}
        new=old.copy()
        times={k:128 for k in old}
        del new["k11"]
        new["wrong"]=False
        with self.assertRaisesRegex(ValueError,"matching identifiers"):
            compare(old,new,times,times,count=12)

if __name__=="__main__":
    unittest.main()

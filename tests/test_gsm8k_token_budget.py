"""No model required to validate paired native-scoring math and safety gates."""
import unittest
from unittest.mock import patch

from plenum_ai import gsm8k_token_budget as b


class BudgetAblationTests(unittest.TestCase):
    def test_default_offline(self):
        p = b.plan()
        self.assertEqual(p["model_id"],"Qwen/Qwen3-0.6B")
        self.assertEqual((p["baseline_max_tokens"],p["candidate_max_tokens"]),(128,256))
        self.assertEqual(p["question_count"],24)
        self.assertEqual(p["local_generation_calls"],0)
        self.assertEqual(p["paid_api_calls"],0)
        for key in ("inference_executed","official_scoring_verified",
                    "model_promoted","AGI_demonstrated"):
            self.assertFalse(p[key])

    def test_matched_original_grades_and_cap_group(self):
        old={f"g{i}":i%2==0 for i in range(24)}
        new=old.copy()
        new["g1"]=True
        new["g0"]=False
        before={f"g{i}":128 if i in (0,1,2) else 20 for i in range(24)}
        after={f"g{i}":30 for i in range(24)}
        data=b.compare(old,new,before,after)
        self.assertEqual(data["question_count"],24)
        self.assertEqual(data["improved_count"],1)
        self.assertEqual(data["regressed_count"],1)
        self.assertEqual(data["baseline_at_token_cap_count"],3)
        self.assertEqual(data["baseline_at_token_cap_correct"],2)
        self.assertEqual(data["candidate_correct_on_baseline_cap_group"],2)

    def test_mismatched_ids_fails(self):
        old={f"g{i}":True for i in range(24)}
        new=old.copy()
        del new["g23"]
        old_tokens={k:2 for k in old}
        with self.assertRaisesRegex(ValueError,"matching"):
            b.compare(old,new,old_tokens,old_tokens)

    def test_forged_grade_fails(self):
        old={f"g{i}":True for i in range(24)}
        new=old.copy()
        new["g0"]="C"
        times={k:10 for k in old}
        with self.assertRaisesRegex(ValueError,"Non-binary"):
            b.compare(old,new,times,times)

    def test_unreviewed_package_fails_before_inference(self):
        with patch("importlib.metadata.version",return_value="changed"):
            with self.assertRaisesRegex(RuntimeError,"Unreviewed"):
                b.audit("reports/inspect-gsm8k-budget-logs","ledger/evidence/inspect-cross-domain")


if __name__=="__main__":
    unittest.main()

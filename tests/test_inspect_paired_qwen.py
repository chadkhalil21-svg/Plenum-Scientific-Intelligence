"""Independent no-network regression checks for paired model comparison."""
import unittest
from unittest.mock import patch

from plenum_ai import inspect_paired_qwen as q

class PairedFrozenQwenTests(unittest.TestCase):
    def test_plan_makes_zero_model_calls(self):
        p=q.plan()
        self.assertEqual(p["total_matched_cases"],48)
        self.assertEqual(p["samples_per_task"],12)
        self.assertEqual(len(p["tasks"]),4)
        self.assertEqual(p["model_calls"],0)
        self.assertEqual(p["paid_api_calls"],0)
        self.assertEqual(p["reference_run_id"],"42341668858")
        for name in ("inference_executed","paired_scoring_verified","automatic_promotion","AGI_demonstrated"):
            self.assertFalse(p[name])
    def test_reference_is_pinned(self):
        self.assertEqual(q.REVISION,"70d244cc86ccca08cf5af4e1e306ecf908b1ad5e")
        self.assertEqual(q.BASELINE_COMMIT,"738e97210ff7e74bd957e06ca8b78cc14750178a")
        self.assertEqual(len(q.TASKS),4)
    def test_only_relative_baseline_sources(self):
        for path in ("../private","/tmp/reference","evidence/../private"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                q.baseline_paths(path)
        a,b=q.baseline_paths("ledger/evidence/inspect-cross-domain")
        self.assertTrue(str(a).endswith("run-42341668858.json"))
        self.assertTrue(str(b).endswith("run-42341668858-raw.zip"))
    def test_unverified_package_rejected_without_model(self):
        with patch("importlib.metadata.version",return_value="unreviewed"):
            with self.assertRaisesRegex(RuntimeError,"release changed"):
                q.audit("reports/inspect-paired-logs","ledger/evidence/inspect-cross-domain")
    def test_matched_scoring_records_improvements_and_regressions(self):
        past = {task:{f"{task}-{i}":i%2==0 for i in range(12)}
                for task in q.TASKS}
        now = {task:grades.copy() for task,grades in past.items()}
        for task in q.TASKS:
            now[task][f"{task}-0"] = False
            now[task][f"{task}-1"] = True
        result=q.compare_matched(past,now)
        for task in q.TASKS:
            row=result[task]
            self.assertEqual(row["reference_correct"],6)
            self.assertEqual(row["candidate_correct"],6)
            self.assertEqual(row["candidate_minus_reference"],0)
            self.assertEqual(row["paired_improved"],1)
            self.assertEqual(row["paired_regressed"],1)
            self.assertEqual(row["attempted"],12)

    def test_mismatched_ids_and_unapproved_grades_fail_closed(self):
        past = {task:{f"{task}-{i}":i%2==0 for i in range(12)}
                for task in q.TASKS}
        now = {task:grades.copy() for task,grades in past.items()}
        del now["gsm8k"]["gsm8k-0"]
        now["gsm8k"]["different"] = True
        with self.assertRaisesRegex(ValueError,"example IDs"):
            q.compare_matched(past,now)
        now["gsm8k"] = past["gsm8k"].copy()
        now["gsm8k"]["gsm8k-0"] = "C"
        with self.assertRaisesRegex(ValueError,"grades"):
            q.compare_matched(past,now)

    def test_original_log_completion_order_is_not_dataset_subset(self):
        # Model completions arrive out of order; the same fixed questions
        # must be selected by exact IDs without a second inference run.
        original={f"q{i}":i%2==0 for i in range(24)}
        candidate={f"q{i}":i%2==1 for i in (11,0,8,4,3,7,1,5,6,2,10,9)}
        subset=q.select_matching_reference(original,candidate)
        self.assertEqual(list(subset),list(candidate))
        self.assertEqual(set(subset),set(candidate))
        self.assertEqual(subset["q0"],True)
        self.assertEqual(subset["q11"],False)

    def test_missing_candidate_id_fails_closed(self):
        original={f"q{i}":True for i in range(24)}
        candidate={f"q{i}":True for i in range(11)}
        candidate["tampered"]=True
        with self.assertRaisesRegex(ValueError,"exact original IDs"):
            q.select_matching_reference(original,candidate)

    def test_original_question_contracts_must_match(self):
        from types import SimpleNamespace
        x=SimpleNamespace(
            samples=[
                SimpleNamespace(id="s0",input="Why?",target="A",choices=("A","B")),
                SimpleNamespace(id="s1",input="How?",target="B",choices=("A","B")),
            ])
        y=SimpleNamespace(
            samples=[
                SimpleNamespace(id="s0",input="Why?",target="A",choices=("A","B")),
                SimpleNamespace(id="s1",input="How?",target="C",choices=("A","B")),
            ])
        self.assertNotEqual(q.question_contract(x),q.question_contract(y))
        y.samples[1].target="B"
        self.assertEqual(q.question_contract(x),q.question_contract(y))

    def test_no_reference_data_fails_closed(self):
        with self.assertRaises(FileNotFoundError):
            q.verify_reference("does-not-exist/inspect-cross-domain")

if __name__=="__main__":
    unittest.main()

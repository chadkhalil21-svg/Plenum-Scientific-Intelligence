"""Pure offline, no-LLM checks for three-case independent original coding comparison."""
import unittest
from unittest.mock import patch

from plenum_ai import inspect_react_three as s


class MatchedReActCodingTests(unittest.TestCase):
    def test_plan_is_bounded_zero_inference(self):
        p=s.plan()
        self.assertEqual(p["expected_original_questions"],3)
        self.assertEqual(p["max_turns_per_task"],6)
        self.assertEqual(p["max_messages_per_task"],14)
        self.assertEqual(p["max_output_tokens_per_turn"],256)
        self.assertEqual(p["model"],"Qwen/Qwen3-1.7B")
        self.assertEqual(p["baseline_run_id"],"42346922772")
        self.assertEqual(p["already_verified_single_agent_run_id"],"42349665865")
        self.assertEqual(p["local_generation_calls"],0)
        self.assertEqual(p["paid_api_calls"],0)
        for k in ("original_inference_executed","original_scorer_verified",
                  "paired_original_questions_verified",
                  "automatic_model_promotion","AGI_demonstrated"):
            self.assertFalse(p[k])

    def test_paired_per_problem_gain_loss_and_genuine_tool_counts(self):
        old={f"HumanEval/{i}":{"correct":i!=1,"contract":f"sha-{i}"}
             for i in range(3)}
        now={f"HumanEval/{i}":{"correct":i!=2,"contract":f"sha-{i}",
                              "tool_calls":i+1,"tool_responses":i+1}
             for i in range(3)}
        report=s.original_and_candidate_rows(old,now)
        self.assertEqual(report["attempted"],3)
        self.assertEqual(report["one_shot_correct"],2)
        self.assertEqual(report["react_correct"],2)
        self.assertEqual(report["original_cases_repaired"],1)
        self.assertEqual(report["original_cases_regressed"],1)
        self.assertEqual(report["actual_tool_calls"],6)
        self.assertEqual(report["actual_tool_responses"],6)

    def test_changed_task_ids_or_targets_are_rejected(self):
        old={f"HumanEval/{i}":{"correct":True,"contract":f"hash{i}"} for i in range(3)}
        now={k:{"correct":True,"contract":v["contract"],
                "tool_calls":1,"tool_responses":1} for k,v in old.items()}
        now["HumanEval/1"]["contract"]="tampered"
        with self.assertRaisesRegex(ValueError,"prompt"):
            s.original_and_candidate_rows(old,now)
        now["HumanEval/1"]["contract"]="hash1"
        now["HumanEval/1"]["tool_responses"]=2
        with self.assertRaisesRegex(ValueError,"Unpaired"):
            s.original_and_candidate_rows(old,now)
        del now["HumanEval/2"]
        with self.assertRaisesRegex(ValueError,"question IDs"):
            s.original_and_candidate_rows(old,now)

    def test_wrong_grade_and_negative_tool_counts_fail_closed(self):
        old={f"HumanEval/{i}":{"correct":True,"contract":f"h{i}"} for i in range(3)}
        now={k:{"correct":True,"contract":v["contract"],
                "tool_calls":0,"tool_responses":0} for k,v in old.items()}
        now["HumanEval/2"]["correct"]="C"
        with self.assertRaisesRegex(ValueError,"grade"):
            s.original_and_candidate_rows(old,now)
        now["HumanEval/2"]["correct"]=True
        now["HumanEval/2"]["tool_calls"]=-1
        with self.assertRaisesRegex(ValueError,"tool transcript"):
            s.original_and_candidate_rows(old,now)

    def test_original_archive_must_exist_and_be_relative(self):
        a,b=s.original_paths("ledger/evidence/inspect-original-coding")
        self.assertEqual(a.name,"run-42346922772.json")
        self.assertEqual(b.name,"run-42346922772-raw.zip")
        for item in ("../secret","a/../bad","/tmp/x"):
            with self.subTest(item=item),self.assertRaises(ValueError):
                s.original_paths(item)
        with self.assertRaises(FileNotFoundError):
            s.verify_original_evidence("nothing/there")

    def test_unreviewed_original_scoring_package_rejected(self):
        with patch("importlib.metadata.version",return_value="unapproved"):
            with self.assertRaisesRegex(RuntimeError,"Unreviewed"):
                s.audit("reports/inspect-react-three-logs",
                        "ledger/evidence/inspect-original-coding")


if __name__=="__main__":
    unittest.main()

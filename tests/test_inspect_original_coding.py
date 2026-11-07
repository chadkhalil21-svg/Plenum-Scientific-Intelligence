"""No-network tests of real upstream-coding audit schema, score/ID checks."""
import sys
import types
from types import SimpleNamespace
from unittest.mock import patch
import unittest
from plenum_ai import inspect_original_coding as c


def fake_record(i,score):
    return SimpleNamespace(
        id=f"HumanEval/{i}",input="def f():\n    pass",
        target="    return 7",metadata={"test":"assert f()==7"},
        output=SimpleNamespace(completion="def f():\n    return 7"),
        scores={"verify":SimpleNamespace(value=score)}
    )


class OriginalCodingTests(unittest.TestCase):
    def test_default_never_generates_or_runs_code(self):
        p=c.plan()
        self.assertEqual(p["official_task"],"inspect_evals/humaneval")
        self.assertEqual(p["official_dataset_revision"],
                         "7dce6050a7d6d172f3cc5c32aa97f52fa1a2e544")
        self.assertEqual(p["expected_original_problems"],3)
        self.assertEqual(p["epochs"],1)
        self.assertEqual(p["maximum_output_tokens"],256)
        self.assertEqual(p["sandbox"],"docker")
        self.assertTrue(p["default_container_network_disabled"])
        self.assertEqual(p["paid_api_calls"],0)
        for name in ("inference_executed","model_generated_code_executed",
                     "independent_function_tests_executed","original_scoring_verified",
                     "automatic_model_promotion","AGI_demonstrated"):
            self.assertFalse(p[name])

    def test_read_independent_original_scores_without_optional_dependency(self):
        fake=types.ModuleType("inspect_ai.scorer")
        fake.CORRECT="C"; fake.INCORRECT="I"
        with patch.dict(sys.modules,{"inspect_ai":types.ModuleType("inspect_ai"),
                                     "inspect_ai.scorer":fake}):
            rows=c._score_rows([fake_record(0,"C"),fake_record(1,"I"),
                                fake_record(2,"C")])
        self.assertEqual([x["correct"] for x in rows],[True,False,True])
        self.assertEqual(len(rows),3)
        self.assertEqual(len(rows[0]["question_and_original_test_sha256"]),64)

    def test_missing_original_test_score_and_duplicate_rejected(self):
        fake=types.ModuleType("inspect_ai.scorer")
        fake.CORRECT="C"; fake.INCORRECT="I"
        xs=[fake_record(i,"C") for i in range(3)]
        with patch.dict(sys.modules,{"inspect_ai":types.ModuleType("inspect_ai"),
                                     "inspect_ai.scorer":fake}):
            xs[0].metadata={}
            with self.assertRaisesRegex(ValueError,"Original source"):
                c._score_rows(xs)
            xs[0]=fake_record(0,"C")
            xs[1].scores={}
            with self.assertRaisesRegex(ValueError,"grade missing"):
                c._score_rows(xs)
            xs[1]=fake_record(0,"C")
            with self.assertRaisesRegex(ValueError,"duplicate"):
                c._score_rows(xs)

    def test_version_gate_fails_without_model_or_sandbox(self):
        with patch("importlib.metadata.version",return_value="unreviewed"):
            with self.assertRaisesRegex(RuntimeError,"not approved"):
                c.audit("reports/inspect-original-coding-logs")


if __name__=="__main__":
    unittest.main()

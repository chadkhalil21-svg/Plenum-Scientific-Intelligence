"""Offline tests for AGI Capability Laboratory. No model inference or services."""
import copy
from hashlib import sha256
import json
import math
import unittest
from plenum_ai import agi_capability_lab as lab

SEED=42329504932
QWEN="Qwen/Qwen3-1.7B"
CRITIC="HuggingFaceTB/SmolLM2-1.7B-Instruct"


def answer_for(task,seed=SEED):
    original=next(x for x in lab._cases(seed) if x["id"]==task["id"])
    gold=original["gold"]
    if task["response_type"]=="numeric_json_answer":
        return json.dumps({"answer":gold})
    if gold[0]=="affine":
        ops=[{"op":"mul","value":gold[1]},
             {"op":"add","value":gold[2]}]
    else:
        ops=[{"op":"add","value":gold[1]},
             {"op":"square"},
             {"op":"add","value":gold[2]}]
    return json.dumps({"ops":ops})


def responses(seed=SEED,wrong=None):
    tasks=lab.prepare(seed)["tasks"]
    return [answer_for(x,seed) if x["id"]!=wrong else '{"answer":0}'
            for x in tasks]


def report_for(model_id=QWEN,seed=SEED,wrong=None):
    results=iter(responses(seed,wrong))
    return lab.propose(lab.prepare(seed),model_id=model_id,
                       revision=lab.MODEL_PINS[model_id],
                       generate=lambda prompt:next(results))


class AGICapabilityLaboratoryTests(unittest.TestCase):
    def test_generates_deterministic_but_seed_fresh_tasks(self):
        a=lab.prepare(SEED)
        b=lab.prepare(SEED)
        c=lab.prepare(SEED+1)
        self.assertEqual(a,b)
        self.assertNotEqual(a["tasks"],c["tasks"])
        self.assertEqual(len(a["tasks"]),6)
        self.assertEqual(
            [x["family"] for x in a["tasks"]],
            [lab.FAMILIES[0]]*2+[lab.FAMILIES[1]]*2+[lab.FAMILIES[2]]*2)
        self.assertFalse(a["model_answer_key_exposed"])
        self.assertFalse(a["heldout_program_inputs_exposed"])

    def test_no_reference_solutions_or_hidden_program_inputs_in_model_prompts(self):
        m=lab.prepare(SEED)
        dumped=json.dumps(m)
        self.assertNotIn('"gold"',dumped)
        self.assertNotIn("hidden_inputs",dumped)
        self.assertNotIn("reference_numeric_value",dumped)
        for t in m["tasks"]:
            self.assertIn("ONLY",t["prompt"])
            self.assertNotIn("eval(",t["prompt"])

    def test_all_independently_verified_reference_answers_succeed(self):
        manifest=lab.prepare(SEED)
        q=report_for(QWEN)
        c=report_for(CRITIC)
        audit=lab.audit(manifest,{QWEN:q,CRITIC:c})
        self.assertEqual(audit["tasks_per_model"],6)
        self.assertEqual(audit["total_model_calls"],12)
        for model in (QWEN,CRITIC):
            self.assertEqual(audit["models"][model]["correct"],6)
            self.assertEqual(audit["models"][model]["valid_json_schema"],6)
            self.assertTrue(all(x["correct"] for x in audit["models"][model]["evaluations"]))
            for f in lab.FAMILIES:
                self.assertEqual(audit["models"][model]["domain_scores"][f],
                                 {"correct":2,"total":2})
        self.assertFalse(audit["AGI_demonstrated"])
        self.assertFalse(audit["model_generated_code_executed"])
        self.assertFalse(audit["auto_model_promotion"])

    def test_bad_program_fails_unseen_inputs_without_runtime_execution(self):
        manifest=lab.prepare(SEED)
        responses=iter(responses())
        def bad_gen(prompt):
            original=next(responses)
            if "Synthesize integer function" in prompt:
                return json.dumps({"ops":[{"op":"add","value":1}]})
            return original
        bad=lab.propose(manifest,model_id=QWEN,revision=lab.MODEL_PINS[QWEN],
                        generate=bad_gen)
        ref=report_for(CRITIC)
        audit=lab.audit(manifest,{QWEN:bad,CRITIC:ref})
        self.assertEqual(audit["models"][QWEN]["correct"],4)
        self.assertEqual(audit["models"][QWEN]["domain_scores"][
                         "restricted_program_synthesis"]["correct"],0)
        for x in audit["models"][QWEN]["evaluations"][-2:]:
            self.assertEqual(x["hidden_program_cases"],28)
            self.assertFalse(x["correct"])

    def test_dangerous_and_unbounded_generated_programs_rejected(self):
        cases=[
            '{"ops":[{"op":"python","value":"import os"}]}',
            '{"ops":[{"op":"add","value":1},{"op":"exec","value":3}]}',
            '{"ops":[{"op":"mul","value":101}]}',
            '{"ops":[{"op":"square","value":100}]}',
            '{"ops":[{"op":"add","value":true}]}',
            '{"ops":[]}',
            '{"ops":['+','.join('{"op":"square"}' for _ in range(7))+']}',
            "import os; os.system('echo bad')",
            '{"ops":[{"op":"mul","value":999999999999}]}'
        ]
        for response in cases:
            with self.subTest(payload=response[:28]):
                self.assertNotEqual(lab.parse_response(
                    response,"arithmetic_json_program")["status"],"valid")

    def test_numeric_schema_rejects_nonfinite_commands_and_extra_fields(self):
        for response in ("NaN",'{"answer":"123"}','{"answer":true}',
                         '{"answer":3,"shell":"run"}',
                         '{"answer":Infinity}',"3", '{"answer": 1e100}'):
            with self.subTest(response=response):
                self.assertNotEqual(
                    lab.parse_response(response,"numeric_json_answer")["status"],"valid")

    def test_interpreter_rejects_magnitude_abuse(self):
        with self.assertRaisesRegex(ValueError,"magnitude"):
            lab.interpret([{"op":"square"}]*4,999)
        with self.assertRaises(ValueError):
            lab.interpret([{"op":"add","value":2}],1001)

    def test_wrong_or_missing_model_cannot_audit(self):
        manifest=lab.prepare(SEED)
        with self.assertRaises(ValueError):
            lab.audit(manifest,{QWEN:report_for(QWEN)})
        with self.assertRaises(ValueError):
            lab.audit(manifest,{"unexpected":report_for(QWEN),CRITIC:report_for(CRITIC)})
        with self.assertRaises(ValueError):
            lab.propose(manifest,model_id=QWEN,revision="main",generate=lambda _: '{}')

    def test_altered_original_prompt_rejected_before_evaluation(self):
        manifest=lab.prepare(SEED)
        manifest["tasks"][0]["prompt"]="What is 2+2?"
        with self.assertRaisesRegex(ValueError,"Task manifest"):
            lab.propose(manifest,model_id=QWEN,revision=lab.MODEL_PINS[QWEN],
                        generate=lambda _:'{"answer":4}')
        with self.assertRaises(ValueError):
            lab.audit(manifest,{QWEN:report_for(QWEN),CRITIC:report_for(CRITIC)})

    def test_altered_response_hash_is_rejected(self):
        r=report_for(QWEN)
        r["records"][0]["response"]='{"answer":0}'
        with self.assertRaisesRegex(ValueError,"response or runtime"):
            lab.audit(lab.prepare(SEED),{QWEN:r,CRITIC:report_for(CRITIC)})

    def test_altered_model_timing_and_holdout_flags_rejected(self):
        for key,value in (("program_holdouts_evaluated",True),
                          ("model_promoted",True),("AGI_demonstrated",True)):
            report=report_for(QWEN)
            report[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                lab.audit(lab.prepare(SEED),{QWEN:report,CRITIC:report_for(CRITIC)})
        report=report_for(QWEN)
        report["records"][0]["inference_seconds"]=-1
        with self.assertRaises(ValueError):
            lab.audit(lab.prepare(SEED),{QWEN:report,CRITIC:report_for(CRITIC)})

    def test_answer_does_not_score_if_numeric_error(self):
        original=lab._cases(SEED)[2]
        task=lab._public_cases(SEED)[2]
        wrong=json.dumps({"answer":original["gold"]*1.1})
        self.assertFalse(lab._evaluate(task,wrong,SEED)["correct"])

    def test_oversize_answer_preserved_as_failure(self):
        manifest=lab.prepare(SEED)
        long_answer="x"*(lab.MAX_RESPONSE_CHARS+1)
        report=lab.propose(manifest,model_id=QWEN,revision=lab.MODEL_PINS[QWEN],
                           generate=lambda _:long_answer)
        self.assertEqual(len(report["records"]),6)
        self.assertTrue(all(x["rejected_oversized"] for x in report["records"]))
        result=lab.audit(manifest,{QWEN:report,CRITIC:report_for(CRITIC)})
        self.assertEqual(result["models"][QWEN]["correct"],0)
        self.assertEqual(result["models"][QWEN]["valid_json_schema"],0)

    def test_honest_refusal_is_scored_zero_not_fabricated(self):
        manifest=lab.prepare(SEED)
        report=lab.propose(manifest,model_id=QWEN,revision=lab.MODEL_PINS[QWEN],
                           generate=lambda _:"I do not know.")
        result=lab.audit(manifest,{QWEN:report,CRITIC:report_for(CRITIC)})
        self.assertEqual(result["models"][QWEN]["correct"],0)
        self.assertTrue(all(r["status"]=="invalid_json"
                            for r in result["models"][QWEN]["evaluations"]))

    def test_seed_restricted_and_no_secret_data(self):
        for seed in (0,-1,2**63,1.0,"1",None):
            with self.subTest(seed=seed),self.assertRaises(ValueError):
                lab.prepare(seed)
        self.assertFalse(lab.prepare(SEED)["confidential_data_used"])


if __name__=="__main__":
    unittest.main()

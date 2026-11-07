"""Offline reasoning-ablation regression tests. No model download or API."""
import copy
import json
import unittest
from plenum_ai import agi_capability_lab as tasks
from plenum_ai import reasoning_ablation as r

SEED=42333546184


def _answers():
    original=tasks._cases(SEED)
    result=[]
    for t in original:
        if t["family"]!=tasks.FAMILIES[2]:
            result.append(json.dumps({"answer":t["gold"]}))
        elif t["gold"][0]=="affine":
            result.append(json.dumps({"ops":[
                {"op":"mul","value":t["gold"][1]},
                {"op":"add","value":t["gold"][2]}]}))
        else:
            result.append(json.dumps({"ops":[
                {"op":"add","value":t["gold"][1]},
                {"op":"square"},
                {"op":"add","value":t["gold"][2]}]}))
    return result


def _report(model, fence=False):
    a=_answers()
    def generating(_prompt):
        s=a.pop(0)
        if not a:
            a.extend(_answers())
        return "```json\n"+s+"\n```" if fence else s
    source=(model if model==r.QWEN_17 else r.GGUF_REPO)
    revision=(r.MODEL_REVISIONS[model] if model==r.QWEN_17 else r.GGUF_REVISION)
    return r.propose(r.prepare(SEED),model,generating,{
        "engine":"mock","model_source":source,"weights_revision":revision})


class ReasoningMethodAblationTests(unittest.TestCase):
    def test_protocol_model_and_quantized_revision_are_frozen(self):
        p=r.protocol()
        self.assertEqual(p["quantized_4b"]["file"],r.GGUF_FILE)
        self.assertEqual(p["quantized_4b"]["revision"],r.GGUF_REVISION)
        self.assertEqual(p["schema"],r.SCHEMA)
        self.assertEqual(tuple(x["key"] for x in p["prompt_conditions"]),r.MODES)

    def test_new_seed_question_manifest_no_answers(self):
        p=r.prepare(SEED)
        self.assertEqual(len(p["task_manifest"]["tasks"]),6)
        self.assertEqual(p["question_count"],6)
        self.assertFalse(p["answer_key_exposed"])
        self.assertNotIn('"gold"',json.dumps(p))
        self.assertNotEqual(p["task_manifest"],r.prepare(SEED+1)["task_manifest"])

    def test_condition_prompts_have_no_fewshot_math_answers(self):
        t=r.prepare(SEED)["task_manifest"]["tasks"][0]
        self.assertEqual(r.prompt_for(t,"baseline"),t["prompt"])
        coached=r.prompt_for(t,"verify")
        self.assertTrue(coached.startswith(t["prompt"]))
        self.assertIn("check the arithmetic",coached)
        with self.assertRaises(ValueError):r.prompt_for(t,"unverified")

    def test_mock_independent_scorer_recovers_both_models(self):
        p=r.prepare(SEED)
        score=r.audit(p,{r.QWEN_17:_report(r.QWEN_17),
                         r.QWEN_4:_report(r.QWEN_4)})
        for x in score["models"].values():
            self.assertEqual(x["total_model_calls"],12)
            for mode in r.MODES:
                self.assertEqual(x["conditions"][mode]["normalized_correct"],6)
                self.assertEqual(x["conditions"][mode]["strict_correct"],6)
                self.assertEqual(x["conditions"][mode]["normalized_schema_valid"],6)
        self.assertTrue(score["independent_deterministic_scoring"])
        self.assertFalse(score["automatic_model_promotion"])
        self.assertFalse(score["AGI_demonstrated"])

    def test_fenced_json_is_format_improvement_not_new_reasoning(self):
        a=r.audit(r.prepare(SEED),{r.QWEN_17:_report(r.QWEN_17),
                   r.QWEN_4:_report(r.QWEN_4,fence=True)})
        case=a["models"][r.QWEN_4]["conditions"]["verify"]
        self.assertEqual(case["strict_schema_valid"],0)
        self.assertEqual(case["normalized_schema_valid"],6)
        self.assertEqual(case["strict_correct"],0)
        self.assertEqual(case["normalized_correct"],6)
        self.assertEqual(case["tasks"][0]["format_normalization"],"entire_response_fenced_json")

    def test_refuses_ambiguous_or_unsafe_final_output(self):
        examples=[
          '```json\n{"answer":2}\n```\n{"answer":3}',
          'This is 4. {"answer":4}',
          '{"answer":2} {"answer":3}',
          'python -c "print(2)"',
          '{"answer": NaN}',
        ]
        for text in examples:
            with self.subTest(text=text[:24]):
                norm,_=r.normalize(text.replace("`","`"))
                self.assertNotEqual(tasks.parse_response(norm,"numeric_json_answer")["status"],"valid")

    def test_untouched_model_output_hash_is_mandatory(self):
        old=_report(r.QWEN_17)
        old["results"][0]["raw_response"]='{"answer":777}'
        with self.assertRaises(ValueError):
            r.audit(r.prepare(SEED),{r.QWEN_17:old,r.QWEN_4:_report(r.QWEN_4)})

    def test_does_not_accept_falsified_model_checkpoint(self):
        proposal=_report(r.QWEN_4)
        proposal["engine"]["weights_revision"]="main"
        with self.assertRaises(ValueError):
            r.audit(r.prepare(SEED),{r.QWEN_17:_report(r.QWEN_17),r.QWEN_4:proposal})

    def test_modified_questions_rejected(self):
        data=r.prepare(SEED)
        data["task_manifest"]["tasks"][0]["prompt"]="2+2"
        with self.assertRaises(ValueError):
            r.audit(data,{r.QWEN_17:_report(r.QWEN_17),r.QWEN_4:_report(r.QWEN_4)})

    def test_missing_output_counts_as_invalid(self):
        m=_report(r.QWEN_17)
        m["results"][1]["raw_response"]='I do not know.'
        from hashlib import sha256
        m["results"][1]["response_sha256"]=sha256(b'I do not know.').hexdigest()
        score=r.audit(r.prepare(SEED),{r.QWEN_17:m,r.QWEN_4:_report(r.QWEN_4)})
        self.assertEqual(score["models"][r.QWEN_17]["conditions"]["baseline"]["normalized_correct"],5)

    def test_overlong_response_rejected_without_invented_answer(self):
        p=r.prepare(SEED)
        calls=[]
        def generate(prompt):
            calls.append(prompt)
            return "x"*5000
        result=r.propose(p,r.QWEN_4,generate,{
            "model_source":r.GGUF_REPO,"weights_revision":r.GGUF_REVISION})
        self.assertEqual(len(result["results"]),12)
        self.assertTrue(all(x["oversized"] for x in result["results"]))
        score=r.audit(p,{r.QWEN_17:_report(r.QWEN_17),r.QWEN_4:result})
        self.assertEqual(score["models"][r.QWEN_4]["conditions"]["verify"]["normalized_correct"],0)

if __name__=="__main__":
    unittest.main()

"""Compare two real CPU reasoning models against independently audited known ODE cases.

Exploratory and review-only: no AGI or research discovery claim.
"""
import argparse
import json
import math
import re
import time
from hashlib import sha256
from pathlib import Path
from .research_pilot import make_proposal, independent_audit

MODELS = ("Qwen/Qwen3-0.6B", "Qwen/Qwen3-1.7B")
DOMAINS = ("materials", "chemistry")
HOLDOUTS = ("electronics", "mechanics")
QUESTION = "Which numerical methods efficiently solve different scientific equations?"
SCHEMA = "plenum-model-challenge-proposals-v1"


def digest(record):
    payload = json.dumps(record, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode()
    return sha256(payload).hexdigest()


def offline_sources(_question, offline=True):
    if not offline:
        raise ValueError("External metadata not needed for this blinded solver comparison")
    return {"providers": [], "records": [], "status": "offline_benchmark_only",
            "scientific_truth_verified": False}


def parse_hypothesis(response):
    """Untrusted text: accepts only JSON DATA, never commands or proof of discovery."""
    if not isinstance(response, str) or len(response) > 6000:
        return {"status": "invalid_response", "draft": None}
    text = response.strip().strip(chr(96)).removeprefix("json").strip()
    try:
        obj = json.loads(text)
    except (ValueError, TypeError):
        return {"status": "invalid_json", "draft": None}
    fields = ("hypothesis", "experiment", "falsification", "alternative_explanation")
    if not isinstance(obj, dict) or any(not isinstance(obj.get(k), str)
              or not 15 <= len(obj[k].strip()) <= 600 for k in fields):
        return {"status": "invalid_schema", "draft": None}
    return {"status": "unverified_draft", "draft": {k: obj[k].strip() for k in fields},
            "experiment_performed": False, "novelty_verified": False,
            "source_claims_verified": False, "scientific_discovery_verified": False}


HYPOTHESIS_PROMPT = (
    "Propose ONE falsifiable, original HYPOTHESIS for a FUTURE scientific "
    "experiment concerning numerical integration of physical equations. "
    "Return ONLY a JSON object with four string fields: hypothesis, experiment, "
    "falsification, alternative_explanation. Include no references, URLs, code, "
    "unverified measurements, or claims of completed discovery."
)


class CpuCandidate:
    """Allowlisted model, immutable resolved revision, CPU inference only."""
    def __init__(self, model_id):
        if model_id not in MODELS:
            raise ValueError("Model is not allowlisted")
        import torch
        from huggingface_hub import HfApi
        from transformers import AutoTokenizer, AutoModelForCausalLM
        self.model_id = model_id
        self.revision = HfApi().model_info(model_id).sha
        if not re.fullmatch(r"[a-f0-9]{40}", self.revision or ""):
            raise ValueError("Unable to resolve immutable model version")
        torch.set_num_threads(2)
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_id, revision=self.revision, trust_remote_code=False)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id, revision=self.revision, trust_remote_code=False,
            use_safetensors=True, torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True).to("cpu").eval()

    def _inputs(self, prompt):
        rendered = self.tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}], tokenize=False,
            add_generation_prompt=True, enable_thinking=False)
        return self.tokenizer(rendered, return_tensors="pt",
                              truncation=True, max_length=1500)

    def choose(self, prompt):
        ids = [self.tokenizer.encode(letter, add_special_tokens=False)
               for letter in "ABC"]
        if any(len(x) != 1 for x in ids):
            raise ValueError("Answer label tokenization changed")
        with self.torch.inference_mode():
            logits = self.model(**self._inputs(prompt)).logits[0, -1, :]
        values = [float(logits[x[0]]) for x in ids]
        if any(not math.isfinite(x) for x in values):
            raise ValueError("Invalid model logits")
        return "ABC"[max(range(3), key=lambda n: values[n])]

    def generate(self, prompt):
        batch = self._inputs(prompt)
        with self.torch.inference_mode():
            output = self.model.generate(**batch, do_sample=False,
                max_new_tokens=250, pad_token_id=self.tokenizer.eos_token_id)
        return self.tokenizer.decode(output[0][batch["input_ids"].shape[1]:],
                                     skip_special_tokens=True).strip()


def propose_comparison(model_id, choose, generate, revision, solver=None):
    if model_id not in MODELS or not re.fullmatch(r"[a-f0-9]{40}", revision or ""):
        raise ValueError("Model ID and immutable revision required")
    start = time.monotonic()
    proposals = []
    for domain in DOMAINS:
        p = make_proposal(QUESTION, domain, choose, model_id,
                          solver=solver, source_search=offline_sources)
        if p["sealed"]["holdout_domain"] not in HOLDOUTS:
            raise ValueError("Precommitted holdout was changed")
        proposals.append(p)
    draft = parse_hypothesis(generate(HYPOTHESIS_PROMPT))
    return {"schema": SCHEMA, "model_id": model_id, "model_revision": revision,
            "proposals": proposals, "draft": draft, "model_inference_executed": True,
            "model_calls": 3, "elapsed_seconds": round(time.monotonic()-start, 3),
            "holdout_executed": False, "AGI_achieved": False,
            "scientific_discovery_verified": False, "auto_model_promotion": False}


def audit_comparison(baseline, candidate, solver=None):
    for record, model_id in ((baseline, MODELS[0]), (candidate, MODELS[1])):
        if (not isinstance(record, dict) or record.get("schema") != SCHEMA
                or record.get("model_id") != model_id
                or not re.fullmatch(r"[a-f0-9]{40}", record.get("model_revision") or "")
                or record.get("holdout_executed") is not False
                or record.get("auto_model_promotion") is not False
                or record.get("model_inference_executed") is not True
                or not isinstance(record.get("proposals"), list)
                or len(record["proposals"]) != len(DOMAINS)):
            raise ValueError("Invalid model provenance or sealed proposal set")
        for idx, p in enumerate(record["proposals"]):
            if (p.get("schema") != "plenum-research-pilot-proposal-v1"
                    or p["sealed"].get("development_domain") != DOMAINS[idx]
                    or p["sealed"].get("holdout_domain") != HOLDOUTS[idx]
                    or p["sealed"].get("model") != model_id):
                raise ValueError("Model task attribution or holdout altered")
    left = [independent_audit(p, solver=solver) for p in baseline["proposals"]]
    right = [independent_audit(p, solver=solver) for p in candidate["proposals"]]
    for a, b in zip(left, right):
        if a["measurements"] != b["measurements"]:
            raise ValueError("Model comparisons used different evidence")
    count = lambda runs: sum(x["selected_is_best_on_one_fixture"] for x in runs)
    return {"schema": "plenum-model-challenge-audit-v1",
            "baseline": {"model": MODELS[0], "correct": count(left), "cases": left},
            "candidate": {"model": MODELS[1], "correct": count(right), "cases": right},
            "tasks_per_model": len(DOMAINS),
            "candidate_better_on_these_tasks": count(right) > count(left),
            "same_holdout_evidence": True, "hypotheses_independently_verified": False,
            "stronger_general_intelligence_proven": False, "AGI_achieved": False,
            "model_weights_modified": False, "model_promoted": False,
            "limitations": "Two known-equation tasks are exploratory, not a blind "
                           "pretraining-independent benchmark; no automatic promotion."}


def write_report(path, report):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(report, indent=2, ensure_ascii=False,
                            allow_nan=False) + "\n", encoding="utf-8")


def main():
    cli = argparse.ArgumentParser(description="Plenum evaluated CPU model candidates")
    sub = cli.add_subparsers(dest="command", required=True)
    pro = sub.add_parser("propose")
    pro.add_argument("--model", required=True, choices=MODELS)
    pro.add_argument("--out", required=True)
    aud = sub.add_parser("audit")
    aud.add_argument("--baseline", required=True)
    aud.add_argument("--candidate", required=True)
    aud.add_argument("--out", required=True)
    args = cli.parse_args()
    if args.command == "propose":
        runtime = CpuCandidate(args.model)
        result = propose_comparison(runtime.model_id, runtime.choose,
                                    runtime.generate, runtime.revision)
        write_report(args.out, result)
        print("Model", args.model, "proposals", len(result["proposals"]),
              "research draft", result["draft"]["status"])
    else:
        result = audit_comparison(
            json.loads(Path(args.baseline).read_text("utf-8")),
            json.loads(Path(args.candidate).read_text("utf-8")))
        write_report(args.out, result)
        print("Holdout audited:", result["baseline"]["correct"],
              "vs", result["candidate"]["correct"], "out of", result["tasks_per_model"])
if __name__ == "__main__":
    main()

"""Reproducible external science-QA evaluation.

ARC-Challenge by Ai2 is CC-BY-SA-4.0: https://huggingface.co/datasets/allenai/ai2_arc .
Load a snapshot from Hugging Face, without copying the questions into this repository.
The public test set may have appeared in pretraining; this is not a blind AGI exam.
"""
import hashlib
import json
import random
import re
from pathlib import Path

LETTERS = "ABCD"
SOURCE = "allenai/ai2_arc"
SUBSET = "ARC-Challenge"
APPROVED_DATA_REVISION = "210d026faf9955653af8916fad021475a3f00453"


def _digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize(row):
    """Normalize four-answer ARC items; never include the correct answer in prompts."""
    choices = row.get("choices") or {}
    labels, values = choices.get("label") or [], choices.get("text") or []
    if len(labels) != 4 or len(values) != 4 or len(set(labels)) != 4:
        return None
    if row.get("answerKey") not in labels:
        return None
    item_id = str(row.get("id") or "")
    question = str(row.get("question") or "").strip()
    if not item_id or not 1 <= len(question) <= 1600:
        return None
    paired = list(zip(labels, (str(v) for v in values)))
    if any(not v or len(v) > 400 for _, v in paired):
        return None
    # Deterministic reordering limits original-option-position artifacts.
    random.Random(int(_digest("plenum-arc-v1|" + item_id), 16)).shuffle(paired)
    correct = labels.index(row["answerKey"])
    correct_text = str(values[correct])
    answer_index = [v for _, v in paired].index(correct_text)
    return {"id": item_id, "question": question,
            "options": [v for _, v in paired], "answer_index": answer_index}


def choose_rows(rows, count):
    if not 4 <= count <= 64:
        raise ValueError("Evaluation count must be between 4 and 64")
    available = {}
    for row in rows:
        record = normalize(row)
        if record and record["id"] not in available:
            available[record["id"]] = record
    if len(available) < count:
        raise ValueError("Not enough valid four-choice external benchmark rows")
    order = sorted(available, key=lambda x: _digest("plenum-arc-sample-v1|" + x))
    return [available[key] for key in order[:count]]


def load_external_cases(split="test", count=12):
    if split not in ("test", "validation"):
        raise ValueError("Only official independent evaluation splits are permitted")
    from huggingface_hub import HfApi, hf_hub_download
    import pyarrow.parquet as pq
    api = HfApi()
    revision = APPROVED_DATA_REVISION
    files = api.list_repo_files(SOURCE, repo_type="dataset", revision=revision)
    prefix = SUBSET + "/" + split + "-"
    chosen = sorted(f for f in files if f.startswith(prefix) and f.endswith(".parquet"))
    if not chosen:
        raise RuntimeError("No official Parquet science benchmark split found")
    all_rows = []
    for filename in chosen:
        file = hf_hub_download(repo_id=SOURCE, filename=filename,
                               repo_type="dataset", revision=revision)
        all_rows.extend(pq.read_table(file).to_pylist())
    return choose_rows(all_rows, count), {
        "source": SOURCE, "subset": SUBSET, "split": split,
        "revision": revision, "license": "CC-BY-SA-4.0",
        "selection": "deterministic SHA-256 ordering; fixed prompt; no adaptive sampling",
    }


def format_prompt(case):
    if len(case["options"]) != 4:
        raise ValueError("Exactly four answers required")
    options = "\n".join(f"{label}. {option}" for label, option
                        in zip(LETTERS, case["options"]))
    return ("You are taking an independent science examination. "
            "Choose the best answer. Output exactly one letter: A, B, C, or D. "
            "Do not use tools and do not provide an explanation.\n"
            f"Question: {case['question']}\n{options}\nAnswer:")


def prepare_prompt(tokenizer, case):
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": format_prompt(case)}],
        tokenize=False, add_generation_prompt=True, enable_thinking=False
    )


def next_token_choice(model, tokenizer, torch, case):
    """Single-forward labeled-choice scoring, no generated citations or chain of thought."""
    prefix = prepare_prompt(tokenizer, case)
    encoded = tokenizer(prefix, return_tensors="pt", truncation=True, max_length=512)
    labels = [tokenizer.encode(x, add_special_tokens=False) for x in LETTERS]
    if any(len(x) != 1 for x in labels):
        raise ValueError("Unexpected multi-token answer label; do not guess")
    with torch.inference_mode():
        logits = model(**encoded).logits[0, -1, :]
    scores = [float(logits[x[0]]) for x in labels]
    return max(range(4), key=lambda i: scores[i])


def evaluate_cases(cases, scorer):
    correct = 0
    details = []
    for case in cases:
        guess = scorer(case)
        if not isinstance(guess, int) or guess not in range(4):
            raise ValueError("Evaluator must return a valid choice index")
        matched = guess == case["answer_index"]
        correct += matched
        details.append({"source_id": case["id"], "correct": matched})
    return {
        "correct": correct, "total": len(cases), "accuracy": correct / len(cases),
        "chance_accuracy": 0.25,
        "sample_sha256": _digest("|".join(x["id"] for x in cases)),
        "per_question_results": details,
        "claim": "multiple-choice science benchmark only; not blind general intelligence",
    }


def run_external_evaluation(count=12, out=None):
    from .hf_model import _load_model, APPROVED_MODEL
    cases, source = load_external_cases(count=count)
    tokenizer, model, torch = _load_model(APPROVED_MODEL)
    output = evaluate_cases(
        cases, lambda case: next_token_choice(model, tokenizer, torch, case)
    )
    from huggingface_hub import HfApi
    output.update({
        "source": source, "model": APPROVED_MODEL,
        "model_revision": HfApi().model_info(APPROVED_MODEL).sha,
        "prompt_version": "plenum-arc-zero-shot-v1",
        "fine_tuning_performed": False,
        "scientific_discovery_verified": False,
        "human_approval_required_for_model_updates": True,
        "limitations": [
            "Public ARC questions may have been included in foundation-model pretraining.",
            "This is grade-school science multiple choice, not original research or AGI.",
            "Answer-choice logit scoring differs from a generation-based exam.",
            "The small count has large statistical uncertainty; avoid broad capability claims.",
        ],
    })
    if out is not None:
        path = Path(out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    return output

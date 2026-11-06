"""Small reproducible CPU LoRA experiment for Qwen3-0.6B.

Author-created synthetic prompts only. Evaluation data is loaded from official
ARC-Challenge *test* after the predetermined training steps are complete; no
validation/test examples contribute gradients. Saving a checkpoint is not
approval to deploy it. This may not improve science reasoning.
"""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import math
import os

from .science_eval import (LETTERS, load_external_cases, evaluate_cases,
                           next_token_choice, format_prompt)
from .hf_model import APPROVED_MODEL, _load_model

SEED = 20261105
CONFIG = {"steps": 2, "rank": 2, "lora_alpha": 4, "learning_rate": 0.0002,
          "max_length": 196, "test_count": 8}

# Authored exclusively for this experiment. None is copied from the ARC dataset.
ORIGINAL_LESSONS = (
    ("A sample cools by transferring thermal energy to a colder environment. What principle applies?",
     ("Newton cooling", "radioactive decay", "optical diffraction", "magnetic induction"), 0),
    ("Which relationship gives gravitational force between two point masses?",
     ("F = m a", "F = G m1 m2 / r^2", "F = q E", "F = k x"), 1),
    ("When a reversible reaction reaches chemical equilibrium, what property is equal?",
     ("reactant concentration to zero", "total molecular mass to zero",
      "forward and reverse rates", "temperature to absolute zero"), 2),
    ("In an ideal capacitor C, which relation defines stored charge Q?",
     ("Q = R I", "Q = P t", "Q = I / R", "Q = C V"), 3),
    ("When a controlled experiment changes only one variable, what is the benefit?",
     ("It isolates a potential cause", "It guarantees causation",
      "It removes measurement error", "It proves every mechanism"), 0),
    ("Which instrument commonly measures light absorption as a function of wavelength?",
     ("Centrifuge", "Spectrophotometer", "Calorimeter", "Barometer"), 1),
    ("What is a required check for a stable numerical simulation?",
     ("Ignore time-step sensitivity", "Assume exact measurements",
      "Test convergence across time steps", "Treat one output as experimental truth"), 2),
    ("For a scientific model with uncertain constants, what strengthens a prediction?",
     ("Fit to a single datapoint", "Hide parameter values",
      "Choose the highest output", "Quantify uncertainty and replicate"), 3),
)


def training_checksum():
    payload = json.dumps(ORIGINAL_LESSONS, ensure_ascii=False, separators=(",", ":"))
    return sha256(payload.encode()).hexdigest()


def _training_example(i):
    q, options, answer = ORIGINAL_LESSONS[i]
    return {"id": "plenum-original-" + str(i), "question": q,
            "options": list(options), "answer_index": answer}


def _manifest(directory, report):
    path = Path(directory)
    adapter = path / "adapter_model.safetensors"
    config = path / "adapter_config.json"
    if not adapter.exists() or not config.exists():
        raise RuntimeError("Missing PEFT adapter files")
    if adapter.stat().st_size > 20_000_000:
        raise ValueError("Candidate checkpoint exceeds 20MB publication bound")
    hashes = {name: sha256((path / name).read_bytes()).hexdigest()
              for name in ("adapter_model.safetensors", "adapter_config.json")}
    manifest = {
        "schema": "plenum-model-candidate-v1",
        "id": "qwen3-science-lora-" + report["training_fixture_sha256"][:12],
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "code_revision": os.environ.get("GITHUB_SHA", ""),
        "run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "base_model": report["base_model"],
        "base_revision": report["base_model_revision"],
        "training_fixture_sha256": report["training_fixture_sha256"],
        "config": CONFIG,
        "files_sha256": hashes,
        "evaluation_source_revision": report["source"]["revision"],
        "evaluation_sample_sha256": report["baseline"]["sample_sha256"],
        "evaluation_results_reported": True,
        "promoted_or_deployed": False,
        "warning": "Unapproved research candidate, potentially worse than its base model; no clinical, scientific or AGI claim.",
    }
    (path / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def verify_manifest(directory):
    path = Path(directory)
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema") != "plenum-model-candidate-v1" or manifest.get("promoted_or_deployed") is not False:
        raise ValueError("Invalid candidate status")
    for name, digest in manifest.get("files_sha256", {}).items():
        if name not in ("adapter_config.json", "adapter_model.safetensors"):
            raise ValueError("Unexpected checkpoint asset")
        if sha256((path / name).read_bytes()).hexdigest() != digest:
            raise ValueError("Checkpoint checksum changed")
    if len(manifest.get("files_sha256", {})) != 2:
        raise ValueError("Incomplete checkpoint manifest")
    return True


def run_fine_tuning(output_dir="candidates/qwen3-science-v1",
                    report_file="reports/qwen3_finetune.json"):
    import torch
    from peft import LoraConfig, get_peft_model
    from huggingface_hub import HfApi

    torch.set_num_threads(4)
    torch.manual_seed(SEED)
    tokenizer, model, _ = _load_model(APPROVED_MODEL)
    model.eval()
    cases, source = load_external_cases(count=CONFIG["test_count"])
    # The below two evaluations are fixed before training, not used to tune hyperparameters.
    baseline = evaluate_cases(
        cases, lambda x: next_token_choice(model, tokenizer, torch, x)
    )
    cfg = LoraConfig(
        task_type="CAUSAL_LM", r=CONFIG["rank"], lora_alpha=CONFIG["lora_alpha"],
        target_modules=["q_proj", "v_proj"], lora_dropout=0.0, bias="none"
    )
    candidate = get_peft_model(model, cfg)
    candidate.train()
    params = [p for p in candidate.parameters() if p.requires_grad]
    if not params:
        raise RuntimeError("PEFT did not expose trainable parameters")
    optimizer = torch.optim.AdamW(params, lr=CONFIG["learning_rate"])
    losses = []
    for i in range(CONFIG["steps"]):
        record = _training_example(i)
        prefix = tokenizer.apply_chat_template(
            [{"role": "user", "content": format_prompt(record)}],
            tokenize=False, add_generation_prompt=True, enable_thinking=False
        )
        full = prefix + LETTERS[record["answer_index"]] + tokenizer.eos_token
        tensors = tokenizer(full, return_tensors="pt", truncation=True,
                            max_length=CONFIG["max_length"])
        prefix_size = len(tokenizer.encode(prefix, add_special_tokens=False))
        ids = tensors["input_ids"]
        if prefix_size >= ids.shape[1]:
            raise ValueError("Training answer was truncated")
        labels = ids.clone()
        labels[0, :prefix_size] = -100
        optimizer.zero_grad(set_to_none=True)
        loss = candidate(**tensors, labels=labels).loss
        if not torch.isfinite(loss):
            raise RuntimeError("Nonfinite LoRA training loss")
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach()))
    candidate.eval()
    after = evaluate_cases(
        cases, lambda x: next_token_choice(candidate, tokenizer, torch, x)
    )
    revision = HfApi().model_info(APPROVED_MODEL).sha
    report = {
        "experiment": "Qwen3-0.6B fixed-configuration tiny LoRA candidate",
        "base_model": APPROVED_MODEL, "base_model_revision": revision,
        "training_fixture_sha256": training_checksum(),
        "training_steps": CONFIG["steps"], "losses": losses,
        "trainable_parameters": sum(x.numel() for x in params),
        "source": source, "baseline": baseline, "candidate": after,
        "measured_holdout_gain": after["accuracy"] - baseline["accuracy"],
        "checkpoint_candidate_only": True,
        "automatic_model_promotion": False,
        "AGI_or_scientific_discovery_demonstrated": False,
        "study_limits": [
            "This is two optimizer steps on short, authored examples, not substantive science training.",
            "ARC is public and may appear in the original model's pretraining data.",
            "Eight held-out questions have extremely high uncertainty.",
            "No training examples were drawn from ARC; test labels did not influence training.",
            "No test-based hyperparameter search or deployment is permitted.",
        ],
    }
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    candidate.save_pretrained(output, safe_serialization=True)
    report["checkpoint_manifest"] = _manifest(output, report)
    verify_manifest(output)
    target = Path(report_file)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report

import json
from pathlib import Path

root = Path(__file__).resolve().parent
paired = json.loads((root / "paired-original.json").read_text())
prior = json.loads((root / "prior-original.json").read_text())
assert paired["same_original_three_question_ids"] is True
assert paired["paid_model_api_calls"] == prior["paid_model_api_calls"] == 0
assert len(paired["domain_scores"]) == 3
for i, (domain, item) in enumerate(sorted(paired["domain_scores"].items()), start=1):
    old = prior["by_domain"][domain.lower()]
    assert old["original_id"] == item["question_id"]
    assert old["native_correct"] == item["prior_0_6b_correct"]
    evaldir = root / "gpqa-genuine" / f"eval-{i}"
    for config, value, artifact_sha in (
        ("candidate_qwen35_4b", item["new_4b_correct"], item["native_eval_sha256"]),
        ("reference_qwen3_06b", item["prior_0_6b_correct"], old["original_eval_sha256"]),
    ):
        path = evaldir / config / "run-1" / "grading.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        grade = {
          "summary": {"pass_rate": float(value), "passed": int(value), "failed": int(not value), "total": 1},
          "expectations": [{"text": f"{domain}: native original GPQA grade", "passed": value,
                            "evidence": f"{item['question_id']}; SHA256 {artifact_sha}"}],
          "user_notes_summary": {"uncertainties": ["Timing and token metrics intentionally omitted: no comparable paired measurements. Upstream displays missing metrics as zero; do not interpret these zeros."]}
        }
        path.write_text(json.dumps(grade, indent=2) + "\n")


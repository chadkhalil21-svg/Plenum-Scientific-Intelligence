"""Optional offline aggregation of the original public GPQA paired scores.

The upstream aggregator is unmodified. This adapter does not infer, score,
train, download, contact a provider, or promote models. It validates the two
frozen public receipts, converts each native score to one grading record, and
only with --execute runs the pinned upstream Python script in a temporary dir.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
UPSTREAM = Path(__file__).resolve().with_name("aggregate_benchmark.py")
UPSTREAM_SHA256 = "540d0ee42b894428350eaf1337e436376e2429185b5ce69485434216f2d0b386"
UPSTREAM_COMMIT = "b1ca788ae9c6e78f5b66df56cc770c3d0bbf55e1"
PAIRED = Path("evidence/inspect-gpqa/2026-11-09-qwen35-4b-paired-original-three-sciences.json")
PRIOR = Path("evidence/inspect-gpqa/2026-11-09-original-three-sciences.json")
SOURCES = {
    PAIRED: "176fad4cf76d98f1758f3b356b7e8783c41c157f41ff8f554804f19cafc8047d",
    PRIOR: "eb6c263f85df672b017841eefa9ebd06eeb313f43b6d3b37c02fdaa448dcb36c",
}
UNMEASURED = (
    "Timing, tokens, tools and errors are unavailable as comparable paired "
    "measurements. Upstream uses zero for missing metrics: none are measurements."
)


def checked_bytes(path, expected):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"SHA-256 mismatch: {path.name}")
    return data


def original_grades(root):
    paired, prior = [
        json.loads(checked_bytes(root / path, digest))
        for path, digest in SOURCES.items()
    ]
    if (
        paired["same_original_three_question_ids"] is not True
        or paired["paid_model_api_calls"] != 0
        or prior["paid_model_api_calls"] != 0
        or set(paired["domain_scores"]) != {"Biology", "Chemistry", "Physics"}
    ):
        raise ValueError("Unapproved paired evidence")
    records = []
    for i, (domain, item) in enumerate(sorted(paired["domain_scores"].items()), 1):
        old = prior["by_domain"][domain.lower()]
        if (
            old["original_id"] != item["question_id"]
            or old["native_correct"] != item["prior_0_6b_correct"]
        ):
            raise ValueError("Native evidence does not match")
        for config, value, artifact_sha in (
            ("candidate_qwen35_4b", item["new_4b_correct"], item["native_eval_sha256"]),
            ("reference_qwen3_06b", item["prior_0_6b_correct"], old["original_eval_sha256"]),
        ):
            if type(value) is not bool:
                raise ValueError("Invalid native grade")
            record = {
                "summary": {
                    "pass_rate": float(value), "passed": int(value),
                    "failed": int(not value), "total": 1,
                },
                "expectations": [{
                    "text": f"{domain}: native original GPQA grade",
                    "passed": value,
                    "evidence": f"{item['question_id']}; SHA256 {artifact_sha}",
                }],
                "user_notes_summary": {"uncertainties": [UNMEASURED]},
            }
            records.append((Path(f"eval-{i}") / config / "run-1/grading.json", record))
    return records


def prepare_grades(root, out):
    records = original_grades(root)
    for path, record in records:
        dest = out / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return [record for _, record in records]


def execute():
    # A fixed report directory; refuse an existing output or symlink parent.
    reports = ROOT / "reports"
    out = reports / "evoscientist-gpqa"
    if out.exists() or out.is_symlink() or reports.is_symlink():
        raise FileExistsError("Refusing to overwrite or follow redirected report paths")
    checked_bytes(UPSTREAM, UPSTREAM_SHA256)
    with tempfile.TemporaryDirectory(prefix="plenum-evo-gpqa-") as scratch:
        workspace = Path(scratch)
        records = workspace / "scores"
        prepare_grades(ROOT, records)
        subprocess.run(
            [sys.executable, "-I", "-S", str(UPSTREAM), str(records),
             "--skill-name", "Paired public GPQA native grades (no new inference)"],
            cwd=workspace,
            env={"PATH": os.defpath, "PYTHONIOENCODING": "utf-8"},
            timeout=30,
            check=True,
        )
        report = json.loads((records / "benchmark.json").read_text())
        summary = report["run_summary"]
        if (len(report["runs"]) != 6
                or summary["candidate_qwen35_4b"]["pass_rate"]["mean"] != 0
                or summary["reference_qwen3_06b"]["pass_rate"]["mean"] != 0.3333):
            raise ValueError("Aggregation does not match the frozen native evidence")
        out.mkdir(parents=True, exist_ok=False)
        for name in ("benchmark.json", "benchmark.md"):
            shutil.copyfile(records / name, out / name)
        (out / "INTERPRETATION.md").write_text(
            "# Read before interpreting the raw upstream reports\n\n"
            "Existing public native grades only: candidate 0/3, reference 1/3. "
            "No new model inference or new score. " + UNMEASURED + "\n",
            encoding="utf-8",
        )
    print(f"Raw upstream aggregation: {out.relative_to(ROOT)}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Aggregate frozen public grades offline")
    args = parser.parse_args(argv)
    if args.execute:
        execute()
    else:
        checked_bytes(UPSTREAM, UPSTREAM_SHA256)
        records = original_grades(ROOT)
        print(json.dumps({
            "mode": "validated read-only plan",
            "upstream_commit": UPSTREAM_COMMIT,
            "native_scores": len(records),
            "new_model_inference": False,
            "paid_model_api_calls": 0,
            "automatic_model_promotion": False,
            "execute": False,
        }, indent=2))


if __name__ == "__main__":
    main()

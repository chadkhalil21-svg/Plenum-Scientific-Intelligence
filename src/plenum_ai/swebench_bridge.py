"""A guarded bridge to the ORIGINAL SWE-bench v5 official evaluator.

No new agent or scorer is implemented. Default only emits a reproducible
command plan. Model-generated patches must come from a separately reviewed
agent; the evaluator reads its JSONL and delegates grading to SWE-bench.
"""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess

SCHEMA = "plenum-external-repo-repair-gate-v1"
UPSTREAM = "SWE-bench/SWE-bench"
VERSION = "5.0.2"
INSTANCE = "sympy__sympy-20590"  # Existing upstream documented public example.
PREDICTIONS = Path("reports/swebench/predictions.jsonl")
MAX_PATCH_BYTES = 120_000
MIN_FREE_GIB = 120
MIN_RAM_GIB = 16
MAX_RUN_SECONDS = 1800


def plan(stage="gold", run_id=None):
    if stage not in ("gold", "candidate"):
        raise ValueError("Only original upstream reference or model candidate")
    if run_id is None:
        run_id = "plenum-gold-v1" if stage == "gold" else "plenum-candidate-v1"
    if not isinstance(run_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,47}", run_id):
        raise ValueError("Short single-use slug required for independent cache key")
    # IMPORTANT: SWE-bench caches by run_id, not by candidate patch contents.
    argv = ["swebench", "eval", "verified"]
    argv += ["--gold"] if stage == "gold" else ["-p", str(PREDICTIONS)]
    argv += ["-i", INSTANCE, "--run-id", run_id, "-j", "1", "-t", "900"]
    return {
        "schema": SCHEMA,
        "framework": UPSTREAM,
        "upstream_version": VERSION,
        "official_dataset": "SWE-bench/SWE-bench_Verified",
        "original_public_instance": INSTANCE,
        "phase": stage,
        "run_id": run_id,
        "original_official_scorer": True,
        "command_argv": argv,
        "minimum_host": {"free_storage_gib": MIN_FREE_GIB, "ram_gib": MIN_RAM_GIB, "architecture": "x86_64"},
        "external_agent_inference_executed": False,
        "official_evaluation_executed": False,
        "official_issue_resolved": None,
        "cost_authorized": False,
        "automatic_deployment": False,
        "AGI_demonstrated": False,
        "limitations": [
            "This is one published reference issue and may be contaminated.",
            "A passed gold reference proves harness installation, not autonomous coding.",
            "Official Docker images may require networking for pulling and substantial host resources.",
            "Actual external agent inference is a separate bounded, approval-gated experiment.",
            "A successful process exit is not a pass; inspect original official results.json.",
            "The source benchmark's tests can reject valid repairs; report that limitation.",
        ],
    }


def host_resources():
    total_ram = os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE")
    free_disk = shutil.disk_usage(Path.cwd()).free
    return {
        "architecture": platform.machine(),
        "ram_gib": total_ram / 1024**3,
        "free_storage_gib": free_disk / 1024**3,
    }


def validate_candidate(path=PREDICTIONS):
    """Check metadata/size only. Do not execute, import, or grade a candidate."""
    expected = PREDICTIONS.resolve()
    file = Path(path)
    if file.resolve() != expected or file.is_symlink() or not file.is_file():
        raise ValueError("Only the reviewed reports/swebench/predictions.jsonl is permitted")
    if file.stat().st_size > MAX_PATCH_BYTES or file.stat().st_size == 0:
        raise ValueError("Prediction report empty or exceeds allowed byte budget")
    lines = file.read_text(encoding="utf-8").splitlines()
    if len(lines) != 1:
        raise ValueError("Exactly one preregistered official issue predicted")
    row = json.loads(lines[0])
    if (not isinstance(row, dict) or row.get("instance_id") != INSTANCE
        or not isinstance(row.get("model_patch"), str)
        or not row["model_patch"].strip()
        or not isinstance(row.get("model_name_or_path"), str)
        or not row["model_name_or_path"].strip()):
        raise ValueError("Original SWE-bench prediction contract missing")
    return True


def execute(record, *, approved=False, installed_version=None, resources=None,
            runner=subprocess.run, docker_runner=subprocess.run):
    if not approved:
        raise PermissionError("Explicit --execute on an isolated public evaluation machine required")
    if not isinstance(record, dict):
        raise ValueError("Invalid benchmark plan")
    expected = plan(record.get("phase"), record.get("run_id"))
    if record != expected:
        raise ValueError("Upstream invocation, resource floor or evidence contract changed")
    version = installed_version
    if version is None:
        try:
            version = importlib.metadata.version("swebench")
        except importlib.metadata.PackageNotFoundError as exc:
            raise RuntimeError("Install reviewed optional swebench==5.0.2 on the isolated host") from exc
    if version != VERSION:
        raise RuntimeError("Unreviewed SWE-bench package version")
    host = host_resources() if resources is None else resources
    if (host.get("architecture") not in ("x86_64", "AMD64")
        or host.get("ram_gib", 0) < MIN_RAM_GIB
        or host.get("free_storage_gib", 0) < MIN_FREE_GIB):
        raise RuntimeError("Host does not meet independently documented upstream resource recommendations")
    if record["phase"] == "candidate":
        validate_candidate()
    # Do not pass credentials to third-party evaluation process.
    safe_env = {k: v for k, v in os.environ.items()
                if not re.search(r"(TOKEN|SECRET|PASSWORD|API_KEY|CREDENTIAL)", k, re.I)}
    docker_runner(["docker", "info"], check=True, timeout=20,
                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=safe_env)
    process = runner(expected["command_argv"], check=True,
                     timeout=MAX_RUN_SECONDS, env=safe_env)
    # Never infer a functional score from a zero exit code.
    return {
        "schema": SCHEMA,
        "official_evaluation_executed": process.returncode == 0,
        "official_issue_resolved": None,
        "original_results_location": f"logs/evaluation/{record['run_id']}/results.json",
        "independent_score_review_required": True,
        "automatic_deployment": False,
        "AGI_demonstrated": False,
    }


def main():
    cli = argparse.ArgumentParser(description="Plan a bounded original SWE-bench single-issue run")
    cli.add_argument("--stage", choices=("gold", "candidate"), default="gold")
    cli.add_argument("--run-id", default=None)
    cli.add_argument("--execute", action="store_true")
    cli.add_argument("--out", default="reports/swebench/plan.json")
    args = cli.parse_args()
    record = plan(args.stage, args.run_id)
    if args.execute:
        record["execution_result"] = execute(record, approved=True)
    dest = Path(args.out)
    if (dest.is_absolute() or ".." in dest.parts or dest.suffix != ".json"
        or not dest.parts[:2] == ("reports", "swebench") or len(dest.parts) > 4):
        raise ValueError("Only relative reports/swebench/*.json output")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("SWE-bench official evaluator:", record["phase"],
          "executed:", args.execute, "AGI:", record["AGI_demonstrated"])


if __name__ == "__main__":
    main()

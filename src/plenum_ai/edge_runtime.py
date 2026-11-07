"""A small, verifiable bridge to the EXISTING llama.cpp local inference engine.

Default operation only describes a bounded public smoke test. Genuine model
execution requires explicit authorization and two local SHA256-pinned artifacts.
This code never downloads weights, starts a server, deploys a model, or runs
untrusted generated code. No AGI capability is inferred from a process exit.
"""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
from time import monotonic

SCHEMA = "plenum-edge-inference-proof-v1"
UPSTREAM = "ggml-org/llama.cpp"
ASSETS_ROOT = Path("edge_assets")
MODEL = Path("models/plenum.gguf")
ENGINE = Path("bin/llama-cli")
PROMPT = "Compute 17 + 25. Reply with only the integer."
MAX_TOKENS = 64
CONTEXT = 1024
THREADS = 2
MAX_RUNTIME_SECONDS = 180
MAX_MODEL_BYTES = 80 * 1024**3
MAX_ENGINE_BYTES = 250 * 1024**2
_DIGEST = re.compile(r"[a-f0-9]{64}\Z")


def plan(model_sha256=None, engine_sha256=None):
    """Immutable dry-run contract: no downloads, network or subprocess."""
    for digest in (model_sha256, engine_sha256):
        if digest is not None and (not isinstance(digest, str) or not _DIGEST.fullmatch(digest)):
            raise ValueError("Only exact lowercase SHA256 fingerprints are accepted")
    return {
        "schema": SCHEMA,
        "engine": UPSTREAM,
        "engine_sha256": engine_sha256,
        "model_sha256": model_sha256,
        "model_path": str(MODEL),
        "engine_path": str(ENGINE),
        "public_smoke_prompt": PROMPT,
        "max_new_tokens": MAX_TOKENS,
        "context_tokens": CONTEXT,
        "cpu_threads": THREADS,
        "gpu_layers": 0,
        "max_runtime_seconds": MAX_RUNTIME_SECONDS,
        "model_downloads_authorized": False,
        "remote_inference_authorized": False,
        "network_isolation_independently_verified": False,
        "inference_executed": False,
        "independent_accuracy_verified": False,
        "private_documents_used": False,
        "automatic_model_promotion": False,
        "AGI_demonstrated": False,
        "limitations": [
            "A trusted device or host must independently deny network egress for an air-gapped claim.",
            "Exact hashes establish artifact identity, not license compliance or model safety.",
            "This is one arithmetic smoke input, not a general reasoning benchmark.",
            "Outputs are never run as code or treated as reliable scientific findings.",
            "No Qwen3.6-27B GGUF compatibility or hardware fit is asserted.",
            "Physical device memory, battery, heat, speed and energy require direct measurement.",
        ],
    }


def _artifact(root, relative, digest, max_bytes, *, gguf=False, executable=False):
    if not isinstance(digest, str) or not _DIGEST.fullmatch(digest):
        raise ValueError("Execution requires original exact SHA256 for each local artifact")
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Local artifact root must exist and not be a symlink")
    # Reject symlinks at every path segment, not only the resolved leaf.
    path = root
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("Symlinks are forbidden in the local runtime chain")
    full = path.resolve(strict=True)
    if not full.is_file() or full.stat().st_size > max_bytes or full.stat().st_size == 0:
        raise ValueError("Missing, empty or oversized local runtime artifact")
    if gguf and full.open("rb").read(4) != b"GGUF":
        raise ValueError("Only locally provided GGUF model files are supported")
    if executable and not os.access(full, os.X_OK):
        raise ValueError("Local inference executable is not executable")
    actual = sha256()
    with full.open("rb") as f:
        for data in iter(lambda: f.read(1024 * 1024), b""):
            actual.update(data)
    if actual.hexdigest() != digest:
        raise ValueError("Local binary or model differs from its preregistered SHA256")
    return full


def execute(record, *, approved=False, assets_root=ASSETS_ROOT,
            runner=subprocess.run, clock=monotonic):
    if not approved:
        raise PermissionError("Real edge inference requires explicit --execute")
    if not isinstance(record, dict):
        raise ValueError("Invalid local model execution request")
    expected = plan(record.get("model_sha256"), record.get("engine_sha256"))
    if record != expected:
        raise ValueError("Original local inference contract changed")
    model = _artifact(assets_root, MODEL, record["model_sha256"],
                      MAX_MODEL_BYTES, gguf=True)
    engine = _artifact(assets_root, ENGINE, record["engine_sha256"],
                       MAX_ENGINE_BYTES, executable=True)
    argv = [
        str(engine), "-m", str(model), "-p", PROMPT,
        "-n", str(MAX_TOKENS), "-c", str(CONTEXT), "-t", str(THREADS),
        "-ngl", "0", "--temp", "0", "--seed", "1",
        "--single-turn", "--no-conversation", "--no-display-prompt"
    ]
    # Strict environment allowlist. No API tokens, cloud service credentials,
    # writable repository access, remote model URLs, shells or dynamic imports.
    safe_env = {k: os.environ[k] for k in ("PATH", "LANG", "LC_ALL")
                if k in os.environ}
    start = clock()
    result = runner(argv, check=False, capture_output=True, text=True,
                    timeout=MAX_RUNTIME_SECONDS, env=safe_env)
    elapsed = clock() - start
    out = result.stdout if isinstance(result.stdout, str) else ""
    err = result.stderr if isinstance(result.stderr, str) else ""
    # Never archive raw outputs, prompts from users, model weights or secrets.
    # A zero exit code confirms invocation only, not an accurate answer.
    return {
        **expected,
        "inference_executed": result.returncode == 0,
        "process_exit_code": result.returncode,
        "elapsed_seconds": round(elapsed, 4),
        "stdout_sha256": sha256(out.encode("utf-8")).hexdigest(),
        "stdout_characters": len(out),
        "stderr_sha256": sha256(err.encode("utf-8")).hexdigest(),
        "stderr_characters": len(err),
        "original_independent_correctness_score": None,
        "local_files_sha256_verified": True,
        "remote_inference_authorized": False,
        "network_isolation_independently_verified": False,
        "independent_accuracy_verified": False,
        "automatic_model_promotion": False,
        "AGI_demonstrated": False,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Offline-by-default local llama.cpp GGUF inference proof"
    )
    parser.add_argument("--model-sha256", default=None)
    parser.add_argument("--engine-sha256", default=None)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--out", default="reports/edge/plan.json")
    args = parser.parse_args()
    report = plan(args.model_sha256, args.engine_sha256)
    if args.execute:
        report = execute(report, approved=True)
    destination = Path(args.out)
    if (destination.is_absolute() or ".." in destination.parts
        or destination.parts[:2] != ("reports", "edge")
        or len(destination.parts) > 4 or destination.suffix != ".json"
        or destination.is_symlink()):
        raise ValueError("Only a relative JSON report inside reports/edge is permitted")
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Real execution records are write-once; historical failures must survive.
    if args.execute:
        with destination.open("x", encoding="utf-8") as f:
            f.write(json.dumps(report, indent=2) + "\n")
    else:
        destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Local llama.cpp:", "executed" if report["inference_executed"] else "not executed",
          "independent AGI proof:", report["AGI_demonstrated"])


if __name__ == "__main__":
    main()

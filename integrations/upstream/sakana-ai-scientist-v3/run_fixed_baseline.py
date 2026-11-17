"""Optional, source-pinned execution of the original Sakana CPU baseline."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile


COMMIT = "de1cd267b8922faa31631fb397bbc202bf714d84"
ROOT = Path(__file__).resolve().parent
SOURCE_HASHES = {
    "examples/circpack/evaluate.py":
        "11187fcb39331efccc1c23aa2761d6eaefce200d2d81df660f32e5595d18a4fa",
    "examples/circpack/capture.py":
        "cc7a660d33180d61479bbf0df59fae815d0119dd19d9e5290e0d2126096804d5",
    "examples/circpack/program_0/src/program.py":
        "72aaca25037f1cdc9f71257eb325ec456b888de55d9328f62eea488335d5101a",
}
OUTPUT_NAMES = ("correct.json", "metrics.json", "extra.npz", "stdout.log", "stderr.log")


def verified_sources():
    sources = {}
    for name, digest in SOURCE_HASHES.items():
        contents = (ROOT / name).read_bytes()
        if hashlib.sha256(contents).hexdigest() != digest:
            raise ValueError("Source integrity failed: " + name)
        sources[name] = contents
    return sources


def _wait_bounded(process, timeout):
    try:
        return process.communicate(timeout=timeout)
    except BaseException:
        # The pinned evaluator starts a multiprocessing child. The parent
        # timeout must terminate the entire session's process group, not just
        # its direct evaluator PID.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate(timeout=2)
        raise


def _execute_baseline():
    if os.name != "posix":
        raise ValueError("Fixed evaluator execution requires POSIX process-group support")
    # Write the already verified bytes into a fresh directory.
    # No generated program, external input, credential or model is accepted.
    sources = verified_sources()
    with tempfile.TemporaryDirectory(prefix="plenum-sakana-fixed-") as directory:
        scratch = Path(directory)
        for name, contents in sources.items():
            path = scratch / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(contents)
        command = [
            sys.executable, "-E", "-s", "-B",
            "examples/circpack/evaluate.py",
            "--program_path", "examples/circpack/program_0/src/program.py",
            "--results_dir", "results",
        ]
        process = subprocess.Popen(
            command,
            cwd=scratch,
            env={"PATH": os.defpath, "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"},
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            start_new_session=True,
        )
        stdout, stderr = _wait_bounded(process, 25)
        if process.returncode:
            raise subprocess.CalledProcessError(
                process.returncode, command, output=stdout, stderr=stderr,
            )
        results = scratch / "results"
        correct = json.loads((results / "correct.json").read_text())
        metrics = json.loads((results / "metrics.json").read_text())
        if correct.get("correct") is not True:
            raise ValueError("Original evaluator rejected the fixed baseline")
        return {
            "evaluator_executed": True,
            "exit_status": process.returncode,
            "correct": True,
            "combined_score": metrics["combined_score"],
            "num_positions": metrics["public"]["num_circles"],
            "output_sha256": {
                name: hashlib.sha256((results / name).read_bytes()).hexdigest()
                for name in OUTPUT_NAMES
            },
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--verify-only", action="store_true", help="Hash fixed source; do not execute")
    action.add_argument("--run", action="store_true", help="Explicitly execute fixed CPU baseline")
    args = parser.parse_args()
    try:
        receipt = {
            "upstream_commit": COMMIT,
            "sources_verified": True,
            "evaluator_executed": False,
            "model_calls": 0,
            "api_calls": 0,
            "scientific_discovery_demonstrated": False,
        }
        if args.run:
            receipt.update(_execute_baseline())
        else:
            verified_sources()
    except (OSError, subprocess.SubprocessError, ValueError, KeyError) as exc:
        parser.exit(1, f"{exc}\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()

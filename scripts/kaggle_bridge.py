"""Kaggle bridge via the *official* Kaggle CLI only.

This adapter is explicitly non-interactive and never prints API credentials or
the contents of a private Kaggle notebook to public CI logs.

An authorized GitHub Actions environment secret KAGGLE_API_TOKEN is required
for any network action. By default this tool only validates its configuration.
It never starts model inference or edits unrelated Kaggle notebooks.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_NOTEBOOK = REPO_ROOT / "notebooks/prometheus_kaggle_qwen36_27b.ipynb"
ALLOWED_SLUG = "plenum-prometheus-qwen-trial"
KERNEL_REF = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_-]{1,60}/[a-z0-9][a-z0-9-]{2,80}$")
MODES = ("offline", "verify", "list", "read", "status", "write-draft")


def check_ref(value, *, for_write=False):
    if not isinstance(value, str) or not KERNEL_REF.fullmatch(value):
        raise ValueError("Notebook reference must be owner/slug, without code or URL")
    if for_write and value.rsplit("/", 1)[-1] != ALLOWED_SLUG:
        raise PermissionError("Writes are restricted to the isolated Prometheus trial slug")
    return value


def safe_notebook(path=PUBLIC_NOTEBOOK):
    content = json.loads(Path(path).read_text(encoding="utf-8"))
    if content.get("nbformat") != 4:
        raise ValueError("Expected a version-4 Jupyter notebook")
    cells = content.get("cells") or []
    source = "\n".join("".join(cell.get("source", []))
                       for cell in cells if cell.get("cell_type") == "code")
    if "APPROVE_FREE_GPU_RUN = False" not in source:
        raise PermissionError("Trial notebook missing its default explicit opt-in guard")
    if any(cell.get("execution_count") is not None or cell.get("outputs")
           for cell in cells if cell.get("cell_type") == "code"):
        raise PermissionError("Published source must contain no prior model outputs")
    return content


def metadata(ref):
    return {
        "id": check_ref(ref, for_write=True),
        "title": "Plenum Prometheus Qwen Trial",
        "code_file": "prometheus_kaggle_qwen36_27b.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": True,
        "enable_internet": True,
        "machine_shape": "NvidiaTeslaT4",
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [],
        "model_sources": [],
    }


def sdk(args):
    if not os.environ.get("KAGGLE_API_TOKEN"):
        raise PermissionError(
            "Kaggle is NOT connected. Configure the environment secret "
            "KAGGLE_API_TOKEN in the protected kaggle-access GitHub environment. "
            "Never paste it into chat, logs or a public repository."
        )
    if not isinstance(args, list) or not args or args[0] != "kernels":
        raise ValueError("Only preapproved official notebook CLI operations are supported")
    # Do not print stdout/stderr: private kernel names and local API diagnostics
    # may contain sensitive metadata. No shell=True or dynamic code execution.
    result = subprocess.run(
        ["kaggle", *args], check=False, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, timeout=180,
    )
    if result.returncode != 0:
        raise RuntimeError("Official Kaggle CLI failed (exit code "
                           + str(result.returncode) + "); no private output printed")
    return result.stdout


def run(mode, ref=None):
    if mode not in MODES:
        raise ValueError("Unsupported mode")
    if mode == "offline":
        safe_notebook()
        print("Validated original public trial notebook; no Kaggle network or tokens used")
        return
    if mode in ("read", "status", "write-draft"):
        ref = check_ref(ref, for_write=(mode == "write-draft"))
    if mode == "verify":
        sdk(["kernels", "list", "-m", "--page-size", "1"])
        print("Authorized Kaggle notebook listing succeeded; contents not disclosed")
        return
    if mode == "list":
        sdk(["kernels", "list", "-m", "--page-size", "10"])
        print("Kaggle account notebook listing succeeded; names withheld from public logs")
        return
    if mode == "status":
        sdk(["kernels", "status", ref])
        print("Authenticated Kaggle notebook status query succeeded")
        return
    if mode == "read":
        with tempfile.TemporaryDirectory(prefix="plenum-kaggle-read-") as folder:
            sdk(["kernels", "pull", ref, "-p", folder, "-m"])
            files = list(Path(folder).glob("*.ipynb")) + list(Path(folder).glob("*.py"))
            if not files:
                raise RuntimeError("Authenticated read returned no notebook source")
            for file in files:
                hash_value = hashlib.sha256(file.read_bytes()).hexdigest()
                print("Authenticated notebook source read; SHA256:", hash_value)
                # Content is deliberately NOT uploaded to a public artifact.
        return
    if mode == "write-draft":
        notebook = safe_notebook()
        with tempfile.TemporaryDirectory(prefix="plenum-kaggle-draft-") as folder:
            dest = Path(folder) / "prometheus_kaggle_qwen36_27b.ipynb"
            dest.write_text(json.dumps(notebook, ensure_ascii=False) + "\n",
                            encoding="utf-8")
            meta = Path(folder) / "kernel-metadata.json"
            meta.write_text(json.dumps(metadata(ref), indent=2) + "\n",
                            encoding="utf-8")
            sdk(["kernels", "push", "-p", folder, "--no-run"])
        print("Private Prometheus notebook draft saved on Kaggle, without running any cells")
        print("Model inference: NOT executed. GPU allocation: NOT started by this command.")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Approval-gated official Kaggle notebook bridge")
    parser.add_argument("--mode", choices=MODES, default="offline")
    parser.add_argument("--kernel-ref", default="")
    args = parser.parse_args(argv)
    run(args.mode, args.kernel_ref)


if __name__ == "__main__":
    main()

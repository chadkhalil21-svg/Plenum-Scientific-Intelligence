"""Opt-in, no-account local audio and model tool adapter.

Actual media transcription works only on a separately authorized owner-managed
machine that already has whisper.cpp and a model. No download, telemetry,
hosted API, private content, or indefinite GitHub CI execution is arranged.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

TOOLS = {
    "whisper.cpp": "whisper-cli",
    "ffmpeg": "ffmpeg",
    "Ollama": "ollama",
    "llama.cpp": "llama-cli",
    "Upscayl CLI": "upscayl-ncnn",
}


def probe(*, find_binary=shutil.which):
    return {
        "schema": "plenum-free-local-tools-v1",
        "binaries": {name: bool(find_binary(command)) for name,command in TOOLS.items()},
        "installed_by_plenum_tool": False,
        "hosted_inference_used": False,
        "permanent_server_verified": False,
        "private_media_uploaded": False,
    }


def _safe_file(path, root: Path, suffixes: tuple[str, ...], limit: int) -> Path:
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.suffix.lower() not in suffixes:
        raise ValueError("Expected an existing permitted plain file, no symlinks")
    resolved = path.resolve(strict=True)
    safe_root = root.resolve(strict=True)
    if not resolved.is_relative_to(safe_root) or not 0 < path.stat().st_size <= limit:
        raise ValueError("Only bounded owner-selected local workspace files")
    return resolved


def transcribe_local(*, workspace: Path, wav_file: Path, model_file: Path,
                     runner=subprocess.run, find_binary=shutil.which) -> dict:
    """Actual existing whisper.cpp execution, no downloads or network access."""
    if os.getenv("GITHUB_ACTIONS") == "true":
        raise PermissionError("Do not run private recordings on public GitHub actions")
    if os.getenv("PLENUM_OWNER_LOCAL_MEDIA") != "authorized":
        raise PermissionError("Owner private local media runtime not authorized")
    root = Path(workspace)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Owner workspace must exist and not be a symlink")
    audio = _safe_file(wav_file, root, (".wav",), 150 * 1024 * 1024)
    model = _safe_file(model_file, root, (".bin", ".gguf"), 8 * 1024 * 1024 * 1024)
    binary = find_binary(TOOLS["whisper.cpp"])
    if not binary:
        raise FileNotFoundError("Owner host lacks whisper-cli; no auto-download attempted")
    output_dir = root.resolve() / "reports" / "local-transcripts"
    if output_dir.is_symlink():
        raise ValueError("Refuse symlinked output directory")
    output_dir.mkdir(parents=True, exist_ok=True)
    # Fixed basename prevents unrelated existing files in a shared workspace
    # from being overwritten by a potentially untrusted media filename.
    basename = "plenum-transcript-" + __import__("hashlib").sha256(
        str(audio).encode("utf-8") + str(audio.stat().st_size).encode("ascii")
    ).hexdigest()[:16]
    output_base = output_dir / basename
    target = output_dir / (basename + ".txt")
    if target.exists():
        raise FileExistsError("Existing transcript; avoid repeated work and overwrites")
    command = [binary, "-m", str(model), "-f", str(audio),
               "-otxt", "-of", str(output_base)]
    result = runner(command, check=False, timeout=900,
                    cwd=str(root.resolve()),capture_output=True,text=True)
    if result.returncode != 0 or not target.is_file():
        raise RuntimeError("Local whisper.cpp did not produce an accepted transcript")
    data = target.read_text(encoding="utf-8")
    if not data.strip() or len(data) > 1000000:
        raise ValueError("Invalid or unexpectedly large local transcript")
    return {
        "schema":"plenum-local-transcript-result-v1", "status":"LOCAL_TRANSCRIPT_FILE_CREATED",
        "file":str(target),"characters":len(data),
        "paid_service_invoked":False, "offline_executable_used":True,
        "owner_local_runtime_verified":True,
    }


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--probe",action="store_true")
    parser.add_argument("--execute",action="store_true")
    parser.add_argument("--workspace")
    parser.add_argument("--wav")
    parser.add_argument("--model")
    args=parser.parse_args(argv)
    if args.execute:
        if not all((args.workspace,args.wav,args.model)):
            parser.error("Owner workspace, wav and model are required")
        print(json.dumps(transcribe_local(
            workspace=Path(args.workspace),wav_file=Path(args.wav),model_file=Path(args.model)),indent=2))
    else:
        print(json.dumps(probe(),indent=2))


if __name__ == "__main__":
    main()

"""One audited source repair for a fixed public development failure.

The candidate is inert text. No candidate code is imported or executed.
The only correction is an immutable replacement of the rejected model by
a distinct upstream model. Verification never runs inference a second time.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import wave

ORIGINAL_BLOB = "fa28960632c325a69e48e7063e959323a85bab42"
OLD_SHA = "921e4cf8686fdd993dcd081a5da5b6c365bfde1162e72b08d75ac75289920b1f"
NEW_SHA = "a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002"
REPLACEMENTS = (
    (b"tiny English model", b"base English model"),
    (b"/ggml-tiny.en.bin", b"/ggml-base.en.bin"),
    (OLD_SHA.encode(), NEW_SHA.encode()),
)
EXPECTED = "the quick brown fox jumps over the lazy dog".split()


def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path, cap):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= cap:
        raise ValueError("Invalid bounded input")
    return path.read_bytes()


def candidate(original):
    if git_blob(original) != ORIGINAL_BLOB:
        raise ValueError("Original immutable source differs")
    data = original
    for old, new in REPLACEMENTS:
        if data.count(old) != 1:
            raise ValueError("Unexpected replacement count")
        data = data.replace(old, new)
    return data


def evidence(original_path, candidate_path, audio, transcript):
    original = read(original_path, 16000)
    corrected = read(candidate_path, 16000)
    if corrected != candidate(original):
        raise ValueError("Candidate exceeds authorized exact replacement")
    sound = read(audio, 2000000)
    with wave.open(str(audio), "rb") as wav:
        if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) != (1, 2, 16000):
            raise ValueError("Unexpected fixture audio format")
        if not 1 <= wav.getnframes() <= 160000:
            raise ValueError("Unexpected fixture length")
    text = read(transcript, 512).decode("utf-8").strip()
    if re.findall(r"[a-z]+", text.lower()) != EXPECTED:
        raise ValueError("Original accuracy gate failed")
    return {
        "schema": "plenum-whisper-exact-repair-v1",
        "original_head": "a9ed286a49308fb5e01ed25a53c08f65e72445af",
        "original_run": 45767285022,
        "original_git_blob": ORIGINAL_BLOB,
        "candidate_sha256": digest(corrected),
        "model_sha256": NEW_SHA,
        "audio_sha256": digest(sound),
        "transcript_sha256": digest(read(transcript, 512)),
        "transcript": text,
        "paid_inference": False,
        "original_model_replayed": False,
        "private_media_processed": False,
        "merge_authorized": False,
    }


def main():
    p = argparse.ArgumentParser()
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--receipt", action="store_true")
    mode.add_argument("--verify", action="store_true")
    p.add_argument("--original", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--audio", type=Path)
    p.add_argument("--transcript", type=Path)
    p.add_argument("--model", type=Path)
    p.add_argument("--receipt-file", type=Path, default=Path("repair-receipt.json"))
    args = p.parse_args()
    if args.receipt or args.verify:
        actual = evidence(args.original, args.out, args.audio, args.transcript)
        if args.receipt:
            if digest(read(args.model, 200000000)) != NEW_SHA:
                raise ValueError("Model bytes differ")
            with args.receipt_file.open("x", encoding="utf-8") as out:
                json.dump(actual, out, indent=2)
        else:
            if actual != json.loads(read(args.receipt_file, 8000)):
                raise ValueError("Independent receipt disagreement")
            print("Independent exact candidate and original accuracy gate passed; no merge authority")
    else:
        data = candidate(read(args.original, 16000))
        with args.out.open("xb") as out:
            out.write(data)


if __name__ == "__main__":
    main()

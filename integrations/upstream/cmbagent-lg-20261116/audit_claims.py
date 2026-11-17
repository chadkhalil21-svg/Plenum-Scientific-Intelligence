"""Offline numeric-token grounding of one selected public JSON evidence artifact."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile

from grounding import SourceIndex, ground

MAX_BYTES = 256_000
UPSTREAM_COMMIT = "bde10cb482357675fc747f8436895b1ed79b12b0"


def audit_claims(repo_root: Path, artifact: str, claims: list[str]) -> dict:
    root = Path(repo_root).resolve(strict=True)
    relative = Path(artifact)
    if (relative.is_absolute() or ".." in relative.parts
            or len(relative.parts) < 2 or relative.parts[0] != "evidence"
            or relative.suffix != ".json"):
        raise ValueError("Select a relative JSON file under public evidence/")
    source = root
    for part in relative.parts:
        source = source / part
        if source.is_symlink():
            raise ValueError("Symbolic evidence paths are not permitted")
    if not source.is_file():
        raise ValueError("Selected public evidence file is absent")
    if not (1 <= len(claims) <= 12) or any(
            not isinstance(c, str) or not 1 <= len(c) <= 512 for c in claims):
        raise ValueError("Select 1–12 nonempty claims (max 512 characters each)")
    with source.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("Evidence exceeds bounded input size")
    if not isinstance(json.loads(raw), dict):
        raise ValueError("Evidence must be a JSON object")
    # The original engine may look in sibling input_files/ directories; stage
    # exactly one artifact under a fresh parent, never expose the repository.
    with tempfile.TemporaryDirectory(prefix="plenum-grounding-") as directory:
        work = Path(directory) / "work"
        data = work / "data"
        data.mkdir(parents=True)
        (data / "artifact.json").write_bytes(raw)
        index = SourceIndex.build(work, budget_s=5)
        results = [ground(claim, index).to_dict() for claim in claims]
        coverage = index.coverage.to_dict()
        details = index.coverage.files.get("data/artifact.json", {})
        complete = (not index.coverage.incomplete and len(index.coverage.files) == 1
                    and details.get("indexed_bytes", 0) > 0
                    and not details.get("truncated", True))
    return {
        "schema": "plenum-cmbagent-numeric-grounding-v1",
        "upstream_commit": UPSTREAM_COMMIT,
        "artifact": relative.as_posix(),
        "artifact_sha256": hashlib.sha256(raw).hexdigest(),
        "coverage": coverage,
        "complete_within_selected_artifact": complete,
        "claims": results,
        "semantic_truth_verified": False,
        "model_inference": False,
        "paid_api_calls": 0,
        "limitation": "Token match, approximate match or absence within selected artifact only; not scientific validity or semantic entailment.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--claim", action="append", required=True)
    args = parser.parse_args()
    # Script is integrations/upstream/cmbagent-lg-20261116/audit_claims.py
    root = Path(__file__).resolve().parents[3]
    print(json.dumps(audit_claims(root, args.artifact, args.claim), indent=2,
                     ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()

"""Durable, public-only progress for the ORIGINAL founder Chief mission.

Checkpoint is materialized in the SAME original GitHub Actions artifact on job
failure; a failed-job rerun can restore it. Not an always-on host or agent.
Never trust a checkpoint unless exact owner/issue/objective/team and artifact
bytes still match. No network calls, secret storage or alternate queue.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

MAX_FILES = 60
MAX_BYTES = 20_000_000


def objective_digest(objective: str) -> str:
    return hashlib.sha256(objective.encode("utf-8")).hexdigest()


def artifact_digest(root: Path, name: str) -> str | None:
    """Hash actual public worker files; refuse escape, symlink and huge trees."""
    if not isinstance(name, str) or not (1 <= len(name) <= 300) or "\\" in name:
        return None
    rel = PurePosixPath(name)
    if rel.is_absolute() or any(x in ("", ".", "..") for x in rel.parts):
        return None
    if not str(rel).startswith("workers/"):
        return None
    path = root / Path(*rel.parts)
    if not path.exists() or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        return None
    files = [path] if path.is_file() else sorted(path.rglob("*"))
    if not files or len(files) > MAX_FILES:
        return None
    h = hashlib.sha256()
    size = 0
    useful = False
    for item in files:
        if item.is_symlink():
            return None
        if not item.is_file():
            continue
        if not item.resolve().is_relative_to(root.resolve()):
            return None
        content = item.read_bytes()
        size += len(content)
        if size > MAX_BYTES:
            return None
        useful = True
        h.update(item.relative_to(root).as_posix().encode("utf-8") + b"\0")
        h.update(hashlib.sha256(content).digest())
    return h.hexdigest() if useful else None


def checkpoint_path(root: Path, issue: int) -> Path:
    return root / f"chief-checkpoint-{issue}.json"


def load_checkpoint(root: Path, *, issue: int, objective: str,
                    team: tuple[str, ...]) -> dict:
    path = checkpoint_path(root, issue)
    if not path.is_file():
        return {}
    if path.stat().st_size > 200_000 or path.is_symlink():
        raise ValueError("Unsafe original checkpoint")
    data = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(data, dict)
            or data.get("schema") != "plenum-chief-restart-v1"
            or data.get("issue_number") != issue
            or data.get("objective_sha256") != objective_digest(objective)
            or data.get("team") != list(team)
            or not isinstance(data.get("results"), dict)
            or set(data["results"]) - set(team)):
        raise ValueError("Checkpoint belongs to a different or untrusted mission")
    return data["results"]


def save_checkpoint(root: Path, *, issue: int, objective: str,
                    team: tuple[str, ...], results: dict) -> None:
    root.mkdir(parents=True, exist_ok=True)
    path = checkpoint_path(root, issue)
    data = {
        "schema": "plenum-chief-restart-v1",
        "issue_number": issue,
        "objective_sha256": objective_digest(objective),
        "team": list(team),
        "results": results,
        "only_original_public_workers": True,
        "owner_private_accounts_used": False,
    }
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def verified_previous_result(root: Path, kind: str, entry: object) -> dict | None:
    if not isinstance(entry, dict) or entry.get("status") != "DRAFT_READY_FOR_FOUNDER":
        return None
    if entry.get("verified") is not True:
        return None
    artifact = entry.get("artifact_path")
    if (not isinstance(artifact, str)
            or not artifact.startswith("workers/" + kind + "/")):
        return None
    actual = artifact_digest(root, artifact)
    if not actual or actual != entry.get("sha256"):
        return None
    return {
        "status": "DRAFT_READY_FOR_FOUNDER",
        "verified": True,
        "worker": entry.get("worker"),
        "verified_scope": entry.get("verified_scope"),
        # Preserve the original functional receipt only after artifact SHA
        # verification. The goal grader still checks the real code/manifest.
        "actual_offline_functional_test_passed": (
            entry.get("actual_offline_functional_test_passed") is True
        ),
        "output_artifact": entry.get("output_artifact"),
        "_artifact_path": artifact,
        "_reused": True,
    }

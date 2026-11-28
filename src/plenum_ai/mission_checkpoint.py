"""Durable, public-only progress for the ORIGINAL founder Chief mission.

Checkpoint is materialized in the SAME original GitHub Actions artifact on job
failure; a failed-job rerun can restore it. Not an always-on host or agent.
Never trust a checkpoint unless exact owner/issue/objective/team and artifact
bytes still match. No network calls, secret storage or alternate queue.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from pathlib import Path, PurePosixPath

MAX_FILES = 60
MAX_BYTES = 20_000_000


def objective_digest(objective: str) -> str:
    return hashlib.sha256(objective.encode("utf-8")).hexdigest()


def _bounded_artifact_entries(path: Path) -> list[Path] | None:
    if path.is_file():
        return [path] if MAX_FILES >= 1 else None
    entries = []
    pending = [path]
    while pending:
        # Do not let pathlib's recursive glob materialize an unbounded tree.
        with os.scandir(pending.pop()) as children:
            for child in children:
                if len(entries) >= MAX_FILES or child.is_symlink():
                    return None
                child_path = Path(child.path)
                entries.append(child_path)
                if child.is_dir(follow_symlinks=False):
                    pending.append(child_path)
    return sorted(entries)


def artifact_digest(root: Path, name: str) -> str | None:
    """Hash actual public worker files; refuse escape, symlink and huge trees."""
    if not isinstance(name, str) or not (1 <= len(name) <= 300) or "\\" in name:
        return None
    rel = PurePosixPath(name)
    if rel.is_absolute() or rel.as_posix() != name or any(x in ("", ".", "..") for x in rel.parts):
        return None
    if not str(rel).startswith("workers/"):
        return None
    path = root / Path(*rel.parts)
    try:
        resolved_root = root.resolve()
        # A symlink in an intermediate worker directory can alias another task.
        if any((root / Path(*rel.parts[:i])).is_symlink() for i in range(1, len(rel.parts) + 1)):
            return None
        if not path.exists() or path.is_symlink() or not path.resolve().is_relative_to(resolved_root):
            return None
        if not (path.is_file() or path.is_dir()):
            return None
        files = _bounded_artifact_entries(path)
        if not files:
            return None
        h = hashlib.sha256()
        size = 0
        useful = False
        for item in files:
            if item.is_symlink():
                return None
            if item.is_dir():
                continue
            if not item.is_file():
                return None
            if not item.resolve().is_relative_to(resolved_root):
                return None
            remaining = MAX_BYTES - size
            if item.stat().st_size > remaining:
                return None
            # Bound the actual read as well: the file can grow after stat().
            with item.open("rb") as stream:
                content = stream.read(remaining + 1)
            size += len(content)
            if size > MAX_BYTES:
                return None
            useful = True
            h.update(item.relative_to(root).as_posix().encode("utf-8") + b"\0")
            h.update(hashlib.sha256(content).digest())
        return h.hexdigest() if useful else None
    except OSError:
        # Failed artifact I/O is invalid resume proof, not a Chief-wide crash.
        return None


def checkpoint_path(root: Path, issue: int) -> Path:
    if type(issue) is not int or not 1 <= issue < 10**9:
        raise ValueError("Invalid original mission issue identifier")
    return root / f"chief-checkpoint-{issue}.json"


def _valid_results(results: object, team: tuple[str, ...]) -> bool:
    return (isinstance(results, dict)
            and not (set(results) - set(team))
            and all(isinstance(entry, dict)
                    and type(entry.get("attempt")) is int
                    and entry["attempt"] in (1, 2)
                    for entry in results.values()))


def _reject_nonfinite(value: str):
    raise ValueError("Nonfinite checkpoint number")


def _finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Nonfinite checkpoint number")
    return number


def load_checkpoint(root: Path, *, issue: int, objective: str,
                    team: tuple[str, ...]) -> dict:
    path = checkpoint_path(root, issue)
    if path.is_symlink():
        raise ValueError("Unsafe original checkpoint")
    if not path.exists():
        return {}
    if not path.is_file() or path.stat().st_size > 200_000:
        raise ValueError("Unsafe original checkpoint")
    with path.open("rb") as stream:
        raw = stream.read(200_001)
    if len(raw) > 200_000:
        raise ValueError("Unsafe original checkpoint")
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate checkpoint object key")
            result[key] = value
        return result

    try:
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object,
                          parse_constant=_reject_nonfinite, parse_float=_finite_float)
    except RecursionError:
        raise ValueError("Unsafe original checkpoint")
    if (not isinstance(data, dict)
            or data.get("schema") != "plenum-chief-restart-v1"
            or type(data.get("issue_number")) is not int
            or data.get("issue_number") != issue
            or data.get("objective_sha256") != objective_digest(objective)
            or data.get("team") != list(team)
            or data.get("only_original_public_workers") is not True
            or data.get("owner_private_accounts_used") is not False
            or not _valid_results(data.get("results"), team)):
        raise ValueError("Checkpoint belongs to a different or untrusted mission")
    return data["results"]


def save_checkpoint(root: Path, *, issue: int, objective: str,
                    team: tuple[str, ...], results: dict) -> None:
    # Validate issue identifier before creating any directories
    path = checkpoint_path(root, issue)
    if not _valid_results(results, team):
        raise ValueError("Invalid original checkpoint results")
    data = {
        "schema": "plenum-chief-restart-v1",
        "issue_number": issue,
        "objective_sha256": objective_digest(objective),
        "team": list(team),
        "results": results,
        "only_original_public_workers": True,
        "owner_private_accounts_used": False,
    }
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError("Unsafe original checkpoint")
    raw = (json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
    if len(raw) > 200_000:
        raise ValueError("Unsafe original checkpoint")
    root.mkdir(parents=True, exist_ok=True)
    # Exclusive random temporary file avoids pre-existing aliases and stale
    # temp filenames; replacement preserves the previous complete checkpoint.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=root, prefix=path.name + ".",
                                         suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def verified_previous_result(root: Path, kind: str, entry: object) -> dict | None:
    if not isinstance(entry, dict) or entry.get("status") != "DRAFT_READY_FOR_FOUNDER":
        return None
    if entry.get("verified") is not True:
        return None
    if type(entry.get("attempt")) is not int or entry["attempt"] not in (1, 2):
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

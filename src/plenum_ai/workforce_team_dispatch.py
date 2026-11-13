"""Founder public-team dispatch reusing Plenum's ALREADY EXISTING worker engines.

No new model framework, arbitrary code execution, private credentials or browser
session. Each outcome is graded to the limited capability actually exercised.
"""
from __future__ import annotations

import ast
from hashlib import sha256
import json
from pathlib import Path
from xml.etree import ElementTree

KINDS = frozenset({"public_program", "public_science", "public_creative"})
ROLES = {
    "public_program": "existing_plenum_program_foundry",
    "public_science": "existing_plenum_durable_science",
    "public_creative": "existing_plenum_creative_studio",
}


def dispatch(task: dict, output_dir: Path) -> dict:
    kind = task["kind"]
    if kind not in KINDS:
        raise ValueError("No approved specialist for task kind")
    num = task["issue_number"]
    base = output_dir / ("issue-" + str(num))
    if base.is_symlink() or base.exists():
        raise FileExistsError("Never overwrite previous public task artifacts")
    base.mkdir(parents=True)
    objective = task["objective"]

    if kind == "public_program":
        from .program_foundry import generate_program
        from .reviewed_domain_workers import match_original_capability, reuse_original_program
        capability = match_original_capability(objective)
        if capability:
            # ORIGINAL reviewed validator, not another irrelevant numeric starter.
            manifest = reuse_original_program(capability, objective, base / "code")
        else:
            # Unknown requests cannot claim beyond a review-only starter.
            manifest = generate_program("data_validator", objective, base / "code")
        code = (base / "code" / "main.py").read_bytes()
        ast.parse(code.decode("utf-8"), filename="main.py")
        if (manifest.get("schema") != "plenum-reviewable-program-v1"
                or manifest["main_sha256"] != sha256(code).hexdigest()
                or manifest["generated_program_has_not_been_deployed"] is not True
                or manifest["human_code_review_required"] is not True
                or manifest["file_count"] != 3):
            raise RuntimeError("Existing code generator integrity check failed")
        return {
            "status": "DRAFT_READY_FOR_FOUNDER", "verified": True,
            "verified_scope": (
                "existing first-party domain tool functional tests passed, not deployed"
                if capability else "public generic starter syntax/hash only"
            ),
            "worker": ROLES[kind], "output_artifact": str(base.relative_to(output_dir)),
            "generated_source_files": manifest["file_count"],
            "reused_existing_domain_program": bool(capability),
            "domain_capability": capability,
            "actual_offline_functional_test_passed": (
                manifest.get("functional_verifier_executed_and_passed", False)
            ),
            "code_executed": bool(capability),
            "production_written": False,
            "general_coding_ability_proved": False,
            "owner_review_required": True,
        }

    if kind == "public_science":
        from .durable_graph import run_persistent, inspect_persistent
        db = base / "checkpoint.sqlite"
        thread_id = "founder-" + str(num)
        done = run_persistent(
            objective, str(db), thread_id,
            tool_keys=["scipy.orbit", "scipy.thermal"],
            offline=True, optimize=True,
        )
        restored = inspect_persistent(str(db), thread_id)
        if (done.get("status") != "executed_and_checkpointed"
                or not restored.get("finished")
                or restored.get("workers_recorded") != 2
                or restored.get("question") != objective
                or done["result"].get("known_model_integration_passed") is not True):
            raise RuntimeError("Original durable science check or readback failed")
        # Never copy private untrusted data into permanent public GitHub issue.
        (base / "public-science-summary.json").write_text(json.dumps({
            "status": "KNOWN_MODEL_CHECK_PASSED",
            "thread_id": thread_id,
            "workers": restored["workers_recorded"],
            "restored_from_durable_checkpoint": True,
            "original_scientific_discovery": False,
        }, indent=2) + "\n", encoding="utf-8")
        return {
            "status": "DRAFT_READY_FOR_FOUNDER", "verified": True,
            "verified_scope": "two previously established scientific models and checkpoint readback",
            "worker": ROLES[kind], "output_artifact": str(base.relative_to(output_dir)),
            "known_models_verified": 2,
            "checkpoint_restored": True,
            "original_scientific_discovery": False,
            "owner_review_required": True,
        }

    from .creative_studio import write_studies
    files = write_studies(objective, 1701, base / "creative")
    if (not files.get("created_from_algorithm")
            or files.get("copied_copyrighted_music_or_art") is not False
            or files.get("novelty_exclusivity_certified") is not False):
        raise RuntimeError("Original creative studio claims unexpected rights")
    svg = (base / "creative" / "geometric_study.svg")
    xml = (base / "creative" / "original_score.musicxml")
    for output in (svg, xml):
        if not output.is_file() or output.stat().st_size > 180000:
            raise RuntimeError("Expected bounded creative artifact missing")
        ElementTree.parse(output)  # independently verify syntax, NOT artistic quality.
    return {
        "status": "DRAFT_READY_FOR_FOUNDER", "verified": True,
        "verified_scope": "original SVG/MusicXML artifact structure only",
        "worker": ROLES[kind], "output_artifact": str(base.relative_to(output_dir)),
        "generated_artifacts": 3,
        "creative_quality_independently_verified": False,
        "owner_review_required": True,
    }

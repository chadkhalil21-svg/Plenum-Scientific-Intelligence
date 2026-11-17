"""Founder public-team dispatch reusing Plenum's ALREADY EXISTING worker engines.

No new model framework, arbitrary code execution, private credentials or browser
session. Each outcome is graded to the limited capability actually exercised.
"""
from __future__ import annotations

import ast
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import re
import os
import subprocess
import sys
from xml.etree import ElementTree

KINDS = frozenset({"public_program", "public_science", "public_creative", "public_verification"})
ROLES = {
    "public_program": "existing_plenum_program_foundry",
    "public_science": "existing_plenum_durable_science",
    "public_creative": "existing_plenum_creative_studio",
    "public_verification": "existing_cmbagent_numeric_grounding",
}

# Only these already-public immutable evidence receipts, not a caller path.
PUBLIC_GROUNDING_RECEIPTS = {
    "gpqa": ("evidence/evoscientist/2026-11-17-gpqa/receipt.json",
             "bd389be2a068c0d99bffebf70259b9cfea9f58bb0c2098a255ed8f4cd77819d2",
             frozenset({"pass_rate_delta_rounded", "candidate_qwen35_4b.correct",
                        "reference_qwen3_06b.correct"})),
    "tls": ("evidence/fermilink/2026-11-17-tls/receipt.json",
            "ecf031efeb690e34d9e3a8c2174280579748642c95dff96b3fc274fe9537f2fa",
            frozenset({"rows", "Pe_min", "Pe_max", "max_abs_muz",
                       "max_population_conservation_error"})),
}
_GROUND_REQUEST = re.compile(
    r"Ground (gpqa|tls) claim / ([A-Za-z][A-Za-z0-9_.]{0,40}) was "
    r"([-+]?\d{1,12}(?:\.\d{1,20})?(?:[eE][-+]?\d{1,2})?)"
)


def parse_numeric_grounding(objective: str) -> tuple[str, str, str, str, str]:
    """Only one fixed receipt alias, approved field and atomic numeric value."""
    match = _GROUND_REQUEST.fullmatch(objective)
    if not match:
        raise ValueError("Use Ground <approved alias> claim / <field> was <number>")
    alias, field, number = match.groups()
    source, digest, fields = PUBLIC_GROUNDING_RECEIPTS[alias]
    if field not in fields:
        raise ValueError("Field is not approved for this public evidence receipt")
    prefix = "outputs." if alias == "gpqa" else "output."
    return source, digest, prefix + field, field, number


def _ground_public_claim(objective: str, base: Path) -> dict:
    artifact, digest, field_path, field, number = parse_numeric_grounding(objective)
    root = Path(__file__).resolve().parents[2]
    source = root / artifact
    if source.resolve() != source or source.stat().st_size > 256_000:
        raise ValueError("Approved public receipt bytes did not match their immutable pin")
    raw = source.read_bytes()
    if sha256(raw).hexdigest() != digest:
        raise ValueError("Approved public receipt bytes did not match their immutable pin")
    # Independently resolve this exact field, not a coincidental token elsewhere.
    recorded = json.loads(raw, parse_float=Decimal, parse_int=Decimal)
    for part in field_path.split("."):
        recorded = recorded[part]
    if not isinstance(recorded, Decimal):
        raise ValueError("Approved field is not an exact JSON number")
    requested = Decimal(number)
    field_value_matches = recorded == requested
    # The original engine treats bare small integers as ordinals. A decimal
    # notation presents the same numeric value without changing the request.
    token_number = number if "." in number or "e" in number.lower() else number + ".0"
    claim = f"{field} was {token_number}"
    adapter = root / "integrations/upstream/cmbagent-lg-20261116/audit_claims.py"
    # Reuse the original exact adapter with no application credential env.
    result = subprocess.run(
        [sys.executable, "-E", "-s", str(adapter), "--artifact", artifact, "--claim", claim],
        cwd=root, env={"PATH": os.defpath, "PYTHONIOENCODING": "utf-8"},
        capture_output=True, text=True, timeout=15, check=True,
    )
    if len(result.stdout) > 64_000:
        raise ValueError("Numeric grounding output exceeds approved bounds")
    report = json.loads(result.stdout)
    claims = report.get("claims", [])
    if (report.get("schema") != "plenum-cmbagent-numeric-grounding-v1"
            or report.get("artifact") != artifact
            or report.get("artifact_sha256") != digest
            or report.get("complete_within_selected_artifact") is not True
            or report.get("semantic_truth_verified") is not False
            or report.get("model_inference") is not False
            or report.get("paid_api_calls") != 0
            or len(claims) != 1 or claims[0].get("statement") != claim
            or claims[0].get("state") not in ("grounded", "weakly_grounded", "ungrounded", "partial", "no_quantities")):
        raise ValueError("Original grounding output failed bounded verification")
    labelled_exact = any(
        hit.get("source") == "data/artifact.json"
        and hit.get("tier") == "primary" and hit.get("label") == field_path
        and hit.get("match") == "exact" and Decimal(hit["value"]) == requested
        for quantity in claims[0]["quantities"] for hit in quantity["hits"]
    )
    field_grounded = field_value_matches and labelled_exact
    field_status = ("exact_field_match" if field_grounded else
                    "field_value_mismatch" if not field_value_matches else
                    "value_matches_without_exact_labelled_hit")
    report["field_verification"] = {
        "requested_statement": f"{field} was {number}",
        "exact_json_field": field_path,
        "requested_value": str(requested), "recorded_value": str(recorded),
        "field_value_matches": field_value_matches,
        "exact_labelled_token_hit": labelled_exact,
        "field_grounded": field_grounded, "field_grounding_status": field_status,
        "semantic_truth_verified": False,
    }
    (base / "numeric-claim-grounding.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return {
        "status": "DRAFT_READY_FOR_FOUNDER", "verified": True,
        "verified_scope": f"Numeric audit completed: {field_status}; receipt comparison only, not semantic truth",
        "worker": ROLES["public_verification"],
        "upstream_numeric_token_grounding": claims[0]["state"],
        "field_value_matches": field_value_matches,
        "field_grounded": field_grounded, "field_grounding_status": field_status,
        "semantic_truth_verified": False,
        "model_inference": False, "paid_api_calls": 0,
        "owner_review_required": True,
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

    if kind == "public_verification":
        try:
            result = _ground_public_claim(objective, base)
        except subprocess.SubprocessError as exc:
            raise RuntimeError("Original numeric grounding worker failed") from exc
        return {**result, "output_artifact": str(base.relative_to(output_dir))}

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

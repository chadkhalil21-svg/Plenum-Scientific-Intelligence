"""Bounded, founder-authorized specialist missions using EXISTING Plenum tools.

One local Qwen Chief previously hit LangGraph's recursion ceiling without
finishing a two-worker mission (original run 42796438425). Do NOT multiply
recursion or inference. For unambiguous, PUBLIC tool missions, deterministic
scope-gated routing is faster, cheaper, and produces durable actual artifacts.

No new agent framework/model, private app access, or arbitrary code execution.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from .chief_workforce_command import (
    CHIEF_MAGIC, CHIEF_TITLE, HINTS, KIND_TO_AGENT,
    parse_founder_chief, worker_event,
)
from .workforce_public_inbox import run_issue
from .agent_library import suggest_sources
from .mission_checkpoint import (
    artifact_digest, load_checkpoint, save_checkpoint, verified_previous_result,
)

MISSION_TITLE = "[Plenum Chief] public mission"
MISSION_MAGIC = "PLENUM_CHIEF_PUBLIC_MISSION_V1"


def independent_expected_team(objective: str) -> tuple[str, ...]:
    """Fixed independent permission gate, not an LLM or externally found text."""
    words = set(re.findall(r"[a-z]+", objective.lower()))
    matching = tuple(kind for kind, terms in HINTS.items() if terms & words)
    if not 2 <= len(matching) <= 3:
        raise ValueError("Only two or three unambiguously supported capabilities")
    return matching


def parse_mission(event: dict) -> dict:
    issue = event.get("issue") or {}
    if issue.get("title") != MISSION_TITLE or not isinstance(issue.get("body"), str):
        raise PermissionError("Not a founder-issued Plenum team mission")
    lines = issue["body"].splitlines()
    if len(lines) != 2 or lines[0] != MISSION_MAGIC or not lines[1].startswith("objective: "):
        raise ValueError("Exact two-line founder mission envelope required")
    # Preserve all existing founder, issue, public-input and scope guards.
    original = {**event, "issue": {**issue, "title": CHIEF_TITLE,
                                   "body": CHIEF_MAGIC + "\n" + lines[1]}}
    checked = parse_founder_chief(original)
    return {**checked, "team": independent_expected_team(checked["objective"]),
            "original": original}


def preflight(event: dict) -> dict:
    task = parse_mission(event)
    return {
        "schema": "plenum-chief-founder-team-v2",
        "issue_number": task["issue_number"],
        "status": "SOURCE_READY_NOT_EXECUTED",
        "mode": "multi",
        "dispatcher": "deterministic_existing_chief_scope_gate",
        "expected_team": list(task["team"]),
        # Read-only source suggestions; never import third-party source into the
        # runner or treat a reference as a verified executable worker.
        "candidate_sources": suggest_sources(task["objective"], limit=6),
        "upstream_sources_installed": 0,
        "new_external_models_started": 0,
        "source_selection_inference_calls": 0,
        "model_called": False,
        "chief_model_delegated": False,
        "executed_workers": 0,
        "tool_outputs_verified": False,
        "independent_verified": False,
        "external_account_changes": False,
        "paid_api_used": False,
    }


def independently_accept_team(expected: tuple[str, ...], observed: dict) -> bool:
    """All requested, distinct original tools must complete their own checks."""
    return (
        2 <= len(expected) <= 3
        and len(set(expected)) == len(expected)
        and set(observed) == set(expected)
        and all(
            observed[k].get("status") == "DRAFT_READY_FOR_FOUNDER"
            and observed[k].get("verified") is True
            and isinstance(observed[k].get("worker"), str)
            and bool(observed[k].get("output_artifact"))
            for k in expected
        )
    )



def named_entity_evidence_gate(objective: str, kinds: tuple[str, ...],
                               observed: dict, root: Path) -> dict:
    """Reject obvious mismatch in real worker outputs; never certify task success.

    This is a narrow NEGATIVE gate for explicit names, not semantic AI.
    Read research record title/source/URL (not echoed topic) and actual Python
    code (not README/manifest). No model, account access, or new service.
    """
    named = tuple(
        word for word in ("cloudflare", "noaa", "nasa", "stripe", "github")
        if re.search(r"\b" + word + r"\b", objective, re.IGNORECASE)
    )
    if not named:
        return {"status": "NOT_APPLICABLE", "irrelevant_kinds": []}
    failures = []
    for kind in ("public_research", "public_program"):
        if kind not in kinds:
            continue
        relative = observed[kind].get("_artifact_path")
        if not isinstance(relative, str) or not relative.startswith("workers/" + kind + "/"):
            failures.append(kind)
            continue
        path = root / relative
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            failures.append(kind)
            continue
        try:
            if kind == "public_research":
                if not path.is_file() or path.stat().st_size > 2_000_000:
                    raise ValueError("unsafe research file")
                data = json.loads(path.read_text("utf-8"))
                records = data.get("records", []) if isinstance(data, dict) else []
                if not isinstance(records, list) or len(records) > 200:
                    raise ValueError("invalid records")
                text = " ".join(
                    str(rec.get(field, ""))[:2000]
                    for rec in records if isinstance(rec, dict)
                    for field in ("title", "source", "url")
                )
            else:
                if not path.is_dir():
                    raise ValueError("unknown code directory")
                candidates = [p for p in path.rglob("*.py")
                              if p.is_file() and not p.is_symlink()
                              and not p.name.startswith("test")]
                if len(candidates) > 20 or sum(p.stat().st_size for p in candidates) > 200_000:
                    raise ValueError("unbounded code")
                text = " ".join(p.read_text("utf-8") for p in candidates)
        except (OSError, ValueError, TypeError, UnicodeError):
            failures.append(kind)
            continue
        if not all(re.search(r"\b" + word + r"\b", text, re.IGNORECASE)
                   for word in named):
            failures.append(kind)
    return {"status": "BLOCKED_NAMED_SOURCE_MISMATCH" if failures
                      else "NAME_MENTION_ONLY_NOT_FULL_OBJECTIVE_PROOF",
            "irrelevant_kinds": failures}


# A very small contract whose ENTIRE goal is observable from real first-party
# HTTP source-read receipts and functional local code execution. No broad goal,
# provider content claim or provider account access is certified by this rule.
# This is not a synthetic "completed all agent work" success switch.
EXACT_PUBLIC_ACCEPTANCE_GOALS = {
    "Survey official Cloudflare Workers AI sources and run existing Python neuron budget validator":
        "cloudflare_workers_ai_free",
    "Survey official NOAA station metadata sources and run existing Python station validator":
        "noaa_water_station_metadata",
}


def grade_complete_bounded_public_goal(objective: str, team: tuple[str, ...],
                                       observed: dict, root: Path,
                                       technical_verified: bool,
                                       named: dict) -> dict:
    """Read the REAL specialists' original evidence; accept only two exact goals.

    This intentionally CANNOT certify reading page body, model quality, any
    arbitrary code generation, signed-in browser tasks or general autonomy.
    """
    from hashlib import sha256
    from .reviewed_domain_workers import DOMAIN_SOURCES, DOMAIN_FILES, match_original_capability

    scope = ("first-party public source URL reachability plus the already-reviewed"
             " original Python validator functional test; no website login,"
             " hosted inference, new program creation or private action")
    rejected = {"status": "NOT_A_FULLY_GRADED_GOAL", "scope": scope}
    capability = EXACT_PUBLIC_ACCEPTANCE_GOALS.get(objective)
    if (not capability or team != ("public_research", "public_program")
            or not technical_verified or named.get("irrelevant_kinds")
            or match_original_capability(objective) != capability):
        return rejected
    research_name = observed["public_research"].get("_artifact_path")
    program_name = observed["public_program"].get("_artifact_path")
    if not (isinstance(research_name, str) and isinstance(program_name, str)):
        return rejected
    research_path = root / research_name
    # The original program agent reports its issue-N root, with code/ inside.
    program_dir = root / program_name / "code"
    try:
        if (research_path.is_symlink() or not research_path.is_file()
                or research_path.stat().st_size > 50000
                or not research_path.resolve().is_relative_to(root.resolve())
                or not program_dir.is_dir() or program_dir.is_symlink()
                or not program_dir.resolve().is_relative_to(root.resolve())):
            return rejected
        evidence = json.loads(research_path.read_text(encoding="utf-8"))
        records = evidence.get("records")
        official = DOMAIN_SOURCES[capability]
        expected_urls = {url for _, _, url in official}
        if (evidence.get("schema") != "plenum-public-horizon-snapshot-v1"
                or evidence.get("topic") != objective
                or evidence.get("publisher_document_text_verified") is not False
                or not isinstance(records, list)
                or len(records) != len(expected_urls)
                or {rec.get("url") for rec in records if isinstance(rec, dict)} != expected_urls
                or any(not isinstance(rec, dict)
                       or rec.get("http_status") != 200
                       or rec.get("independently_quoted_page_text") is not False
                       or rec.get("source") != organization
                       for rec, (_, organization, _) in zip(
                           sorted(records, key=lambda x: x.get("url", "")),
                           sorted(official, key=lambda x: x[2])))):
            return rejected
        manifest_path = program_dir / "manifest.json"
        copied_code = program_dir / "main.py"
        original_code = DOMAIN_FILES[capability]
        verifier = program_dir / "test_generated.py"
        if any(p.is_symlink() or not p.is_file()
               or p.stat().st_size > 40000 for p in (
                   manifest_path, copied_code, original_code, verifier)):
            return rejected
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        code = copied_code.read_bytes()
        if (code != original_code.read_bytes()
                or manifest.get("schema") != "plenum-reviewable-program-v1"
                or manifest.get("kind") != capability
                or manifest.get("public_topic") != objective
                or manifest.get("functional_verifier_executed_and_passed") is not True
                or manifest.get("main_sha256") != sha256(code).hexdigest()
                or observed["public_program"].get("actual_offline_functional_test_passed") is not True
                or manifest.get("generated_program_has_not_been_deployed") is not True
                or manifest.get("human_code_review_required") is not True):
            return rejected
    except (OSError, ValueError, TypeError, KeyError, UnicodeError):
        return rejected
    return {
        "status": "VERIFIED_FULL_BOUNDED_PUBLIC_OBJECTIVE",
        "scope": scope,
        "http_200_official_urls": sorted(expected_urls),
        "original_program_sha256": sha256(code).hexdigest(),
        "existing_validator_real_functional_test_passed": True,
        "new_provider_account_or_paid_host_used": False,
    }



def execute(event: dict, *, output_dir: Path) -> dict:
    report = preflight(event)
    task = parse_mission(event)
    # The SAME founder issue and bounded public artifacts are the only mission
    # identity. When a failed GitHub job is retried, its original artifact
    # restores the checkpoint first; do not re-execute completed specialists.
    progress = load_checkpoint(
        output_dir, issue=task["issue_number"],
        objective=task["objective"], team=task["team"],
    )
    observed = {}
    resumed = 0
    executed = 0
    for kind in task["team"]:
        saved = progress.get(kind)
        recovered = verified_previous_result(output_dir, kind, saved)
        if recovered is not None:
            observed[kind] = recovered
            resumed += 1
            continue
        attempt = int(saved.get("attempt", 0)) + 1 if isinstance(saved, dict) else 1
        if attempt > 2:
            observed[kind] = {
                "status": "BLOCKED_RETRY_LIMIT", "verified": False,
                "failure_type": "PreviouslyAttemptedTwice",
            }
            continue
        original_event = worker_event(task["original"], kind)
        base = output_dir / "workers" / kind
        worker_dir = base if attempt == 1 else base / "retry-2"
        executed += 1
        try:
            result = run_issue(original_event, output_dir=worker_dir)
            if not isinstance(result, dict):
                raise ValueError("Original worker returned a non-object")
        except (OSError, ValueError, RuntimeError, KeyError, TypeError, ImportError) as exc:
            result = {
                "status": "BLOCKED_WORKER_OR_VERIFICATION",
                "verified": False,
                "failure_type": type(exc).__name__,
            }
        artifact = result.get("output_artifact")
        relative = (
            (worker_dir / artifact).relative_to(output_dir).as_posix()
            if isinstance(artifact, str) and artifact and not
               (artifact.startswith("/") or ".." in artifact.split("/"))
            else None
        )
        fingerprint = artifact_digest(output_dir, relative) if relative else None
        if (result.get("status") == "DRAFT_READY_FOR_FOUNDER"
                and result.get("verified") is True and not fingerprint):
            result = {
                **result, "status": "BLOCKED_ARTIFACT_NOT_PRESERVED",
                "verified": False, "failure_type": "MissingOrUnsafeArtifact",
            }
        if fingerprint:
            result["_artifact_path"] = relative
        observed[kind] = result
        progress[kind] = {
            "attempt": attempt,
            "status": result.get("status", "BLOCKED"),
            "verified": result.get("verified") is True,
            "worker": result.get("worker"),
            "verified_scope": result.get("verified_scope"),
            "actual_offline_functional_test_passed": (
                result.get("actual_offline_functional_test_passed") is True
            ),
            "output_artifact": artifact,
            "artifact_path": relative if fingerprint else None,
            "sha256": fingerprint,
        }
        # Atomic checkpoint after EACH original specialist, even on failure.
        save_checkpoint(
            output_dir, issue=task["issue_number"],
            objective=task["objective"], team=task["team"],
            results=progress,
        )
    technical_verified = independently_accept_team(task["team"], observed)
    relevance = (named_entity_evidence_gate(
        task["objective"], task["team"], observed, output_dir
    ) if technical_verified else {"status": "NOT_RUN", "irrelevant_kinds": []})
    verified = technical_verified and not relevance["irrelevant_kinds"]
    goal_proof = grade_complete_bounded_public_goal(
        task["objective"], task["team"], observed, output_dir,
        technical_verified, relevance,
    )
    report.update({
        "status": ("VERIFIED_BOUNDED_TEAM" if verified else
                   "BLOCKED_OBJECTIVE_RELEVANCE" if technical_verified else
                   "BLOCKED_PARTIAL_TEAM"),
        "worker_artifacts_technically_verified": technical_verified,
        "founder_objective_verified": (
            goal_proof["status"] == "VERIFIED_FULL_BOUNDED_PUBLIC_OBJECTIVE"
        ),
        "bounded_founder_goal_evidence": goal_proof,
        "named_entity_evidence": relevance["status"],
        "irrelevant_worker_kinds": relevance["irrelevant_kinds"],
        "automated_routing": True,
        "model_called": False,
        "chief_model_delegated": False,
        "executed_workers": len(observed),
        "new_worker_invocations": executed,
        "reused_prior_verified_workers": resumed,
        "resume_checkpoint": ("chief-checkpoint-" + str(task["issue_number"]) + ".json"),
        "checkpoint_is_reusable_across_same_run_retries": True,
        "successfully_verified_workers": sum(
            x.get("status") == "DRAFT_READY_FOR_FOUNDER"
            and x.get("verified") is True for x in observed.values()
        ),
        "specialists": [KIND_TO_AGENT[k] for k in task["team"]],
        "tool_outputs_verified": verified,
        "independent_verified": verified,
        "worker_results": [{
            "kind": kind,
            "worker": observed[kind].get("worker"),
            "status": observed[kind].get("status", "BLOCKED"),
            "verified_scope": observed[kind].get("verified_scope", "not_verified"),
            "output_artifact": (
                observed[kind].get("_artifact_path")
                if observed[kind].get("output_artifact") else None
            ),
            "failure_type": observed[kind].get("failure_type"),
        } for kind in task["team"]],
        "all_existing_worker_tools_reused": True,
        "founder_review_required": True,
        "new_general_agent_capability_claimed": False,
        "external_account_changes": False,
        "paid_api_used": False,
    })
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--out-dir", default="reports/workforce-chief")
    args = parser.parse_args()
    out = Path(args.out_dir)
    if out.is_absolute() or ".." in out.parts or not out.parts or out.parts[0] != "reports":
        parser.error("Only relative reports/ paths accepted")
    event = json.loads(Path(args.event).read_text(encoding="utf-8"))
    report = execute(event, output_dir=out) if args.execute else preflight(event)
    out.mkdir(parents=True, exist_ok=True)
    (out / ("chief-result-" + str(report["issue_number"]) + ".json")).write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print("PLENUM_BOUNDED_TEAM " + report["status"])
    if args.execute and not report["independent_verified"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

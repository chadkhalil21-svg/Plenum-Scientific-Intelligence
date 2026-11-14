"""No-charge, AQuA-informed quality readback of EXISTING public Chief traces.

Google's Ambient Quality Agent (AQuA) diagnoses actual agent traces and
deduplicates recurring failure insights. Its official production application
requires ADK + a cloud telemetry stack; this narrow local adapter does NOT
claim to run Google's package or reach its BigQuery/LLM services.

We inspect the ORIGINAL Chief's already-written JSON artifact, not a fake
success story and never private user/website content. The audit does not
complete the founder's goal or claim that source HTTP 200 means research.
"""
from __future__ import annotations

import argparse
from hashlib import sha256, sha1
from datetime import datetime, timezone
import json
from pathlib import Path
import re

MAX_REPORT_BYTES = 200_000
ALLOWED_STATUSES = frozenset({
    "VERIFIED_BOUNDED_TEAM", "BLOCKED_PARTIAL_TEAM",
    "BLOCKED_OBJECTIVE_RELEVANCE",
    "BLOCKED_WORKER_OR_VERIFICATION", "BLOCKED_NO_PRIMARY_SOURCE_EVIDENCE",
    "SOURCE_READY_NOT_EXECUTED",
    "VERIFIED_BOUNDED_DATA_MISSION", "BLOCKED_DATA_INTEGRITY",
})
AQUA_ORIGINAL = (
    "https://github.com/google/adk-recipes/tree/"
    "ambient-quality-agent/v0.3.0/core/python/ambient-quality-agent"
)


# This is the ACTUAL upstream Google AQuA BigQuery event schema, pinned at
# v0.3.0; using it as a local format does NOT install Google's GCP/ADK engine.
ORIGINAL_AQUA_EVENT_SCHEMA = (
    Path(__file__).resolve().parents[2]
    / "integrations/upstream/google-aqua-v0.3.0/schemas/agent_events.schema.json"
)
AQUA_EVENTS_GIT_BLOB_SHA = "78b6fbe3319a0932cd2fcdf3f55ecca3ee5822e1"
AQUA_FIELDS = (
    "timestamp", "event_type", "agent", "session_id",
    "invocation_id", "content", "attributes", "error_message",
)


def read_official_aqua_event_schema():
    """Original Google v0.3.0 telemetry format and byte-identical Git blob."""
    path = ORIGINAL_AQUA_EVENT_SCHEMA
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 2000:
        raise ValueError("Missing or unsafe official Google AQuA telemetry source")
    raw = path.read_bytes()
    digest = sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
    if digest != AQUA_EVENTS_GIT_BLOB_SHA:
        raise ValueError("Google AQuA source checksum mismatch")
    fields = json.loads(raw)
    if not isinstance(fields, list) or tuple(x.get("name") for x in fields) != AQUA_FIELDS:
        raise ValueError("Unexpected official Google AQuA schema")
    return fields


def make_offline_aqua_event(issue, status, disposition, findings):
    """No private data: map ORIGINAL public mission flags to original schema."""
    read_official_aqua_event_schema()
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "PLENUM_PUBLIC_CHIEF_QUALITY_INSIGHT",
        "agent": "plenum-original-chief",
        "session_id": "public-issue-" + str(issue),
        "invocation_id": "same-run-original-" + str(issue),
        "content": {"finding_codes": [x["code"] for x in findings]},
        "attributes": {"original_status": status, "disposition": disposition},
        "error_message": None,
    }
    if tuple(event) != AQUA_FIELDS:
        raise ValueError("Original event schema mapping drifted")
    return event


def inspect_chief_report(report: dict) -> dict:
    """Fail closed: outcome evidence from a real bounded public Chief report."""
    if not isinstance(report, dict) or (
        report.get("schema") != "plenum-chief-founder-team-v2"
    ) or not isinstance(report.get("issue_number"), int) or (
        report["issue_number"] <= 0
    ):
        raise ValueError("Not the original Chief mission result")
    status = report.get("status")
    if status not in ALLOWED_STATUSES:
        raise ValueError("Unrecognized original Chief result status")
    findings = []

    def record(code, reason):
        findings.append({
            "code": code,
            "reason": reason,
            "identity": sha256(
                (str(report["issue_number"]) + ":" + code).encode()
            ).hexdigest()[:16],
            "state": "OBSERVED_THIS_RUN_NOT_LONGITUDINALLY_PROVEN",
        })

    if report.get("paid_api_used") is not False or (
        report.get("external_account_changes") is not False
    ):
        record("COST_OR_PRIVATE_SCOPE_UNVERIFIED",
               "Public run cost/account scope not independently safe")
    bounded_delivery = status == "VERIFIED_BOUNDED_TEAM" or (
        status == "VERIFIED_BOUNDED_DATA_MISSION"
        and report.get("bounded_metadata_contract_verified") is True
    )
    if not bounded_delivery:
        record("ORIGINAL_WORKFORCE_NOT_COMPLETED",
               "The original specialist team did not finish with bounded verification")
    if report.get("worker_artifacts_technically_verified") is not True:
        record("ARTIFACT_VERIFICATION_MISSING",
               "Missing verified original specialist output")
    full_goal = (
        status == "VERIFIED_BOUNDED_TEAM"
        and report.get("founder_objective_verified") is True
        and isinstance(report.get("bounded_founder_goal_evidence"), dict)
        and report["bounded_founder_goal_evidence"].get("status")
            == "VERIFIED_FULL_BOUNDED_PUBLIC_OBJECTIVE"
    )
    if not full_goal and report.get("named_entity_evidence") == (
        "NAME_MENTION_ONLY_NOT_FULL_OBJECTIVE_PROOF"
    ):
        record("NAME_MENTION_NOT_TASK_COMPLETION",
               "A source mentioning the named provider is not proof of the full task")
    if report.get("founder_objective_verified") is not True:
        record("FOUNDER_OBJECTIVE_NOT_PROVEN",
               "Original Chief explicitly did not prove founder-level completion")
    if not findings:
        # Do not permit generic downstream jobs to silently promote
        # a verifier flag to account-write or global-autonomy permission.
        disposition = (
            "VERIFIED_FULL_BOUNDED_PUBLIC_OBJECTIVE_NOT_GENERAL_AUTONOMY"
            if full_goal else "PUBLIC_TASK_FLAGS_VERIFIED_NOT_GENERAL_AUTONOMY"
        )
    elif bounded_delivery and all(
        x["code"] in {
            "FOUNDER_OBJECTIVE_NOT_PROVEN",
            "NAME_MENTION_NOT_TASK_COMPLETION",
        }
        for x in findings
    ):
        disposition = "BOUNDED_DELIVERY_FOUNDER_OBJECTIVE_OPEN"
    else:
        disposition = "BLOCKED_OR_UNVERIFIED_DO_NOT_PROMOTE"

    return {
        "schema": "plenum-chief-offline-ambient-quality-v1",
        "original_issue_number": report["issue_number"],
        "original_chief_status": status,
        "disposition": disposition,
        "findings": findings,
        "source": "original_same_run_chief_result_json",
        "cost_ceiling_additional_usd": 0,
        "external_model_calls": 0,
        "private_accounts_touched": False,
        "method": "local trace diagnostic following Google AQuA insight discipline",
        "method_source": AQUA_ORIGINAL,
        "actual_google_aqua_event_schema_used": True,
        "event_schema_git_blob_sha": AQUA_EVENTS_GIT_BLOB_SHA,
        "offline_aqua_compatible_event": make_offline_aqua_event(
            report["issue_number"], status, disposition, findings
        ),
        "official_google_aqua_engine_installed": False,
        "google_cloud_telemetry_queried": False,
        "longitudinal_recurring_insights_claimed": False,
        "full_general_autonomy_claimed": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue", type=int, required=True)
    parser.add_argument("--root", type=Path, default=Path("reports/workforce-chief"))
    args = parser.parse_args()
    if args.issue < 1 or args.issue > 999999999:
        parser.error("Invalid original founder issue")
    root = args.root
    source = root / ("chief-result-" + str(args.issue) + ".json")
    if (not source.is_file() or source.is_symlink()
            or source.stat().st_size > MAX_REPORT_BYTES
            or not source.resolve().is_relative_to(root.resolve())):
        parser.error("No safe original Chief report exists")
    data = json.loads(source.read_text(encoding="utf-8"))
    result = inspect_chief_report(data)
    output = root / ("ambient-quality-" + str(args.issue) + ".json")
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print("ORIGINAL_CHIEF_AQUA_INSPIRED_DISPOSITION " + result["disposition"])


if __name__ == "__main__":
    main()

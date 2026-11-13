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
from hashlib import sha256
import json
from pathlib import Path
import re

MAX_REPORT_BYTES = 200_000
ALLOWED_STATUSES = frozenset({
    "VERIFIED_BOUNDED_TEAM", "BLOCKED_PARTIAL_TEAM",
    "BLOCKED_WORKER_OR_VERIFICATION", "BLOCKED_NO_PRIMARY_SOURCE_EVIDENCE",
    "SOURCE_READY_NOT_EXECUTED",
})
AQUA_ORIGINAL = (
    "https://github.com/google/adk-recipes/tree/"
    "ambient-quality-agent/v0.3.0/core/python/ambient-quality-agent"
)


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
    if status != "VERIFIED_BOUNDED_TEAM":
        record("ORIGINAL_WORKFORCE_NOT_COMPLETED",
               "The original specialist team did not finish with bounded verification")
    if report.get("worker_artifacts_technically_verified") is not True:
        record("ARTIFACT_VERIFICATION_MISSING",
               "Missing verified original specialist output")
    if report.get("named_entity_evidence") == (
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
        disposition = "PUBLIC_TASK_FLAGS_VERIFIED_NOT_GENERAL_AUTONOMY"
    elif status == "VERIFIED_BOUNDED_TEAM" and all(
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

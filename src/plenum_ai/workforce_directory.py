"""Read-only five-workforce directory from Plenum's ORIGINAL registries.

This command reports known logical departments and existing role definitions.
It never installs managers, launches agents, authenticates, or asserts 24/7 work.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "integrations/workforces/five-workforces.json"
ROSTER = ROOT / "integrations/hermes/roster.json"
EXPECTED = frozenset({
    "scientific_research", "engineering_manufacturing", "commercial_operations",
    "global_intelligence", "verification_council",
})


def build_directory(registry_path: Path = REGISTRY, roster_path: Path = ROSTER) -> dict:
    registry = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    roster = json.loads(Path(roster_path).read_text(encoding="utf-8"))
    divisions = registry["workforces"]
    roles = {role["name"]: role for role in roster["roles"]}
    if (registry.get("schema") != "plenum-five-workforce-registry-v1"
            or roster.get("schema") != "plenum-hermes-profile-roster-v1"
            or len(divisions) != 5
            or {division["id"] for division in divisions} != EXPECTED
            or len(roles) != len(roster["roles"])
            or "chief" not in roles
            or registry.get("default_cost_ceiling_usd") != 0):
        raise ValueError("Unreviewed source registries cannot form workforce directory")
    groups = []
    for division in divisions:
        members = []
        for role in division["roles"]:
            # Existing source registry says engineering; Hermes named role is coding.
            slug = "coding" if role == "engineering" else role
            if slug not in roles:
                raise ValueError("Division refers to an unknown existing specialist")
            members.append({
                "role": role,
                "named_hermes_profile": slug,
                "display_title": roles[slug]["title"],
                "profile_only_not_proof_of_running_agent": True,
            })
        groups.append({
            "id": division["id"],
            "name": division["name"],
            "lead": division["lead"],
            "members": members,
            "runtime": division["runtime"],
            "verified_source_state": division["state"],
            "private_access": division["private_integrations"],
        })
    return {
        "schema": "plenum-operating-directory-v1",
        "source_date_utc": registry["updated_utc"],
        "chief_role": "chief",
        "chief_current_title": roles["chief"]["title"],
        "chief_proposed_display_title": "AI Minister of Operations",
        "workforce_count": len(groups),
        "named_profile_definitions": len(roles),
        "named_profiles_confirmed_running": None,
        "division_members_can_overlap": True,
        "business_advisory": {
            "status": "business_advisor_profile_defined_and_public_council_available; private execution not verified",
            "named_business_advisor_role": "business_advisor",
            "owner_divisions": ["commercial_operations", "verification_council"],
            "advice_areas": [
                "strategy", "operations", "finance_and_funding",
                "partnerships", "governance_and_IP_issues", "independent_review",
            ],
            "private_account_access": False,
            "live_billing_or_legal_advice": False,
        },
        "integration_layers": [
            {"tool": "GitHub", "job": "canonical public work and evidence", "state": "existing_active_bounded"},
            {"tool": "LangGraph and Deep Agents", "job": "existing Chief delegation and checkpointed orchestration", "state": "existing_bounded"},
            {"tool": "n8n", "job": "nine specialist draft workflows and schedules", "state": "source_review_only_not_live_full_company"},
            {"tool": "Paperclip", "job": "optional org chart, approvals, budget and task dashboard", "state": "source_review_only_host_missing"},
            {"tool": "Hermes", "job": "existing named profile definitions and proposed messaging gateway", "state": "profiles_prepared_no_live_gateway"},
            {"tool": "OpenClaw", "job": "optional distinct agent or channel adapter under Paperclip; never duplicate WhatsApp Chief", "state": "source_candidate_not_installed"},
        ],
        "group_count_is_not_running_agent_count": True,
        "groups": groups,
    }


def format_chart(directory: dict) -> str:
    lines = [
        "FOUNDER — Plenum Industries",
        "  AI Minister of Operations (PROPOSED title; technical role chief)",
    ]
    for index, group in enumerate(directory["groups"], 1):
        people = ", ".join(m["named_hermes_profile"] for m in group["members"])
        lines.append(f"    {index}. {group['name']} — roles: {people}")
    lines.append("  Business Advisor — named profile in Commercial Operations; Advisory Council — consultative review across Commercial Operations + Verification")
    lines.append("  Source-only profiles and workforces are not all always-on employees.")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print factual machine-readable operating directory")
    args = parser.parse_args(argv)
    report = build_directory()
    print(json.dumps(report, indent=2) if args.json else format_chart(report))


if __name__ == "__main__":
    main()

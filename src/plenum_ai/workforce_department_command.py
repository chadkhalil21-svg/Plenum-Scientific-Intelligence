"""Direct one of nine EXISTING native n8n AI Agent role profiles from ChatGPT.

PUBLIC GitHub issue commands only. Never move private data into public CI.
The actual model, n8n workflow and model-agent node remain the originals.
"""
from __future__ import annotations

import json
from pathlib import Path

from .workforce_public_inbox import OWNER, REPO, TOPIC

TITLE = "[Plenum Department] public assignment"
MAGIC = "PLENUM_DEPARTMENT_PUBLIC_V1"
ROLES = frozenset({
    "research", "engineering", "browser", "creative", "marketing",
    "operations", "simulation", "support", "verification",
})
BANNED = (
    "password", "token", "secret", "credential", "private", "confidential",
    "customer", "patient", "payment", "bank", "account", "deploy", "send email",
    "live customer", "contact leads", "personally identifiable", "patent",
)


def parse_founder_department(event):
    issue = event.get("issue") or {}
    if (
        event.get("action") != "opened"
        or (event.get("repository") or {}).get("full_name") != REPO
        or (issue.get("user") or {}).get("login") != OWNER
        or issue.get("title") != TITLE
        or not isinstance(issue.get("number"), int)
        or not 0 < issue["number"] < 10**9
        or not isinstance(issue.get("body"), str)
    ):
        raise PermissionError("Only founder PUBLIC department issues")
    lines = issue["body"].splitlines()
    if (
        len(lines) != 3 or lines[0] != MAGIC
        or not lines[1].startswith("role: ")
        or not lines[2].startswith("objective: ")
    ):
        raise ValueError("Exact founder role and objective required")
    role = lines[1][6:]
    objective = lines[2][11:]
    if role not in ROLES or not TOPIC.fullmatch(objective) or objective != objective.strip():
        raise ValueError("Unknown department or unbounded objective")
    if any(x in objective.lower() for x in BANNED):
        raise PermissionError("Sensitive or consequential work forbidden in PUBLIC issue")
    return {
        "schema": "plenum-department-command-v1",
        "issue_number": issue["number"],
        "role": role,
        "objective": objective,
        "approval": "public-draft-only",
        "external_writes_authorized": False,
        "customer_accounts_connected": False,
    }


def tailor_original_n8n_workflow(source: dict, task: dict) -> dict:
    """Edit ONLY original n8n mission+one-role selection; no tool permissions."""
    if (not isinstance(source, dict) or task["role"] not in ROLES
            or task.get("approval") != "public-draft-only"):
        raise PermissionError("Invalid authorized department")
    workflow = json.loads(json.dumps(source))
    if workflow.get("active") is not False or len(workflow.get("nodes", [])) != 6:
        raise ValueError("Original native n8n workforce schema changed")
    node = next(x for x in workflow["nodes"] if x.get("name") == "Assign Nine Roles")
    script = node["parameters"]["jsCode"]
    original = (
        'const mission = "Prepare an evidence-based, non-confidential '
        'operating plan for a one-person technology company.";'
    )
    if script.count(original) != 1 or script.count("return roles.map(") != 1:
        raise ValueError("Original n8n role dispatcher changed; fail closed")
    script = script.replace(original, "const mission = " + json.dumps(task["objective"]) + ";")
    script = script.replace(
        "return roles.map(",
        "return roles.filter(([role]) => role === "
        + json.dumps(task["role"]) + ").map(",
    )
    node["parameters"]["jsCode"] = script
    workflow["id"] = "plenum-n8n-single-public-department"
    return workflow


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True)
    parser.add_argument("--workflow", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    task = parse_founder_department(json.loads(Path(args.event).read_text()))
    original = json.loads(Path(args.workflow).read_text())
    tailored = tailor_original_n8n_workflow(original, task)
    out = Path(args.out)
    if out.is_absolute() or ".." in out.parts or out.parts[0] != "runtime-trial":
        parser.error("Output must remain inside isolated runtime-trial")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(tailored) + "\n")
    (out.parent / "department-metadata.json").write_text(
        json.dumps({k:task[k] for k in ("schema","issue_number","role","approval")})+"\n")
    print("APPROVED_PUBLIC_DEPARTMENT role=" + task["role"]
          + " issue=" + str(task["issue_number"]) + " no_customer_accounts")


if __name__ == "__main__":
    main()

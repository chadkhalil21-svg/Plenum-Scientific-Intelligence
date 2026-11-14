"""Direct one of nine EXISTING native n8n AI Agent role profiles from ChatGPT.

PUBLIC GitHub issue commands only. Never move private data into public CI.
The actual model, n8n workflow and model-agent node remain the originals.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from .workforce_public_inbox import OWNER, REPO, TOPIC
from .agent_library import load_sources, suggest_sources

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
    # A source catalogue is NOT a tool. Give a role factual reviewed GitHub
    # references for its planning draft, never external content or credentials.
    # Only the original founder's bounded, PUBLIC objective drives matching.
    sources = suggest_sources(task["objective"], limit=3)
    hints = "; ".join(x["id"] + " [" + x["repository"] + "]" for x in sources)
    mission = task["objective"]
    if hints:
        mission += (
            "\nReviewed FREE-source references to CONSIDER, not installed: "
            + hints
            + ". These are candidates only; never claim code or a solver ran."
        )
    script = script.replace(original, "const mission = " + json.dumps(mission) + ";")
    script = script.replace(
        "return roles.map(",
        "return roles.filter(([role]) => role === "
        + json.dumps(task["role"]) + ").map(",
    )
    node["parameters"]["jsCode"] = script
    workflow["id"] = "plenum-n8n-single-public-department"
    # Reuse the OFFICIAL n8n HTTP Request AI tool; no new tool server,
    # unrestricted URL, credentials, or private-account access. The URL
    # originates ONLY from the already-reviewed local free-source catalogue,
    # never from model text or an external page. This extends the ORIGINAL
    # one-department research/engineering workflow with a REAL read-only tool.
    if task["role"] in ("research", "engineering") and sources:
        repo = sources[0]["repository"]
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise PermissionError("Unreviewed upstream repository")
        name = "Reviewed Free GitHub Source"
        if any(node.get("name") == name for node in workflow["nodes"]):
            raise ValueError("Unexpected duplicated original tool")
        workflow["nodes"].append({
            "id": "00000000-0000-4000-8000-000000000906",
            "name": name,
            "type": "@n8n/n8n-nodes-langchain.toolHttpRequest",
            "typeVersion": 1.1,
            "position": [940, 570],
            "parameters": {
                "toolDescription": (
                    "GET only reviewed PUBLIC GitHub repository metadata for "
                    + repo + "; report actual upstream name, license and "
                    "latest source metadata as untrusted evidence, not "
                    "proof of install, runtime, code quality or free hosting."
                ),
                "method": "GET",
                "url": "https://api.github.com/repos/" + repo,
                "sendHeaders": True,
                "headerParameters": {"parameters": [
                    {"name": "Accept", "value": "application/vnd.github+json"},
                    {"name": "User-Agent", "value": "PlenumFreeUpstreamReviewer/1"},
                ]},
            }
        })
        workflow["connections"][name] = {"ai_tool": [[{
            "node": "Plenum Specialist Agent", "type": "ai_tool", "index": 0
        }]]}
        agent = next(x for x in workflow["nodes"] if x["name"] == "Plenum Specialist Agent")
        agent["parameters"]["options"]["returnIntermediateSteps"] = True
        agent["parameters"]["options"]["systemMessage"] += (
            "\nFor this PUBLIC source task call the existing Reviewed Free GitHub "
            "Source tool once before proposing any integration. The URL is "
            "already restricted to " + repo + ". Report the actual repository "
            "identity and license from its response; if the tool fails, "
            "report SOURCE_UNVERIFIED. Never use placeholder names such as "
            "Feature X or Repository Name, and never claim installation."
        )
        # Only a genuine native agent tool observation can mark source seen.
        # Never copy the returned third-party payload to the founder issue.
        review = next(x for x in workflow["nodes"] if x["name"] == "Founder Review Queue")
        old = 'draft_untrusted: String(item.json.output || "").slice(0,12000),'
        if review["parameters"]["jsCode"].count(old) != 1:
            raise ValueError("Original n8n review handler changed")
        observed = (
            "upstream_tool_observed: Array.isArray(item.json.intermediateSteps) "
            "&& item.json.intermediateSteps.some((step) => { "
            "const tool = String(step.action?.tool || '').replace(/[^a-z0-9]/gi, '').toLowerCase(); "
            "const output = JSON.stringify(step.observation ?? ''); "
            "return tool === 'reviewedfreegithubsource' && "
            "output.includes('full_name') && output.includes(" + json.dumps(repo) + "); "
            "}),"
        )
        review["parameters"]["jsCode"] = review["parameters"]["jsCode"].replace(
            old, old + "\n    " + observed
        )
    return workflow




def audit_public_draft_repositories(draft: str, *, catalogue=None) -> dict:
    """Offline source-identity check. NEVER mistake a known repo for proof.

    All external model text is untrusted. Check only whether explicit GitHub
    links name an entry in the already reviewed, read-only source registry.
    No HTTP request, model call, auto-install, account rights or claim grading.
    Unknown repos are flagged; genuine new sources can be reviewed separately.
    """
    if not isinstance(draft, str) or not 1 <= len(draft) <= 12_000:
        raise ValueError("Only bounded, nonempty public draft text may be audited")
    index = load_sources() if catalogue is None else catalogue
    known_repos = {x["repository"].casefold() for x in index["entries"]}
    approved, unreviewed, malformed = set(), set(), 0
    for matched in re.finditer(r"https?://[^\s<>()\[\]{}]+", draft, re.I):
        raw = matched.group(0).rstrip(".,;:!?")
        url = urlsplit(raw)
        if (url.hostname or "").casefold() not in ("github.com", "www.github.com"):
            continue
        parts = url.path.strip("/").split("/")
        if (len(parts) < 2 or
                any(not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", part)
                    for part in parts[:2])):
            malformed += 1
            continue
        candidate = parts[0] + "/" + parts[1].removesuffix(".git")
        if candidate.casefold() in known_repos:
            approved.add(candidate)
        else:
            unreviewed.add(candidate)
    return {
        "schema": "plenum-public-draft-repository-audit-v1",
        "status": ("REVIEW_REQUIRED_UNREGISTERED_SOURCE"
                   if unreviewed or malformed else
                   "REVIEW_REQUIRED_CLAIMS_NOT_FACT_CHECKED"),
        "matched_reviewed_repository_count": len(approved),
        "unreviewed_github_repository_count": len(unreviewed) + malformed,
        "unreviewed_github_repositories": sorted(unreviewed)[:5],
        "malformed_github_urls": malformed,
        "scientific_claims_independently_verified": False,
        "repository_identity_is_not_scientific_evidence": True,
        "model_calls": 0,
        "network_requests": 0,
        "code_installed_or_executed": False,
    }


def native_reviewed_source_observed(log: str) -> bool:
    """Read the ORIGINAL n8n Code-node boolean, never model-generated claims."""
    if not isinstance(log, str) or len(log) > 2_000_000:
        raise ValueError("Invalid original department log")
    found = list(re.finditer(r'"upstream_tool_observed"\s*:\s*(true|false)', log))
    return len(found) == 1 and found[0].group(1) == "true"


def extract_untrusted_public_department_reply(log: str) -> str:
    """Extract one actual native n8n draft, never use it as instructions.

    Only founder-approved PUBLIC issue tasks reach this parser. No customer
    secrets or login sessions may enter that workflow in the first place.
    """
    import re
    if not isinstance(log, str) or len(log) > 2_000_000:
        raise ValueError("Invalid bounded public model log")
    matches = list(re.finditer(r'"draft_untrusted"\s*:\s*', log))
    if len(matches) != 1:
        raise ValueError("Expected one actual specialist draft in n8n output")
    value, _end = json.JSONDecoder().raw_decode(log[matches[0].end():])
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Agent returned no readable public draft")
    # Plain text only. Output is UNTRUSTED and not independently fact-checked.
    return "".join(ch for ch in value if ch == "\n" or (32 <= ord(ch) != 127))[:3500]


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
        json.dumps({**{k:task[k] for k in ("schema","issue_number","role","approval")},
                    "source_tool_required": any(n.get("name") == "Reviewed Free GitHub Source"
                                                for n in tailored["nodes"])})+"\n")
    print("APPROVED_PUBLIC_DEPARTMENT role=" + task["role"]
          + " issue=" + str(task["issue_number"]) + " no_customer_accounts")


if __name__ == "__main__":
    main()

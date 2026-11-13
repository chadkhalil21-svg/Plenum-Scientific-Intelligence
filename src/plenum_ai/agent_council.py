"""Founder-gated, PUBLIC, ephemeral multi-perspective Plenum AI council.

The Chief is a coordinator, not a new model. Each seat is a fresh call to
the pre-existing local Ollama runtime and receives no app/browser/tool access.
No advisor/person is impersonated; Ford/Rockefeller/Jobs are public lenses.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import urllib.request

REPO = "chadkhalil21-svg/Plenum-Scientific-Intelligence"
FOUNDER = "chadkhalil21-svg"
TITLE = "[Plenum Council] public agenda"
MARKER = "PLENUM_COUNCIL_PUBLIC_V1"
MODEL_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen3:1.7b"
# Compact instruction derived from pinned MIT Humanizer and Plenum editorial standard.
# Full 32k Markdown skill is for an approved Hermes skill-loader, not every Qwen call.
EDITORIAL_DIRECTIVE = (
    "Be factual, natural, concise and specific. Lead with the real answer; "
    "omit inflated claims, staged slogans, rote three-item lists and closing "
    "fragments. Vary sentence rhythm without changing evidence, citations, "
    "names, financial values or uncertainty. Plain prose must not disguise "
    "lack of source verification or pretend a model recommendation is execution."
)

BANNED = (
    "password", "credential", "token", "secret", "private", "confidential",
    "customer", "patient", "patent", "bank", "account", "production",
    "send email", "payment", "delete", "deploy", "authorization",
)
VERIFIED_CONTEXT = (
    "Evidence from Plenum's 2026-11-10 public repository: "
    "the existing Plenum Chief and nine n8n specialist departments already exist; "
    "the current new catalog contains 283 MIT-licensed *dormant persona definitions*, "
    "not 283 autonomous employees; the media index has 1106 AGPL-3.0 "
    "Markdown skills/reference files, not 1106 running AI agents; "
    "GitHub Actions supports bounded public tasks, and the existing dashboard "
    "is a static source-backed UI, not a verified always-on private agent host. "
    "No verified Plenum blockchain, decentralized consensus backend, "
    "external customer-base size, production agent account integrations, or "
    "unlimited free model inference are evidenced. "
    "Do not recommend inventing a blockchain, new hosting framework or "
    "duplicate master agent without a concrete measured need. "
    "Prefer reusing these established components and small reversible tests. "
    "Any claim outside these recorded facts must be marked UNVERIFIED."
)
SEATS = (
    ("chief", "Clarify the founder's objective, two alternative approaches, and acceptance criteria. Do not claim that tools were used."),
    ("engineer", "Independently critique technical feasibility, reuse of existing Plenum components, measurable tests, and failure modes. Ford standardization and MIT engineering rigor are decision lenses, not actual participants."),
    ("economist", "Independently assess zero-cost options, operating complexity, and opportunity cost. Rockefeller resource discipline and Harvard business reasoning are decision lenses, not actual participants."),
    ("product", "Independently consider user experience, simplicity, speed and practicality. Jobs product clarity and Stanford commercialization reasoning are decision lenses, not actual participants."),
)


# Separate simulated business-advisory lenses. One shared ephemeral model;
# these are not employees, a board of directors, or licensed advisors.
BUSINESS_SEATS = (
    ("operations", "As a fractional COO lens, prioritize deliverables, owners, milestones, and evidence of completed work; do not assume business account access."),
    ("finance", "As a CFO lens, challenge cash runway and funding assumptions, identify data still needed, prefer zero new cost, and never invent cash or revenue numbers."),
    ("strategy", "As a strategy and commercialization lens, identify customer hypotheses, go-to-market experiments, alternatives, and a measurable next decision."),
    ("governance", "As a nonbinding governance and IP-risk lens, flag matters for qualified professional counsel, distinguish advisory advice from corporate board authority, and challenge unsupported claims."),
)


def council_seats(objective: str):
    """Route business advisory agendas to useful specialist perspectives.

    No new models, credentials, tools, executive appointments or payments.
    The same existing founder-public council invocation runs either set.
    """
    topic = objective.lower()
    if "business advisory" in topic or "business operations" in topic:
        return BUSINESS_SEATS
    return SEATS


def _valid_objective(s):
    return (
        isinstance(s, str) and 20 <= len(s) <= 120
        and s == s.strip() and "\n" not in s and "\r" not in s
        and all(c.isalnum() or c in " .,()-_+/?" for c in s)
        and not any(word in s.lower() for word in BANNED)
    )


def parse_event(event):
    issue = event.get("issue") or {}
    if (
        event.get("action") != "opened"
        or (event.get("repository") or {}).get("full_name") != REPO
        or (issue.get("user") or {}).get("login") != FOUNDER
        or issue.get("title") != TITLE
        or not isinstance(issue.get("number"), int)
        or not 0 < issue["number"] < 10**9
        or not isinstance(issue.get("body"), str)
    ):
        raise PermissionError("Only original founder-issued PUBLIC council agendas")
    lines = issue["body"].splitlines()
    if len(lines) != 2 or lines[0] != MARKER or not lines[1].startswith("objective: "):
        raise ValueError("Exact council agenda envelope required")
    objective = lines[1][11:]
    if not _valid_objective(objective):
        raise PermissionError("Council agenda must be short, public and nonsensitive")
    return {"issue": issue["number"], "objective": objective}


ELEPHANT_PUBLIC_FILE = Path(__file__).resolve().parents[2] / "docs/PLENUM_ELEPHANT_PUBLIC.json"

PLATFORM_PUBLIC_REGISTRY = Path(__file__).resolve().parents[2] / "integrations/workforces/founder_all_tools_registry.json"

def read_public_tool_adoption_context(objective: str, path=PLATFORM_PUBLIC_REGISTRY) -> str:
    """Selective fact context for approved PUBLIC tool-adoption council agendas."""
    text = objective.casefold()
    if not any(term in text for term in ("tool", "skills", "platform", "software", "adopt", "free", "workforce")):
        return ""
    registry = json.loads(Path(path).read_text(encoding="utf-8"))
    items = registry.get("items")
    if (registry.get("schema") != "plenum-founder-all-tools-registry-v1"
            or not isinstance(items, list) or len(items) != 84
            or registry.get("summary", {}).get("installed_all") is not False):
        raise ValueError("Unexpected or unchecked public platform registry")
    wanted = ("Humanizer", "Last30Days", "SkillSpector", "Superpowers",
              "whisper.cpp", "Freebuff", "Airia", "Google AQuA",
              "Cloudflare Workers Free", "GitHub Actions", "Hermes Agent")
    selected = {row["name"]: row for row in items if row.get("name") in wanted}
    if len(selected) != len(wanted):
        raise ValueError("Missing core founder adoption evidence")
    decisions = "; ".join(name + "=" + selected[name]["adoption_status"] for name in wanted)
    return ("Founder no-new-spend policy. Verified PUBLIC 84-platform registry,"
            " not 84 installations; role-specific skills only. " + decisions +
            ". Full vendor apps and owner accounts NOT auto-installed. ")



def read_elephant_public(path=ELEPHANT_PUBLIC_FILE):
    """Read founder-approved public fact links, not a previous model's thoughts."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = data.get("records")
    if (data.get("schema") != "plenum-elephant-public-facts-v1"
            or not isinstance(rows,list) or not 1 <= len(rows) <= 8):
        raise ValueError("Missing or unreviewed Elephant facts")
    lines=[]
    for row in rows:
        fact, url, status = row.get("fact"), row.get("url"), row.get("status")
        if (not isinstance(fact,str) or not 20 <= len(fact) <= 180
                or any(c in fact for c in (chr(10), chr(13), "<", ">"))
                or not isinstance(url,str)
                or not url.startswith("https://github.com/" + REPO + "/")
                or status not in ("VERIFIED_BOUNDED","SOURCE_ONLY","BLOCKED","APPROVAL_NEEDED")):
            raise ValueError("Unreviewed Elephant fact or reference")
        lines.append(status + ": " + fact + " (" + url + ")")
    return "DATED PUBLIC ELEPHANT EVIDENCE ONLY; verify live status independently:" + chr(10) + chr(10).join(lines)



# Genuine upstream Google Elephant-Goldfish Model source, Apache-2.0.
# v0.1.1 is pinned by its EXACT source Git blob, not a mutable GitHub URL.
# This selects ONE native fresh-context role of the original EGM plugin;
# the full 5-stage EGM review pipeline is NOT installed or claimed active.
EGM_PERSONA = (
    Path(__file__).resolve().parents[2]
    / "integrations/upstream/google-egm-v0.1.1/agents/design_critic.md"
)
EGM_GIT_BLOB_SHA = "7f57159d623f898a8e683a5b7f312e8f11f84321"


def read_real_google_egm_design_critic(path=EGM_PERSONA):
    """Read exact pinned upstream read-only Goldfish persona, never invented.

    A model receives this persona in a fresh request without previous
    council prompts, private context, credentials or account actions.
    """
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 8000:
        raise ValueError("Missing, oversized or unsafe official EGM persona")
    raw = path.read_bytes()
    digest = hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()
    if digest != EGM_GIT_BLOB_SHA:
        raise ValueError("Official EGM reviewer source did not match pinned v0.1.1")
    text = raw.decode("utf-8")
    if ("name: egm-design" not in text
            or "license: Apache-2.0" not in text
            or "You are **Design Critic Goldfish**." not in text
            or "Strict Read-Only Protocol" not in text):
        raise ValueError("Original EGM reviewer instructions not verified")
    return text

def _ask_local(system, user):
    payload = json.dumps({
        "model": MODEL, "stream": False, "think": False,
        "messages": [
            {"role": "system", "content": system + "\n" + EDITORIAL_DIRECTIVE},
            {"role": "user", "content": user},
        ],
        "options": {"num_predict": 500, "temperature": 0.2, "num_ctx": 4096},
    }).encode()
    request = urllib.request.Request(
        MODEL_URL, data=payload, method="POST",
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=110) as reply:
        if reply.status != 200:
            raise RuntimeError("Local model unavailable")
        data = json.loads(reply.read(40000))
    answer = data.get("message", {}).get("content")
    if not isinstance(answer, str) or len(answer.strip()) < 25:
        raise ValueError("Local agent produced no meaningful deliberation")
    return answer.strip()[:2200]


def deliberate(event):
    task = parse_event(event)
    if (os.environ.get("PLENUM_EPHEMERAL_RUNNER") != "confirmed"
            or os.environ.get("PLENUM_COUNCIL_MODEL_URL") != MODEL_URL):
        raise PermissionError("Council requires explicit isolated Qwen runner")
    elephant = read_elephant_public()
    tool_decisions = read_public_tool_adoption_context(task["objective"])
    results = []
    for name, remit in council_seats(task["objective"]):
        # Distinct fresh model contexts, not synthetic labels on one response.
        draft = _ask_local(
            "You are a separate Plenum AI council reviewer. " + VERIFIED_CONTEXT +
            " " + elephant + " " + tool_decisions + " " + remit +
            " Return: proposal, strongest objection, suggested small first test. "
            "Do not access tools, accounts or invent citations. You are an AI "
            "using an intellectual lens, NOT the historical person or institution.",
            "PUBLIC founder agenda: " + task["objective"],
        )
        results.append({"role": name, "draft_untrusted": draft,
                        "independent_context": True, "model_used": MODEL})
    dossier = "\n".join(
        item["role"] + ":\n" + item["draft_untrusted"]
        for item in results
    )
    # Reviewer sees the decision artifacts, but none of the earlier seat prompts.
    fresh = _ask_local(
        "You are a fresh-context Plenum Goldfish Reviewer using the "
        "authentic pinned Google EGM v0.1.1 Design Critic persona below. "
        "Act strictly read-only. Apply the REVIEW mode to only the "
        "four PUBLIC proposals that follow. You have no previous chat "
        "history, tools or authority to approve execution. "
        "Distinguish missing verification from concrete failures. "
        "No private documents or credentials. "
        + read_real_google_egm_design_critic(),
        "PUBLIC founder agenda: " + task["objective"] + "\n\n" + dossier[:9000],
    )
    # Founder Business Advisor synthesizes the five existing council
    # deliberation calls into a recommendation with action/why.
    is_business = council_seats(task["objective"]) is BUSINESS_SEATS
    advisor_decision = None
    if is_business:
        advisor_decision = _ask_local(
            "You are the founder's BUSINESS ADVISOR, not merely a committee. "
            "Give a decisive RECOMMENDATION FIRST: DO X rather than Y BECAUSE "
            "A and B. Follow Stanford disciplined decision choice, Harvard "
            "alternatives and SBA cash/operations principles. Assess at least "
            "two realistic alternatives including defer; identify the greatest "
            "business bottleneck, evidence quality, plausible risks, cost only "
            "where directly supported, the named Plenum workforce to execute, "
            "one concrete next step and independently observable success. "
            "Clearly flag unsupported assumptions. Do NOT invent financial "
            "numbers, sources, legal approval, an account action or grant. "
            "This is preliminary public AI advice; founder retains decision. " + elephant,
            "PUBLIC founder decision: " + task["objective"]
            + "\n\nIndependent reviewer proposals:\n" + dossier[:7200]
            + "\n\nAdversarial critique:\n" + fresh[:1800],
        )
    return {
        "schema": "plenum-ai-council-result-v1",
        "issue": task["issue"], "objective": task["objective"],
        "status": "ADVISORY_DELIBERATION_AWAITING_FOUNDER",
        "seats_completed": len(results),
        "council_type": ("business_advisory" if is_business else "general"),
        "founder_business_advisor_recommendation": advisor_decision,
        "recommendation_verified_against_external_sources": False,
        "review_completed": True,
        "independent_counsel_or_advisors_contacted": False,
        "sources_independently_checked": False,
        "tasks_executed": False,
        "account_actions_executed": False,
        "next_steps_approved": False,
        "model": MODEL,
        "perspectives": results,
        "founder_public_tool_registry_used": bool(tool_decisions),
        "elephant_public_facts_used": True,
        "goldfish_received_elephant_history": False,
        "fresh_reviewer": {"role": "goldfish-verifier", "draft_untrusted": fresh},
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--event", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--execute", action="store_true")
    args = p.parse_args()
    event = json.loads(Path(args.event).read_text())
    pre = parse_event(event)
    out = Path(args.output)
    if out.is_absolute() or out.parts[0] != "reports" or ".." in out.parts:
        p.error("Only relative reports/ output is allowed")
    if args.execute:
        result = deliberate(event)
    else:
        result = {
            "schema": "plenum-ai-council-result-v1",
            "issue": pre["issue"],
            "status": "PREFLIGHT_PASSED_MODEL_NOT_RUN",
            "seats_completed": 0, "review_completed": False,
        }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("PLENUM_COUNCIL_STATUS " + result["status"])


if __name__ == "__main__":
    main()

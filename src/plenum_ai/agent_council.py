"""Founder-gated, PUBLIC, ephemeral multi-perspective Plenum AI council.

The Chief is a coordinator, not a new model. Each seat is a fresh call to
the pre-existing local Ollama runtime and receives no app/browser/tool access.
No advisor/person is impersonated; Ford/Rockefeller/Jobs are public lenses.
"""
import argparse
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


def _ask_local(system, user):
    payload = json.dumps({
        "model": MODEL, "stream": False, "think": False,
        "messages": [
            {"role": "system", "content": system},
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
    results = []
    for name, remit in council_seats(task["objective"]):
        # Distinct fresh model contexts, not synthetic labels on one response.
        draft = _ask_local(
            "You are a separate Plenum AI council reviewer. " + VERIFIED_CONTEXT +
            " " + remit +
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
        "You are a fresh-context Plenum Goldfish Reviewer. " + VERIFIED_CONTEXT +
        " Critique the following four independent AI proposals without any prior chat context. "
        "Identify conflicts, missing empirical evidence, hidden costs, "
        "privacy risks, and one inexpensive reversible experiment. "
        "Clearly mark unverified claims. Do not decide for the founder.",
        "PUBLIC founder agenda: " + task["objective"] + "\n\n" + dossier[:9000],
    )
    return {
        "schema": "plenum-ai-council-result-v1",
        "issue": task["issue"], "objective": task["objective"],
        "status": "ADVISORY_DELIBERATION_AWAITING_FOUNDER",
        "seats_completed": len(results),
        "council_type": ("business_advisory" if council_seats(task["objective"]) is BUSINESS_SEATS else "general"),
        "review_completed": True,
        "independent_counsel_or_advisors_contacted": False,
        "sources_independently_checked": False,
        "tasks_executed": False,
        "account_actions_executed": False,
        "next_steps_approved": False,
        "model": MODEL,
        "perspectives": results,
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

"""Deterministic skill activation for actual ROLE and TASK; no agent spawning.

Elephant planning memory stays separate from Goldfish review. This script only
chooses already-approved skill filenames; it does not read private data, load a
model, grant accounts, install packages, or give a named role new permissions.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROSTER = Path(__file__).resolve().parents[2] / "integrations/hermes/roster.json"
MATCHES = {
    "plenum-business-advisor": ("advise", "advisor", "decision", "strategy", "recommendation", "choose", "priority"),
    "plenum-minister-operations": ("assignment", "workforce", "delegate", "dispatch", "schedule", "coordinate", "operations"),
    "plenum-research-youtube": ("youtube", "video", "research", "sources", "news", "recent", "search"),
    "plenum-science-evidence": ("paper", "journal", "experiment", "hypothesis", "citation", "science", "prior art"),
    "plenum-coding-delivery": ("code", "git", "program", "software", "bug", "test", "repository"),
    "plenum-browser-operations": ("browser", "website", "page", "login", "navigation", "web"),
    "plenum-finance-operations": ("cash", "budget", "finance", "runway", "expense", "revenue", "pricing"),
    "plenum-growth-sales": ("sales", "customer", "market", "growth", "lead", "campaign"),
    "plenum-creative-quality": ("design", "visual", "image", "creative", "illustration", "video"),
    "plenum-support-service": ("support", "reply", "customer service", "answer", "complaint"),
    "plenum-independent-verification": ("verify", "audit", "check", "evidence", "independent", "source"),
    "plenum-simulation-validity": ("simulate", "model", "physics", "numerical", "thermal"),
    "plenum-skill-curation": ("skill", "plugin", "install", "repository", "license", "import"),
    "plenum-platform-adoption": ("adopt", "integrate", "platform", "software", "tools", "free", "license", "vendor", "install", "plugin"),
    "plenum-recency-research": ("recent", "last 30", "trends", "new developments", "youtube", "news", "research", "up to date"),
    "plenum-design-audit": ("design", "website", "deck", "presentation", "visual", "interface", "layout", "slides"),
    "plenum-local-media": ("audio", "transcript", "subtitle", "video", "music", "render", "recording", "whisper"),
}
WRITING_TRIGGERS = (
    "write", "draft", "rewrite", "edit", "proofread", "article", "email", "letter",
    "memo", "proposal", "report", "presentation", "slides", "speech", "copy", "script",
)
HUMANIZER_TRIGGERS = (
    "humanize", "slop", "natural", "tone", "rewrite", "polish", "proofread",
    "email", "letter", "presentation", "speech", "public statement",
)


def route(role: str, objective: str, *, roster_path: Path = ROSTER, max_skills: int = 3) -> dict:
    if not isinstance(role, str) or not isinstance(objective, str) or not 8 <= len(objective) <= 350:
        raise ValueError("Require bounded named role and objective")
    if max_skills not in (1, 2, 3) or "\n" in objective or "\r" in objective:
        raise ValueError("Invalid skill-selection request")
    data = json.loads(Path(roster_path).read_text(encoding="utf-8"))
    by_name = {item["name"]: item for item in data["roles"]}
    if data.get("schema") != "plenum-hermes-profile-roster-v1" or role not in by_name:
        raise PermissionError("Unknown or unapproved named role")
    permitted = by_name[role]["skill_ids"]
    text = objective.casefold()
    # Deterministic, task-specific activation. An unchanged global editorial
    # guideline is not the same as giving each role a new tool or account.
    ranked = []
    for index, slug in enumerate(permitted):
        if slug in ("humanizer", "plenum-editorial-quality"):
            continue
        overlap = sum(1 for word in MATCHES.get(slug, ()) if word in text)
        ranked.append((-overlap, index, slug))
    ranked.sort()
    chosen = [item[2] for item in ranked[:1]] if ranked else []
    # Specialized skill for the specific request may outrank the default.
    for _score, _index, slug in ranked[1:]:
        if len(chosen) >= max_skills:
            break
        if _score < 0:
            chosen.append(slug)
    needs_writing = any(v in text for v in WRITING_TRIGGERS)
    needs_humanizing = any(v in text for v in HUMANIZER_TRIGGERS)
    if needs_writing and "plenum-editorial-quality" in permitted and len(chosen) < max_skills:
        chosen.append("plenum-editorial-quality")
    if needs_humanizing and "humanizer" in permitted and len(chosen) < max_skills:
        chosen.append("humanizer")
    return {
        "schema": "plenum-lazy-skill-routing-v1",
        "role": role,
        "selected_skills": chosen,
        "available_role_skills": len(permitted),
        "every_skill_loaded": False,
        "authorizes_new_tools": False,
        "private_account_access_granted": False,
        "model_or_agent_started": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", required=True)
    parser.add_argument("--objective", required=True)
    args = parser.parse_args(argv)
    print(json.dumps(route(args.role, args.objective), indent=2))


if __name__ == "__main__":
    main()

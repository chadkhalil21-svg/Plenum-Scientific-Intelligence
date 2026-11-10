"""First real Plenum-wide Chief of Staff pilot: Deep Agents + local free model.

Evidence limit: one model-driven specialist delegation on a NONCONFIDENTIAL,
allowlisted public-source task, then a separate provider readback.
No business connectors, browser sessions, credentials, code execution or writes.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler

ALLOWED_REPOSITORIES = frozenset({
    "langchain-ai/deepagents",
    "msitarzewski/agency-agents",
    "NousResearch/hermes-agent",
})
DEFAULT_REPOSITORY = "langchain-ai/deepagents"
MODEL = "qwen3:1.7b"
MODEL_ENDPOINT = "http://127.0.0.1:11434"
SKILL = Path(__file__).resolve().parents[2] / "skills/plenum-chief-of-staff/SKILL.md"
_seen_worker_calls: list[dict[str, Any]] = []


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def read_public_repo(repo: str, *, opener=None) -> dict:
    """Never let an arbitrary model-selected URL, path or owner be fetched."""
    if repo not in ALLOWED_REPOSITORIES:
        raise ValueError("Repository is not on the fixed public allowlist")
    url = "https://api.github.com/repos/" + repo
    req = Request(
        url,
        headers={"Accept": "application/vnd.github+json",
                 "User-Agent": "PlenumChiefPublicTrial/1"},
        method="GET",
    )
    client = opener or build_opener(NoRedirects)
    try:
        with client.open(req, timeout=12) as res:
            if res.status != 200:
                raise RuntimeError("Upstream lookup did not return HTTP 200")
            raw = res.read(70001)
            if len(raw) > 70000:
                raise RuntimeError("Public metadata response exceeds 70 kB")
            obj = json.loads(raw)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise RuntimeError("Upstream read unavailable") from exc
    if (not isinstance(obj, dict) or obj.get("full_name") != repo
            or obj.get("private") is not False or obj.get("archived") is not False
            or not isinstance(obj.get("id"), int)):
        raise ValueError("Public upstream identity is not independently established")
    license_data = obj.get("license")
    spdx = license_data.get("spdx_id") if isinstance(license_data, dict) else None
    if spdx not in ("MIT", "Apache-2.0", "NOASSERTION", None):
        raise ValueError("Unexpected public upstream license; require manual review")
    return {
        "repository": repo, "repository_id": obj["id"],
        "license_spdx": spdx or "UNVERIFIED",
        "source": "github_rest_repository_metadata",
        "fetched_over_https": True,
    }


def skill_prompt() -> str:
    text = SKILL.read_text(encoding="utf-8")
    assert text.startswith("---\nname: plenum-chief-of-staff\n")
    assert "cost ceiling **$0" in text
    # Only the relevant excerpt is included to bound the local model context.
    return "\n".join((
        "You are the Plenum Chief of Staff. You work for ALL Plenum programs,",
        "not a particular subsidiary. No spending, sending, logins, deployments,",
        "permissions, payments or external account changes. Read-only public facts.",
        "Follow the founder's recorded Chief of Staff principles:",
        text.split("## Founder mandate and source of truth", 1)[1]
            .split("## Dispatch existing capabilities", 1)[0][:1800],
        "For the public GitHub license verification objective, delegate ONCE",
        "using the task tool to the 'upstream-auditor' subagent.",
        "Ask the subagent to call inspect_public_upstream on the exact repo.",
        "Never invent the evidence. Report only after the tool returns.",
    ))


def preflight(repo: str = DEFAULT_REPOSITORY) -> dict:
    if repo not in ALLOWED_REPOSITORIES:
        raise ValueError("Unapproved public input repository")
    return {
        "schema": "plenum-chief-of-staff-delegation-v1",
        "mode": "SOURCE_READY_NOT_EXECUTED", "repository": repo,
        "upstream": "langchain-ai/deepagents",
        "model": MODEL, "paid_api_used": False,
        "model_called": False, "subagent_delegation_verified": False,
        "independent_external_readback": False,
        "business_account_action_executed": False,
        "customer_or_private_data_used": False,
        "approval_required_for_external_writes": True,
    }


def run(repo: str = DEFAULT_REPOSITORY) -> dict:
    report = preflight(repo)
    if os.environ.get("PLENUM_EPHEMERAL_RUNNER") != "confirmed":
        raise RuntimeError("Chief may execute only in an isolated disposable runner")
    if os.environ.get("PLENUM_CHIEF_MODEL_URL") != MODEL_ENDPOINT:
        raise RuntimeError("Only the local Ollama loopback model endpoint is permitted")
    # Imports do not occur in preflight or existing production workflows.
    from langchain_core.tools import tool
    from langchain_ollama import ChatOllama
    from deepagents import create_deep_agent
    from langgraph.checkpoint.memory import MemorySaver

    _seen_worker_calls.clear()

    @tool
    def inspect_public_upstream(repository: str) -> str:
        """Read ONLY exact allowlisted public upstream GitHub repository metadata."""
        evidence = read_public_repo(repository)
        _seen_worker_calls.append(evidence)
        return json.dumps(evidence, separators=(",", ":"))

    model = ChatOllama(
        model=MODEL, base_url=MODEL_ENDPOINT,
        temperature=0, num_ctx=8192, num_predict=384,
        reasoning=False,
    )
    agent = create_deep_agent(
        model=model,
        system_prompt=skill_prompt(),
        tools=[],
        subagents=[{
            "name": "upstream-auditor",
            "description": "Verify the official public GitHub repository license "
                           "through the inspect_public_upstream read-only tool; "
                           "return exact source evidence, never invent.",
            "system_prompt": (
                "You are a narrowly authorized public upstream auditor. "
                "Call inspect_public_upstream with the exact repository requested. "
                "Return the repository name and exact SPDX result from that tool. "
                "Do not invent facts; perform no external writes."
            ),
            "tools": [inspect_public_upstream],
            "model": model,
        }],
        checkpointer=MemorySaver(),
    )
    mission = (
        "Chief of Staff, delegate the read-only task to upstream-auditor via "
        "the task tool: check the official GitHub API license for " + repo
        + ". Do not answer from memory. Then summarize the verified SPDX license. "
          "This is company-wide supplier due diligence, not American Rider work."
    )
    outcome = agent.invoke(
        {"messages": [{"role": "user", "content": mission}]},
        config={"configurable": {"thread_id": "public-chief-pilot"},
                "recursion_limit": 22},
    )
    messages = outcome.get("messages", [])
    delegated = any(
        c.get("name") == "task"
        for m in messages for c in (getattr(m, "tool_calls", None) or [])
    )
    worker_evidence = next(
        (item for item in _seen_worker_calls if item["repository"] == repo), None
    )
    # Independent second GET, outside the model/subagent loop.
    readback = read_public_repo(repo) if worker_evidence is not None else None
    verified = bool(
        delegated and worker_evidence and readback
        and worker_evidence == readback
        and worker_evidence["license_spdx"] == "MIT"
    )
    final = messages[-1].content if messages else ""
    report.update({
        "mode": "VERIFIED_NARROW_DELEGATION" if verified else "NOT_VERIFIED",
        "model_called": True,
        "subagent_delegation_verified": delegated,
        "worker_read_only_tool_called": worker_evidence is not None,
        "independent_external_readback": readback is not None,
        "upstream_metadata_agrees": bool(readback == worker_evidence) if readback else False,
        "source_repository": repo,
        "source_license_spdx": readback["license_spdx"] if readback else "UNVERIFIED",
        "model_summary_untrusted": str(final)[:1200],
        "business_account_action_executed": False,
    })
    if not verified:
        raise RuntimeError(
            "Chief of Staff did not demonstrate independently verified delegated work"
        )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=DEFAULT_REPOSITORY, choices=sorted(ALLOWED_REPOSITORIES))
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--out", default="reports/chief-of-staff-delegation.json")
    args = parser.parse_args()
    path = Path(args.out)
    if (path.is_absolute() or ".." in path.parts or not path.parts
            or path.parts[0] != "reports" or path.suffix != ".json"):
        parser.error("Output must be a relative JSON within reports/")
    result = run(args.repo) if args.execute else preflight(args.repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("CHIEF_OF_STAFF " + result["mode"])


if __name__ == "__main__":
    main()

"""Independent domain-transfer test for Plenum's *existing* Deep Agents Chief.

Two genuinely different permitted task types:
- Crossref scholarly metadata sourced from a public provider.
- Existing Plenum SciPy thermal-physics fixture, chosen through a worker.

This tests routing and bounded outcome checking, NOT scientific invention,
universal competence, persistent hosting, or authority over private accounts.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, build_opener

from .chief_of_staff_pilot import NoRedirects, MODEL, MODEL_ENDPOINT, skill_prompt

DOI = "10.1103/PhysRevLett.116.061102"
CASES = ("scholarly", "thermal")
ALLOWED_DOIS = frozenset({DOI.lower()})
_seen: list[dict[str, Any]] = []


def read_crossref(doi: str, *, opener=None, sleep_fn=time.sleep) -> dict:
    """Only known public scholarly identifiers. Never browse arbitrary URLs."""
    if not isinstance(doi, str) or doi.lower() not in ALLOWED_DOIS:
        raise ValueError("DOI not permitted in first public cross-domain trial")
    url = "https://api.crossref.org/works/" + quote(doi, safe="")
    req = Request(
        url,
        headers={"Accept": "application/json",
                 "User-Agent": "PlenumCrossDomainResearchTrial/1.0"},
        method="GET",
    )
    client = opener or build_opener(NoRedirects)
    for attempt in range(3):
        try:
            with client.open(req, timeout=12) as response:
                if response.status != 200:
                    raise RuntimeError("Crossref HTTP not 200")
                raw = response.read(2000001)
                if len(raw) > 2000000:
                    raise ValueError("Crossref response exceeded 2 MB bounded metadata size")
                message = json.loads(raw).get("message")
            if not isinstance(message, dict):
                raise ValueError("Invalid Crossref record")
            if str(message.get("DOI", "")).lower() != doi.lower():
                raise ValueError("Crossref DOI identity did not match request")
            titles = message.get("title")
            title = titles[0] if isinstance(titles, list) and titles else None
            published = message.get("published") or message.get("issued")
            # Treat provider metadata as untrusted: empty or malformed
            # date-parts must fail cleanly instead of raising IndexError.
            parts = published.get("date-parts") if isinstance(published, dict) else None
            first = parts[0] if isinstance(parts, list) and parts else None
            year = first[0] if isinstance(first, list) and first and type(first[0]) is int else None
            publisher = message.get("publisher")
            if not (isinstance(title, str) and 8 <= len(title) <= 300
                    and isinstance(year, int) and 1900 <= year <= 2026
                    and isinstance(publisher, str) and 3 <= len(publisher) <= 200):
                raise ValueError("Required primary deposited bibliographic fields absent")
            return {
                "doi": doi.lower(), "title": title,
                "year": year, "publisher": publisher,
                "source": "Crossref member-deposited metadata via HTTPS",
                "retrieval_kind": "public_read_only",
            }
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            if attempt == 2:
                raise RuntimeError("Crossref request unavailable after bounded retry") from exc
            sleep_fn(attempt + 1)
    raise RuntimeError("Unreachable retry state")


def existing_science_tool(domain: str) -> dict:
    """Reuse Plenum's already validated mature numerical engine; no new simulator."""
    if domain != "materials":
        raise ValueError("Only the explicitly approved thermal domain is enabled")
    from .lab import solve
    result = solve("materials")
    if not result.get("verified_fixture"):
        raise RuntimeError("Existing physical solver failed its analytic fixture")
    return {
        "domain": "materials",
        "observed_kelvin": float(result["observed"]),
        "method": str(result["method"]),
        "verified_known_fixture": True,
        "source": "existing Plenum SciPy cooling model",
        "scientific_discovery": False,
    }


def independent_science_readback(evidence: dict) -> bool:
    """Second independent analytic calculation, distinct from the SciPy solver."""
    expected = 300.0 + 60.0 * math.exp(-0.12 * 30.0)
    return (
        evidence.get("domain") == "materials"
        and evidence.get("verified_known_fixture") is True
        and evidence.get("scientific_discovery") is False
        and isinstance(evidence.get("observed_kelvin"), float)
        and abs(evidence["observed_kelvin"] - expected) < 1e-5
    )


def mission(case: str) -> str:
    if case == "scholarly":
        return (
            "Founder requests a scientific bibliography check: obtain the original "
            "publisher-deposited paper title, publication year, and publisher "
            "for DOI " + DOI + ". Independently establish metadata through an "
            "approved source tool. Do not guess, claim to have read full paper, "
            "or perform any writing, sending or private app operation."
        )
    if case == "thermal":
        return (
            "Founder requests a reproducible basic physical-science sanity check: "
            "what temperature is predicted after 30 time units for a 360 K body "
            "in a 300 K ambient with cooling rate 0.12 per time unit? Use the "
            "existing approved Plenum numerical thermal engine; label this "
            "a known equation, not a new discovery. Do not touch production."
        )
    raise ValueError("Invalid cross-domain mission")


def source_preflight(case: str) -> dict:
    if case not in CASES:
        raise ValueError("Only two explicitly authorized public cases")
    return {
        "schema": "plenum-chief-cross-domain-v1",
        "case": case, "status": "SOURCE_READY_NOT_EXECUTED",
        "model": MODEL, "model_called": False,
        "chief_delegated": False, "worker_tool_called": False,
        "correct_worker_selected": False, "independent_verified": False,
        "paid_api_used": False, "business_account_write": False,
        "private_data_used": False, "human_review_for_writes": True,
        "upstream": "Plenum original Deep Agents Chief 0.7.35",
    }


def execute(case: str) -> dict:
    report = source_preflight(case)
    if os.environ.get("PLENUM_EPHEMERAL_RUNNER") != "confirmed":
        raise RuntimeError("Require isolated temporary runner")
    if os.environ.get("PLENUM_CHIEF_MODEL_URL") != MODEL_ENDPOINT:
        raise RuntimeError("Require already approved local Ollama loopback")
    # Optional real model deps, no side effects during preflight.
    from langchain_core.tools import tool
    from langchain_ollama import ChatOllama
    from deepagents import create_deep_agent
    from langgraph.checkpoint.memory import MemorySaver

    _seen.clear()

    @tool
    def inspect_scholarly_metadata(doi: str) -> str:
        """Read a strictly allowlisted public DOI in the Crossref REST API."""
        value = read_crossref(doi)
        _seen.append({"role": "scholarly-auditor", "value": value})
        return json.dumps(value)

    @tool
    def inspect_thermal_model(domain: str) -> str:
        """Read the verified result of the existing Plenum thermal numerical tool."""
        value = existing_science_tool(domain)
        _seen.append({"role": "numerical-analyst", "value": value})
        return json.dumps(value)

    model = ChatOllama(
        model=MODEL, base_url=MODEL_ENDPOINT, temperature=0,
        reasoning=False, num_ctx=8192, num_predict=384,
    )
    agents = [
        {
            "name": "scholarly-auditor",
            "description": "Use Crossref to retrieve exact official primary publisher-deposited DOI citation metadata for scientific references. Not numerical engineering.",
            "system_prompt": "You are a scientific bibliographic metadata auditor. Call inspect_scholarly_metadata with the exact DOI in the task. Return only evidence. Do not guess, invent sources or read unrelated pages.",
            "model": model, "tools": [inspect_scholarly_metadata],
        },
        {
            "name": "numerical-analyst",
            "description": "Use the existing Plenum numerical physics engine for thermal cooling and quantitative science verification. Not bibliographic lookup.",
            "system_prompt": "You are a numerical specialist. For thermal cooling, call inspect_thermal_model with domain='materials'. Explain the result as a known model, not a discovery; do not invent measurements.",
            "model": model, "tools": [inspect_thermal_model],
        },
    ]
    chief = create_deep_agent(
        model=model,
        system_prompt=(
            skill_prompt().split("For the public GitHub license verification objective")[0]
            + "\nDelegate the founder's task to ONE appropriate specialist using the "
              "task tool. Choose based on the task, not prior demonstrations. "
              "Do not use public repo license auditing for these tasks. "
              "The Chief has no provider tools itself; specialists have only "
              "their own read-only tool. Report no fabricated evidence."
        ),
        tools=[],
        subagents=agents,
        checkpointer=MemorySaver(),
    )
    output = chief.invoke(
        {"messages": [{"role": "user", "content": mission(case)}]},
        config={"configurable": {"thread_id": "crossdomain-" + case},
                "recursion_limit": 22},
    )
    messages = output.get("messages", [])
    task_calls = [
        c for m in messages for c in (getattr(m, "tool_calls", None) or [])
        if c.get("name") == "task"
    ]
    required_role = ("scholarly-auditor" if case == "scholarly"
                     else "numerical-analyst")
    correct = any(
        c.get("args", {}).get("subagent_type") == required_role
        for c in task_calls if isinstance(c.get("args"), dict)
    )
    evidence = next(
        (x["value"] for x in _seen if x["role"] == required_role), None
    )
    if case == "scholarly":
        readback = read_crossref(DOI) if evidence is not None else None
        independently_verified = bool(readback and evidence == readback)
    else:
        readback = {"independent_analytic_check": True} if evidence is not None and independent_science_readback(evidence) else None
        independently_verified = readback is not None
    report.update({
        "status": "VERIFIED_CROSS_DOMAIN" if (task_calls and correct and independently_verified) else "NOT_VERIFIED",
        "model_called": True,
        "chief_delegated": bool(task_calls),
        "correct_worker_selected": correct,
        "worker_tool_called": evidence is not None,
        "independent_verified": independently_verified,
        "evidence": evidence,
        "provider_readback": readback if case == "scholarly" else readback,
        "model_summary_untrusted": str(messages[-1].content)[:800] if messages else "",
    })
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=CASES, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--out", default="reports/chief-cross-domain.json")
    args = parser.parse_args()
    out = Path(args.out)
    if (out.is_absolute() or ".." in out.parts or not out.parts
            or out.parts[0] != "reports" or out.suffix != ".json"):
        parser.error("Report must be relative JSON within reports/")
    result = execute(args.case) if args.execute else source_preflight(args.case)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"CHIEF_DOMAIN_TRANSFER {args.case} {result['status']}")
    if args.execute and result["status"] != "VERIFIED_CROSS_DOMAIN":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

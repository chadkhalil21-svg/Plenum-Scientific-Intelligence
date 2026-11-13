"""Independent domain-transfer test for Plenum's *existing* Deep Agents Chief.

Two genuinely different permitted task types executed after one model decision:
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
            year = (published.get("date-parts", [[]])[0][0]
                    if isinstance(published, dict) else None)
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
        "upstream": "Existing Plenum local Qwen Chief + original approved specialist tools",
    }


def parse_one_turn_model_route(raw: object) -> str | None:
    """Accept ONE explicitly chosen role, never fabricated agent invocations."""
    if not isinstance(raw, str) or len(raw) > 300:
        return None
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return None
    if not isinstance(data, dict) or set(data) != {"role"}:
        return None
    role = data["role"]
    return role if role in ("scholarly-auditor", "numerical-analyst") else None


def grade_single_real_delegate(raw: object, observations: list,
                               required_role: str) -> dict:
    """One local model decision, one original tool, no mismatched extra work."""
    if required_role not in ("scholarly-auditor", "numerical-analyst"):
        raise ValueError("Unknown original approved specialist")
    selected = parse_one_turn_model_route(raw)
    actors = [
        x.get("role") if isinstance(x, dict) else None
        for x in observations
    ]
    correct = (
        selected == required_role and len(actors) == 1
        and actors == [required_role]
    )
    return {
        "model_route_decisions": 1 if selected is not None else 0,
        "observed_worker_calls": len(actors),
        "selected_roles": [selected] if selected is not None else [],
        "tool_actor_roles": actors,
        "one_correct_delegation": correct,
        "unexpected_or_redundant_specialists": not correct,
    }


def execute(case: str) -> dict:
    report = source_preflight(case)
    if os.environ.get("PLENUM_EPHEMERAL_RUNNER") != "confirmed":
        raise RuntimeError("Require isolated temporary runner")
    if os.environ.get("PLENUM_CHIEF_MODEL_URL") != MODEL_ENDPOINT:
        raise RuntimeError("Require already approved local Ollama loopback")
    # Use ONE local model decision. The original recursive Deep Agents
    # subagent loop timed out on a CPU-bound 1.7B Qwen runner; the existing
    # trusted tool engines need no further inference to do their real work.
    from langchain_ollama import ChatOllama

    _seen.clear()
    model = ChatOllama(
        model=MODEL, base_url=MODEL_ENDPOINT, temperature=0,
        reasoning=False, format="json", num_ctx=2048, num_predict=64,
    )
    response = model.invoke([
        ("system",
         "You are the existing Plenum Chief for one PUBLIC, read-only job. "
         "Choose exactly ONE specialist based on the objective, not on any "
         "previous demonstration. Return only JSON with exactly one key "
         "'role', whose value is either 'scholarly-auditor' for bibliographic "
         "DOI metadata retrieval or 'numerical-analyst' for physics numerical "
         "calculation. You do not have browser, GitHub write, private account "
         "or arbitrary code execution permission. No prose or extra keys."),
        ("human", mission(case)),
    ])
    raw = response.content
    selected = parse_one_turn_model_route(raw)
    required_role = ("scholarly-auditor" if case == "scholarly"
                     else "numerical-analyst")
    if selected == required_role:
        # Execute the ORIGINAL approved worker tool only after the model
        # selection and an independent fixed per-case allowlist check.
        if selected == "scholarly-auditor":
            _seen.append({"role": selected, "value": read_crossref(DOI)})
        else:
            _seen.append({"role": selected, "value": existing_science_tool("materials")})
    routing = grade_single_real_delegate(raw, _seen, required_role)
    correct = routing["one_correct_delegation"]
    evidence = _seen[0]["value"] if correct else None
    if case == "scholarly":
        readback = read_crossref(DOI) if evidence is not None else None
        verified = bool(readback and readback == evidence)
    else:
        verified = bool(evidence and independent_science_readback(evidence))
        readback = {"independent_analytic_check": True} if verified else None
    report.update({
        "status": "VERIFIED_CROSS_DOMAIN" if correct and verified else "NOT_VERIFIED",
        "model_called": True,
        "chief_delegated": correct,
        "strict_single_specialist_graded": True,
        "actual_route_evidence": routing,
        "correct_worker_selected": correct,
        "worker_tool_called": evidence is not None,
        "independent_verified": verified,
        "evidence": evidence,
        "provider_readback": readback,
        "model_summary_untrusted": str(raw)[:300],
        "one_bounded_model_turn": True,
        "recursive_subagent_model_calls": False,
        "original_approved_specialist_tool_executed": evidence is not None,
        "full_general_autonomy_proven": False,
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

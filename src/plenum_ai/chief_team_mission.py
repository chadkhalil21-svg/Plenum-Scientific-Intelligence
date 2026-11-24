"""Bounded, founder-authorized specialist missions using EXISTING Plenum tools.

One local Qwen Chief previously hit LangGraph's recursion ceiling without
finishing a two-worker mission (original run 42796438425). Do NOT multiply
recursion or inference. For unambiguous, PUBLIC tool missions, deterministic
scope-gated routing is faster, cheaper, and produces durable actual artifacts.

No new agent framework/model, private app access, or arbitrary code execution.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from .chief_workforce_command import (
    CHIEF_MAGIC, CHIEF_TITLE, HINTS, KIND_TO_AGENT,
    parse_founder_chief, worker_event, independent_expected_kind,
)
from .workforce_public_inbox import run_issue
from .agent_library import suggest_sources
from .mission_checkpoint import (
    artifact_digest, load_checkpoint, save_checkpoint, verified_previous_result,
)

MISSION_TITLE = "[Plenum Chief] public mission"
MISSION_MAGIC = "PLENUM_CHIEF_PUBLIC_MISSION_V1"
DATA_MAGIC = "PLENUM_CHIEF_PUBLIC_DATA_MISSION_V1"


def independent_expected_team(objective: str) -> tuple[str, ...]:
    """Fixed independent permission gate, not an LLM or externally found text."""
    words = set(re.findall(r"[a-z]+", objective.lower()))
    matching = tuple(kind for kind, terms in HINTS.items() if terms & words)
    if not 2 <= len(matching) <= 3:
        raise ValueError("Only two or three unambiguously supported capabilities")
    return matching


def parse_mission(event: dict) -> dict:
    issue = event.get("issue") or {}
    if issue.get("title") != MISSION_TITLE or not isinstance(issue.get("body"), str):
        raise PermissionError("Not a founder-issued Plenum team mission")
    lines = issue["body"].splitlines()
    from .chief_contract_plan import MAGIC as CONTRACT_MAGIC, parse_contract_mission
    if lines and lines[0] == CONTRACT_MAGIC:
        return parse_contract_mission(event)
    if len(lines) != 2 or lines[0] not in (MISSION_MAGIC, DATA_MAGIC) or not lines[1].startswith("objective: "):
        raise ValueError("Exact two-line founder mission envelope required")
    # Preserve all existing founder, issue, public-input and scope guards.
    original = {**event, "issue": {**issue, "title": CHIEF_TITLE,
                                   "body": CHIEF_MAGIC + "\n" + lines[1]}}
    checked = parse_founder_chief(original)
    if lines[0] == DATA_MAGIC:
        ids = tuple(dict.fromkeys(re.findall(r"(?<![A-Za-z0-9])([0-9]{7})(?![A-Za-z0-9])", checked["objective"])))
        if not 20 <= len(checked["objective"]) <= 120 or not 1 <= len(ids) <= 3:
            raise ValueError("Data mission requires one to three explicit seven-digit NOAA station IDs")
        return {**checked, "team": ("public_research", "public_program"),
                "original": original, "data_mission": True, "station_ids": ids}
    objective = checked["objective"]
    if objective.startswith("Plan "):
        # This mode is deliberately confined to independent public assignments.
        # Real data dependencies use the existing contract mission graph.
        content = objective[5:]
        if re.search(r"\b(?:then|after|before|combine|integrate|depend|dependency|depends)\b", content, re.I) or re.search(r"\b(?:using|from|with)\s+(?:its|their|the previous|the resulting)\b", content, re.I):
            raise ValueError("Dependent goals require the original typed contract route")
        return {**checked, "team": independent_expected_team(content),
                "original": original, "model_team_mission": True}
    return {**checked, "team": independent_expected_team(objective),
            "original": original}


def validate_specialist_graph(nodes: list, approved: dict) -> list:
    """Order only approved goal nodes with explicit, trusted acceptance criteria.

    The owner-scoped caller supplies the approved capability manifest. A proposed
    graph cannot add a worker, input, acceptance rule or dependency. Preserve
    the proposed order among ready nodes for existing checkpoint compatibility.
    """
    from graphlib import CycleError, TopologicalSorter

    if not isinstance(nodes, list) or not approved or len(nodes) != len(approved):
        raise ValueError("Graph must contain every approved specialist subgoal once")
    by_id = {}
    for node in nodes:
        if (not isinstance(node, dict)
                or set(node) != {"id", "specialist", "depends_on", "acceptance"}):
            raise ValueError("Invalid specialist graph node")
        key = node["id"]
        if not isinstance(key, str) or key not in approved or key in by_id:
            raise ValueError("Unknown or duplicate specialist graph node")
        expected = approved[key]
        deps = node["depends_on"]
        if (not isinstance(deps, list) or any(not isinstance(x, str) for x in deps)
                or len(deps) != len(set(deps)) or set(deps) != set(expected["depends_on"])
                or not set(deps) <= set(approved)
                or node["specialist"] != expected["specialist"]
                or not isinstance(node["acceptance"], str) or not node["acceptance"]
                or node["acceptance"] != expected["acceptance"]):
            raise ValueError("Graph expands scope or changes trusted acceptance criteria")
        by_id[key] = node
    sorter = TopologicalSorter({key: node["depends_on"] for key, node in by_id.items()})
    try:
        sorter.prepare()
    except CycleError as exc:
        raise ValueError("Cyclic specialist dependency graph") from exc
    ready = set(sorter.get_ready())
    ordered = []
    while ready:
        key = next(key for key in by_id if key in ready)
        ready.remove(key)
        ordered.append(by_id[key])
        sorter.done(key)
        ready.update(sorter.get_ready())
    if len(ordered) != len(nodes):
        raise ValueError("Incomplete specialist graph")
    return ordered


def validate_team_plan(task, plan):
    """Model may extract distinct exact founder clauses, never invent inputs."""
    if not task.get("model_team_mission") or not isinstance(plan,dict) or set(plan)!={"steps"}:
        raise ValueError("Expected original planned team scope")
    steps=plan["steps"]
    if not isinstance(steps,list) or len(steps)!=len(task["team"]):
        raise ValueError("Missing or repeated specialist goal")
    remaining=task["objective"][5:]
    seen=set()
    for index, step in enumerate(steps):
        if not isinstance(step,dict) or set(step)!={"kind","objective"}:
            raise ValueError("Invalid specialist assignment")
        kind=step["kind"]
        goal=step["objective"]
        if (not isinstance(kind,str) or kind not in task["team"] or kind in seen
                or not isinstance(goal,str) or not goal or goal!=goal.strip()
                or not remaining.startswith(goal)):
            raise ValueError("Assignment is not an exact owner objective span")
        # Revalidate each extracted clause with the same original owner and worker gates.
        subevent={**task["original"],"issue":{**task["original"]["issue"],
                    "body":CHIEF_MAGIC+"\nobjective: "+goal}}
        parse_founder_chief(subevent)
        if independent_expected_kind(goal)!=kind:
            raise ValueError("Assignment does not match its specialist")
        worker_event(subevent,kind)
        seen.add(kind)
        remaining=remaining[len(goal):]
        if index<len(steps)-1:
            separator=re.match(r"(?:, and | and |, )",remaining)
            if not separator:
                raise ValueError("Unconsumed founder requirement")
            remaining=remaining[separator.end():]
    if remaining or seen!=set(task["team"]):
        raise ValueError("Unconsumed founder requirement")
    return plan


TEAM_PLANNER_MODEL = "qwen3.5:4b"


def materialize_boundary_plan(task, choice):
    """The model selects boundaries and roles; the host preserves exact text."""
    content=task["objective"][5:]
    separators=list(re.finditer(r", and | and |, ",content))
    if len(separators)>20 or not isinstance(choice,dict) or set(choice)!={"boundaries","roles"}:
        raise ValueError("Invalid compact plan")
    boundaries, roles=choice["boundaries"],choice["roles"]
    count=len(task["team"])
    if (not isinstance(boundaries,list) or len(boundaries)!=count-1
            or any(type(i) is not int or not 0<=i<len(separators) for i in boundaries)
            or boundaries!=sorted(set(boundaries))
            or not isinstance(roles,list) or len(roles)!=count
            or any(not isinstance(role,str) for role in roles)):
        raise ValueError("Invalid compact boundary selection")
    spans=[]
    cursor=0
    for i in boundaries:
        separator=separators[i]
        spans.append(content[cursor:separator.start()])
        cursor=separator.end()
    spans.append(content[cursor:])
    return validate_team_plan(task,{"steps":[{"kind":kind,"objective":goal}
                 for kind,goal in zip(roles,spans)]})


def plan_independent_team(task):
    """One compact structured inference with the existing isolated local runner."""
    import os
    from .chief_workforce_command import MODEL_URL
    if (os.environ.get("PLENUM_EPHEMERAL_RUNNER")!="confirmed"
            or os.environ.get("PLENUM_CHIEF_MODEL_URL")!=MODEL_URL):
        raise PermissionError("Team planning requires the original isolated loopback model")
    from langchain_ollama import ChatOllama
    content=task["objective"][5:]
    separators=list(re.finditer(r", and | and |, ",content))
    count=len(task["team"])
    if not count-1<=len(separators)<=20:
        raise ValueError("Invalid available separators")
    schema={"type":"object","additionalProperties":False,"required":["boundaries","roles"],
            "properties":{"boundaries":{"type":"array","minItems":count-1,"maxItems":count-1,
                        "items":{"type":"integer","enum":list(range(len(separators)))}},
                        "roles":{"type":"array","minItems":count,"maxItems":count,
                                 "items":{"enum":list(task["team"])}}}}
    marked=content
    for i in reversed(range(len(separators))):
        m=separators[i]
        marked=marked[:m.start()]+f" [SEP {i}] "+marked[m.end():]
    model=ChatOllama(model=TEAM_PLANNER_MODEL,base_url=MODEL_URL,temperature=0,reasoning=False,
                    format=schema,num_ctx=2048,num_predict=160)
    response=model.invoke([("system","Select the separator indices that divide the instruction into independent assignments. "
        "Return ordered boundaries and corresponding specialist roles as JSON. "
        "Research retrieves sources; program creates review-only code; science runs known numerical tools; "
        "creative creates drafts. Use each authorized role exactly once. No new instructions."),
        ("human",json.dumps({"instruction":marked,"roles":list(task["team"])}))])
    raw=getattr(response,"content",None)
    if not isinstance(raw,str) or len(raw)>1000:
        raise ValueError("Invalid bounded team plan")
    return materialize_boundary_plan(task,json.loads(raw))


def deterministic_team_recovery(task):
    """Different, extractive strategy after a failed model plan, never broaden scope."""
    from itertools import combinations
    content=task["objective"][5:]
    separators=list(re.finditer(r", and | and |, ",content))
    if len(separators)>20:
        raise ValueError("Ambiguous independent goal")
    valid=[]
    for selected in combinations(separators,len(task["team"])-1):
        spans=[]
        start=0
        for sep in selected:
            spans.append(content[start:sep.start()])
            start=sep.end()
        spans.append(content[start:])
        try:
            plan={"steps":[{"kind":independent_expected_kind(goal),"objective":goal} for goal in spans]}
            valid.append(validate_team_plan(task,plan))
        except (ValueError,PermissionError,TypeError,KeyError):
            continue
    if len(valid)!=1:
        raise ValueError("No unique authorized team decomposition")
    return valid[0]


def team_plan_receipt(task, output_dir, progress):
    """Bind all subgoals to the original immutable founder issue and restart state."""
    from hashlib import sha256
    from .mission_checkpoint import objective_digest
    import tempfile
    path=output_dir/f"chief-team-plan-{task['issue_number']}.json"
    if path.is_symlink() or (path.exists() and (not path.is_file() or path.stat().st_size>8000)):
        raise ValueError("Unsafe original team plan")
    called=False
    if path.exists():
        receipt=json.loads(path.read_text("utf-8"))
        validate_team_receipt(task,receipt)
    else:
        if progress:
            raise ValueError("Existing team checkpoint cannot be replanned")
        called=True
        try:
            plan=plan_independent_team(task)
            provenance="local_ollama"
        except PermissionError:
            raise
        except (ValueError,RuntimeError,OSError,ImportError,TypeError,KeyError):
            plan=deterministic_team_recovery(task)
            provenance="deterministic_extractive_recovery"
        receipt={"issue":task["issue_number"],"objective_sha256":objective_digest(task["objective"]),
                 "plan":plan,"provenance":provenance}
        validate_team_receipt(task,receipt)
        output_dir.mkdir(parents=True,exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=output_dir,mode="w",encoding="utf-8",delete=False) as temp:
            json.dump(receipt,temp,sort_keys=True)
            temp_path=Path(temp.name)
        try:
            temp_path.replace(path)
        finally:
            temp_path.unlink(missing_ok=True)
    digest=sha256(json.dumps(receipt,sort_keys=True).encode()).hexdigest()
    return receipt,digest,called


def validate_team_receipt(task,receipt):
    from .mission_checkpoint import objective_digest
    if (not isinstance(receipt,dict) or set(receipt)!={"issue","objective_sha256","plan","provenance"}
            or type(receipt["issue"]) is not int or receipt["issue"]!=task["issue_number"]
            or receipt["objective_sha256"]!=objective_digest(task["objective"])
            or receipt["provenance"] not in ("local_ollama","deterministic_extractive_recovery")):
        raise ValueError("Team plan receipt binding changed")
    return validate_team_plan(task,receipt["plan"])


def preflight(event: dict) -> dict:
    task = parse_mission(event)
    return {
        "schema": "plenum-chief-founder-team-v2",
        "issue_number": task["issue_number"],
        "status": "SOURCE_READY_NOT_EXECUTED",
        "mode": "multi",
        "planned_data_mission": task.get("data_mission", False) or (task.get("contract_mission", False) and len(task["team"]) > 2),
        "planned_contract_mission": task.get("contract_mission", False),
        "planned_model_team_mission": task.get("model_team_mission", False),
        "requires_numerical": bool(task.get("scope", {}).get("cooling")),
        "station_ids": list(task.get("station_ids", ())),
        "dispatcher": "deterministic_existing_chief_scope_gate",
        "expected_team": list(task["team"]),
        # Read-only source suggestions; never import third-party source into the
        # runner or treat a reference as a verified executable worker.
        "candidate_sources": suggest_sources(task["objective"], limit=6),
        "upstream_sources_installed": 0,
        "new_external_models_started": 0,
        "source_selection_inference_calls": 0,
        "model_called": False,
        "chief_model_delegated": False,
        "executed_workers": 0,
        "tool_outputs_verified": False,
        "independent_verified": False,
        "external_account_changes": False,
        "paid_api_used": False,
    }


def independently_accept_team(expected: tuple[str, ...], observed: dict) -> bool:
    """All requested, distinct original tools must complete their own checks."""
    return (
        2 <= len(expected) <= 3
        and len(set(expected)) == len(expected)
        and set(observed) == set(expected)
        and all(
            observed[k].get("status") == "DRAFT_READY_FOR_FOUNDER"
            and observed[k].get("verified") is True
            and isinstance(observed[k].get("worker"), str)
            and bool(observed[k].get("output_artifact"))
            for k in expected
        )
    )



def named_entity_evidence_gate(objective: str, kinds: tuple[str, ...],
                               observed: dict, root: Path) -> dict:
    """Reject obvious mismatch in real worker outputs; never certify task success.

    This is a narrow NEGATIVE gate for explicit names, not semantic AI.
    Read research record title/source/URL (not echoed topic) and actual Python
    code (not README/manifest). No model, account access, or new service.
    """
    named = tuple(
        word for word in ("cloudflare", "noaa", "nasa", "stripe", "github")
        if re.search(r"\b" + word + r"\b", objective, re.IGNORECASE)
    )
    if not named:
        return {"status": "NOT_APPLICABLE", "irrelevant_kinds": []}
    failures = []
    for kind in ("public_research", "public_program"):
        if kind not in kinds:
            continue
        relative = observed[kind].get("_artifact_path")
        if not isinstance(relative, str) or not relative.startswith("workers/" + kind + "/"):
            failures.append(kind)
            continue
        path = root / relative
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            failures.append(kind)
            continue
        try:
            if kind == "public_research":
                if not path.is_file() or path.stat().st_size > 2_000_000:
                    raise ValueError("unsafe research file")
                data = json.loads(path.read_text("utf-8"))
                records = data.get("records", []) if isinstance(data, dict) else []
                if not isinstance(records, list) or len(records) > 200:
                    raise ValueError("invalid records")
                text = " ".join(
                    str(rec.get(field, ""))[:2000]
                    for rec in records if isinstance(rec, dict)
                    for field in ("title", "source", "url")
                )
            else:
                if not path.is_dir():
                    raise ValueError("unknown code directory")
                candidates = [p for p in path.rglob("*.py")
                              if p.is_file() and not p.is_symlink()
                              and not p.name.startswith("test")]
                if len(candidates) > 20 or sum(p.stat().st_size for p in candidates) > 200_000:
                    raise ValueError("unbounded code")
                text = " ".join(p.read_text("utf-8") for p in candidates)
        except (OSError, ValueError, TypeError, UnicodeError):
            failures.append(kind)
            continue
        if not all(re.search(r"\b" + word + r"\b", text, re.IGNORECASE)
                   for word in named):
            failures.append(kind)
    return {"status": "BLOCKED_NAMED_SOURCE_MISMATCH" if failures
                      else "NAME_MENTION_ONLY_NOT_FULL_OBJECTIVE_PROOF",
            "irrelevant_kinds": failures}


# A very small contract whose ENTIRE goal is observable from real first-party
# HTTP source-read receipts and functional local code execution. No broad goal,
# provider content claim or provider account access is certified by this rule.
# This is not a synthetic "completed all agent work" success switch.
EXACT_PUBLIC_ACCEPTANCE_GOALS = {
    "Survey official Cloudflare Workers AI sources and run existing Python neuron budget validator":
        "cloudflare_workers_ai_free",
    "Survey official NOAA station metadata sources and run existing Python station validator":
        "noaa_water_station_metadata",
}


def grade_complete_bounded_public_goal(objective: str, team: tuple[str, ...],
                                       observed: dict, root: Path,
                                       technical_verified: bool,
                                       named: dict) -> dict:
    """Read the REAL specialists' original evidence; accept only two exact goals.

    This intentionally CANNOT certify reading page body, model quality, any
    arbitrary code generation, signed-in browser tasks or general autonomy.
    """
    from hashlib import sha256
    from .reviewed_domain_workers import DOMAIN_SOURCES, DOMAIN_FILES, match_original_capability

    scope = ("first-party public source URL reachability plus the already-reviewed"
             " original Python validator functional test; no website login,"
             " hosted inference, new program creation or private action")
    rejected = {"status": "NOT_A_FULLY_GRADED_GOAL", "scope": scope}
    capability = EXACT_PUBLIC_ACCEPTANCE_GOALS.get(objective)
    if (not capability or team != ("public_research", "public_program")
            or not technical_verified or named.get("irrelevant_kinds")
            or match_original_capability(objective) != capability):
        return rejected
    research_name = observed["public_research"].get("_artifact_path")
    program_name = observed["public_program"].get("_artifact_path")
    if not (isinstance(research_name, str) and isinstance(program_name, str)):
        return rejected
    research_path = root / research_name
    # The original program agent reports its issue-N root, with code/ inside.
    program_dir = root / program_name / "code"
    try:
        if (research_path.is_symlink() or not research_path.is_file()
                or research_path.stat().st_size > 50000
                or not research_path.resolve().is_relative_to(root.resolve())
                or not program_dir.is_dir() or program_dir.is_symlink()
                or not program_dir.resolve().is_relative_to(root.resolve())):
            return rejected
        evidence = json.loads(research_path.read_text(encoding="utf-8"))
        records = evidence.get("records")
        official = DOMAIN_SOURCES[capability]
        expected_urls = {url for _, _, url in official}
        if (evidence.get("schema") != "plenum-public-horizon-snapshot-v1"
                or evidence.get("topic") != objective
                or evidence.get("publisher_document_text_verified") is not False
                or not isinstance(records, list)
                or len(records) != len(expected_urls)
                or {rec.get("url") for rec in records if isinstance(rec, dict)} != expected_urls
                or any(not isinstance(rec, dict)
                       or rec.get("http_status") != 200
                       or rec.get("independently_quoted_page_text") is not False
                       or rec.get("source") != organization
                       for rec, (_, organization, _) in zip(
                           sorted(records, key=lambda x: x.get("url", "")),
                           sorted(official, key=lambda x: x[2])))):
            return rejected
        manifest_path = program_dir / "manifest.json"
        copied_code = program_dir / "main.py"
        original_code = DOMAIN_FILES[capability]
        verifier = program_dir / "test_generated.py"
        if any(p.is_symlink() or not p.is_file()
               or p.stat().st_size > 40000 for p in (
                   manifest_path, copied_code, original_code, verifier)):
            return rejected
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        code = copied_code.read_bytes()
        if (code != original_code.read_bytes()
                or manifest.get("schema") != "plenum-reviewable-program-v1"
                or manifest.get("kind") != capability
                or manifest.get("public_topic") != objective
                or manifest.get("functional_verifier_executed_and_passed") is not True
                or manifest.get("main_sha256") != sha256(code).hexdigest()
                or observed["public_program"].get("actual_offline_functional_test_passed") is not True
                or manifest.get("generated_program_has_not_been_deployed") is not True
                or manifest.get("human_code_review_required") is not True):
            return rejected
    except (OSError, ValueError, TypeError, KeyError, UnicodeError):
        return rejected
    return {
        "status": "VERIFIED_FULL_BOUNDED_PUBLIC_OBJECTIVE",
        "scope": scope,
        "http_200_official_urls": sorted(expected_urls),
        "original_program_sha256": sha256(code).hexdigest(),
        "existing_validator_real_functional_test_passed": True,
        "new_provider_account_or_paid_host_used": False,
    }



def _planned_cooling_parameters(goal):
    match = re.fullmatch(r"cooling initial ([0-9]+(?:\.[0-9]+)?) K ambient ([0-9]+(?:\.[0-9]+)?) K rate ([0-9]+(?:\.[0-9]+)?) time ([0-9]+(?:\.[0-9]+)?)", goal, re.I)
    if not match:
        return None
    p = dict(zip(("initial_kelvin", "ambient_kelvin", "rate", "duration"), map(float, match.groups())))
    if not (0 < p["initial_kelvin"] <= 2000 and 0 < p["ambient_kelvin"] <= 2000
            and 0 < p["rate"] <= 10 and 0 < p["duration"] <= 10000):
        raise ValueError("Invalid original cooling parameters")
    return p


def _grade_planned_cooling(goal, path, relative, digest):
    """Independently recompute exact requested numerical outcome from saved bytes."""
    import math
    p = _planned_cooling_parameters(goal)
    receipt = path / "cooling.json"
    if receipt.is_symlink() or not receipt.is_file() or not 0 < receipt.stat().st_size <= 20000:
        return False
    report = json.loads(receipt.read_text("utf-8"))
    if not isinstance(report, dict) or set(report) != {"cooling_solution", "cooling_readback"}:
        return False
    solution, readback = report["cooling_solution"], report["cooling_readback"]
    if not isinstance(solution, dict) or not isinstance(readback, dict):
        return False
    actual = solution.get("observed_kelvin")
    if (type(actual) not in (int, float) or not math.isfinite(actual)
            or solution.get("parameters") != p
            or (solution.get("library"), solution.get("method")) not in
               (("SciPy solve_ivp", "RK45"), ("SciPy linalg.expm", "expm"))):
        return False
    expected = p["ambient_kelvin"] + (p["initial_kelvin"] - p["ambient_kelvin"]) * math.exp(-p["rate"] * p["duration"])
    error = abs(actual - expected)
    if (error > 1e-6 or readback != {"analytic_kelvin": expected, "absolute_error_kelvin": error,
                                    "experimental_validation": False}
            or readback.get("experimental_validation") is not False):
        return False
    return {"kind": "public_science", "objective": goal, "artifact": relative, "sha256": digest,
            "acceptance": "exact requested cooling inputs and independently recomputed numerical agreement",
            "observed_kelvin": actual, "analytic_kelvin": expected, "absolute_error_kelvin": error,
            "experimental_validation": False}


def grade_planned_clause(step, worker, root):
    """Read actual bytes; None means no trusted criterion yet, False means failed."""
    from hashlib import sha256
    from .world_horizon import paper_survey_subject, paper_title_matches
    from .reviewed_domain_workers import DOMAIN_FILES, _original_functional_test
    kind,goal=step["kind"],step["objective"]
    if kind=="public_research":
        if not paper_survey_subject(goal):
            return None
    elif kind=="public_program":
        if not re.fullmatch(r"(?:create|prepare|provide) (?:a |the )?(?:existing )?(cloudflare neuron budget|noaa station metadata) validator program",goal.lower()):
            return None
    elif kind=="public_science":
        try:
            if _planned_cooling_parameters(goal) is None:
                return None
        except ValueError:
            return False
    else:
        return None
    if (worker.get("status")!="DRAFT_READY_FOR_FOUNDER" or worker.get("verified") is not True):
        return False
    try:
        relative=worker.get("_artifact_path")
        if not isinstance(relative,str) or not relative.startswith("workers/"+kind+"/"):
            return False
        digest=artifact_digest(root,relative)
        if not digest:
            return False
        path=root/relative
        if kind=="public_science":
            return _grade_planned_cooling(goal, path, relative, digest)
        if kind=="public_research":
            subject=paper_survey_subject(goal)
            if not subject or not path.is_file() or path.stat().st_size>200000:
                return False
            report=json.loads(path.read_text("utf-8"))
            records=report.get("records")
            if (report.get("schema")!="plenum-public-horizon-snapshot-v1"
                    or report.get("topic")!=goal or report.get("category")!="journals"
                    or report.get("independent_breakthrough_verified") is not False
                    or not isinstance(records,list) or not 1<=len(records)<=4
                    or any(not isinstance(r,dict) or r.get("source")!="crossref_journals"
                           or r.get("category")!="journals"
                           or not isinstance(r.get("url"),str)
                           or not re.fullmatch(r"https://doi\.org/10\.[0-9]{4,9}/[^\s?#]+",r["url"])
                           or not paper_title_matches(subject,r.get("title"))
                           or r.get("independent_fact_check_complete") is not False
                           for r in records)
                    or len({r["url"].lower() for r in records})!=len(records)):
                return False
            return {"kind":kind,"objective":goal,"artifact":relative,"sha256":digest,
                "acceptance":"distinct topic-matched Crossref DOI metadata",
                "records":[{"title":r["title"],"url":r["url"]} for r in records],
                "paper_content_verified":False}
        elif kind=="public_program":
            # Accept only explicit requests for the reviewed existing tools;
            # no generic starter or extra features can inherit this credit.
            normalized=goal.lower()
            match=re.fullmatch(r"(?:create|prepare|provide) (?:a |the )?(?:existing )?(cloudflare neuron budget|noaa station metadata) validator program",normalized)
            if not match or worker.get("actual_offline_functional_test_passed") is not True:
                return False
            capability={"cloudflare neuron budget":"cloudflare_workers_ai_free",
                        "noaa station metadata":"noaa_water_station_metadata"}[match.group(1)]
            code_dir=path/"code"
            paths=[code_dir/"manifest.json",code_dir/"main.py",code_dir/"test_generated.py"]
            if any(p.is_symlink() or not p.is_file() or p.stat().st_size>40000 for p in paths):
                return False
            manifest=json.loads(paths[0].read_text("utf-8"))
            code=paths[1].read_bytes()
            if (code!=DOMAIN_FILES[capability].read_bytes()
                    or paths[2].read_text("utf-8")!=_original_functional_test(capability)
                    or manifest.get("schema")!="plenum-reviewable-program-v1"
                    or manifest.get("kind")!=capability or manifest.get("public_topic")!=goal
                    or manifest.get("main_sha256")!=sha256(code).hexdigest()
                    or manifest.get("functional_verifier_executed_and_passed") is not True
                    or manifest.get("generated_program_has_not_been_deployed") is not True
                    or manifest.get("human_code_review_required") is not True):
                return False
            return {"kind":kind,"objective":goal,"artifact":relative,"sha256":digest,
                "acceptance":"exact reviewed original source and functional test receipt",
                "program_sha256":sha256(code).hexdigest(),"new_program_invented":False}
        else:
            return False

    except (OSError,ValueError,TypeError,KeyError,AttributeError,UnicodeError):
        return False


def grade_planned_deliverables(task, plan, observed, root):
    """Grade every supported requested deliverable from actual saved bytes.

    Unknown requirements remain open; a worker's generic green receipt alone
    never certifies the objective. This is bounded metadata and tool reuse,
    not general research or novel autonomous software engineering.
    """
    from hashlib import sha256
    from .world_horizon import paper_survey_subject, paper_title_matches
    from .reviewed_domain_workers import DOMAIN_FILES, _original_functional_test
    rejected={"status":"NOT_A_FULLY_GRADED_GOAL","scope":"explicit paper metadata survey and reviewed validator reuse only"}
    try:
        validate_team_plan(task,plan)
        if not independently_accept_team(task["team"],observed):
            return rejected
        deliverables=[]
        for step in plan["steps"]:
            proof=grade_planned_clause(step,observed[step["kind"]],root)
            if not isinstance(proof,dict):
                return rejected
            deliverables.append(proof)
        if len(deliverables)!=len(plan["steps"]):
            return rejected
        return {"status":"VERIFIED_FULL_BOUNDED_PUBLIC_OBJECTIVE",
                "scope":(rejected["scope"]+"; explicit parameterized numerical cooling" if any(d["kind"]=="public_science" for d in deliverables) else rejected["scope"]),"deliverables":deliverables,
                "all_requested_clauses_accepted":True,"general_autonomy_proved":False}
    except (OSError,ValueError,TypeError,KeyError,AttributeError,UnicodeError):
        return rejected



def execute(event: dict, *, output_dir: Path) -> dict:
    task = parse_mission(event)
    if task.get("contract_mission"):
        from .chief_contract_plan import execute_contract_mission
        try:
            return execute_contract_mission(event, output_dir=output_dir)
        except (OSError, ValueError, RuntimeError, TypeError, KeyError, ImportError) as exc:
            # Preserve a real terminal receipt for the original native retry
            # gate; never leave a source-only preflight masquerading as work.
            report=preflight(event)
            report.update(status="BLOCKED_CONTRACT_EXECUTION", independent_verified=False,
                          founder_objective_verified=False, model_called=None,
                          failure_type=type(exc).__name__,
                          model_execution_state="UNCONFIRMED_SEE_IMMUTABLE_PLAN_RECEIPT",
                          objective_review_required=True)
            from .chief_contract_plan import PlanningFailure
            if isinstance(exc,PlanningFailure):
                report['planning_failure']=exc.diagnostic
                if exc.diagnostic['stage'] in ('MODEL_RESPONSE_SHAPE','MODEL_JSON','MODEL_CONTRACT_VALIDATION'):
                    report['model_called']=True
                    report['model_execution_state']='RESPONSE_RECEIVED_PLAN_REJECTED'
            return report
    if task.get("data_mission"):
        return execute_data_mission(event, output_dir=output_dir)
    report = preflight(event)
    # The SAME founder issue and bounded public artifacts are the only mission
    # identity. When a failed GitHub job is retried, its original artifact
    # restores the checkpoint first; do not re-execute completed specialists.
    progress = load_checkpoint(
        output_dir, issue=task["issue_number"],
        objective=task["objective"], team=task["team"],
    )
    plan_hash=None
    if task.get("model_team_mission"):
        receipt,plan_hash,called=team_plan_receipt(task,output_dir,progress)
        assignments={step["kind"]:step["objective"] for step in receipt["plan"]["steps"]}
        order=tuple(assignments)
    else:
        assignments={kind:task["objective"] for kind in task["team"]}
        order=task["team"]
    observed = {}
    resumed = 0
    executed = 0
    for kind in order:
        saved = progress.get(kind)
        if plan_hash and saved is not None and (not isinstance(saved,dict) or saved.get("plan_sha256")!=plan_hash):
            raise ValueError("Checkpoint is bound to a different team plan")
        recovered = verified_previous_result(output_dir, kind, saved)
        if recovered is not None:
            observed[kind] = recovered
            resumed += 1
            continue
        attempt = int(saved.get("attempt", 0)) + 1 if isinstance(saved, dict) else 1
        if attempt > 2:
            observed[kind] = {
                "status": "BLOCKED_RETRY_LIMIT", "verified": False,
                "failure_type": "PreviouslyAttemptedTwice",
            }
            continue
        source_event={**task["original"],"issue":{**task["original"]["issue"],
                      "body":CHIEF_MAGIC+"\nobjective: "+assignments[kind]}}
        original_event = worker_event(source_event, kind)
        base = output_dir / "workers" / kind
        worker_dir = base if attempt == 1 else base / "retry-2"
        # Reserve this attempt atomically BEFORE a worker can be interrupted.
        # A restored RUNNING entry is unverified and consumes the same budget.
        progress[kind] = {"attempt": attempt, "status": "RUNNING", "verified": False}
        if plan_hash:
            progress[kind]["plan_sha256"]=plan_hash
        save_checkpoint(
            output_dir, issue=task["issue_number"],
            objective=task["objective"], team=task["team"], results=progress,
        )
        executed += 1
        try:
            result = run_issue(original_event, output_dir=worker_dir)
            if not isinstance(result, dict):
                raise ValueError("Original worker returned a non-object")
        except (OSError, ValueError, RuntimeError, KeyError, TypeError, ImportError) as exc:
            result = {
                "status": "BLOCKED_WORKER_OR_VERIFICATION",
                "verified": False,
                "failure_type": type(exc).__name__,
            }
        artifact = result.get("output_artifact")
        relative = (
            (worker_dir / artifact).relative_to(output_dir).as_posix()
            if isinstance(artifact, str) and artifact and not
               (artifact.startswith("/") or ".." in artifact.split("/"))
            else None
        )
        fingerprint = artifact_digest(output_dir, relative) if relative else None
        if (result.get("status") == "DRAFT_READY_FOR_FOUNDER"
                and result.get("verified") is True and not fingerprint):
            result = {
                **result, "status": "BLOCKED_ARTIFACT_NOT_PRESERVED",
                "verified": False, "failure_type": "MissingOrUnsafeArtifact",
            }
        if fingerprint:
            result["_artifact_path"] = relative
        # A green worker flag cannot reserve acceptance when an independently
        # gradeable requested clause fails. Preserve the rejected bytes and
        # leave only this worker eligible for the existing bounded retry gate.
        if plan_hash and result.get("verified") is True:
            proof=grade_planned_clause({"kind":kind,"objective":assignments[kind]},result,output_dir)
            if proof is False:
                result={**result,"status":"BLOCKED_WORKER_OR_VERIFICATION",
                        "verified":False,"failure_type":"IndependentClauseAcceptanceFailed"}
        observed[kind] = result
        progress[kind] = {
            "attempt": attempt,
            "status": result.get("status", "BLOCKED"),
            "verified": result.get("verified") is True,
            "worker": result.get("worker"),
            "verified_scope": result.get("verified_scope"),
            "actual_offline_functional_test_passed": (
                result.get("actual_offline_functional_test_passed") is True
            ),
            "output_artifact": artifact,
            "artifact_path": relative if fingerprint else None,
            "sha256": fingerprint,
        }
        if plan_hash:
            progress[kind]["plan_sha256"]=plan_hash
        # Atomic checkpoint after EACH original specialist, even on failure.
        save_checkpoint(
            output_dir, issue=task["issue_number"],
            objective=task["objective"], team=task["team"],
            results=progress,
        )
    technical_verified = independently_accept_team(task["team"], observed)
    if plan_hash and technical_verified:
        failures=[]
        for kind in order:
            scoped=named_entity_evidence_gate(assignments[kind],(kind,),observed,output_dir)
            failures.extend(scoped["irrelevant_kinds"])
        relevance={"status":"BLOCKED_NAMED_SOURCE_MISMATCH" if failures else "NAME_MENTION_ONLY_NOT_FULL_OBJECTIVE_PROOF",
                   "irrelevant_kinds":failures}
    else:
        relevance = (named_entity_evidence_gate(
            task["objective"], task["team"], observed, output_dir
        ) if technical_verified else {"status": "NOT_RUN", "irrelevant_kinds": []})
    verified = technical_verified and not relevance["irrelevant_kinds"]
    goal_proof = grade_complete_bounded_public_goal(
        task["objective"], task["team"], observed, output_dir,
        technical_verified, relevance,
    )
    report.update({
        "status": ("VERIFIED_BOUNDED_TEAM" if verified else
                   "BLOCKED_OBJECTIVE_RELEVANCE" if technical_verified else
                   "BLOCKED_PARTIAL_TEAM"),
        "worker_artifacts_technically_verified": technical_verified,
        "founder_objective_verified": (
            goal_proof["status"] == "VERIFIED_FULL_BOUNDED_PUBLIC_OBJECTIVE"
        ),
        "bounded_founder_goal_evidence": goal_proof,
        "named_entity_evidence": relevance["status"],
        "irrelevant_worker_kinds": relevance["irrelevant_kinds"],
        "automated_routing": True,
        "model_called": False,
        "chief_model_delegated": False,
        "executed_workers": len(observed),
        "new_worker_invocations": executed,
        "reused_prior_verified_workers": resumed,
        "resume_checkpoint": ("chief-checkpoint-" + str(task["issue_number"]) + ".json"),
        "checkpoint_is_reusable_across_same_run_retries": True,
        "successfully_verified_workers": sum(
            x.get("status") == "DRAFT_READY_FOR_FOUNDER"
            and x.get("verified") is True for x in observed.values()
        ),
        "specialists": [KIND_TO_AGENT[k] for k in task["team"]],
        "tool_outputs_verified": verified,
        "independent_verified": verified,
        "worker_results": [{
            "kind": kind,
            "worker": observed[kind].get("worker"),
            "status": observed[kind].get("status", "BLOCKED"),
            "verified_scope": observed[kind].get("verified_scope", "not_verified"),
            "output_artifact": (
                observed[kind].get("_artifact_path")
                if observed[kind].get("output_artifact") else None
            ),
            "failure_type": observed[kind].get("failure_type"),
        } for kind in task["team"]],
        "all_existing_worker_tools_reused": True,
        "founder_review_required": True,
        "new_general_agent_capability_claimed": False,
        "external_account_changes": False,
        "paid_api_used": False,
    })
    if plan_hash:
        planned_proof=grade_planned_deliverables(task,receipt["plan"],observed,output_dir)
        full=verified and planned_proof["status"]=="VERIFIED_FULL_BOUNDED_PUBLIC_OBJECTIVE"
        report.update({"dispatcher":"original_chief_extractive_team_plan",
                       "model_called":(False if not called else True if receipt["provenance"]=="local_ollama" else None),
                       "new_model_plan_attempted":called,
                       "chief_model_delegated":called and receipt["provenance"]=="local_ollama",
                       "planning_provenance":receipt["provenance"],"plan_sha256":plan_hash,
                       "plan_artifact":f"chief-team-plan-{task['issue_number']}.json",
                       "specialist_assignments":receipt["plan"]["steps"],
                       "objective":task["objective"],
                       "bounded_founder_goal_evidence":planned_proof,
                       "founder_objective_verified":full,
                       "founder_review_required":True})
    return report



def validate_data_plan(plan: object, station_ids: tuple[str, ...]) -> dict:
    """Only a two-tool data dependency; never an arbitrary general planner."""
    if (not isinstance(plan, dict) or set(plan) != {"steps"}
            or not isinstance(plan["steps"], list) or len(plan["steps"]) != 2):
        raise ValueError("Exactly two approved data steps required")
    first, second = plan["steps"]
    if (not isinstance(first, dict) or set(first) != {"tool", "station_ids"}
            or first["tool"] != "noaa_metadata"
            or not isinstance(first["station_ids"], list)
            or any(not isinstance(x, str) for x in first["station_ids"])
            or len(first["station_ids"]) != len(station_ids)
            or set(first["station_ids"]) != set(station_ids)
            or second != {"tool": "station_validation", "input_from": "noaa_metadata"}):
        raise ValueError("Plan expands scope, omits stations or changes dependency")
    return plan


def plan_data_mission(objective: str, station_ids: tuple[str, ...]) -> dict:
    import os
    from .chief_workforce_command import MODEL, MODEL_URL
    if (os.environ.get("PLENUM_EPHEMERAL_RUNNER") != "confirmed"
            or os.environ.get("PLENUM_CHIEF_MODEL_URL") != MODEL_URL):
        raise PermissionError("Data planning requires the original isolated loopback model")
    from langchain_ollama import ChatOllama
    schema = {"type":"object", "additionalProperties":False, "required":["steps"],
              "properties":{"steps":{"type":"array", "minItems":2, "maxItems":2,
              "prefixItems":[
                  {"type":"object","additionalProperties":False,"required":["tool","station_ids"],
                   "properties":{"tool":{"const":"noaa_metadata"},"station_ids":{"type":"array","minItems":1,"maxItems":3,"items":{"type":"string","enum":list(station_ids)}}}},
                  {"type":"object","additionalProperties":False,"required":["tool","input_from"],
                   "properties":{"tool":{"const":"station_validation"},"input_from":{"const":"noaa_metadata"}}}]}}}
    model = ChatOllama(model=MODEL, base_url=MODEL_URL, temperature=0,
                       reasoning=False, format=schema, num_ctx=2048, num_predict=300)
    response = model.invoke([
        ("system", "Plan this bounded public NOAA metadata check. Use noaa_metadata to fetch every explicitly requested station, then station_validation with input_from noaa_metadata. Return only the JSON schema. No other tools or goals are supported."),
        ("human", objective),
    ])
    raw = response.content
    if not isinstance(raw, str) or len(raw) > 4000:
        raise ValueError("Invalid bounded model plan")
    return validate_data_plan(json.loads(raw), station_ids)


def fetch_noaa_metadata(station_id: str) -> bytes:
    """Fixed first-party JSON endpoint, no redirects, arbitrary URLs or secrets."""
    from urllib.request import Request, build_opener
    from .chief_of_staff_pilot import NoRedirects
    if not isinstance(station_id, str) or not re.fullmatch(r"[0-9]{7}", station_id):
        raise ValueError("Invalid station identifier")
    url = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations/" + station_id + ".json"
    for attempt in range(2):
        try:
            with build_opener(NoRedirects).open(Request(url, headers={"User-Agent":"PlenumPublicMetadata/1"}), timeout=15) as response:
                raw = response.read(500001)
                if response.status != 200 or response.geturl() != url or len(raw) > 500000:
                    raise ValueError("Unexpected NOAA response")
                return raw
        except (OSError, TimeoutError):
            if attempt:
                raise
    raise RuntimeError("NOAA fetch unavailable")


def _station_rows(payload: dict, station_ids: tuple[str, ...]) -> list[dict]:
    """Independent provider identity/coordinate gate before trusted validation."""
    import math
    if not isinstance(payload, dict) or set(payload) != set(station_ids):
        raise ValueError("Missing or additional provider records")
    rows = []
    for station in station_ids:
        raw = payload[station]
        if not isinstance(raw, str) or len(raw.encode("utf-8")) > 500000:
            raise ValueError("Unsafe source receipt")
        doc = json.loads(raw)
        records = doc.get("stations") if isinstance(doc, dict) else None
        if not isinstance(records, list) or len(records) != 1 or not isinstance(records[0], dict):
            raise ValueError("Expected exactly one provider station")
        row = records[0]
        if row.get("id") != station:
            raise ValueError("Provider station identity mismatch")
        for field, low, high in (("lat", -90, 90), ("lng", -180, 180)):
            value = row.get(field)
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(value) or not low <= value <= high):
                raise ValueError("Provider coordinates not valid")
        rows.append(row)
    return rows


def execute_data_mission(event: dict, *, output_dir: Path, planner=None) -> dict:
    """Original Research -> Engineering tools; narrow data pipeline, not general autonomy."""
    from hashlib import sha256
    import importlib.util
    from .mission_checkpoint import objective_digest
    task = parse_mission(event)
    if not task.get("data_mission"):
        raise ValueError("Explicit public data mission required")
    ids = task["station_ids"]
    report = preflight(event)
    output_dir.mkdir(parents=True, exist_ok=True)
    progress = load_checkpoint(output_dir, issue=task["issue_number"], objective=task["objective"], team=task["team"])
    plan_path = output_dir / ("chief-data-plan-" + str(task["issue_number"]) + ".json")
    if plan_path.exists():
        if plan_path.is_symlink() or plan_path.stat().st_size > 8000:
            raise ValueError("Unsafe saved plan")
        receipt = json.loads(plan_path.read_text("utf-8"))
        if (not isinstance(receipt, dict) or set(receipt) != {"issue", "objective_sha256", "plan"}
                or receipt["issue"] != task["issue_number"]
                or receipt["objective_sha256"] != objective_digest(task["objective"])):
            raise ValueError("Saved plan belongs to another mission")
        plan = validate_data_plan(receipt["plan"], ids)
        model_called = False
    else:
        if progress:
            raise ValueError("Cannot replan an existing checkpoint")
        plan = validate_data_plan(planner(ids) if planner else plan_data_mission(task["objective"], ids), ids)
        receipt = {"issue":task["issue_number"], "objective_sha256":objective_digest(task["objective"]), "plan":plan}
        temporary_plan = plan_path.with_suffix(".json.tmp")
        if temporary_plan.is_symlink():
            raise ValueError("Unsafe temporary plan")
        temporary_plan.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
        temporary_plan.replace(plan_path)
        model_called = planner is None
    plan_hash = sha256(json.dumps(receipt, sort_keys=True).encode()).hexdigest()
    invoked = 0
    for kind in task["team"]:
        saved = progress.get(kind)
        expected_relative = "workers/" + kind + ("/noaa.json" if kind == "public_research" else "/validation.json")
        if (isinstance(saved, dict) and saved.get("verified")
                and (saved.get("artifact_path") != expected_relative
                     or saved.get("output_artifact") != expected_relative)):
            raise ValueError("Checkpoint does not bind the exact consumed artifact")
        if saved is not None and (not isinstance(saved, dict) or saved.get("plan_sha256") != plan_hash):
            raise ValueError("Checkpoint plan binding changed")
        if saved and saved.get("verified"):
            if verified_previous_result(output_dir, kind, saved) is None:
                raise ValueError("Completed data artifact changed")
            continue
        attempt = int(saved.get("attempt", 0)) + 1 if isinstance(saved, dict) else 1
        if attempt > 2:
            raise ValueError("Original two-attempt ceiling reached")
        progress[kind] = {"attempt":attempt,"status":"RUNNING","verified":False,"plan_sha256":plan_hash}
        save_checkpoint(output_dir, issue=task["issue_number"], objective=task["objective"], team=task["team"], results=progress)
        relative = "workers/" + kind + ("/noaa.json" if kind == "public_research" else "/validation.json")
        path = output_dir / relative
        if path.is_symlink() or not path.resolve().is_relative_to(output_dir.resolve()):
            raise ValueError("Unsafe artifact path")
        path.parent.mkdir(parents=True, exist_ok=True)
        invoked += 1
        if kind == "public_research":
            payload = {station:fetch_noaa_metadata(station).decode("utf-8") for station in plan["steps"][0]["station_ids"]}
            _station_rows(payload, ids)
            evidence = {"payload":payload,"plan_sha256":plan_hash}
        else:
            source = output_dir / "workers/public_research/noaa.json"
            payload = json.loads(source.read_text("utf-8"))["payload"]
            rows = _station_rows(payload, ids)
            validator_path = Path(__file__).resolve().parents[2] / "tools/water_level_metadata.py"
            spec = importlib.util.spec_from_file_location("plenum_original_station_validator", validator_path)
            validator = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(validator)
            evidence = {"input":rows,"source_sha256":sha256(source.read_bytes()).hexdigest(),
                        "input_sha256":sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
                        "validation":validator.validate_station_metadata(rows),"plan_sha256":plan_hash}
        path.write_text(json.dumps(evidence, sort_keys=True), encoding="utf-8")
        progress[kind] = {"attempt":attempt,"status":"DRAFT_READY_FOR_FOUNDER","verified":True,
                          "worker":KIND_TO_AGENT[kind],"artifact_path":relative,"output_artifact":relative,
                          "sha256":artifact_digest(output_dir, relative),"plan_sha256":plan_hash}
        save_checkpoint(output_dir, issue=task["issue_number"], objective=task["objective"], team=task["team"], results=progress)
    source = output_dir / "workers/public_research/noaa.json"
    data = json.loads(source.read_text("utf-8"))
    result = json.loads((output_dir / "workers/public_program/validation.json").read_text("utf-8"))
    rows = _station_rows(data["payload"], ids)
    validator_path = Path(__file__).resolve().parents[2] / "tools/water_level_metadata.py"
    spec = importlib.util.spec_from_file_location("plenum_original_station_validator_readback", validator_path)
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    validation_readback = validator.validate_station_metadata(rows)
    valid = (result.get("validation") == validation_readback
             and data.get("plan_sha256") == plan_hash == result.get("plan_sha256")
             and result.get("source_sha256") == sha256(source.read_bytes()).hexdigest()
             and result.get("input") == rows
             and result.get("input_sha256") == sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
             and result.get("validation", {}).get("total_rows") == len(ids)
             and result["validation"].get("invalid_rows") == sum(
                 not isinstance(row.get("name"), str) or not row["name"].strip() or len(row["name"]) > 200
                 or any(field in row and not isinstance(row[field], bool) for field in ("tidal","greatlakes"))
                 for row in rows))
    report.update({"status":"VERIFIED_BOUNDED_DATA_MISSION" if valid else "BLOCKED_DATA_INTEGRITY",
                   "dispatcher":"original_chief_bounded_model_data_plan","model_called":model_called,
                   "chief_model_delegated":model_called,"founder_objective_verified":False,"independent_verified":valid,
                   "bounded_metadata_contract_verified":valid,
                   "objective_review_required":True,
                   "verified_scope":"NOAA station identity/coordinates and exact source-to-validator structural review only; broader founder objective remains unverified",
                   "worker_artifacts_technically_verified":valid,"tool_outputs_verified":valid,
                   "executed_workers":2,"new_worker_invocations":invoked,"reused_prior_verified_workers":2-invoked,
                   "specialists":[KIND_TO_AGENT[k] for k in task["team"]],"station_ids":list(ids),
                   "plan_sha256":plan_hash,"plan_artifact":plan_path.name,
                   "metadata_review":{"total_rows":validation_readback["total_rows"],
                                      "structurally_valid_rows":validation_readback["structurally_valid_rows"],
                                      "invalid_rows":validation_readback["invalid_rows"],
                                      "errors":validation_readback["errors"],
                                      "all_metadata_structurally_valid":validation_readback["invalid_rows"] == 0,
                                      "warnings":["Datum references and instrument accuracy are not validated"]
                                                 + (["Malformed station metadata found; review completed, metadata not certified valid"] if validation_readback["invalid_rows"] else [])},
                   "worker_results":[{"kind":k,"worker":KIND_TO_AGENT[k],"status":progress[k]["status"],"output_artifact":progress[k]["artifact_path"],"verified_scope":"public NOAA identity and coordinates plus original structural validation"} for k in task["team"]],
                   "bounded_founder_goal_evidence":{"status":"VERIFIED_PUBLIC_METADATA_STRUCTURE" if valid else "NOT_VERIFIED", "datum_reference_validated":False,"instrument_accuracy_verified":False},
                   "new_general_agent_capability_claimed":False,"founder_review_required":True})
    return report



def execute_with_recovery(event: dict, *, output_dir: Path) -> dict:
    """Resume one eligible interrupted public team without a new founder prompt."""
    task = parse_mission(event)
    first = execute(event, output_dir=output_dir)
    if (task.get("contract_mission") or task.get("data_mission")
            or first.get("status") != "BLOCKED_PARTIAL_TEAM"):
        return first
    progress = load_checkpoint(output_dir, issue=task["issue_number"],
                               objective=task["objective"], team=task["team"])
    # Only retry a single bounded transient worker failure, never invalid
    # inputs, missing evidence, permission errors, or exhausted attempts.
    retryable = {"TimeoutError", "ConnectionError", "HTTPError", "URLError", "OSError"}
    failed = [row for row in first["worker_results"]
              if row["status"] != "DRAFT_READY_FOR_FOUNDER"]
    if (not failed or set(progress) != set(task["team"])
            or any(row.get("failure_type") not in retryable
                   or progress[row["kind"]].get("attempt") != 1
                   for row in failed)
            or any(verified_previous_result(output_dir, k, progress[k]) is None
                   for k in task["team"] if k not in {row["kind"] for row in failed})):
        return first
    receipt = output_dir / f"chief-recovery-{task['issue_number']}.json"
    # Exclusive preservation of the original negative outcome before retry.
    with receipt.open("x", encoding="utf-8") as stream:
        json.dump(first, stream, indent=2, sort_keys=True)
    second = execute(event, output_dir=output_dir)
    second["automatic_partial_recovery"] = {
        "initial_report": receipt.name,
        "retry_worker_kinds": [row["kind"] for row in failed],
        "first_new_worker_invocations": first["new_worker_invocations"],
        "first_model_plan_attempted": first.get("new_model_plan_attempted", False),
        "initial_plan_sha256": first.get("plan_sha256"),
        "completed_workers_not_replayed": second["reused_prior_verified_workers"],
        "retry_new_worker_invocations": second["new_worker_invocations"],
    }
    return second


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--out-dir", default="reports/workforce-chief")
    args = parser.parse_args()
    out = Path(args.out_dir)
    if out.is_absolute() or ".." in out.parts or not out.parts or out.parts[0] != "reports":
        parser.error("Only relative reports/ paths accepted")
    event = json.loads(Path(args.event).read_text(encoding="utf-8"))
    report = execute_with_recovery(event, output_dir=out) if args.execute else preflight(event)
    out.mkdir(parents=True, exist_ok=True)
    (out / ("chief-result-" + str(report["issue_number"]) + ".json")).write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print("PLENUM_BOUNDED_TEAM " + report["status"])
    if args.execute and not report["independent_verified"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

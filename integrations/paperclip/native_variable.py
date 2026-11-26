"""Native division bridge for the reviewed variable graph; no new providers.

Candidate for isolated Paperclip CI only. Every contract is bound to the
original company, mission and assigned native issue before execution. An
ambiguous reservation is never replayed. Independent verification is read-only.
"""
import json
import os
import re
from pathlib import Path
from checkpoint_store import checked, exclusive
from lifecycle import canonical
from model_plan import MODEL, check_local_model, read_json, digest
import variable_mission as vm

ORDER = ("intelligence", "research", "engineering", "commercial")
OWNERS = {
    "noaa_metadata": "intelligence",
    "crossref_metadata": "intelligence",
    "bibliography_readback": "research",
    "station_validation": "engineering",
    "cooling_solution": "engineering",
    "cooling_readback": "engineering",
    "business_readback": "commercial",
    "business_review": "commercial",
    "evidence_report": "commercial",
}

def validate(scope):
    if not isinstance(scope, dict) or set(scope) != {"kind", "mission", "selection_commitment"} or scope["kind"] != "variable_graph":
        raise ValueError("Exact variable graph scope required")
    vm.validate(scope["mission"])
    if not isinstance(scope["selection_commitment"], str) or not re.fullmatch(r"[0-9a-f]{64}", scope["selection_commitment"]):
        raise ValueError("Independent capability commitment required")
    return scope

def fixture(case):
    chosen = {"science":["bibliography","stations"], "engineering":["thermal"], "commercial":["commercial"]}
    return {"kind":"variable_graph", "mission":vm.fixture(case), "selection_commitment":digest(sorted(chosen[case]))}

def partition(plan):
    groups = {r: [] for r in ORDER}
    seen = set()
    for node in plan["nodes"]:
        name = node["id"]
        if name not in OWNERS or name in seen:
            raise ValueError("Unapproved or repeated native contract")
        for dep in node["depends_on"]:
            if dep not in seen or ORDER.index(OWNERS[dep]) > ORDER.index(OWNERS[name]):
                raise ValueError("Native division order conflicts with dependency")
        groups[OWNERS[name]].append(name)
        seen.add(name)
    if not groups["commercial"] or groups["commercial"][-1] != "evidence_report":
        raise ValueError("Final report must be assembled after producers")
    return groups

def evidence_root(directory):
    root = Path(directory) / "variable-graph"
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Unsafe variable graph evidence directory")
    return root

def prepare(directory, scope, company, mission):
    validate(scope)
    if os.getenv("GITHUB_ACTIONS") != "true":
        raise PermissionError("Variable graph is not enabled outside isolated public CI")
    company, mission = canonical(company), canonical(mission)
    root = Path(directory) / "variable-graph"
    root.mkdir(mode=0o700, exist_ok=True)
    root = evidence_root(directory)
    identity = {"company":company, "mission":mission, "scope_sha256":digest(scope), "paid_inference":False}
    binding = root / "native-binding.json"
    if binding.exists() or binding.is_symlink():
        if checked(binding, identity) != identity:
            raise ValueError("Variable native identity changed")
    else:
        exclusive(binding, identity)
    path = root / "plan.json"
    if not path.exists():
        md = check_local_model()
        req = vm.request(scope["mission"])
        exclusive(root / "model-reservation.json", {"request_sha256":digest(req),"maximum":1,"model_digest":md})
        response = read_json("/api/chat", req, timeout=90)
        if response.get("model") != MODEL or response.get("done") is not True:
            raise ValueError("Incomplete local model response")
        raw = response.get("message", {}).get("content")
        if not isinstance(raw, str) or len(raw) > 2000:
            raise ValueError("Invalid local model content")
        def unique(pairs):
            row = {}
            for k,v in pairs:
                if k in row:
                    raise ValueError("Duplicate capability selection")
                row[k] = v
            return row
        selection = json.loads(raw, object_pairs_hook=unique)
        plan = vm.manifest(scope["mission"], selection, md)
        n, p = response.get("eval_count"), response.get("prompt_eval_count")
        if type(n) is not int or not 0 < n <= 128 or type(p) is not int or not 0 < p <= 2048:
            raise ValueError("Incomplete inference counters")
        exclusive(root / "model-response.json", {"request_sha256":digest(req), "selection_sha256":digest(selection),
                   "model_digest":md, "eval_count":n, "prompt_eval_count":p, "paid_inference":False})
        exclusive(path, plan)
    return load(directory, scope, company, mission, require_dispatch=False)

def load(directory, scope, company, mission, *, require_dispatch=True):
    validate(scope)
    company, mission = canonical(company), canonical(mission)
    root = evidence_root(directory)
    identity = {"company":company, "mission":mission, "scope_sha256":digest(scope), "paid_inference":False}
    if checked(root / "native-binding.json", identity) != identity:
        raise ValueError("Variable native identity changed")
    plan = checked(root / "plan.json", {})
    if plan != vm.manifest(scope["mission"], plan["selection"], plan["model_digest"]):
        raise ValueError("Variable graph changed")
    vm.require_commitment(plan, scope["selection_commitment"])
    vm.validate_model_receipt(root, plan)
    partition(plan)
    if require_dispatch:
        dispatch = checked(Path(directory) / "minister-plan.json", {"company":company, "parent":mission, "variable_graph_sha256":digest(plan)})
        if dispatch.get("order") != [*ORDER, "verification"] or set(dispatch.get("tasks", {})) != {*ORDER, "verification"}:
            raise ValueError("Wrong native division graph")
        if len({canonical(v) for v in dispatch["tasks"].values()}) != 5:
            raise ValueError("Duplicate native issue")
    return plan

def context(directory, scope):
    dispatch = checked(Path(directory) / "minister-plan.json", {})
    plan = load(directory, scope, dispatch["company"], dispatch["parent"])
    return evidence_root(directory), dispatch, plan

def collect(root, dispatch, plan, roles, *, execute_role=None):
    if tuple(roles) != ORDER[:len(roles)]:
        raise ValueError("Unexpected division order")
    if execute_role is not None and (not roles or roles[-1] != execute_role or os.getenv("GITHUB_ACTIONS") != "true"):
        raise PermissionError("Only assigned isolated division execution permitted")
    groups = partition(plan)
    nodes = {n["id"]:n for n in plan["nodes"]}
    values, hashes, products = {}, {}, {}
    for role in roles:
        role_hashes = {}
        for name in groups[role]:
            deps = nodes[name]["depends_on"]
            inputs = {k:values[k] for k in deps}
            identity = {"company":dispatch["company"], "mission":dispatch["parent"], "native_issue":dispatch["tasks"][role],
                        "division":role, "plan_sha256":digest(plan), "tool":name,
                        "inputs":{k:hashes[k] for k in deps}, "paid_inference":False}
            reserved = root / (name + ".reserved.json")
            result = root / (name + ".result.json")
            if result.exists() or result.is_symlink() or role != execute_role:
                if checked(reserved, identity) != identity:
                    raise ValueError("Contract reservation changed")
                row = checked(result, identity)
            else:
                # A prior reservation without an acknowledged result is terminal.
                exclusive(reserved, identity)
                value = vm.run_contract(name, plan["scope"], inputs)
                vm.check_contract_result(name, plan["scope"], inputs, value)
                row = {**identity,"result":value,"result_sha256":digest(value)}
                exclusive(result, row)
            if set(row) != set(identity) | {"result","result_sha256"} or row["result_sha256"] != digest(row["result"]):
                raise ValueError("Native contract receipt changed")
            vm.check_contract_result(name, plan["scope"], inputs, row["result"])
            values[name] = row["result"]
            hashes[name] = role_hashes[name] = digest(row)
        products[role] = {"native_issue":dispatch["tasks"][role], "plan_sha256":digest(plan),
                          "contract_receipts":role_hashes, "scope_review_only":not bool(role_hashes)}
    return products, values, hashes

def run(role, scope, prior, directory):
    root, dispatch, plan = context(directory, scope)
    if role not in ORDER:
        raise ValueError("Unknown variable graph producer")
    if os.getenv("PAPERCLIP_COMPANY_ID") != dispatch["company"]:
        raise PermissionError("Native company assignment required")
    # division_adapter already authenticates the agent, checkout and parent;
    # additionally bind the original issue when the adapter supplies its ID.
    hint = os.getenv("PAPERCLIP_TASK_ID")
    if hint and hint != dispatch["tasks"][role]:
        raise PermissionError("Wrong native task assignment")
    i = ORDER.index(role)
    products, _, _ = collect(root, dispatch, plan, ORDER[:i])
    if set(prior) != set(products) or any(prior[k]["result"] != v for k,v in products.items()):
        raise ValueError("Prior native division receipts changed")
    products, _, _ = collect(root, dispatch, plan, ORDER[:i+1], execute_role=role)
    return products[role]

def verify(scope, prior, directory, *, functional_test):
    root, dispatch, plan = context(directory, scope)
    products, values, hashes = collect(root, dispatch, plan, ORDER)
    if set(prior) != set(products) or any(prior[k]["result"] != v for k,v in products.items()):
        raise ValueError("Native division results changed")
    expected = {"native-binding.json","plan.json","model-reservation.json","model-response.json"}
    for name in hashes:
        expected.update({name+".reserved.json",name+".result.json"})
    if {p.name for p in root.iterdir()} != expected:
        raise ValueError("Unexpected variable graph evidence")
    return {"verified_producers":4, "independent_actual_input_test":functional_test,
            "native_variable_graph_verified":True, "verified_contracts":len(hashes),
            "active_contract_divisions":[r for r in ORDER if not products[r]["scope_review_only"]],
            "plan_sha256":digest(plan), "contract_receipt_sha256":hashes,
            "report_sha256":digest(values["evidence_report"]),
            "model_calls_replayed":0, "provider_calls_replayed":0,
            "general_autonomy_verified":False, "paid_inference":False}

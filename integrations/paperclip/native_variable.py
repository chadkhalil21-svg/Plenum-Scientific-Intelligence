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
    "paper_discovery": "intelligence",
    "paper_readback": "research",
    "station_validation": "engineering",
    "cooling_solution": "engineering",
    "cooling_readback": "engineering",
    "business_readback": "commercial",
    "business_review": "commercial",
    "evidence_report": "commercial",
}

def validate(scope):
    fields = {"kind", "mission", "selection_commitment"}
    if (not isinstance(scope, dict) or set(scope) not in (fields, fields | {"planning_recovery"}, fields | {"planning_engine"})
            or scope["kind"] != "variable_graph"
            or ("planning_recovery" in scope and scope["planning_recovery"] is not True)
            or ("planning_engine" in scope and scope["planning_engine"] not in ("upstream-peer-v1","contract-graph-v2"))):
        raise ValueError("Exact variable graph scope required")
    vm.validate(scope["mission"])
    if not isinstance(scope["selection_commitment"], str) or not re.fullmatch(r"[0-9a-f]{64}", scope["selection_commitment"]):
        raise ValueError("Independent capability commitment required")
    return scope

def fixture(case):
    if case=="discovery":
        mission={"objective":"Find public concrete corrosion papers, independently check the discovered scholarly records, and solve and verify the illustrative thermal cooling model.",
                 "authorized_inputs":{"literature_discovery":"Survey public concrete corrosion papers",
                                      "thermal":{"initial_kelvin":350,"ambient_kelvin":300,"rate":0.05,"duration":20},
                                      "commercial":True}}
        return {"kind":"variable_graph","mission":mission,"selection_commitment":digest(["literature_discovery","thermal"]),
                "planning_engine":"upstream-peer-v1"}
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

def recovery_request(scope, rejected=None):
    request = vm.request(scope["mission"])
    if rejected is not None:
        # Only validated Boolean selections from the original capability set.
        vm.graph(scope["mission"], rejected)
        message = json.loads(request["messages"][1]["content"])
        message.update(previous_rejected_selection=rejected,
            correction="Independent acceptance rejected this selection. Re-read every objective clause and independently decide each available capability. Choose a different selection, omit unrelated capabilities, include all explicitly required capabilities.")
        request["messages"][1]["content"] = json.dumps(message, sort_keys=True)
    return request

def recovery_plan(scope, selection, md, request):
    return {**vm.manifest(scope["mission"], selection, md), "request_sha256":digest(request)}

def recovery_result(scope, identity, selection, n, p):
    if type(n) is not int or not 0 < n <= 128 or type(p) is not int or not 0 < p <= 2048:
        raise ValueError("Incomplete inference counters")
    vm.graph(scope["mission"], selection)
    accepted = digest(sorted(k for k,v in selection.items() if v)) == scope["selection_commitment"]
    return {**identity, "selection":selection, "selection_sha256":digest(selection),
            "eval_count":n, "prompt_eval_count":p, "accepted":accepted}

def prepare_recovery(root, scope):
    """One new corrective request, only after a complete, known wrong selection."""
    md = check_local_model()
    rejected = None
    for i in (1, 2):
        req = recovery_request(scope, rejected)
        identity = {"index":i,"maximum":2,"scope_sha256":digest(scope),
                    "request_sha256":digest(req),"model_digest":md,"paid_inference":False}
        # Exclusive reservation: a crash or ambiguous response is never replayed.
        exclusive(root / ("planning-attempt-%d.json" % i), identity)
        response = read_json("/api/chat", req, timeout=90)
        if response.get("model") != MODEL or response.get("done") is not True:
            raise ValueError("Incomplete local model response")
        raw = response.get("message", {}).get("content")
        if not isinstance(raw, str) or len(raw) > 2000:
            raise ValueError("Invalid local model content")
        def unique(pairs):
            row = {}
            for k,v in pairs:
                if k in row:raise ValueError("Duplicate capability selection")
                row[k] = v
            return row
        selection = json.loads(raw, object_pairs_hook=unique)
        receipt = recovery_result(scope, identity, selection, response.get("eval_count"), response.get("prompt_eval_count"))
        exclusive(root / ("planning-response-%d.json" % i), receipt)
        if receipt["accepted"]:
            plan = recovery_plan(scope, selection, md, req)
            exclusive(root / "model-reservation.json", {"request_sha256":digest(req),"maximum":1,"model_digest":md})
            exclusive(root / "model-response.json", {"request_sha256":digest(req),"selection_sha256":digest(selection),
                       "model_digest":md,"eval_count":receipt["eval_count"],"prompt_eval_count":receipt["prompt_eval_count"],"paid_inference":False})
            exclusive(root / "plan.json", plan)
            return
        if selection == rejected:raise ValueError("Repeated rejected capability selection")
        rejected = selection
    raise ValueError("Independent objective commitment mismatch after bounded correction")

def verify_recovery(root, scope, plan):
    """Reconstruct every attempted request; no model or provider invocation."""
    rejected = None
    names = set()
    requests = set()
    for i in (1, 2):
        req = recovery_request(scope, rejected)
        identity = {"index":i,"maximum":2,"scope_sha256":digest(scope),
                    "request_sha256":digest(req),"model_digest":plan["model_digest"],"paid_inference":False}
        if identity["request_sha256"] in requests:raise ValueError("Repeated planning request")
        requests.add(identity["request_sha256"])
        attempt, response = ("planning-attempt-%d.json" % i, "planning-response-%d.json" % i)
        names.update((attempt,response))
        if checked(root / attempt, identity) != identity:raise ValueError("Planning reservation changed")
        row = checked(root / response, identity)
        expected = recovery_result(scope,identity,row["selection"],row["eval_count"],row["prompt_eval_count"])
        if row != expected:raise ValueError("Planning receipt changed")
        if row["accepted"]:
            if plan != recovery_plan(scope,row["selection"],plan["model_digest"],req):
                raise ValueError("Corrected plan changed")
            final = checked(root / "model-response.json", {})
            if final["eval_count"] != row["eval_count"] or final["prompt_eval_count"] != row["prompt_eval_count"]:
                raise ValueError("Accepted inference counters changed")
            if {p.name for p in root.glob("planning-*.json")} != names:
                raise ValueError("Unexpected planning history")
            return names
        if row["selection"] == rejected:raise ValueError("Repeated rejected capability selection")
        rejected = row["selection"]
    raise ValueError("No accepted planning attempt")

def upstream_module():
    import sys
    deps=Path("/opt/plenum-upstream-specialists")
    if deps.is_dir():sys.path.insert(0,str(deps))
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"prometheus_oss"))
    import upstream_specialists
    return upstream_specialists

def upstream_identity(scope,company,mission):
    return {"case":"native","company":company,"native_mission":mission,"scope_sha256":digest(scope)}

def upstream_plan(root,scope,company,mission,*,execute=False):
    u=upstream_module()
    sub=root/"upstream-planner"
    identity=upstream_identity(scope,company,mission)
    args=(sub,scope["mission"],scope["selection_commitment"],identity)
    proof=u.execute_bound(*args) if execute else u.verify_bound(*args)
    stage="correction" if proof.get("independent_rejection_recovered") is True else "peer"
    row=checked(sub/(stage+".result.json"),{"answer":proof["selection"],"paid_inference":False})
    plan={**vm.manifest(scope["mission"],proof["selection"],row["model_digest"]),"request_sha256":row["request_sha256"]}
    expected={"request_sha256":plan["request_sha256"],"selection_sha256":digest(plan["selection"]),
              "model_digest":plan["model_digest"],"eval_count":row["eval_count"],"prompt_eval_count":row["prompt_eval_count"],"paid_inference":False}
    if execute:
        exclusive(root/"model-reservation.json",{"request_sha256":plan["request_sha256"],"maximum":1,"model_digest":plan["model_digest"]})
        exclusive(root/"model-response.json",expected)
        exclusive(root/"plan.json",plan)
    elif checked(root/"model-response.json",expected)!=expected:
        raise ValueError("Upstream accepted model receipt changed")
    return plan,proof

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
    if not path.exists() and scope.get("planning_engine")=="upstream-peer-v1":
        upstream_plan(root,scope,company,mission,execute=True)
    elif not path.exists() and scope.get("planning_engine")=="contract-graph-v2":
        from contract_graph_plan import prepare as prepare_graph
        prepare_graph(root,scope)
    elif not path.exists() and scope.get("planning_recovery") is True:
        prepare_recovery(root, scope)
    elif not path.exists():
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
    if scope.get("planning_engine")=="upstream-peer-v1":
        if plan!=upstream_plan(root,scope,company,mission)[0]:raise ValueError("Upstream native plan changed")
    elif scope.get("planning_engine")=="contract-graph-v2":
        from contract_graph_plan import verify as verify_graph
        verify_graph(root,scope,plan)
    elif scope.get("planning_recovery") is True:
        verify_recovery(root,scope,plan)
    elif plan != vm.manifest(scope["mission"], plan["selection"], plan["model_digest"]):
        raise ValueError("Variable graph changed")
    vm.require_commitment(plan, scope["selection_commitment"])
    if scope.get("planning_engine")!="contract-graph-v2":
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

def discovery_failure_summary(value):
    """Record only bounded provider status/counts; never raw remote text."""
    statuses = value.get("providers") if isinstance(value, dict) else None
    rows = value.get("records") if isinstance(value, dict) else None
    safe = []
    if isinstance(statuses, list):
        for row in statuses[:1]:
            if not isinstance(row, dict) or row.get("source") != "crossref_journals":
                continue
            def facts(item):
                status = item.get("status")
                records = item.get("records")
                return {"status": status if status in ("retrieved_metadata", "unavailable") else "unknown",
                        "records": min(len(records), 100) if isinstance(records, list) else None,
                        "error_type": item.get("error_type") if item.get("error_type") in
                            ("HTTPError","URLError","TimeoutError","ValueError","OSError","JSONDecodeError",
                             "TypeError","KeyError","AttributeError","RuntimeError") else None}
            entry = facts(row)
            entry["bibliographic_recovery"] = row.get("query_strategy") == "bibliographic_recovery"
            first = row.get("first_attempt")
            entry["first_attempt"] = facts(first) if isinstance(first, dict) else None
            safe.append(entry)
    return {"records": min(len(rows), 100) if isinstance(rows, list) else None, "providers": safe}


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
                try:
                    vm.check_contract_result(name, plan["scope"], inputs, value)
                except ValueError:
                    if name == "paper_discovery":
                        exclusive(root / "paper_discovery.rejected.json", {**identity,
                            "accepted":False, "diagnostic":discovery_failure_summary(value)})
                    raise
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
    if scope.get("planning_recovery") is True:
        expected.update(verify_recovery(root,scope,plan))
    if scope.get("planning_engine")=="upstream-peer-v1":
        expected.add("upstream-planner")
    if scope.get("planning_engine")=="contract-graph-v2":
        from contract_graph_plan import verify as verify_graph
        expected.update(verify_graph(root,scope,plan))
    for name in hashes:
        expected.update({name+".reserved.json",name+".result.json"})
    if {p.name for p in root.iterdir()} != expected:
        raise ValueError("Unexpected variable graph evidence")
    recovery = ({"planning_attempts":len(list(root.glob("planning-attempt-*.json"))),
                 "planning_recovery_verified":True} if scope.get("planning_recovery") is True else {})
    if scope.get("planning_engine")=="upstream-peer-v1":
        proof=upstream_plan(root,scope,dispatch["company"],dispatch["parent"])[1]
        recovery.update({"upstream_planning_verified":True,"upstream_planning_proof_sha256":digest(proof),
                         "upstream_model_calls":proof["model_calls"],"upstream_peer_changed_selection":proof["peer_changed_selection"]})
    if scope.get("planning_engine")=="contract-graph-v2":
        recovery.update({"model_composed_contract_graph_verified":True,
                         "graph_planning_attempts":len(list(root.glob("graph-attempt-*.json")))})
    return {**recovery,"verified_producers":4, "independent_actual_input_test":functional_test,
            "native_variable_graph_verified":True, "verified_contracts":len(hashes),
            "active_contract_divisions":[r for r in ORDER if not products[r]["scope_review_only"]],
            "plan_sha256":digest(plan), "contract_receipt_sha256":hashes,
            "report_sha256":digest(values["evidence_report"]),
            "model_calls_replayed":0, "provider_calls_replayed":0,
            "general_autonomy_verified":False, "paid_inference":False}

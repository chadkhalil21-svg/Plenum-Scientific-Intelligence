"""Composable owner objectives: explicit acceptance operations, public metadata and synthetic inputs."""
import json,re,sys,hashlib,tempfile,subprocess
from pathlib import Path
from fractions import Fraction
from statistics import median
from checkpoint_store import exclusive,DomainBlocked
from objective_program import TOOLS,OPS

from composition_contract import is_composition
from synthesis_contract import is_synthesis
SYNTHESIS_SOURCE=Path(__file__).with_name("synthesis_program.py")
COMPOSITION_SOURCE=Path(__file__).with_name("composition_program.py")
SOURCE=Path(__file__).with_name("objective_program.py")
PIPELINE_SOURCE=Path(__file__).with_name("pipeline_program.py")
def source_for(scope):return SYNTHESIS_SOURCE if is_synthesis(scope) else COMPOSITION_SOURCE if is_composition(scope) else PIPELINE_SOURCE if "pipeline" in scope.get("inputs",{}) else SOURCE
NUMERIC={"mean","median","range","population_variance","least_squares_slope","max_step_change"}
TEXT={"word_counts","shared_terms","term_frequency"}

def tools_for(scope):return (("collections",) if "pipeline" in scope.get("inputs",{}) or is_composition(scope) or is_synthesis(scope) else TOOLS) if scope["kind"]=="public_objective" else None

def operation_policy(scope):
    if scope["kind"]!="public_objective" or "operations" in scope or is_composition(scope) or is_synthesis(scope):return None
    if "pipeline" in scope["inputs"]:
        from pipeline_contract import policy
        return policy(scope["inputs"]["pipeline"],scope["operation_commitment"])
    groups=[]
    if "samples" in scope["inputs"]:groups.append(tuple(op for op in OPS if op in NUMERIC))
    if "documents" in scope["inputs"]:groups.append(tuple(op for op in OPS if op in TEXT))
    return {"allowed":tuple(op for op in OPS if any(op in group for group in groups)),
            "required_groups":tuple(groups),"commitment":scope["operation_commitment"]}

def planning_kwargs(scope):
    return {"tools":tools_for(scope),"operation_policy":operation_policy(scope)}

def validate(scope):
    explicit=set(scope)=={"kind","objective","dois","inputs","operations"}
    natural=set(scope)=={"kind","objective","dois","inputs","operation_commitment"}
    if not (explicit or natural or is_composition(scope) or is_synthesis(scope)):raise ValueError("Exact objective envelope required")
    label=scope["objective"]
    if not isinstance(label,str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9 ,().?'-]{9,239}",label):raise ValueError("Invalid public objective")
    ids=scope["dois"]
    if not isinstance(ids,list) or not 1<=len(ids)<=2 or any(not isinstance(x,str) or not re.fullmatch(r"10\.[0-9]{4,9}/[a-z0-9][a-z0-9.()/_+-]{0,100}",x) for x in ids) or len(set(ids))!=len(ids):raise ValueError("Invalid public DOI scope")
    data=scope["inputs"]
    if is_synthesis(scope):
        from synthesis_contract import validate as validate_synthesis
        validate_synthesis(scope)
        return
    if is_composition(scope):
        from composition_contract import validate as validate_composition
        validate_composition(scope)
        return
    if isinstance(data,dict) and "pipeline" in data:
        if not natural or set(data)!={"pipeline"} or not isinstance(scope["operation_commitment"],str) or not re.fullmatch(r"[0-9a-f]{64}",scope["operation_commitment"]):
            raise ValueError("Pipeline requires independent natural objective commitment")
        from pipeline_contract import validate as validate_pipeline
        validate_pipeline(data["pipeline"])
        return
    if explicit:
        ops=scope["operations"]
        if not isinstance(ops,list) or not 1<=len(ops)<=len(OPS) or any(type(x) is not str or x not in OPS for x in ops) or len(set(ops))!=len(ops):raise ValueError("Unsupported acceptance operation")
        if not isinstance(data,dict) or set(data)!=( {"samples"} if set(ops)&NUMERIC else set())|({"documents"} if set(ops)&TEXT else set()):raise ValueError("Input/acceptance mismatch")
    else:
        if not isinstance(data,dict) or not data or not set(data)<={"samples","documents"}:raise ValueError("Natural objective requires bounded inputs")
        commitment=scope["operation_commitment"]
        if not isinstance(commitment,str) or not re.fullmatch(r"[0-9a-f]{64}",commitment):raise ValueError("Independent acceptance commitment required")
    if "samples" in data:
        v=data["samples"]
        if not isinstance(v,list) or not 2<=len(v)<=64 or any(type(x) is not int or abs(x)>10**9 for x in v):raise ValueError("Invalid synthetic samples")
    if "documents" in data:
        docs=data["documents"]
        if not isinstance(docs,list) or not 2<=len(docs)<=4 or any(not isinstance(x,str) or not re.fullmatch(r"[A-Za-z0-9 ,().?'-]{1,240}",x) for x in docs):raise ValueError("Invalid public synthetic documents")

def goals(scope):
    validate(scope)
    engineering_goal=("Extract and compare cited evidence from the approved source corpus" if is_synthesis(scope) else "Compose exact arithmetic expressions from authorized input names" if is_composition(scope) else "Execute reviewed tool for acceptance operations "+", ".join(scope["operations"])
                      if "operations" in scope else "Select necessary reviewed operations from the natural objective and available "+", ".join(sorted(scope["inputs"])))
    return {"C":"Prepare bounded evidence brief for "+scope["objective"],
            "E":"Independently verify each requested acceptance operation and producer receipt",
            "A":"Retrieve approved public DOI metadata for "+", ".join(scope["dois"]),
            "D":"Index approved source text and independently read back scholarly metadata" if is_synthesis(scope) else "Independently read back scholarly metadata",
            "B":engineering_goal+"; objective: "+scope["objective"]}
def inputs(scope,directory=None):
    if is_synthesis(scope):
        from synthesis_contract import inputs as synthesis_inputs
        return synthesis_inputs(scope,directory)
    if is_composition(scope):
        from composition_contract import inputs as composition_inputs
        return composition_inputs(scope,directory)
    if "operations" in scope:return {**scope["inputs"],"operations":scope["operations"]}
    if directory is None:raise ValueError("Natural objective requires original model receipt")
    from model_plan import validate_operations
    choice=planned_choice(directory,scope)
    return {**scope["inputs"],"operations":validate_operations(choice["operations"],operation_policy(scope))}
def simulation_input(data):
    if "records" in data:
        from synthesis_contract import perturb
        return perturb(data)
    if "expressions" in data:
        return dict(data,values=dict(data["holdout"]))
    if "pipeline" in data:
        from pipeline_contract import perturb
        return perturb(data)
    out=dict(data)
    if "samples" in out:out["samples"]=[*out["samples"],out["samples"][-1]]
    if "documents" in out:out["documents"]=[*out["documents"],out["documents"][-1]]
    return out
def evaluate(source,data,tool):
    if tool not in TOOLS:raise ValueError("Unknown reviewed tool")
    # Explicit capability blocker, not a generic exception or security bypass.
    if tool=="sqlite":
        import importlib.util
        if importlib.util.find_spec("sqlite3") is None:raise DomainBlocked("Reviewed sqlite capability unavailable")
    try:
        res=subprocess.run([sys.executable,str(source),tool],input=json.dumps(data),capture_output=True,text=True,timeout=15,check=True)
    except subprocess.TimeoutExpired as exc:raise TimeoutError("Reviewed local computation timed out") from exc
    return json.loads(res.stdout)
def independent(data):
    if "records" in data:
        from synthesis_contract import independent as synthesis_independent
        return synthesis_independent(data)
    if "expressions" in data:
        from composition_contract import independent as composition_independent
        return composition_independent(data)
    if "pipeline" in data:
        from pipeline_contract import independent as pipeline_independent
        return pipeline_independent(data)
    docs=[re.findall("[a-z0-9]+",x.lower()) for x in data.get("documents",[])]
    v=data.get("samples",[])
    out={}
    for op in data["operations"]:
        if op=="word_counts":out[op]=list(map(len,docs))
        elif op=="shared_terms":out[op]=sorted(t for t in set(docs[0]) if all(t in row for row in docs))
        elif op=="term_frequency":out[op]=[{t:row.count(t) for t in sorted(set(row))} for row in docs]
        else:
            n=len(v);mean=Fraction(sum(v),n);center=Fraction(n-1,2)
            value={"mean":lambda:mean,"median":lambda:Fraction(median(v)),"range":lambda:Fraction(max(v)-min(v)),
                   "population_variance":lambda:sum((Fraction(x)-mean)**2 for x in v)/n,
                   "least_squares_slope":lambda:sum((i-center)*(y-mean) for i,y in enumerate(v))/sum((i-center)**2 for i in range(n)),
                   "max_step_change":lambda:Fraction(max(abs(v[i]-v[i-1]) for i in range(1,n)))}[op]()
            out[op]={"numerator":value.numerator,"denominator":value.denominator}
    return {"results":out}
def planned_choice(directory,scope):
    from model_plan import validate_receipt
    row=json.loads((directory/"minister-model-plan.json").read_text())
    plan=json.loads((directory/"minister-plan.json").read_text())
    from model_plan import digest
    if digest(row)!=plan["model_receipt_sha256"]:raise ValueError("Model plan changed")
    validate_receipt(row,plan["company"],plan["parent"],goals=goals(scope),**planning_kwargs(scope))
    return row["response"]["step_3"]
def planned_tool(directory,scope):return planned_choice(directory,scope)["tool"]
def engineering(scope,directory,tool):
    if tool not in tools_for(scope):raise ValueError("Invalid tool")
    artifact=Path(tempfile.mkdtemp(prefix="engineering-artifact-",dir=directory))
    source=artifact/"main.py";source.write_bytes(source_for(scope).read_bytes())
    data=inputs(scope,directory);observed=evaluate(source,data,tool)
    if observed!=independent(data):raise ValueError("Objective analysis disagrees")
    manifest={"main_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"functional_verifier_executed_and_passed":True}
    exclusive(artifact/"manifest.json",manifest)
    return {"artifact_dir":artifact.name,"manifest":manifest,"input":data,"validation":observed,"tool":tool}
def brief(scope,prior,directory=None,*,execute_followup=False):
    if is_synthesis(scope):
        results=prior["engineering"]["result"]["validation"]
        conflict=any(x["relation"]=="conflict" for x in results["comparisons"])
        row={"objective":scope["objective"],"results":results,
            "recommendation":"Resolve the explicitly conflicting requirements before an external decision; consult the cited evidence" if conflict else "Review the cited evidence before any external decision",
            "limitations":["The supplied source text is not independently established as true","Live DOI metadata is not full-text confirmation",*results["limitations"]],
            "new_paid_services":False,"external_actions_executed":False}
        from adaptive_turns import enabled,execute,verify
        if enabled(scope):
            if directory is None:raise ValueError("Followup requires original mission receipts")
            outcome=(execute if execute_followup else verify)(scope,prior,directory)
            row["adaptive_followup"]=outcome
            if scope["inputs"]["synthesis"]["followup"].get("engine")=="deepagents":
                import sys
                sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"prometheus_oss"))
                from native_bridge import apply
                row["oss_followup"]=apply(scope,prior,directory,outcome,execute=execute_followup)
            row["recommendation"]={"review":"Prepare bounded review of disputed requirements; no expenditure authorized","defer":"Defer review commitment because the estimated cost exceeds the stated budget","no_review":"No disputed requirements selected for review"}[outcome["action"]]
        return row
    return {"objective":scope["objective"],"results":prior["engineering"]["result"]["validation"],
            "recommendation":"Review the bounded synthetic results against independently collected evidence before decisions",
            "limitations":["Synthetic public inputs are not measured evidence","DOI metadata does not independently validate these inputs","Only the scoped arithmetic grammar was executed" if is_composition(scope) else "Only the explicitly approved acceptance operations were executed"],
            "new_paid_services":False,"external_actions_executed":False}
def run(role,scope,prior,directory):
    validate(scope)
    if role in ("intelligence","research"):
        from plenum_ai.chief_contract_plan import run_contract,check_contract_result
        ids={"dois":scope["dois"]};tool="crossref_metadata" if role=="intelligence" else "bibliography_readback"
        previous={} if role=="intelligence" else {"crossref_metadata":prior["intelligence"]["result"]}
        value=run_contract(tool,ids,previous);check_contract_result(tool,ids,previous,value)
        if is_synthesis(scope) and role=="research":
            from synthesis_contract import index,digest
            records=index(scope["inputs"]["synthesis"]["documents"])
            return {**value,"source_index":records,"source_index_sha256":digest(records)}
        return value
    if role=="engineering":
        if is_synthesis(scope):
            from synthesis_contract import digest
            data=inputs(scope,directory);r=prior["research"]["result"]
            if r["source_index"]!=data["records"] or r["source_index_sha256"]!=digest(data["records"]):raise ValueError("Research source index changed")
        return engineering(scope,directory,planned_tool(directory,scope))
    if role=="commercial":return brief(scope,prior,directory,execute_followup=True)
    raise ValueError("Unknown objective role")
def verify(scope,prior,directory,*,functional_test):
    from plenum_ai.chief_contract_plan import check_contract_result
    ids={"dois":scope["dois"]};intel=prior["intelligence"]["result"]
    check_contract_result("crossref_metadata",ids,{},intel)
    research=prior["research"]["result"]
    if is_synthesis(scope):
        from synthesis_contract import index,digest
        expected_index=index(scope["inputs"]["synthesis"]["documents"])
        if research["source_index"]!=expected_index or research["source_index_sha256"]!=digest(expected_index):raise ValueError("Research source index verification")
        research={k:v for k,v in research.items() if k not in ("source_index","source_index_sha256")}
    check_contract_result("bibliography_readback",ids,{"crossref_metadata":intel},research)
    eng=prior["engineering"]["result"];name=eng["artifact_dir"]
    if not isinstance(name,str) or not name.startswith("engineering-artifact-") or Path(name).name!=name:raise ValueError("Unsafe artifact")
    artifact=directory/name;source=artifact/"main.py"
    if artifact.is_symlink() or source.is_symlink() or source.read_bytes()!=source_for(scope).read_bytes() or eng["input"]!=inputs(scope,directory):raise ValueError("Objective source or input mismatch")
    manifest=json.loads((artifact/"manifest.json").read_text())
    if manifest!=eng["manifest"] or manifest!={"main_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"functional_verifier_executed_and_passed":True}:raise ValueError("Manifest mismatch")
    expected=planned_tool(directory,scope)
    if eng["tool"]!=expected:
        from objective_replan import validate_saved
        plan=json.loads((directory/"minister-plan.json").read_text())
        row=validate_saved(directory,plan["company"],plan["parent"],plan["tasks"]["engineering"],scope)
        if eng["tool"]!=row["choice"]["tool"]:raise ValueError("Unapproved alternate tool")
    if eng["validation"]!=independent(eng["input"]) or (functional_test and evaluate(source,eng["input"],eng["tool"])!=eng["validation"]):raise ValueError("Independent objective verification disagrees")
    if brief(scope,prior,directory)!=prior["commercial"]["result"]:raise ValueError("Brief changed")
    result={"verified_producers":4,"independent_actual_input_test":functional_test,"scholarly_metadata_records":len(intel),"synthetic_data_only":True,"general_autonomy_verified":False,"paid_inference":False}
    if is_synthesis(scope):
        v=eng["validation"]
        result.update(grounded_synthesis_verified=True,source_sentence_count=len(eng["input"]["records"]),
            comparison_count=len(v["comparisons"]),extract_count=len(v["extracts"]),semantic_truth_verified=False)
        from adaptive_turns import enabled
        if enabled(scope):
            result.update(adaptive_followup_verified=True,dependent_model_turns=2,followup_sha256=hashlib.sha256(json.dumps(prior["commercial"]["result"]["adaptive_followup"],sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest())
            if scope["inputs"]["synthesis"]["followup"].get("engine")=="deepagents":
                oss=prior["commercial"]["result"]["oss_followup"]
                result.update(native_oss_graph_verified=True,oss_graph_sha256=hashlib.sha256(json.dumps(oss,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest())
    return result

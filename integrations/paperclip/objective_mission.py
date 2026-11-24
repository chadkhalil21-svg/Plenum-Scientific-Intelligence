"""Composable owner objectives: explicit acceptance operations, public metadata and synthetic inputs."""
import json,re,sys,hashlib,tempfile,subprocess
from pathlib import Path
from fractions import Fraction
from statistics import median
from checkpoint_store import exclusive,DomainBlocked
from objective_program import TOOLS,OPS

SOURCE=Path(__file__).with_name("objective_program.py")
NUMERIC={"mean","median","range","population_variance","least_squares_slope","max_step_change"}
TEXT={"word_counts","shared_terms","term_frequency"}

def tools_for(scope):return TOOLS if scope["kind"]=="public_objective" else None
def validate(scope):
    if set(scope)!={"kind","objective","dois","inputs","operations"}:raise ValueError("Exact objective envelope required")
    label=scope["objective"]
    if not isinstance(label,str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9 ,().?'-]{9,239}",label):raise ValueError("Invalid public objective")
    ids=scope["dois"]
    if not isinstance(ids,list) or not 1<=len(ids)<=2 or any(not isinstance(x,str) or not re.fullmatch(r"10\.[0-9]{4,9}/[a-z0-9][a-z0-9.()/_+-]{0,100}",x) for x in ids) or len(set(ids))!=len(ids):raise ValueError("Invalid public DOI scope")
    data=scope["inputs"];ops=scope["operations"]
    if not isinstance(ops,list) or not 1<=len(ops)<=len(OPS) or any(type(x) is not str or x not in OPS for x in ops) or len(set(ops))!=len(ops):raise ValueError("Unsupported acceptance operation")
    if not isinstance(data,dict) or set(data)!=( {"samples"} if set(ops)&NUMERIC else set())|({"documents"} if set(ops)&TEXT else set()):raise ValueError("Input/acceptance mismatch")
    if "samples" in data:
        v=data["samples"]
        if not isinstance(v,list) or not 2<=len(v)<=64 or any(type(x) is not int or abs(x)>10**9 for x in v):raise ValueError("Invalid synthetic samples")
    if "documents" in data:
        docs=data["documents"]
        if not isinstance(docs,list) or not 2<=len(docs)<=4 or any(not isinstance(x,str) or not re.fullmatch(r"[A-Za-z0-9 ,().?'-]{1,240}",x) for x in docs):raise ValueError("Invalid public synthetic documents")

def goals(scope):
    validate(scope)
    return {"C":"Prepare bounded evidence brief for "+scope["objective"],
            "E":"Independently verify each requested acceptance operation and producer receipt",
            "A":"Retrieve approved public DOI metadata for "+", ".join(scope["dois"]),
            "D":"Independently read back scholarly metadata",
            "B":"Execute reviewed tool for acceptance operations "+", ".join(scope["operations"])+"; objective: "+scope["objective"]}
def inputs(scope):return {**scope["inputs"],"operations":scope["operations"]}
def simulation_input(data):
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
def planned_tool(directory,scope):
    from model_plan import validate_receipt
    row=json.loads((directory/"minister-model-plan.json").read_text())
    plan=json.loads((directory/"minister-plan.json").read_text())
    from model_plan import digest
    if digest(row)!=plan["model_receipt_sha256"]:raise ValueError("Model plan changed")
    validate_receipt(row,plan["company"],plan["parent"],goals=goals(scope),tools=TOOLS)
    return row["response"]["step_3"]["tool"]
def engineering(scope,directory,tool):
    if tool not in TOOLS:raise ValueError("Invalid tool")
    artifact=Path(tempfile.mkdtemp(prefix="engineering-artifact-",dir=directory))
    source=artifact/"main.py";source.write_bytes(SOURCE.read_bytes())
    data=inputs(scope);observed=evaluate(source,data,tool)
    if observed!=independent(data):raise ValueError("Objective analysis disagrees")
    manifest={"main_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"functional_verifier_executed_and_passed":True}
    exclusive(artifact/"manifest.json",manifest)
    return {"artifact_dir":artifact.name,"manifest":manifest,"input":data,"validation":observed,"tool":tool}
def brief(scope,prior):
    return {"objective":scope["objective"],"results":prior["engineering"]["result"]["validation"],
            "recommendation":"Review the bounded synthetic results against independently collected evidence before decisions",
            "limitations":["Synthetic public inputs are not measured evidence","DOI metadata does not independently validate these inputs","Only the explicitly approved acceptance operations were executed"],
            "new_paid_services":False,"external_actions_executed":False}
def run(role,scope,prior,directory):
    validate(scope)
    if role in ("intelligence","research"):
        from plenum_ai.chief_contract_plan import run_contract,check_contract_result
        ids={"dois":scope["dois"]};tool="crossref_metadata" if role=="intelligence" else "bibliography_readback"
        previous={} if role=="intelligence" else {"crossref_metadata":prior["intelligence"]["result"]}
        value=run_contract(tool,ids,previous);check_contract_result(tool,ids,previous,value);return value
    if role=="engineering":return engineering(scope,directory,planned_tool(directory,scope))
    if role=="commercial":return brief(scope,prior)
    raise ValueError("Unknown objective role")
def verify(scope,prior,directory,*,functional_test):
    from plenum_ai.chief_contract_plan import check_contract_result
    ids={"dois":scope["dois"]};intel=prior["intelligence"]["result"]
    check_contract_result("crossref_metadata",ids,{},intel)
    check_contract_result("bibliography_readback",ids,{"crossref_metadata":intel},prior["research"]["result"])
    eng=prior["engineering"]["result"];name=eng["artifact_dir"]
    if not isinstance(name,str) or not name.startswith("engineering-artifact-") or Path(name).name!=name:raise ValueError("Unsafe artifact")
    artifact=directory/name;source=artifact/"main.py"
    if artifact.is_symlink() or source.is_symlink() or source.read_bytes()!=SOURCE.read_bytes() or eng["input"]!=inputs(scope):raise ValueError("Objective source or input mismatch")
    manifest=json.loads((artifact/"manifest.json").read_text())
    if manifest!=eng["manifest"] or manifest!={"main_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"functional_verifier_executed_and_passed":True}:raise ValueError("Manifest mismatch")
    expected=planned_tool(directory,scope)
    if eng["tool"]!=expected:
        from objective_replan import validate_saved
        plan=json.loads((directory/"minister-plan.json").read_text())
        row=validate_saved(directory,plan["company"],plan["parent"],plan["tasks"]["engineering"],scope)
        if eng["tool"]!=row["choice"]["tool"]:raise ValueError("Unapproved alternate tool")
    if eng["validation"]!=independent(eng["input"]) or (functional_test and evaluate(source,eng["input"],eng["tool"])!=eng["validation"]):raise ValueError("Independent objective verification disagrees")
    if brief(scope,prior)!=prior["commercial"]["result"]:raise ValueError("Brief changed")
    return {"verified_producers":4,"independent_actual_input_test":functional_test,"scholarly_metadata_records":len(intel),"synthetic_data_only":True,"general_autonomy_verified":False,"paid_inference":False}

"""Composable owner objectives: explicit acceptance operations, public metadata and synthetic inputs."""
import json,re,sys,hashlib,tempfile,subprocess
from pathlib import Path
from fractions import Fraction
from statistics import median
from checkpoint_store import exclusive,DomainBlocked
from objective_program import TOOLS,OPS,PIPELINES,PIPELINE_OPS

SOURCE=Path(__file__).with_name("objective_program.py")
NUMERIC={"mean","median","range","population_variance","least_squares_slope","max_step_change"}
TEXT={"word_counts","shared_terms","term_frequency"}

def tools_for(scope):return TOOLS if scope["kind"]=="public_objective" else None

def operation_policy(scope):
    if scope["kind"]!="public_objective" or "operations" in scope:return None
    groups=[]
    if set(scope["inputs"])&set(PIPELINES):
        domain=next(iter(set(scope["inputs"])&set(PIPELINES)))
        groups.append(tuple(PIPELINES[domain]))
    if "samples" in scope["inputs"]:groups.append(tuple(op for op in OPS if op in NUMERIC))
    if "documents" in scope["inputs"]:groups.append(tuple(op for op in OPS if op in TEXT))
    return {"allowed":tuple(op for op in (*OPS,*PIPELINE_OPS) if any(op in group for group in groups)),
            "required_groups":tuple(groups),"commitment":scope["operation_commitment"]}

def planning_kwargs(scope):
    return {"tools":tools_for(scope),"operation_policy":operation_policy(scope)}

def validate(scope):
    explicit=set(scope)=={"kind","objective","dois","inputs","operations"}
    natural=set(scope)=={"kind","objective","dois","inputs","operation_commitment"}
    if not (explicit or natural):raise ValueError("Exact objective envelope required")
    label=scope["objective"]
    if not isinstance(label,str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9 ,().?'-]{9,239}",label):raise ValueError("Invalid public objective")
    ids=scope["dois"]
    if not isinstance(ids,list) or not 1<=len(ids)<=2 or any(not isinstance(x,str) or not re.fullmatch(r"10\.[0-9]{4,9}/[a-z0-9][a-z0-9.()/_+-]{0,100}",x) for x in ids) or len(set(ids))!=len(ids):raise ValueError("Invalid public DOI scope")
    data=scope["inputs"]
    if isinstance(data,dict) and set(data)&set(PIPELINES):
        validate_pipeline_scope(scope,explicit)
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


def validate_pipeline_scope(scope,explicit):
    data=scope["inputs"]
    if len(data)!=1 or next(iter(data)) not in PIPELINES:raise ValueError("One new domain per mission")
    domain=next(iter(data));raw=data[domain]
    def integer(v,low=0,high=10**8):return type(v) is int and low<=v<=high
    def series(v):return isinstance(v,list) and 2<=len(v)<=64 and all(integer(x,1,10**6) for x in v)
    if not isinstance(raw,dict):raise ValueError("Typed pipeline parameters")
    if domain=="experiment":
        if set(raw)!={"control","treatment"} or not series(raw["control"]) or not series(raw["treatment"]) or len(raw["control"])!=len(raw["treatment"]):
            raise ValueError("Paired positive experiment observations required")
    elif domain=="design":
        if set(raw)!={"loads","capacity"} or not series(raw["loads"]) or not integer(raw["capacity"],1):
            raise ValueError("Bounded positive service capacity required")
    elif set(raw)!={"units","price","variable_cost","fixed_cost"} or not all(integer(v) for v in raw.values()) or raw["price"]<=raw["variable_cost"]:
        raise ValueError("Positive unit contribution required")
    if explicit:
        ops=scope["operations"]
        if not isinstance(ops,list) or not ops or any(type(op) is not str or op not in PIPELINES[domain] for op in ops) or len(set(ops))!=len(ops):
            raise ValueError("Unapproved pipeline terminal")
    elif not isinstance(scope["operation_commitment"],str) or not re.fullmatch(r"[0-9a-f]{64}",scope["operation_commitment"]):
        raise ValueError("Independent pipeline commitment required")

def independent_pipeline(data):
    # Independent direct oracle, not the executor's aggregation or DAG.
    domain=next(iter(set(data)&set(PIPELINES)));r=data[domain]
    if domain=="experiment":
        n=len(r["control"]);c=sum(r["control"]);t=sum(r["treatment"])
        expected={"control_mean":Fraction(c,n),"treatment_mean":Fraction(t,n),
                  "absolute_reduction":Fraction(sum(a-b for a,b in zip(r["control"],r["treatment"])),n),
                  "relative_reduction":Fraction(c-t,c)}
        deps={"control_mean":[],"treatment_mean":[],"absolute_reduction":["control_mean","treatment_mean"],
              "relative_reduction":["absolute_reduction","control_mean"]}
    elif domain=="design":
        total=sum(r["loads"]);capacity=r["capacity"]
        expected={"total_load":Fraction(total),"reserve_capacity":Fraction(capacity-total),
                  "reserve_fraction":Fraction(capacity-total,capacity),"utilization_fraction":Fraction(total,capacity)}
        deps={"total_load":[],"reserve_capacity":["total_load"],"reserve_fraction":["reserve_capacity"],"utilization_fraction":["total_load"]}
    else:
        margin=r["price"]-r["variable_cost"]
        expected={"unit_contribution":Fraction(margin),"total_contribution":Fraction(r["units"]*margin),
                  "break_even_units":Fraction((r["fixed_cost"]+margin-1)//margin),
                  "operating_profit":Fraction(r["units"]*r["price"]-r["units"]*r["variable_cost"]-r["fixed_cost"])}
        deps={"unit_contribution":[],"total_contribution":["unit_contribution"],"break_even_units":["unit_contribution"],"operating_profit":["total_contribution"]}
    def rational(v):return {"numerator":v.numerator,"denominator":v.denominator}
    trace=[];seen=set()
    for op in sorted(data["operations"]):
        if op not in expected:raise ValueError("Unknown terminal")
        stack=[(op,False)]
        while stack:
            node,ready=stack.pop()
            if node in seen:continue
            if ready:
                if not set(deps[node])<=seen:raise ValueError("Invalid graph order")
                trace.append({"operation":node,"depends_on":deps[node],"value":rational(expected[node])});seen.add(node)
            else:
                stack.append((node,True))
                stack.extend((dep,False) for dep in reversed(deps[node]))
    return {"results":{op:rational(expected[op]) for op in data["operations"]},"pipeline":{"domain":domain,"steps":trace}}


def goals(scope):
    validate(scope)
    engineering_goal=("Execute reviewed tool for acceptance operations "+", ".join(scope["operations"])
                      if "operations" in scope else "Select necessary reviewed operations from the natural objective and available "+", ".join(sorted(scope["inputs"])))
    return {"C":"Prepare bounded evidence brief for "+scope["objective"],
            "E":"Independently verify each requested acceptance operation and producer receipt",
            "A":"Retrieve approved public DOI metadata for "+", ".join(scope["dois"]),
            "D":"Independently read back scholarly metadata",
            "B":engineering_goal+"; objective: "+scope["objective"]}
def inputs(scope,directory=None):
    if "operations" in scope:return {**scope["inputs"],"operations":scope["operations"]}
    if directory is None:raise ValueError("Natural objective requires original model receipt")
    from model_plan import validate_operations
    choice=planned_choice(directory,scope)
    return {**scope["inputs"],"operations":validate_operations(choice["operations"],operation_policy(scope))}
def simulation_input(data):
    out=dict(data)
    if "experiment" in out:
        x=out["experiment"];out["experiment"]={k:[*v,v[-1]] for k,v in x.items()}
    if "design" in out:
        x=out["design"];out["design"]={**x,"loads":[*x["loads"],x["loads"][-1]]}
    if "business" in out:
        x=out["business"];out["business"]={**x,"units":x["units"]+1}
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
    if set(data)&set(PIPELINES):return independent_pipeline(data)
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
    if tool not in TOOLS:raise ValueError("Invalid tool")
    artifact=Path(tempfile.mkdtemp(prefix="engineering-artifact-",dir=directory))
    source=artifact/"main.py";source.write_bytes(SOURCE.read_bytes())
    data=inputs(scope,directory);observed=evaluate(source,data,tool)
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
    if artifact.is_symlink() or source.is_symlink() or source.read_bytes()!=SOURCE.read_bytes() or eng["input"]!=inputs(scope,directory):raise ValueError("Objective source or input mismatch")
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

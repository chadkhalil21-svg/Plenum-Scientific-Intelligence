"""Domain-independent bounded synthetic sample analysis plus separate public bibliography."""
import json
import re
import sys
import hashlib
import tempfile
import subprocess
from pathlib import Path
from fractions import Fraction
from statistics import median
from checkpoint_store import exclusive

SOURCE=Path(__file__).with_name("dataset_program.py")
def validate(scope):
    if set(scope)!={"kind","subject","dois","values","operations"}:raise ValueError("Exact dataset scope required")
    subject=scope["subject"]
    if not isinstance(subject,str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9 ,()-]{2,79}",subject):raise ValueError("Invalid public subject label")
    ids=scope["dois"]
    if not isinstance(ids,list) or not 1<=len(ids)<=2 or any(not isinstance(x,str) or not re.fullmatch(r"10\.[0-9]{4,9}/[a-z0-9][a-z0-9.()/_+-]{0,100}",x) for x in ids) or len(set(ids))!=len(ids):raise ValueError("Invalid public DOI scope")
    v=scope["values"];o=scope["operations"]
    if not isinstance(v,list) or not 2<=len(v)<=64 or any(type(x) is not int or abs(x)>10**9 for x in v):raise ValueError("Invalid synthetic samples")
    if not isinstance(o,list) or not 1<=len(o)<=3 or any(x not in ("mean","median","range") for x in o) or len(set(o))!=len(o):raise ValueError("Invalid operations")
def goals(scope):
    return {"C":"Draft a bounded evidence brief from numerical results and bibliography",
            "E":"Independently verify numerical results and all producer receipts",
            "A":"Retrieve public scholarly metadata for approved DOI "+", ".join(scope["dois"]),
            "D":"Independently read back the public DOI metadata",
            "B":"Execute and functionally test the reviewed generic numerical sample analysis program: "+", ".join(scope["operations"])}
def evaluate(source,data):
    return json.loads(subprocess.run([sys.executable,str(source)],input=json.dumps(data),capture_output=True,text=True,timeout=15,check=True).stdout)
def inputs(scope):return {"values":scope["values"],"operations":scope["operations"]}
def brief(scope,prior):
    return {"objective":"Review synthetic numerical evidence for "+scope["subject"],"results":prior["engineering"]["result"]["validation"],
            "recommendation":"Obtain independently measured samples before external decisions",
            "limitations":["Synthetic owner-provided values are not measured evidence","DOI metadata is not validation of the sample data"],
            "new_paid_services":False,"external_actions_executed":False}
def run(role,scope,prior,directory):
    validate(scope)
    if role in ("intelligence","research"):
        from plenum_ai.chief_contract_plan import run_contract,check_contract_result
        ids={"dois":scope["dois"]}
        tool="crossref_metadata" if role=="intelligence" else "bibliography_readback"
        previous={} if role=="intelligence" else {"crossref_metadata":prior["intelligence"]["result"]}
        value=run_contract(tool,ids,previous);check_contract_result(tool,ids,previous,value);return value
    if role=="engineering":
        artifact=Path(tempfile.mkdtemp(prefix="engineering-artifact-",dir=directory))
        source=artifact/"main.py";source.write_bytes(SOURCE.read_bytes())
        data=inputs(scope);observed=evaluate(source,data)
        if observed!=independent(data):raise ValueError("Numerical analysis disagrees")
        manifest={"main_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"functional_verifier_executed_and_passed":True}
        exclusive(artifact/"manifest.json",manifest)
        return {"artifact_dir":artifact.name,"manifest":manifest,"input":data,"validation":observed}
    if role=="commercial":return brief(scope,prior)
    raise ValueError("Unknown dataset role")
def independent(data):
    v=data["values"];n=len(v)
    values={"mean":Fraction(sum(v),n),"median":Fraction(median(v)),"range":Fraction(max(v)-min(v))}
    return {"count":n,"results":{op:{"numerator":values[op].numerator,"denominator":values[op].denominator} for op in data["operations"]}}
def verify(scope,prior,directory,*,functional_test):
    from plenum_ai.chief_contract_plan import check_contract_result
    ids={"dois":scope["dois"]};intel=prior["intelligence"]["result"]
    check_contract_result("crossref_metadata",ids,{},intel)
    check_contract_result("bibliography_readback",ids,{"crossref_metadata":intel},prior["research"]["result"])
    eng=prior["engineering"]["result"];name=eng["artifact_dir"]
    if not isinstance(name,str) or not name.startswith("engineering-artifact-") or Path(name).name!=name:raise ValueError("Unsafe artifact")
    artifact=directory/name;source=artifact/"main.py"
    if artifact.is_symlink() or source.is_symlink() or source.read_bytes()!=SOURCE.read_bytes() or eng["input"]!=inputs(scope):raise ValueError("Dataset source or input mismatch")
    manifest=json.loads((artifact/"manifest.json").read_text())
    if manifest!=eng["manifest"] or manifest!={"main_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"functional_verifier_executed_and_passed":True}:raise ValueError("Dataset manifest mismatch")
    if eng["validation"]!=independent(eng["input"]) or (functional_test and evaluate(source,eng["input"])!=eng["validation"]):raise ValueError("Dataset verification disagrees")
    if brief(scope,prior)!=prior["commercial"]["result"]:raise ValueError("Brief changed")
    return {"verified_producers":4,"independent_actual_input_test":functional_test,"scholarly_metadata_records":len(intel),"synthetic_data_only":True,"general_autonomy_verified":False,"paid_inference":False}

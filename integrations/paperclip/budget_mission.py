"""Second reviewed native domain: explicit public DOI readback plus offline AI budget.

Reuses existing first-party contracts and program. Synthetic budget inputs are
not live billing data; never perform inference through the budget validator.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import hashlib
from mission_scope import validate_scope


def budget_input(scope):
    # Pin the reviewed pricing date so simulation is reproducible, not live entitlement.
    from plenum_ai.reviewed_domain_workers import DOMAIN_FILES
    import importlib.util
    spec=importlib.util.spec_from_file_location("plenum_reviewed_budget",DOMAIN_FILES["cloudflare_workers_ai_free"])
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return {"plan":"free","usage_day_utc":module.REVIEWED.isoformat(),**scope["budget"]}


def evaluate(source,data):
    # Run only the verified original program at its reviewed date, in a subprocess.
    result=subprocess.run([sys.executable,"-c",
        "import json,runpy,sys; m=runpy.run_path(sys.argv[1]); print(json.dumps(m['validate'](json.loads(sys.stdin.read()),today=m['REVIEWED']),sort_keys=True))",
        str(source)],input=json.dumps(data),capture_output=True,text=True,timeout=15,check=True)
    return json.loads(result.stdout)


def brief(scope, prior):
    result=prior["engineering"]["result"]["validation"]
    return {"objective":"Screen an offline AI budget scenario against reviewed source and public bibliography",
            "dois":sorted(scope["dois"]),"budget_status":result["status"],
            "estimated_neurons":result.get("estimate_neurons"),
            "recommendation":"Review current official pricing and actual authorized account usage before any provider call",
            "limitations":["Historical reviewed pricing and synthetic inputs only","Crossref metadata is not full-paper validation",
                           "No actual account entitlement, zero-cost guarantee or deployment"],
            "new_paid_services":False,"external_actions_executed":False}


def run(role,scope,prior,directory):
    from plenum_ai.chief_contract_plan import run_contract,check_contract_result
    from plenum_ai.reviewed_domain_workers import reuse_original_program
    scope=validate_scope(scope)
    doi_scope={"dois":scope["dois"]}
    if role=="intelligence":
        result=run_contract("crossref_metadata",doi_scope,{})
        check_contract_result("crossref_metadata",doi_scope,{},result)
        return result
    if role=="research":
        source=prior["intelligence"]["result"]
        result=run_contract("bibliography_readback",doi_scope,{"crossref_metadata":source})
        check_contract_result("bibliography_readback",doi_scope,{"crossref_metadata":source},result)
        return result
    if role=="engineering":
        artifact=Path(tempfile.mkdtemp(prefix="engineering-artifact-",dir=directory))
        manifest=reuse_original_program("cloudflare_workers_ai_free","Validate offline synthetic Workers AI budget",artifact)
        data=budget_input(scope)
        return {"artifact_dir":artifact.name,"manifest":manifest,"input":data,
                "validation":evaluate(artifact/"main.py",data)}
    if role=="commercial":return brief(scope,prior)
    raise ValueError("Unknown budget division")


def verify(scope,prior,directory,*,functional_test):
    from plenum_ai.chief_contract_plan import check_contract_result
    from plenum_ai.reviewed_domain_workers import DOMAIN_FILES
    scope=validate_scope(scope)
    doi_scope={"dois":scope["dois"]}
    intel=prior["intelligence"]["result"]
    research=prior["research"]["result"]
    check_contract_result("crossref_metadata",doi_scope,{},intel)
    check_contract_result("bibliography_readback",doi_scope,{"crossref_metadata":intel},research)
    eng=prior["engineering"]["result"]
    name=eng["artifact_dir"]
    if not isinstance(name,str) or not name.startswith("engineering-artifact-") or Path(name).name!=name:
        raise ValueError("Unsafe artifact path")
    artifact=directory/name
    source=artifact/"main.py"
    manifest=json.loads((artifact/"manifest.json").read_text())
    if (artifact.is_symlink() or source.is_symlink() or manifest!=eng["manifest"]
        or manifest.get("functional_verifier_executed_and_passed") is not True
        or source.read_bytes()!=DOMAIN_FILES["cloudflare_workers_ai_free"].read_bytes()
        or hashlib.sha256(source.read_bytes()).hexdigest()!=manifest.get("main_sha256")
        or eng["input"]!=budget_input(scope)):
        raise ValueError("Original budget artifact or input mismatch")
    if functional_test and evaluate(source,eng["input"])!=eng["validation"]:
        raise ValueError("Independent budget readback disagrees")
    if any(eng["validation"].get(k) is not False for k in ("account_plan_and_usage_verified","inference_executed","zero_cost_guaranteed")):
        raise ValueError("Unsupported account or inference claim")
    if brief(scope,prior)!=prior["commercial"]["result"]:raise ValueError("Commercial evidence mismatch")
    return {"verified_public_artifact_scope":True,"verified_producers":4,
            "scholarly_metadata_records":len(intel),"separate_same_provider_metadata_readback":True,
            "independent_actual_input_test":functional_test,"synthetic_budget_only":True,
            "general_autonomy_verified":False,"paid_inference":False}

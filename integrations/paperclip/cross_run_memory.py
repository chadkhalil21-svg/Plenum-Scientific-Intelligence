"""Owner-authorized cross-workflow continuation of a single qualified public source.

No untrusted source selector, no arbitrary URL or private state. The existing
workflow performs GitHub/Sigstore verification before this loader is invoked.
The original same-run memory loader and public issue gate remain unchanged.
"""
import hashlib,json,os,re,sys
from pathlib import Path
from checkpoint_store import checked,encoded
from pipeline_contract import validate_memory,digest,EXPORTS
from mission_scope import validate_scope

SOURCE_RUN="45549381583"
SOURCE_COMMIT="16738e2e366e9078701a1209adbc73209684231d"
SOURCE_REF="refs/pull/906/merge"
SOURCE_HEAD="9955e8b3ca29f512f6a89cb6e8681d3ca4afb3ab"
SOURCE_ARTIFACT=14993446038
SOURCE_ZIP="45eb1b613cdde690b8c99cfc4215b6646dbe50081367298b59f61766326a4fbc"
SOURCE_MEMORY="62ad650fa46a14976be18238822a73c5fde3301e978650d6828e01f84e16c676"
SOURCE_QUALIFICATION="12d3930fc9ba5765d014ba3ffabe6477addbde3b56581f77ce1ed676be5c5698"
REPO="chadkhalil21-svg/Plenum-Scientific-Intelligence"

def validate_source(run,artifact):
    if (str(run.get("id"))!=SOURCE_RUN or run.get("status")!="completed" or run.get("conclusion")!="success"
        or run.get("event")!="pull_request" or run.get("head_sha")!=SOURCE_HEAD
        or run.get("path")!=".github/workflows/paperclip-multidisciplinary.yml"
        or run.get("repository",{}).get("full_name")!=REPO):
        raise ValueError("Wrong original accepted workflow")
    if (artifact.get("id")!=SOURCE_ARTIFACT or artifact.get("name")!="paperclip-pipeline-memory-engineering"
        or artifact.get("expired") is not False or artifact.get("digest")!="sha256:"+SOURCE_ZIP
        or str(artifact.get("workflow_run",{}).get("id"))!=SOURCE_RUN):
        raise ValueError("Wrong or expired original artifact")

def build_scope(prior,current_run,current_commit,case):
    if not re.fullmatch(r"[1-9][0-9]{0,12}",current_run) or current_run==SOURCE_RUN or not re.fullmatch(r"[0-9a-f]{40}",current_commit):
        raise ValueError("Distinct invocation required")
    validate_memory(prior,"engineering")
    if prior["run_id"]!=SOURCE_RUN or prior["commit"]!=SOURCE_COMMIT or prior["qualification_sha256"]!=SOURCE_QUALIFICATION or digest(prior)!=SOURCE_MEMORY:
        raise ValueError("Exact original memory binding")
    # Novel synthetic tariffs and revenue, not repeated original commercial case.
    if case=="pr":params={"tariff_cents_kwh":50,"labor_cents_module_day":175,"revenue_cents_day":2800,"capital_cents_module":55000}
    elif case=="live":params={"tariff_cents_kwh":60,"labor_cents_module_day":200,"revenue_cents_day":3200,"capital_cents_module":60000}
    else:raise ValueError("Unsupported authorized continuation case")
    return validate_scope({"kind":"public_objective","objective":"Calculate daily operating cost, daily margin and whole-day payback.",
        "dois":["10.3390/w15020243"],"inputs":{"pipeline":{"stage":"commercial","parameters":params,"prior":prior}},
        "operation_commitment":digest(sorted(EXPORTS["commercial"]))})

def prepare(path,current_run,current_commit,case):
    row=checked(path,{})
    if hashlib.sha256(path.read_bytes()).hexdigest()!=SOURCE_MEMORY:raise ValueError("Exact signed bytes required")
    return build_scope(row,current_run,current_commit,case)

if __name__=="__main__":
    if sys.argv[1]=="metadata":
        validate_source(json.loads(Path(sys.argv[2]).read_text()),json.loads(Path(sys.argv[3]).read_text()))
    elif sys.argv[1]=="prepare":
        scope=prepare(Path(sys.argv[2]),os.environ["GITHUB_RUN_ID"],os.environ["GITHUB_SHA"],sys.argv[3])
        with open(os.environ["GITHUB_OUTPUT"],"a") as out:out.write("scope="+encoded(scope).decode()+"\n")
    else:raise ValueError("Unknown command")

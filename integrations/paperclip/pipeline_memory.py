"""Public-only attested mission memory export and successor scope construction.

The GitHub workflow verifies the Sigstore attestation before calling prepare.
A manifest is not a private checkpoint grant and does not restore a native board.
"""
import json,os,sys
from pathlib import Path
from checkpoint_store import checked,exclusive,encoded
from pipeline_contract import validate_memory,digest,PREVIOUS,EXPORTS
from mission_scope import validate_scope

def build_scope(stage,prior,run,commit):
    if stage not in PREVIOUS:raise ValueError("Unknown pipeline stage")
    if stage=="science":
        if prior is not None:raise ValueError("Unexpected prior")
        objective="Find paired removed mass, overall removal efficiency and worst-pair efficiency."
        dois=["10.1016/j.watres.2020.115551"]
        params={"control_mg":[100,120,80,100],"treated_mg":[20,30,20,30]}
    else:
        validate_memory(prior,PREVIOUS[stage])
        if prior["run_id"]!=run or prior["commit"]!=commit:raise ValueError("Wrong accepted predecessor run or commit")
        if stage=="engineering":
            objective="Determine effective capacity, required module count and daily energy requirement."
            dois=["10.1007/s13201-024-02185-4"]
            params={"target_mg_day":1000,"nominal_mg_day":400,"energy_wh_module_day":600}
        else:
            objective="Calculate daily operating cost, daily margin and whole-day payback."
            dois=["10.2166/wrd.2021.016"]
            params={"tariff_cents_kwh":25,"labor_cents_module_day":150,"revenue_cents_day":2500,"capital_cents_module":50000}
    return validate_scope({"kind":"public_objective","objective":objective,"dois":dois,
        "inputs":{"pipeline":{"stage":stage,"parameters":params,"prior":prior}},
        "operation_commitment":digest(sorted(EXPORTS[stage]))})

def prepare(stage,prior_file,run,commit):
    prior=None if stage=="science" else checked(Path(prior_file),{})
    return build_scope(stage,prior,run,commit)

def export(root,scope,run,commit):
    from fresh_runner_acceptance import accept
    accepted=accept(root,run,commit,scope)
    if accepted["verified_divisions"]!=5 or accepted["verified_profile_work_products"]!=11 or not accepted["model_receipt_verified"] or accepted["provider_calls_replayed"]!=0 or accepted["model_calls_replayed"]!=0 or accepted["paid_inference"] is not False:
        raise ValueError("Unqualified predecessor")
    directory=root/accepted["company"]/accepted["mission"]
    eng=checked(directory/"engineering.json",{"company":accepted["company"],"role":"engineering"})
    stage=scope["inputs"]["pipeline"]["stage"];prior=scope["inputs"]["pipeline"]["prior"]
    row={"schema":"plenum-public-pipeline-memory-v1","stage":stage,"run_id":run,"commit":commit,
         "scope_sha256":accepted["scope_sha256"],"qualification_sha256":accepted["qualification_sha256"],
         "previous_sha256":digest(prior) if prior is not None else None,
         "outcomes":eng["result"]["result"]["validation"]["results"],
         "fresh_runner_independent_acceptance":True,"verified_divisions":5,"verified_profile_work_products":11,
         "provider_calls_replayed":0,"model_calls_replayed":0,"paid_inference":False}
    return validate_memory(row,stage)

def main():
    run=os.environ["GITHUB_RUN_ID"];commit=os.environ["GITHUB_SHA"]
    if sys.argv[1]=="prepare":
        scope=prepare(sys.argv[2],sys.argv[3],run,commit)
        with open(os.environ["GITHUB_OUTPUT"],"a") as stream:stream.write("scope="+encoded(scope).decode()+"\n")
    elif sys.argv[1]=="export":
        scope=validate_scope(json.loads(os.environ["EXPECTED_SCOPE"]))
        row=export(Path(sys.argv[2]),scope,run,commit)
        exclusive(Path(sys.argv[3]),row)
        print(encoded(row).decode())
    else:raise ValueError("Unknown pipeline command")

if __name__=="__main__":main()

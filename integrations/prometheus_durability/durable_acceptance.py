"""DBOS durable coordination of accepted receipts. Never calls a model/provider.

The DBOS recovery mechanism may re-enter unacknowledged steps. Such steps
are restricted here to deterministic, read-only validation; a duplicate
write to an already existing receipt fails closed, rather than replays.
"""
import os,sys,json
from pathlib import Path
from importlib.metadata import version
from dbos import DBOS,SetWorkflowID
from receipts import read_accepted,digest,encoded,ARCHIVE_SHA
ROOT=None
WF="plenum-public-912-acceptance-v1"
TOKEN="continue-verified-public-acceptance"
def write_once(name,row):
    with (ROOT/name).open("xb") as f:
        f.write(encoded(row));f.flush();os.fsync(f.fileno())
@DBOS.step()
def review_original():
    cases=read_accepted(ROOT/"original.zip")
    row={"source_archive_sha256":ARCHIVE_SHA,"cases_sha256":digest(cases),"cases":len(cases),"paid_inference":False}
    write_once("step-one.json",row)
    return row
@DBOS.step()
def finish_review(previous):
    cases=read_accepted(ROOT/"original.zip")
    if json.loads((ROOT/"step-one.json").read_text())!=previous or previous["cases_sha256"]!=digest(cases):raise ValueError("Acknowledged predecessor changed")
    row={"schema":"plenum-dbos-accepted-receipt-v1","workflow":WF,"dbos_version":version("dbos"),
        "source_archive_sha256":ARCHIVE_SHA,"cases_sha256":digest(cases),"verified_native_cases":len(cases),
        "verified_divisions_per_case":5,"verified_work_products_per_case":11,
        "predecessor_sha256":digest(previous),"paid_inference":False,"model_calls_replayed":0,"provider_calls_replayed":0}
    write_once("step-two.json",row)
    return row
@DBOS.workflow()
def qualified_receipt_workflow():
    previous=review_original()
    DBOS.set_event("acknowledged",digest(previous))
    if DBOS.recv("resume",timeout_seconds=3600)!=TOKEN:raise ValueError("Authorized continuation missing")
    return finish_review(previous)
def main():
    global ROOT
    phase,folder=sys.argv[1:]
    ROOT=Path(folder).resolve()
    if os.environ.get("GITHUB_ACTIONS")!="true" or not ROOT.is_dir():raise PermissionError("Public synthetic CI only")
    if any(os.environ.get(k) for k in ("DBOS_CONDUCTOR_KEY","DBOS_CONDUCTOR_URL","DBOS_API_KEY","DBOS_CLOUD_TOKEN","OPENAI_API_KEY","ANTHROPIC_API_KEY","LANGSMITH_API_KEY")):raise PermissionError("Remote provider credentials forbidden")
    read_accepted(ROOT/"original.zip")
    db=ROOT/"workflow.sqlite"
    if phase=="prepare":
        if db.exists() or (ROOT/"step-one.json").exists():raise FileExistsError("New workflow required")
    elif phase=="resume":
        if not db.is_file() or not (ROOT/"step-one.json").is_file() or (ROOT/"step-two.json").exists():raise ValueError("Acknowledged predecessor required")
    else:raise ValueError("Unknown phase")
    DBOS(config={"name":"plenum-public-receipt","application_version":"1","executor_id":"local",
        "system_database_url":"sqlite:///"+str(db),"enable_otlp":False})
    DBOS.launch()
    if phase=="prepare":
        with SetWorkflowID(WF,workflow_id_reuse_policy="reject"):
            DBOS.start_workflow(qualified_receipt_workflow)
        ack=DBOS.get_event(WF,"acknowledged",timeout_seconds=30)
        if ack!=digest(json.loads((ROOT/"step-one.json").read_text())):raise ValueError("Step not acknowledged")
        # Actual abrupt process termination AFTER DBOS persisted the step.
        # No native mission or provider call exists in this workflow.
        os._exit(0)
    else:
        try:
            if DBOS.get_event(WF,"acknowledged",timeout_seconds=10)!=digest(json.loads((ROOT/"step-one.json").read_text())):raise ValueError("Restored acknowledgement missing")
            handle=DBOS.retrieve_workflow(WF)
            DBOS.send(WF,TOKEN,topic="resume",idempotency_key="single-public-continuation")
            result=handle.get_result()
            if result!=json.loads((ROOT/"step-two.json").read_text()):raise ValueError("Final receipt mismatch")
            print(json.dumps(result,sort_keys=True),flush=True)
        finally:DBOS.destroy()
if __name__=="__main__":main()

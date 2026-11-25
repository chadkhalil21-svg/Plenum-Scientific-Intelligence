"""Mock host/transport regression only; no production claims or credential use."""
import json,os
from unittest.mock import patch
from uuid import uuid4
from owner_restart import prove,NAME,SCHEMA
cid,mid=map(str,(uuid4(),uuid4()))
roles=("intelligence","research","engineering","commercial","verification")
def fixture(mismatch=False,wrong=False,stale=False):
    restarted=False;calls=[]
    def run(args):
        nonlocal restarted
        calls.append(args)
        if args[1]=="inspect":
            return json.dumps({"id":"1"*64,"started":"later" if restarted and not stale else "earlier","running":True,
                "network":"default","ports":{"3100/tcp":None},"mounts":[
                {"Destination":"/paperclip","Type":"volume","Name":"different" if restarted and mismatch else "original","RW":True},
                {"Destination":"/run/plenum-checkpoint","Type":"bind","RW":False}]})
        if args[1]=="restart":restarted=True;return NAME
        if args[-1]=="verify-live":
            return json.dumps({"schema":SCHEMA,"company":cid,"mission":mid,"verified_divisions":5,"verified_profile_work_products":11,
                "minister_model_executed":True,"remote_checkpoint_count":5,"wrong_scope_http_status":200 if wrong else 403,
                "wrong_scope_error":"checkpoint_scope_unavailable","independent_native_readback":True,"provider_calls_replayed":0,"paid_inference":False,
                "scope_sha256":"2"*64,"qualification_sha256":"3"*64,"model_receipt_sha256":"4"*64,
                "remote_checkpoints":{k:{"sha256":"5"*64} for k in roles},"recovery_receipt_sha256":{},"replan_receipt_sha256":{},
                "restart_readback_receipt_sha256":"6"*64 if restarted else None})
        if args[-1]=="restart-readback":return json.dumps({"container_restart_readback":True,"provider_calls_replayed":0,"qualification_sha256":"3"*64})
        return ""
    return run,calls
with patch.dict(os.environ,{"GITHUB_ACTIONS":"false"}):
    run,calls=fixture();r=prove(cid,mid,run)
    assert r["actual_same_container_restart"] and r["paid_inference"] is False
    assert sum(x[1]=="restart" for x in calls)==1 and sum(x[-1]=="verify-live" for x in calls)==2
    for opts in ({"mismatch":True},{"wrong":True},{"stale":True}):
        run,calls=fixture(**opts)
        try:prove(cid,mid,run)
        except (ValueError,PermissionError):pass
        else:raise AssertionError("Unverified continuity accepted")
        if opts.get("wrong"):assert not any(x[1]=="restart" for x in calls)
with patch.dict(os.environ,{"GITHUB_ACTIONS":"true"}):
    run,calls=fixture()
    try:prove(cid,mid,run)
    except PermissionError:pass
    else:raise AssertionError("Public CI owner proof allowed")
    assert not calls
print("PASS: mock owner same-volume restart, wrong-scope/changed-volume/stale-start rejection, public CI denial")

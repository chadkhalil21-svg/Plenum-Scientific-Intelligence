"""Isolated GitHub event mission launcher; no owner credentials or board export."""
import json,os,sys
from pathlib import Path
from lifecycle import canonical
from mission_scope import validate_scope,digest
from checkpoint_store import exclusive,checked
import sequential_mission as native

MARKER="event-native-mission.json"

def persistent_required(scope):
    return validate_scope(scope)["kind"]=="public_objective"

def execute():
    scope=native.active_scope()
    if not persistent_required(scope):return native.qualify()
    if os.getenv("PLENUM_PAPERCLIP_MODEL")!="local":raise PermissionError("Public objective requires local model")
    if native.api("/api/companies"):raise ValueError("Expected isolated empty board")
    company=canonical(native.api("/api/companies","POST",{"name":"Plenum bounded event objective","description":"Isolated public evidence mission"})["id"])
    os.environ.update(PLENUM_PERSISTENT_BOARD="confirmed",PLENUM_PAPERCLIP_COMPANY_UUID=company,PLENUM_PERSISTENT_CHECKPOINT_MODE="local")
    prepared=native.qualify("prepare")
    mission=canonical(prepared["mission"])
    row={"company":company,"mission":mission,"scope_sha256":digest(scope),"paid_inference":False}
    exclusive(native.ROOT/MARKER,row)
    os.environ["PLENUM_PAPERCLIP_MISSION_UUID"]=mission
    return native.qualify("activate")

def readback():
    path=native.ROOT/MARKER
    if path.exists() or path.is_symlink():
        row=checked(path,{"paid_inference":False})
        os.environ.update(PLENUM_PERSISTENT_BOARD="confirmed",PLENUM_PAPERCLIP_COMPANY_UUID=canonical(row["company"]),
                          PLENUM_PAPERCLIP_MISSION_UUID=canonical(row["mission"]))
        directory=native.ROOT/row["company"]/row["mission"]
        checked(directory/"qualification.json",{"company":row["company"],"parent":row["mission"],"scope_sha256":row["scope_sha256"]})
    return native.restart_readback()

if __name__=="__main__":
    if os.getenv("GITHUB_ACTIONS")!="true":raise SystemExit("Isolated public CI only")
    if len(sys.argv)!=2 or sys.argv[1] not in ("execute","readback"):raise SystemExit("Unknown isolated event action")
    try:
        (execute if sys.argv[1]=="execute" else readback)()
    except Exception as exc:
        native.failure_receipt(sys.argv[1],exc)
        raise SystemExit(1) from None

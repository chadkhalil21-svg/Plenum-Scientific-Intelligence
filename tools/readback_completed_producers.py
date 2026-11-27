"""Independent recovery of completed public outputs after native bootstrap failure.

Never restores a board, assigns workers, repeats model/provider requests, or
fabricates a native verification receipt. Uses the existing independent reviewer.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import tempfile
import zipfile

from checkpoint_store import checked, exclusive
from fresh_runner_acceptance import safe_tree, digest
from lifecycle import canonical
from mission_scope import validate_scope, profile_routes, digest as scope_digest
from profile_execution import chief_receipt, division_receipts
from sequential_mission import MISSION_ORDER, scope_binding, scope_inputs, verify

ARCHIVE_SHA = "5a33e4880a8d72956bda840d25748f7dde653e8908be124bbbba84221603ffb6"

def recover(archive, output):
    if (archive.is_symlink() or not archive.is_file()
            or not 0 < archive.stat().st_size < 2_000_000
            or hashlib.sha256(archive.read_bytes()).hexdigest()!=ARCHIVE_SHA):
        raise ValueError("Original failure archive identity")
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        with zipfile.ZipFile(archive) as z:
            entries=z.infolist()
            if (len(entries)>500 or len({i.filename for i in entries})!=len(entries)
                    or sum(i.file_size for i in entries)>20_000_000 or z.testzip() is not None):
                raise ValueError("Original evidence bounds")
            for i in entries:
                p=PurePosixPath(i.filename)
                if (p.is_absolute() or any(x in ("",".","..") for x in p.parts)
                        or p.as_posix()!=i.filename or "\\" in i.filename
                        or stat.S_ISLNK(i.external_attr>>16) or i.is_dir()):
                    raise ValueError("Unsafe archived path")
                dest=root.joinpath(*p.parts)
                dest.parent.mkdir(parents=True,exist_ok=True)
                with dest.open("xb") as stream:stream.write(z.read(i))
        safe_tree(root)
        checked(root/"ci-diagnostic.json",{"run_id":"46069339477","commit":"8f67e70bf1ef8d95a295985c251bb339bb1618e1",
                "startup":"success","checkpoint":"success","mission":"failure",
                "restart":"skipped","evidence_copy":"success","failure_receipts":1})
        m=checked(root/"event-native-mission.json",{"paid_inference":False})
        cid,mid=canonical(m["company"]),canonical(m["mission"])
        directory=root/cid/mid
        binding=checked(directory/"mission-scope.json",{})
        scope=validate_scope(binding["scope"])
        if binding!=scope_binding(scope) or m["scope_sha256"]!=scope_digest(scope):
            raise ValueError("Scope mismatch")
        plan=checked(directory/"minister-plan.json",{"company":cid,"parent":mid,"order":list(MISSION_ORDER)})
        handoff=checked(directory/"failure-handoff.json",{"company":cid,"mission":mid,
            "scope_sha256":scope_digest(scope),"mission_accepted":False,"automatic_replay_authorized":False,
            "no_local_reservation_observed":["verification"],"reserved_unfinished":[],"paid_inference":False})
        if handoff["plan_sha256"]!=digest(plan) or set(handoff["completed_receipts"])!=set(MISSION_ORDER[:-1]):
            raise ValueError("Producer handoff mismatch")
        if any((directory/n).exists() for n in ("verification.json","verification.attempt-1","qualification.json")):
            raise ValueError("Unexpected native acceptance state")
        if checked(directory/"profile-routing.json",{})!=profile_routes(scope):
            raise ValueError("Profile routing mismatch")
        chief=checked(directory/"chief-profile.json",{})
        if chief!=chief_receipt(scope,plan):raise ValueError("Chief receipt mismatch")
        profiles={"chief":digest(chief)}
        prior={}
        for role in MISSION_ORDER[:-1]:
            issue=canonical(plan["tasks"][role])
            row=checked(directory/(role+".json"),{"company":cid,"role":role,"issue":issue})
            value=row["result"]
            if row["sha256"]!=digest(value) or value["input_sha256"]!=scope_inputs(prior):
                raise ValueError("Producer receipt mismatch")
            if handoff["completed_receipts"][role]!={"issue":issue,"receipt_sha256":digest(row)}:
                raise ValueError("Handoff producer digest mismatch")
            expected=division_receipts(role,scope,prior,value["result"],directory)
            if value["profile_receipts"]!=expected or set(expected)&set(profiles):
                raise ValueError("Profile evidence mismatch")
            profiles.update({k:digest(v) for k,v in expected.items()})
            prior[role]=value
        result=verify(prior,directory,functional_test=True,scope=scope)
        exclusive(output,{"source_artifact":15231859914,"source_archive_sha256":ARCHIVE_SHA,
            "company":cid,"mission":mid,"scope_sha256":scope_digest(scope),
            "completed_producers_verified":4,"verified_existing_profile_count":len(profiles),
            "existing_profile_receipts":profiles,"independent_output_readback":result,
            "native_verification_completed":False,"native_board_restored":False,
            "mission_accepted":False,"model_calls_replayed":0,"provider_calls_replayed":0,
            "paid_inference":False,"general_autonomy_verified":False})

if __name__=="__main__":
    if os.getenv("GITHUB_ACTIONS")!="true":raise PermissionError("Original evidence-only CI")
    recover(Path(sys.argv[1]),Path(sys.argv[2]))

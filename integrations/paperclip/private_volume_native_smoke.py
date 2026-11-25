"""CI-only real synthetic native evidence recovery on a separate private volume."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import sys
from checkpoint_store import checked,encoded,exclusive
from private_volume import collect,grant,seal,restore,sign,accepted
from mission_scope import digest
from composition_smoke import scope as fixture_scope

ROOT=Path("/paperclip/plenum-mission-evidence")
STORE=Path("/plenum-private-proof")

def identity():
    if os.getenv("GITHUB_ACTIONS")!="true":raise PermissionError("Isolated synthetic CI only")
    marker=checked(ROOT/"event-native-mission.json",{"paid_inference":False,"scope_sha256":digest(fixture_scope("composition-energy"))})
    from lifecycle import canonical
    company,mission=canonical(marker["company"]),canonical(marker["mission"])
    directory=ROOT/company/mission
    return company,mission,directory

def main(action):
    company,mission,directory=identity()
    if action=="seal":
        if any(STORE.iterdir()):raise ValueError("Fresh isolated recovery volume required")
        checked(directory/"mission-scope.json",{"scope":fixture_scope("composition-energy")})
        exclusive(STORE/"grant.json",{"scope":company+"/"+mission,"key_hex":secrets.token_hex(32)})
        os.chmod(STORE/"grant.json",0o600)
        original=collect(directory)
        qualification=seal(directory,STORE,company,mission)
        signed=checked(STORE/"snapshot.json",{})
        key=grant(STORE,company,mission)
        if signed["body"]["entries"]!=original or signed["signature"]!=sign(key,signed["body"]):raise ValueError("Local backup readback mismatch")
        if qualification!=accepted(original,company,mission):raise ValueError("Qualification binding")
        # Destroy ONLY the exact isolated completed synthetic evidence directory.
        shutil.rmtree(directory)
        if directory.exists():raise ValueError("Original synthetic evidence still present")
    elif action=="restore":
        if directory.exists():raise ValueError("Expected missing original evidence")
        restore(directory,STORE,company,mission)
    elif action=="finish":
        signed=checked(STORE/"snapshot.json",{})
        key=grant(STORE,company,mission)
        entries=collect(directory)
        if signed["signature"]!=sign(key,signed["body"]) or entries!=signed["body"]["entries"]:raise ValueError("Restored bytes disagree")
        q=accepted(entries,company,mission)
        if q!=signed["body"]["qualification_sha256"]:raise ValueError("Restored qualification mismatch")
        exclusive(ROOT/"private-restore-proof.json",{"schema":"plenum-isolated-native-private-restore-v1","company":company,"mission":mission,
            "qualification_sha256":q,"file_manifest_sha256":hashlib.sha256(encoded(entries)).hexdigest(),"restored_file_count":len(entries),
            "scope_sha256":digest(fixture_scope("composition-energy")),"separate_private_volume":True,"synthetic_grant":True,
            "native_restart_readback_after_restore":True,"provider_calls_replayed":0,"model_calls_replayed":0,"paid_inference":False})
    else:raise ValueError("Unknown isolated recovery action")

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("Exact isolated recovery action")
    main(sys.argv[1])

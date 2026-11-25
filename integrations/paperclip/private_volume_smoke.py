"""Separate-process local private fixture: grant, authenticated bytes, fail closed."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
from uuid import uuid4
from checkpoint_store import encoded

def run():
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);evidence=root/"evidence";evidence.mkdir(mode=0o700);store=root/"private";store.mkdir(mode=0o700)
        company,mission=str(uuid4()),str(uuid4())
        q={"company":company,"parent":mission,"scope_sha256":"a"*64,"verified_divisions":5,"verified_profile_work_products":11,"paid_inference":False}
        d=hashlib.sha256(encoded(q)).hexdigest()
        for name,row in {"qualification.json":q,"prepared.json":{"company":company,"mission":mission,"scope_sha256":"a"*64},
                         "restart-timing.json":{"qualification_sha256":d,"container_restart_readback":True,"provider_calls_replayed":0},
                         "synthetic.json":{"text":"synthetic private fixture"}}.items():
            (evidence/name).write_bytes(encoded(row))
        grant={"scope":company+"/"+mission,"key_hex":secrets.token_hex(32)}
        (store/"grant.json").write_bytes(encoded(grant));os.chmod(store/"grant.json",0o600)
        script=Path(__file__).with_name("private_volume.py")
        def invoke(action,c=company,m=mission,success=True):
            p=subprocess.run([sys.executable,str(script),action,str(evidence),str(store),c,m],capture_output=True,text=True)
            assert (p.returncode==0)==success,p.stderr
            if success:assert json.loads(p.stdout)["qualification_sha256"]==d
        original={p.name:p.read_bytes() for p in evidence.iterdir()}
        invoke("seal");invoke("restore",success=False)
        shutil.rmtree(evidence)
        invoke("restore",m=str(uuid4()),success=False)
        snapshot=store/"snapshot.json";raw=snapshot.read_bytes()
        row=json.loads(raw);row["body"]["entries"]["synthetic.json"]="e30="
        snapshot.write_bytes(encoded(row));invoke("restore",success=False);snapshot.write_bytes(raw)
        grant_path=store/"grant.json";grant_path.write_bytes(encoded(dict(grant,key_hex=secrets.token_hex(32))))
        invoke("restore",success=False);grant_path.write_bytes(encoded(grant))
        invoke("restore")
        assert {p.name:p.read_bytes() for p in evidence.iterdir()}==original
        print("Separate-process synthetic private checkpoint restoration, wrong scope/key, tamper and overwrite rejection passed; no production grant or board claimed")
if __name__=="__main__":run()

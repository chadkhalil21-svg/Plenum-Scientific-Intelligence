"""Two native missions on the same persistent board, including container restart.
Invoked from the isolated CI host, never a production credentials context."""
import json
import subprocess
import sys

CONTAINER="plenum-paperclip-integration"
def run(*args):
    return subprocess.check_output(["docker","exec","--user","node","-e","PYTHONPATH=/plenum/src",*args,CONTAINER],text=True)
def py(code):
    return subprocess.check_output(["docker","exec","--user","node","-e","PYTHONPATH=/plenum/src",CONTAINER,"python3","-c",code],text=True)
def mission(cid,scope,mid=None):
    args=["docker","exec","--user","node","-e","PYTHONPATH=/plenum/src","-e","PLENUM_PERSISTENT_BOARD=confirmed",
          "-e","PLENUM_PAPERCLIP_COMPANY_UUID="+cid,"-e","PLENUM_MISSION_SCOPE="+json.dumps(scope)]
    if mid:args+=["-e","PLENUM_PAPERCLIP_MISSION_UUID="+mid]
    args += [CONTAINER,"python3","/plenum/integrations/paperclip/sequential_mission.py","restart-readback" if mid else "qualify"]
    output=subprocess.check_output(args,text=True)
    print(output,flush=True)
    return json.loads(output.strip().splitlines()[-1])
def restart():
    import time
    subprocess.run(["docker","restart",CONTAINER],check=True)
    for _ in range(90):
        if subprocess.run(["docker","exec",CONTAINER,"curl","--fail","--silent","http://127.0.0.1:3100/api/health"],stdout=subprocess.DEVNULL).returncode==0:return
        time.sleep(2)
    raise RuntimeError("Persistent restart unavailable")
def main():
    cid=py("import sys;sys.path.insert(0,'/plenum/integrations/paperclip');from acceptance import api;print(api('/api/companies','POST',{'name':'Plenum durable lifecycle qualification','description':'Bounded isolated test'})['id'])").strip()
    scope={"kind":"bibliography_budget","dois":["10.1145/3442188.3445922"],"budget":{"model":"@cf/zai-org/glm-4.7-flash","neurons_used_today":100,"neurons_reserved":200,"input_tokens_upper_bound":3000,"output_tokens_upper_bound":1000}}
    a=mission(cid,scope)
    restart()
    r1=mission(cid,scope,a["parent"])
    scope["budget"]["neurons_reserved"]=201
    b=mission(cid,scope)
    restart()
    r2=mission(cid,scope,b["parent"])
    again=mission(cid,scope,a["parent"])
    assert a["company"]==b["company"]==cid and a["minister"]==b["minister"]
    assert a["parent"]!=b["parent"] and a["scope_sha256"]!=b["scope_sha256"]
    assert a["verified_profile_work_products"]==b["verified_profile_work_products"]==11
    assert r1["qualification_sha256"]==again["qualification_sha256"]!=r2["qualification_sha256"]
    proof={"same_company":cid,"same_minister":a["minister"],"missions":[a["parent"],b["parent"]],"restart_digests":[r1["qualification_sha256"],r2["qualification_sha256"]],"first_mission_preserved":True,"paid_inference":False}
    # Store only bounded public acceptance evidence in the existing mounted volume.
    subprocess.run(["docker","exec","--user","node",CONTAINER,"python3","-c","from pathlib import Path;import sys;Path('/paperclip/plenum-mission-evidence/persistent-lifecycle.json').write_text(sys.argv[1])",json.dumps(proof)],check=True)
    print(json.dumps(proof))
if __name__=="__main__":main()

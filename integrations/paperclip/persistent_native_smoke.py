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
def mission(cid,scope,mid=None,action=None,mode="off",inject=False):
    args=["docker","exec","--user","node","-e","PYTHONPATH=/plenum/src","-e","PLENUM_PERSISTENT_BOARD=confirmed",
          "-e","PLENUM_PAPERCLIP_COMPANY_UUID="+cid,"-e","PLENUM_MISSION_SCOPE="+json.dumps(scope)]
    args+=["-e","PLENUM_PAPERCLIP_MODEL="+mode]
    if inject:args+=["-e","PLENUM_CI_TRANSIENT_INTELLIGENCE=confirmed"]
    if mid:args+=["-e","PLENUM_PAPERCLIP_MISSION_UUID="+mid]
    args += [CONTAINER,"python3","/plenum/integrations/paperclip/sequential_mission.py",action or ("restart-readback" if mid else "qualify")]
    try:
        output=subprocess.check_output(args,text=True)
    except subprocess.CalledProcessError as exc:
        # Only the bounded, sanitized failure receipt emitted by the entrypoint.
        for line in (exc.output or "").splitlines():
            try:row=json.loads(line)
            except ValueError:continue
            if isinstance(row,dict) and set(row)=={"stage","error_type","missing_field","http_status","frames","native_run_id"}:
                print(json.dumps(row),flush=True)
        raise
    print(output,flush=True)
    return json.loads(output.strip().splitlines()[-1])
def restart():
    import time
    subprocess.run(["docker","restart",CONTAINER],check=True)
    for _ in range(90):
        if subprocess.run(["docker","exec",CONTAINER,"curl","--fail","--silent","http://127.0.0.1:3100/api/health"],stdout=subprocess.DEVNULL).returncode==0:return
        time.sleep(2)
    raise RuntimeError("Persistent restart unavailable")
def model_stop():
    subprocess.run(["docker","rm","-f","plenum-paperclip-qwen"],check=True)
def model_start():
    import time
    subprocess.run(["docker","run","-d","--name","plenum-paperclip-qwen","--network","container:"+CONTAINER,
                    "-e","OLLAMA_HOST=127.0.0.1:11434","-e","OLLAMA_CONTEXT_LENGTH=2048","-e","OLLAMA_NUM_PARALLEL=1",
                    "--memory=8g","--cpus=3","--mount","type=volume,src=plenum-paperclip-qwen-cache,dst=/root/.ollama","ollama/ollama:latest"],check=True)
    for _ in range(45):
        if subprocess.run(["docker","exec",CONTAINER,"curl","--fail","--silent","http://127.0.0.1:11434/api/tags"],stdout=subprocess.DEVNULL).returncode==0:return
        time.sleep(2)
    raise RuntimeError("Local model restart unavailable")
def main():
    mode=sys.argv[1] if len(sys.argv)>1 else "off"
    cid=py("import sys;sys.path.insert(0,'/plenum/integrations/paperclip');from acceptance import api;print(api('/api/companies','POST',{'name':'Plenum durable lifecycle qualification','description':'Bounded isolated test'})['id'])").strip()
    scope={"kind":"bibliography_budget","dois":["10.1145/3442188.3445922"],"budget":{"model":"@cf/zai-org/glm-4.7-flash","neurons_used_today":100,"neurons_reserved":200,"input_tokens_upper_bound":3000,"output_tokens_upper_bound":1000}}
    prep1=mission(cid,scope,action="prepare",mode=mode)
    a=mission(cid,scope,prep1["mission"],action="activate")
    if mode=="local":model_stop()
    restart()
    r1=mission(cid,scope,a["parent"])
    if mode=="local":model_start()
    scope["budget"]["neurons_reserved"]=201
    prep2=mission(cid,scope,action="prepare",mode=mode)
    b=mission(cid,scope,prep2["mission"],action="activate")
    if mode=="local":model_stop()
    restart()
    r2=mission(cid,scope,b["parent"])
    again=mission(cid,scope,a["parent"])
    assert a["parent"]==prep1["mission"] and b["parent"]==prep2["mission"]
    assert a["company"]==b["company"]==cid and a["minister"]==b["minister"]
    assert a["persistent_roster"]==b["persistent_roster"] and len(set(a["persistent_roster"].values()))==6
    assert a["parent"]!=b["parent"] and a["scope_sha256"]!=b["scope_sha256"]
    assert a["verified_profile_work_products"]==b["verified_profile_work_products"]==11
    assert a["minister_model_executed"]==b["minister_model_executed"]==(mode=="local")
    assert a["paid_inference"] is b["paid_inference"] is False
    if mode=="local":assert a["model_receipt_sha256"]!=b["model_receipt_sha256"]
    assert r1["qualification_sha256"]==again["qualification_sha256"]!=r2["qualification_sha256"]
    proof={"same_company":cid,"same_minister":a["minister"],"same_six_agent_ids":a["persistent_roster"],"missions":[a["parent"],b["parent"]],"restart_digests":[r1["qualification_sha256"],r2["qualification_sha256"]],"first_mission_preserved":True,"staged_prepare_activate":True,"model_mode":mode,"paid_inference":False}
    # Store only bounded public acceptance evidence in the existing mounted volume.
    subprocess.run(["docker","exec","--user","node",CONTAINER,"python3","-c","from pathlib import Path;import sys;Path('/paperclip/plenum-mission-evidence/persistent-lifecycle.json').write_text(sys.argv[1])",json.dumps(proof)],check=True)
    print(json.dumps(proof))
if __name__=="__main__":main()

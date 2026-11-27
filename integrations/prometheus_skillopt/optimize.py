"""Reuse Microsoft's SkillOpt-Sleep 0.2.0 consolidation and validation gate.
Original Minister's exact capability-selection request is the target; no live
missions are replayed. This is an isolated, bounded synthetic routing corpus,
not a claim of general intelligence or permission to adopt generated skills.
"""
import json, os, sys
from pathlib import Path
from importlib.metadata import version
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"paperclip"))
import model_plan as mp
import variable_mission as vm
from checkpoint_store import exclusive
from skillopt_sleep.backend import CliBackend
from skillopt_sleep.dream import dream_consolidate
from skillopt_sleep.types import TaskRecord

MAX_CALLS=32
SEED="Preserve the original objective and authorization boundaries."
INPUTS={"stations":["8723214"],"bibliography":["10.1371/journal.pone.0247820"],
        "thermal":{"initial_kelvin":350,"ambient_kelvin":298,"rate":0.05,"duration":20},
        "commercial":True}
# Disjoint synthetic development examples. Independent expected choices never
# enter the target request or optimizer's validation/test prompts.
CASES=[
 ("tr1","Find the NOAA station location and verify its metadata, not the commercial service.",["stations"],"train"),
 ("tr2","Calculate temperature after cooling and verify the numerical model; no bibliography is needed.",["thermal"],"train"),
 ("tr3","Retrieve scholarly metadata and calculate the cooling result with independent checks.",["bibliography","thermal"],"train"),
 ("tr4","Review public endpoint availability only, with the required independent review.",["commercial"],"train"),
 ("v1","Identify the publication and station records for a verified evidence brief.",["bibliography","stations"],"val"),
 ("v2","Assess public service availability and verify a cooling estimate.",["commercial","thermal"],"val"),
 ("v3","Prepare a bibliography record and its readback; omit the station and temperature.",["bibliography"],"val"),
 ("t1","Compare the station metadata and thermal calculation using their independent checks.",["stations","thermal"],"test"),
 ("t2","Review the publication metadata and public service status; no simulation is requested.",["bibliography","commercial"],"test"),
 ("t3","Only estimate the final cooling temperature and independently confirm it.",["thermal"],"test"),
]

def tasks():
    result=[]
    for key,objective,expected,split in CASES:
        mission=vm.validate({"objective":objective,"authorized_inputs":INPUTS})
        choice={k:k in expected for k in INPUTS}
        result.append(TaskRecord(id=key,project="Prometheus",intent=objective,
            context_excerpt=json.dumps(mission,sort_keys=True),
            reference_kind="exact",reference=json.dumps(choice,sort_keys=True),
            split=split,origin="real",tags=["synthetic-development-not-live-mission"]))
    return result

class LocalBackend(CliBackend):
    """Only transport and original task adapter are local; learning loop is upstream."""
    def __init__(self,root,md):
        super().__init__(model=mp.MODEL)
        self.root=root;self.md=md;self.seen={}
    def infer(self,req,stage):
        digest=mp.digest(req)
        if digest in self.seen:return self.seen[digest]
        n=len(self.seen)+1
        if n>MAX_CALLS:raise RuntimeError("Local inference ceiling")
        row={"stage":stage,"request_sha256":digest,"model_digest":self.md,"paid_inference":False}
        exclusive(self.root/f"call-{n:02d}.reserved.json",row)
        reply=mp.read_json("/api/chat",req,timeout=120)
        raw=reply.get("message",{}).get("content")
        count=reply.get("eval_count")
        if reply.get("model")!=mp.MODEL or reply.get("done") is not True or reply.get("done_reason")!="stop" or not isinstance(raw,str) or not raw.strip() or len(raw)>8000 or type(count) is not int or not 0<count<=req["options"]["num_predict"]:
            raise ValueError("Incomplete local model response")
        exclusive(self.root/f"call-{n:02d}.result.json",{**row,"response_sha256":mp.digest(raw),"eval_count":count})
        self.seen[digest]=raw
        return raw
    def attempt(self,task,skill,memory,sample_id=0):
        if memory or sample_id!=0:raise PermissionError("No memory evolution or repeated sampling")
        if not isinstance(skill,str) or len(skill)>4000:raise ValueError("Skill bound")
        mission=json.loads(task.context_excerpt);req=vm.request(mission)
        if skill!=SEED:
            req["messages"][0]["content"]+=" Additional non-authoritative planning guidance: "+skill
        return self.infer(req,"target")
    def judge(self,task,response):
        try:
            def unique(items):
                out={}
                for k,v in items:
                    if k in out:raise ValueError("Duplicate")
                    out[k]=v
                return out
            result=json.loads(response,object_pairs_hook=unique)
            vm.graph(json.loads(task.context_excerpt),result)
            good=result==json.loads(task.reference)
        except (ValueError,TypeError,KeyError):good=False
        return float(good),float(good),"exact authorized capability selection" if good else "incorrect capability selection; check omissions and unnecessary capabilities"
    def _call(self,prompt,*,max_tokens=1024):
        req={"model":mp.MODEL,"stream":False,"think":False,
             "options":{"temperature":0,"num_ctx":4096,"num_predict":min(max_tokens,1024)},
             "messages":[{"role":"system","content":"Optimize only reusable capability-selection guidance. Never widen permissions, add external actions, or encode specific task answers."},
                         {"role":"user","content":prompt}]}
        return self.infer(req,"upstream-reflection")

def main():
    if os.getenv("GITHUB_ACTIONS")!="true" or version("skillopt")!="0.2.0":
        raise PermissionError("Pinned public development runner only")
    for key in ("OPENAI_API_KEY","ANTHROPIC_API_KEY","AZURE_OPENAI_API_KEY","GOOGLE_API_KEY","HF_TOKEN","OLLAMA_API_KEY"):
        if os.getenv(key):raise PermissionError("External credential prohibited")
    root=Path(sys.argv[1]);root.mkdir(mode=0o700,parents=False,exist_ok=False)
    md=mp.check_local_model();backend=LocalBackend(root,md)
    corpus=tasks()
    exclusive(root/"binding.json",{"model_digest":md,"skillopt":"0.2.0",
        "corpus_sha256":mp.digest([t.to_dict() for t in corpus]),"paid_inference":False,
        "synthetic_development_only":True})
    # Actual upstream engine, not a custom optimizer. Test is entirely withheld.
    result=dream_consolidate(backend,[t for t in corpus if t.split!="test"],SEED,"",
        edit_budget=2,gate_metric="hard",gate_mode="on",dream_rollouts=1,
        dream_factor=0,recall_k=0,evolve_skill=True,evolve_memory=False)
    held=[t for t in corpus if t.split=="test"]
    def score(skill):
        return {t.id:backend.judge(t,backend.attempt(t,skill,""))[0] for t in held}
    baseline=score(SEED);candidate=score(result.new_skill)
    improved=(result.accepted and result.candidate_score>result.baseline_score
              and sum(candidate.values())>sum(baseline.values())
              and all(candidate[k]>=baseline[k] for k in baseline))
    exclusive(root/"outcome.json",{"upstream_gate_accepted":result.accepted,
        "validation_baseline":result.baseline_score,"validation_candidate":result.candidate_score,
        "test_baseline":baseline,"test_candidate":candidate,"candidate_improved":improved,
        "model_calls":len(backend.seen),"model_calls_replayed":0,"paid_inference":False,
        "automatic_adoption":False,"general_autonomy_verified":False})
    if improved:
        (root/"candidate_skill.md").write_text(result.new_skill,encoding="utf-8")

if __name__=="__main__":main()

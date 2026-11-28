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
# Former held-out observations are now training only. The original archive is
# immutable: run 45981480956, artifact 15190141010, exact SHA256 below.
# The original raw Boolean content was recovered by enumerating the finite
# answer space and matching the archived response hashes, not by new inference.
ARCHIVE_SHA256="494837bc2e558c8c7c93a400eefb4d2e3eea07735a460ef8a2878934fa587080"
ARCHIVE_MODEL="d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04"
ARCHIVED={
 "old_v1":("0eace987d5534f2093034ac71e410860c16484523b48e61a32a0364afe7a0f14","cd872214a6f61c3a2956cd84b9a490c6aa702b708a193841a86e53695707f1f3",[]),
 "old_v2":("457f4fdacd909634566ed35964e2e673e9e0dbd8150fc7fb89d50ea499d4fa16","cd872214a6f61c3a2956cd84b9a490c6aa702b708a193841a86e53695707f1f3",[]),
 "old_v3":("29f4b8b8fd3296960835c684d18397ff474637e48d38e6915f9fef512ebd1080","d8176ab997ed47dd617dd1bccdcc28e774df231d47ed03a767fea78f2c136d02",["bibliography"]),
 "old_t2":("07d52bb0c74e04cb4a01bc7e2492644cdf4e9d717498c7aae6ffa61924aac589","cd872214a6f61c3a2956cd84b9a490c6aa702b708a193841a86e53695707f1f3",[]),
}
CASES=[
 ("old_v1","Identify the publication and station records for a verified evidence brief.",["bibliography","stations"],"train"),
 ("old_v2","Assess public service availability and verify a cooling estimate.",["commercial","thermal"],"train"),
 ("old_v3","Prepare a bibliography record and its readback, omit the station and temperature.",["bibliography"],"train"),
 ("old_t2","Review the publication metadata and public service status, no simulation is requested.",["bibliography","commercial"],"train"),
 ("v4","For the evidence brief establish the station coordinates and verify the public endpoint status.",["stations","commercial"],"val"),
 ("v5","Review publication details, predict the cooling temperature and verify the service availability.",["bibliography","commercial","thermal"],"val"),
 ("v6","Establish the scholarly record and its independent confirmation without undertaking other work.",["bibliography"],"val"),
 ("t4","Prepare a verified brief covering station identity, literature metadata and the thermal estimate.",["bibliography","stations","thermal"],"test"),
 ("t5","Determine whether the public service is reachable and establish its independent review.",["commercial"],"test"),
 ("t6","Report the cooling prediction and the public station identity, with independent confirmation of both.",["stations","thermal"],"test"),
]

def archived_response(task,req,md):
    expected=ARCHIVED.get(task.id)
    if expected is None:return None
    request_hash,response_hash,selected=expected
    raw=json.dumps({k:k in selected for k in sorted(INPUTS)})
    if md.removeprefix("sha256:")!=ARCHIVE_MODEL or mp.digest(req)!=request_hash or mp.digest(raw)!=response_hash:
        raise ValueError("Archived training evidence mismatch")
    return raw,request_hash,response_hash


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
        self.root=root;self.md=md;self.seen={};self.restored=set()
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
        if skill==SEED and task.id in ARCHIVED:
            raw,request_hash,response_hash=archived_response(task,req,self.md)
            if task.id not in self.restored:
                exclusive(self.root/(task.id+".archive-readback.json"),
                    {"source_artifact":15190141010,"archive_sha256":ARCHIVE_SHA256,
                     "task":task.id,"request_sha256":request_hash,"response_sha256":response_hash,
                     "model_digest":self.md,"new_inference":False})
                self.restored.add(task.id)
            return raw
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
        "model_calls":len(backend.seen),"archived_training_readbacks":len(backend.restored),
        "optimizer_model_calls":sum(1 for p in root.glob("call-*.result.json") if json.loads(p.read_text())["stage"]=="upstream-reflection"),
        "model_calls_replayed":0,"paid_inference":False,
        "automatic_adoption":False,"general_autonomy_verified":False})
    if len(backend.restored)!=len(ARCHIVED):raise ValueError("Incomplete archived training evidence")
    if improved:
        (root/"candidate_skill.md").write_text(result.new_skill,encoding="utf-8")

if __name__=="__main__":main()

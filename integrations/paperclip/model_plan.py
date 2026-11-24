"""One real local Qwen plan for the approved native five-division mission.

No external model/API, arbitrary tool names, task text execution or fallback.
A valid response drives native assignment; invalid output fails closed.
"""
import json
import os
from urllib.request import Request, build_opener
from acceptance import NoRedirect
from checkpoint_store import encoded, exclusive
from hashlib import sha256

MODEL = "qwen3.5:4b"
MODEL_DIGEST = "d8b0f5e9760c"
URL = "http://127.0.0.1:11434"
# Fixed scope and shuffled input, not the desired ordered output.
GOALS = {"C": "Produce a commercial brief from scientific and engineering receipts",
         "E": "Independently verify every previous receipt and test the engineering artifact",
         "A": "Retrieve a public NOAA station metadata signal",
         "D": "Find and validate scholarly DOI metadata for corrosion monitoring",
         "B": "Build and functionally test the reviewed station metadata validator"}
ROLE_MAP = {"A":"intelligence","D":"research","B":"engineering","C":"commercial","E":"verification"}
ORDER = ["intelligence","research","engineering","commercial","verification"]


def digest(value):
    return sha256(encoded(value)).hexdigest()


def validate_choice(value):
    if not isinstance(value,dict) or set(value)!={"steps"} or not isinstance(value["steps"],list) or len(value["steps"])!=5:
        raise ValueError("Invalid bounded Minister plan shape")
    roles=[]
    for step in value["steps"]:
        if not isinstance(step,dict) or set(step)!={"goal","division"}:
            raise ValueError("Invalid model assignment")
        goal,role=step["goal"],step["division"]
        if not isinstance(goal,str) or not isinstance(role,str) or ROLE_MAP.get(goal)!=role:
            raise ValueError("Model assignment outside authorized scope")
        roles.append(role)
    if roles!=ORDER:
        raise ValueError("Model dependency order not accepted")
    return roles


def read_json(path, payload=None, timeout=10):
    data=None if payload is None else encoded(payload)
    with build_opener(NoRedirect).open(Request(URL+path,data=data,headers={"Content-Type":"application/json"}),timeout=timeout) as res:
        raw=res.read(65537)
    if len(raw)>65536: raise ValueError("Local model response too large")
    return json.loads(raw)


def validate_receipt(receipt, company, parent):
    if not isinstance(receipt,dict) or set(receipt)!={"company","parent","model","model_digest","goals_sha256","response","response_sha256","eval_count","prompt_eval_count","paid_inference"}:
        raise ValueError("Invalid local model receipt")
    if (receipt["company"]!=company or receipt["parent"]!=parent or receipt["model"]!=MODEL
            or not receipt["model_digest"].startswith("sha256:"+MODEL_DIGEST)
            or receipt["goals_sha256"]!=digest(GOALS) or receipt["response_sha256"]!=digest(receipt["response"])
            or type(receipt["eval_count"]) is not int or not 0<receipt["eval_count"]<=256
            or type(receipt["prompt_eval_count"]) is not int or not 0<receipt["prompt_eval_count"]<=2048
            or receipt["paid_inference"] is not False):
        raise ValueError("Invalid local model receipt binding")
    return validate_choice(receipt["response"])


def model_plan(directory, company, parent):
    path=directory/"minister-model-plan.json"
    if path.exists():
        receipt=json.loads(path.read_text())
        return validate_receipt(receipt,company,parent),receipt
    if os.getenv("PLENUM_EPHEMERAL_RUNNER")!="confirmed" or os.getenv("PLENUM_PAPERCLIP_MODEL")!="local":
        raise PermissionError("Only explicitly isolated local model qualification")
    # Do not make a second model call after an ambiguous interruption.
    exclusive(directory/"minister-model-attempt.json",{"company":company,"parent":parent,"maximum":1})
    tags=read_json("/api/tags")
    matches=[x for x in tags.get("models",[]) if x.get("name")==MODEL]
    if len(matches)!=1 or not matches[0].get("digest","").startswith("sha256:"+MODEL_DIGEST):
        raise ValueError("Unexpected local Qwen model digest")
    schema={"type":"object","required":["steps"],"additionalProperties":False,"properties":{"steps":{
        "type":"array","minItems":5,"maxItems":5,"items":{"type":"object","additionalProperties":False,
        "required":["goal","division"],"properties":{"goal":{"enum":list(GOALS)},"division":{"enum":sorted(ORDER)}}}}}}
    request={"model":MODEL,"stream":False,"think":False,"format":schema,
       "options":{"temperature":0,"num_ctx":2048,"num_predict":256},
       "messages":[{"role":"system","content":"Assign each goal to exactly one matching division. Order assignments so input data comes first, scholarly validation next, engineering then commercial, and independent verification last. Return only the five assignments. Never add goals or tools."},
       {"role":"user","content":json.dumps({"goals":GOALS,"divisions":sorted(ORDER)})}]}
    reply=read_json("/api/chat",request,timeout=100)
    if reply.get("done") is not True or reply.get("model")!=MODEL: raise ValueError("Incomplete local inference")
    raw=reply.get("message",{}).get("content")
    if not isinstance(raw,str) or len(raw)>4000: raise ValueError("Invalid model content")
    choice=json.loads(raw)
    receipt={"company":company,"parent":parent,"model":MODEL,"model_digest":matches[0]["digest"],
             "goals_sha256":digest(GOALS),"response":choice,"response_sha256":digest(choice),
             "eval_count":reply.get("eval_count"),"prompt_eval_count":reply.get("prompt_eval_count"),"paid_inference":False}
    roles=validate_receipt(receipt,company,parent)
    exclusive(path,receipt)
    return roles,receipt

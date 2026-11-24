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


def valid_digest(value):
    import re
    return isinstance(value,str) and bool(re.fullmatch(r"(?:sha256:)?"+MODEL_DIGEST+r"[0-9a-f]{52}",value))


SLOTS = tuple("step_"+str(i) for i in range(1,6))


class PlanRejected(ValueError):
    def __init__(self, code):
        self.code=code
        super().__init__(code)


def plan_schema():
    # Object properties give the grammar five independently constrained slots.
    # No reliance on unsupported array uniqueItems/prefixItems behavior.
    return {"type":"object","required":list(SLOTS),"additionalProperties":False,
            "properties":{slot:{"type":"object","required":["goal","division"],
              "additionalProperties":False,"properties":{
                "goal":{"type":"string","enum":list(GOALS)},
                "division":{"type":"string","enum":[role]}}}
              for slot,role in zip(SLOTS,ORDER)}}


def validate_choice(value):
    if not isinstance(value,dict) or set(value)!=set(SLOTS):
        raise PlanRejected("PLAN_SHAPE")
    roles=[]
    seen=set()
    for slot,expected in zip(SLOTS,ORDER):
        step=value[slot]
        if not isinstance(step,dict) or set(step)!={"goal","division"}:
            raise PlanRejected("ASSIGNMENT_SHAPE")
        goal,role=step["goal"],step["division"]
        if not isinstance(goal,str) or not isinstance(role,str) or ROLE_MAP.get(goal)!=role:
            raise PlanRejected("ASSIGNMENT_SCOPE")
        if goal in seen or role in roles:
            raise PlanRejected("DUPLICATE_ASSIGNMENT")
        if role!=expected:
            raise PlanRejected("DEPENDENCY_ORDER")
        seen.add(goal)
        roles.append(role)
    if seen!=set(GOALS) or roles!=ORDER:
        raise PlanRejected("INCOMPLETE_ASSIGNMENTS")
    return roles


def rejected_choice(directory, company, parent, choice, reason):
    # Only known goal IDs, division names and numeric slot positions leave the
    # model boundary. No raw response, arbitrary keys, prompts or provider text.
    positions=[]
    if isinstance(choice,dict):
        for i,slot in enumerate(SLOTS,1):
            step=choice.get(slot)
            if not isinstance(step,dict):
                positions.append({"position":i,"goal":None,"division":None})
                continue
            goal,role=step.get("goal"),step.get("division")
            positions.append({"position":i,
                "goal":goal if isinstance(goal,str) and goal in GOALS else None,
                "division":role if isinstance(role,str) and role in ORDER else None})
    exclusive(directory/"minister-model-rejection.json",{
        "schema":"plenum-model-rejection-v1","company":company,"parent":parent,
        "reason":reason,"expected_order":ORDER,"assignments":positions,
        "accepted":False,"paid_inference":False})


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
            or not valid_digest(receipt["model_digest"])
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
    if len(matches)!=1 or not valid_digest(matches[0].get("digest")):
        raise ValueError("Unexpected local Qwen model digest")
    request={"model":MODEL,"stream":False,"think":False,"format":plan_schema(),
       "options":{"temperature":0,"num_ctx":2048,"num_predict":256},
       "messages":[{"role":"system","content":"Fill exactly five numbered slots. The dependency order is fixed: step_1 intelligence, step_2 research, step_3 engineering, step_4 commercial, step_5 verification. Match each slot's division to the goal description; select one goal ID per slot. Use every goal ID exactly once. Do not repeat, omit, invent or reorder assignments. Each slot contains goal and division only. Return JSON only."},
       {"role":"user","content":json.dumps({"goals":GOALS,"required_order":ORDER})}]}
    reply=read_json("/api/chat",request,timeout=100)
    if not isinstance(reply,dict) or reply.get("done") is not True or reply.get("model")!=MODEL:
        rejected_choice(directory,company,parent,None,"INCOMPLETE_INFERENCE")
        raise PlanRejected("INCOMPLETE_INFERENCE")
    message=reply.get("message")
    raw=message.get("content") if isinstance(message,dict) else None
    if not isinstance(raw,str) or len(raw)>4000:
        rejected_choice(directory,company,parent,None,"MODEL_CONTENT")
        raise PlanRejected("MODEL_CONTENT")
    try:
        choice=json.loads(raw)
    except (ValueError,TypeError):
        rejected_choice(directory,company,parent,None,"MODEL_JSON")
        raise PlanRejected("MODEL_JSON") from None
    receipt={"company":company,"parent":parent,"model":MODEL,"model_digest":matches[0]["digest"],
             "goals_sha256":digest(GOALS),"response":choice,"response_sha256":digest(choice),
             "eval_count":reply.get("eval_count"),"prompt_eval_count":reply.get("prompt_eval_count"),"paid_inference":False}
    try:
        roles=validate_receipt(receipt,company,parent)
    except ValueError as exc:
        rejected_choice(directory,company,parent,choice,
                        exc.code if isinstance(exc,PlanRejected) else "RECEIPT_BINDING")
        raise
    exclusive(path,receipt)
    return roles,receipt

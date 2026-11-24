"""Typed owner-authorized public mission scopes; no URLs, code, secrets or paid actions."""
import json
import re
from hashlib import sha256
from checkpoint_store import encoded

TITLE = "[Plenum Paperclip] public evidence mission"
MAGIC = "PLENUM_PAPERCLIP_PUBLIC_EVIDENCE_V2"
LEGACY = {"kind":"coastal"}
MODELS = ("@cf/zai-org/glm-4.7-flash","@cf/google/gemma-4-26b-a4b-it","@cf/nvidia/nemotron-3-120b-a12b")
PROFILE_DIVISIONS = {"chief":"minister","operations":"commercial","research":"research",
    "coding":"engineering","simulation":"engineering","browser":"intelligence",
    "creative":"commercial","marketing":"commercial","support":"commercial",
    "verification":"verification","business_advisor":"verification"}


def validate_scope(value):
    if not isinstance(value,dict):raise ValueError("Exact typed scope required")
    if value==LEGACY:return dict(LEGACY)
    kind=value.get("kind")
    if kind=="station":
        if set(value)!={"kind","station_ids","paper_survey"}:raise ValueError("Exact station scope required")
        ids=value["station_ids"]
        topic=value["paper_survey"]
        if (not isinstance(ids,list) or not 1<=len(ids)<=3
                or any(not isinstance(x,str) or not re.fullmatch(r"[0-9]{7}",x) for x in ids)
                or len(set(ids))!=len(ids) or not isinstance(topic,str)):
            raise ValueError("Bounded station identifiers required")
        from plenum_ai.world_horizon import paper_survey_subject
        if not paper_survey_subject(topic):raise ValueError("Bounded scholarly topic required")
    elif kind=="bibliography_budget":
        if set(value)!={"kind","dois","budget"}:raise ValueError("Exact bibliography and budget scope required")
        ids=value["dois"]
        if (not isinstance(ids,list) or not 1<=len(ids)<=2
                or any(not isinstance(x,str) or not re.fullmatch(r"10\.[0-9]{4,9}/[a-z0-9][a-z0-9.()/_+-]{0,100}",x) for x in ids)
                or len(set(ids))!=len(ids)):raise ValueError("Bounded public DOI identifiers required")
        budget=value["budget"]
        limits={"neurons_used_today":10000,"neurons_reserved":10000,
                "input_tokens_upper_bound":1000000,"output_tokens_upper_bound":1000000}
        if (not isinstance(budget,dict) or set(budget)!={"model",*limits}
                or budget["model"] not in MODELS):raise ValueError("Exact offline budget scope required")
        for key,maximum in limits.items():
            n=budget[key]
            if type(n) is not int or not (1 if "tokens" in key else 0)<=n<=maximum:
                raise ValueError("Budget parameter outside bounds")
    elif kind=="public_dataset":
        from dataset_mission import validate
        validate(value)
    else:raise ValueError("Unsupported mission kind")
    return json.loads(encoded(value))


def digest(scope):
    return sha256(encoded(validate_scope(scope))).hexdigest()


def parse_body(body):
    if not isinstance(body,str) or len(body)>1800:raise ValueError("Bounded public envelope required")
    prefix=MAGIC+"\n"
    if not body.startswith(prefix):raise ValueError("Unknown mission envelope")
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError("Duplicate scope field")
            result[key]=value
        return result
    value=validate_scope(json.loads(body[len(prefix):],object_pairs_hook=pairs))
    if value==LEGACY:raise ValueError("Legacy mission requires original envelope")
    return value


def profile_routes(scope):
    from plenum_ai.role_skill_router import route
    from pathlib import Path
    roster=json.loads((Path(__file__).resolve().parents[2]/"integrations/hermes/roster.json").read_text())
    if set(PROFILE_DIVISIONS)!={r["name"] for r in roster["roles"]}:
        raise ValueError("Original profile mapping drift")
    # Profile readiness is scope/skill routing only, not eleven worker runs.
    kind=validate_scope(scope)["kind"]
    objective=("Review public bibliography and owner-supplied synthetic numerical data" if kind=="public_dataset" else "Review public scholarly metadata and offline AI budget evidence" if kind=="bibliography_budget"
               else "Review public station metadata and scholarly evidence")
    return {name:{"division":division,"routing":route(name,objective)}
            for name,division in PROFILE_DIVISIONS.items()}

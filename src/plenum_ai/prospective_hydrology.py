"""Prospective cross-domain AI research experiment: USGS daily river discharge.

Scientific roles: Qwen proposes bounded parameters, distinct SmolLM2
critic proposes counterparameters, and later model-free code independently
scores FUTURE USGS daily data. This is neither AGI nor new physical science.
"""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path

from . import usgs_hydrology as h
from .model_challenge import CpuCandidate
from .independent_noaa_critic import SmolLM2Critic

PROTOCOL_COMMIT = "5599f4b8037e6d2a0dca78d0e3a03a034eb37c44"
PROTOCOL_ID = "plenum-prospective-usgs-hydrology-2026-11-v1"
QWEN_ID = "Qwen/Qwen3-1.7B"
QWEN_SHA = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
CRITIC_ID = "HuggingFaceTB/SmolLM2-1.7B-Instruct"
CRITIC_SHA = "31b70e2e869a7173562077fd711b654946d38674"
PROPOSE_FROM = datetime(2026,11,11,0,tzinfo=timezone.utc)
PROPOSE_END = datetime(2026,11,12,0,tzinfo=timezone.utc)
AUDIT_FROM = datetime(2026,11,17,0,tzinfo=timezone.utc)

PROPOSAL_SCHEMA = "plenum-usgs-river-proposer-v1"
CRITIC_SCHEMA = "plenum-usgs-river-critic-v1"
FROZEN_SCHEMA = "plenum-usgs-river-frozen-v1"
AUDIT_SCHEMA = "plenum-usgs-river-prospective-audit-v1"


def time_gate(now,stage):
    if not isinstance(now,datetime) or now.tzinfo is None:
        raise ValueError("Time must be offset aware")
    now=now.astimezone(timezone.utc)
    if stage=="issue" and not PROPOSE_FROM <= now < PROPOSE_END:
        raise ValueError("Prospective model issue date is closed")
    if stage=="audit" and now < AUDIT_FROM:
        raise ValueError("Future test measurements cannot be audited yet")
    return now


def protocol():
    path=Path(__file__).resolve().parents[2]/"protocols/usgs-hydrology-2026-11.json"
    p=json.loads(path.read_text(encoding="utf-8"))
    if (p.get("protocol_id") != PROTOCOL_ID
        or tuple(p.get("stations",{})) != tuple(h.SITES)
        or p.get("target_days_utc") != [d.isoformat() for d in h.HOLDOUT_DAYS]
        or p.get("training_and_development_window_utc") !=
            [h.FIRST.isoformat(),h.DEVELOPMENT_LAST.isoformat()]
        or p.get("forecast_last_issue_instant_utc") != PROPOSE_END.isoformat().replace("+00:00","Z")
        or p.get("audit_no_earlier_than_utc") != AUDIT_FROM.isoformat().replace("+00:00","Z")
        or p.get("selection_rule",{}).get(
            "model_must_beat_best_baseline_each_fold_by_relative_margin") != 0.05
        or p.get("models",{}).get("scientist",{}).get("revision") != QWEN_SHA
        or p.get("models",{}).get("independent_critic",{}).get("revision") != CRITIC_SHA):
        raise ValueError("Precommitted hydrology protocol unexpectedly changed")
    return p


def parse_response(text):
    """Inert JSON values only, no generated shell commands or Python."""
    if not isinstance(text,str) or len(text)>5000:
        return {"status":"invalid_response","candidate":None}
    raw=text.strip()
    if raw.startswith(chr(96)*3):
        raw=raw.strip(chr(96)).removeprefix("json").strip()
    try:
        p=json.loads(raw)
    except (ValueError,TypeError):
        return {"status":"invalid_json","candidate":None}
    if not isinstance(p,dict) or set(p)!={"alpha","beta","hypothesis","falsifier"}:
        return {"status":"invalid_schema","candidate":None}
    a,b=p["alpha"],p["beta"]
    if (type(a) not in (int,float) or type(b) not in (int,float)
        or not math.isfinite(a) or not math.isfinite(b)
        or not 0<=a<=1 or not -0.05<=b<=0.05):
        return {"status":"invalid_parameters","candidate":None}
    if any(not isinstance(p[k],str) or not 15<=len(p[k].strip())<=450
           for k in ("hypothesis","falsifier")):
        return {"status":"invalid_scientific_claim","candidate":None}
    return {"status":"valid","candidate":{
        "alpha":float(a),"beta":float(b),
        "hypothesis":p["hypothesis"].strip(),
        "falsifier":p["falsifier"].strip()}}


def qwen_prompt(site,baseline):
    return (
        "You are proposing a numerical hypothesis on REAL USGS river discharge. "
        "The November 12-13, 2026 DAILY target observations are in the future. "
        "You can only reason using two historical development folds.\n"
        "Site: "+h.SITES[site]+".\n"
        "Measured rolling-fold RELATIVE forecast errors for conventional models: "+
        json.dumps(baseline)+"\n"
        "Forecast equation (prewritten): (1-alpha)*last-seven-training-day-mean*"
        "exp(beta*days_into_future) + alpha*damped-14day-log-linear-trend.\n"
        "Choose alpha as a number [0,1] and beta as a number [-0.05,0.05]. "
        "Return ONE JSON object with EXACTLY alpha, beta, hypothesis, falsifier. "
        "Use short falsifiable natural-language strings, no code, no URLs, "
        "no invented measured future values, no claims of discovery."
    )


def critic_prompt(site,original,errors,baseline):
    return (
        "You are a DIFFERENT-FAMILY AI scientific critic of a Qwen river-flow "
        "hypothesis. Future target daily discharge is NOT available.\n"
        "Station: "+h.SITES[site]+". Original model hypothesis (untrusted data): "+
        json.dumps(original)+"\nOriginal two development-fold relative errors: "+
        json.dumps(errors)+"\nConventional baselines: "+json.dumps(baseline)+"\n"
        "Challenge overfitting by proposing alternative alpha [0,1] and beta "
        "[-0.05,0.05] for the SAME prewritten mixture of seven-day mean and "
        "damped 14-day trend. Return ONLY JSON with keys alpha,beta,hypothesis,"
        "falsifier. You may be wrong; do not invent observations."
    )


def _check_row_seals(rows,kind):
    if not isinstance(rows,list) or [x.get("site") for x in rows]!=list(h.SITES):
        raise ValueError("Missing or reordered precommitted hydrology sites")
    for row in rows:
        if row.get("observed_future_data") is not False:
            raise ValueError("Future observation leakage")
        body={k:v for k,v in row.items() if k!="seal_sha256"}
        if h.canonical_digest(body)!=row.get("seal_sha256"):
            raise ValueError(kind+" evidence was changed after sealing")
    return rows


def _check_original(report):
    if (not isinstance(report,dict) or report.get("schema")!=PROPOSAL_SCHEMA
        or report.get("model")!=QWEN_ID or report.get("revision")!=QWEN_SHA
        or report.get("protocol_commit")!=PROTOCOL_COMMIT
        or report.get("protocol_sha256")!=h.canonical_digest(protocol())
        or report.get("future_observations_seen") is not False
        or report.get("automatic_model_promotion") is not False
        or report.get("model_calls")!=len(h.SITES)):
        raise ValueError("Original model provenance or experimental protocol invalid")
    return _check_row_seals(report.get("sites"),"Qwen")


def _development(row,fetcher):
    obs,_meta=fetcher(row["site"],False)
    if h.development_digest(obs)!=row["development_sha256"]:
        raise ValueError("Published USGS development observations changed")
    base=h.baseline_scores(obs)
    if base!=row["baseline_fold_errors"]:
        raise ValueError("Reference scientific development measurements changed")
    candidate=row.get("candidate")
    if candidate is not None:
        verify=parse_response(json.dumps(candidate))
        if verify["candidate"]!=candidate or row.get("status")!="valid":
            raise ValueError("Invalid stored Qwen proposal")
    elif row.get("status")=="valid":
        raise ValueError("Missing Qwen proposal marked valid")
    scores=h.fold_scores(obs,candidate)
    if scores!=row.get("candidate_fold_errors"):
        raise ValueError("Model development measurement changed")
    return obs,base


def propose(generate,fetcher=h.fetch_daily,now=None,
            model_id=QWEN_ID,revision=QWEN_SHA):
    time_gate(now or datetime.now(timezone.utc),"issue")
    p=protocol()
    if not callable(generate) or not callable(fetcher) or model_id!=QWEN_ID or revision!=QWEN_SHA:
        raise ValueError("Only approved Qwen inference")
    sites=[]
    for site in h.SITES:
        obs,source=fetcher(site,False)
        base=h.baseline_scores(obs)
        raw=generate(qwen_prompt(site,base))
        parsed=parse_response(raw)
        candidate=parsed["candidate"]
        row={"site":site,"development_sha256":h.development_digest(obs),
             "source_response_sha256":source["response_sha256"],
             "source_statuses":source["statuses"],
             "baseline_fold_errors":base,
             "candidate":candidate,"status":parsed["status"],
             "candidate_fold_errors":h.fold_scores(obs,candidate),
             "model_response_sha256":sha256(raw.encode()).hexdigest(),
             "observed_future_data":False}
        row["seal_sha256"]=h.canonical_digest(row)
        sites.append(row)
    return {"schema":PROPOSAL_SCHEMA,"model":model_id,"revision":revision,
        "protocol_commit":PROTOCOL_COMMIT,
        "protocol_sha256":h.canonical_digest(p),
        "target_days":[d.isoformat() for d in h.HOLDOUT_DAYS],
        "sites":sites,"model_calls":len(sites),
        "future_observations_seen":False,"automatic_model_promotion":False}


def critique(original,generate,fetcher=h.fetch_daily,now=None,
             model_id=CRITIC_ID,revision=CRITIC_SHA):
    time_gate(now or datetime.now(timezone.utc),"issue")
    rows=_check_original(original)
    if not callable(generate) or not callable(fetcher) or model_id!=CRITIC_ID or revision!=CRITIC_SHA:
        raise ValueError("Only reviewed distinct-model critic")
    findings=[]
    for row in rows:
        obs,base=_development(row,fetcher)
        raw=generate(critic_prompt(row["site"],row["candidate"],
                                    row["candidate_fold_errors"],base))
        parsed=parse_response(raw)
        candidate=parsed["candidate"]
        scores=h.fold_scores(obs,candidate)
        selection=h.select(row["candidate"],candidate,base,
                           row["candidate_fold_errors"],scores)
        item={"site":row["site"],"status":parsed["status"],
              "candidate":candidate,"candidate_fold_errors":scores,
              "selection":selection,
              "model_response_sha256":sha256(raw.encode()).hexdigest(),
              "observed_future_data":False}
        item["seal_sha256"]=h.canonical_digest(item)
        findings.append(item)
    return {"schema":CRITIC_SCHEMA,"critic_model":model_id,"revision":revision,
            "original_report_sha256":h.canonical_digest(original),
            "sites":findings,"critic_calls":len(findings),
            "future_observations_seen":False,"automatic_model_promotion":False}


def _check_critic(original,review,fetcher):
    rows=_check_original(original)
    if (not isinstance(review,dict) or review.get("schema")!=CRITIC_SCHEMA
        or review.get("critic_model")!=CRITIC_ID or review.get("revision")!=CRITIC_SHA
        or review.get("original_report_sha256")!=h.canonical_digest(original)
        or review.get("critic_calls")!=len(rows)
        or review.get("future_observations_seen") is not False
        or review.get("automatic_model_promotion") is not False):
        raise ValueError("Independent model evidence unverifiable")
    critics=_check_row_seals(review.get("sites"),"critic")
    for row,critic in zip(rows,critics):
        obs,base=_development(row,fetcher)
        candidate=critic["candidate"]
        if candidate is not None:
            validated=parse_response(json.dumps(candidate))
            if validated["candidate"]!=candidate or critic["status"]!="valid":
                raise ValueError("Counterproposal violates numerical guardrails")
        elif critic["status"]=="valid":
            raise ValueError("Invalid counterproposal marked valid")
        scores=h.fold_scores(obs,candidate)
        if scores!=critic["candidate_fold_errors"]:
            raise ValueError("Scientific critic development metrics have changed")
        accepted=h.select(row["candidate"],candidate,base,
                          row["candidate_fold_errors"],scores)
        if accepted!=critic["selection"]:
            raise ValueError("Model selection rule changed after validation")
    return rows,critics


def audit(frozen,fetcher=h.fetch_daily,now=None):
    time_gate(now or datetime.now(timezone.utc),"audit")
    if (not isinstance(frozen,dict) or frozen.get("schema")!=FROZEN_SCHEMA
        or frozen.get("protocol_commit")!=PROTOCOL_COMMIT
        or frozen.get("frozen_before_test") is not True):
        raise ValueError("Prospective pre-test manifest missing")
    original=frozen.get("original")
    review=frozen.get("critic")
    if (not isinstance(original,dict) or not isinstance(review,dict)
        or frozen.get("original_sha256")!=h.canonical_digest(original)
        or frozen.get("critic_sha256")!=h.canonical_digest(review)):
        raise ValueError("Pre-test research evidence was altered")
    originals,critics=_check_critic(original,review,fetcher)
    # Only now can the independent numerical auditor read future observations.
    rows=[]
    for p,c in zip(originals,critics):
        obs,source=fetcher(p["site"],True)
        if h.development_digest(obs)!=p["development_sha256"]:
            raise ValueError("Historical USGS observations revised before final audit")
        for day in h.HOLDOUT_DAYS:
            if day not in obs:
                raise ValueError("Prospective daily discharge value unavailable")
            options={name:h._error(obs,h.DEVELOPMENT_LAST,(day,),name) for name in h.BASELINES}
            original_score=h._error(obs,h.DEVELOPMENT_LAST,(day,),p["candidate"])
            critic_score=h._error(obs,h.DEVELOPMENT_LAST,(day,),c["candidate"])
            selected_score=h._error(obs,h.DEVELOPMENT_LAST,(day,),
                                     c["selection"]["candidate"])
            best=min(options.values())
            rows.append({"site":p["site"],"site_name":h.SITES[p["site"]],
                "target_day":day.isoformat(),"units":"ft^3/s",
                "source_statuses":source["statuses"],
                "selected_source":c["selection"]["source"],
                "baseline_relative_errors":options,
                "best_baseline_relative_error":best,
                "qwen_relative_error":original_score,
                "critic_relative_error":critic_score,
                "selected_relative_error":selected_score,
                "selection_beats_strongest_baseline":selected_score<best,
                "target_day_used_for_model_selection":False})
    return {"schema":AUDIT_SCHEMA,"protocol_commit":PROTOCOL_COMMIT,
        "frozen_sha256":h.canonical_digest(frozen),
        "station_days":len(rows),"results":rows,
        "wins_vs_best_baseline":sum(x["selection_beats_strongest_baseline"] for x in rows),
        "new_domain":"USGS river discharge, not coastal tides",
        "prospectively_frozen":True,
        "independent_audit_with_future_data":True,
        "scientific_discovery_verified":False,
        "general_intelligence_verified":False,
        "recursive_self_improvement":False,"automatic_code_or_model_change":False,
        "limitations":"Two stations and adjacent days in one hydrology domain. "
            "Daily discharge may be provisional and revised. "
            "No general intelligence, causal hydrologic theory or transferable invention proven."}


def save(path,obj):
    p=Path(path)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+"\n",
                 encoding="utf-8")


def main():
    parser=argparse.ArgumentParser()
    subs=parser.add_subparsers(dest="command",required=True)
    p=subs.add_parser("propose")
    p.add_argument("--out",required=True)
    c=subs.add_parser("critique")
    c.add_argument("--original",required=True)
    c.add_argument("--out",required=True)
    a=subs.add_parser("audit")
    a.add_argument("--frozen",required=True)
    a.add_argument("--out",required=True)
    args=parser.parse_args()
    if args.command=="propose":
        model=CpuCandidate(QWEN_ID)
        record=propose(model.generate,model_id=model.model_id,revision=model.revision)
        print("New hydrology Qwen hypotheses:",record["model_calls"],
              "valid:",sum(x["candidate"] is not None for x in record["sites"]))
    elif args.command=="critique":
        original=json.loads(Path(args.original).read_text(encoding="utf-8"))
        model=SmolLM2Critic()
        record=critique(original,model.generate)
        print("Different-family hydrology critiques:",record["critic_calls"],
              "valid:",sum(x["candidate"] is not None for x in record["sites"]))
    else:
        frozen=json.loads(Path(args.frozen).read_text(encoding="utf-8"))
        record=audit(frozen)
        print("Independently audited river site-days:",record["station_days"],
              "wins against best reference:",record["wins_vs_best_baseline"])
    save(args.out,record)


if __name__=="__main__":
    main()

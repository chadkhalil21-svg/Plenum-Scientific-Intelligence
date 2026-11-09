"""Prospective NOAA hypothesis test with independent model criticism and hard data gates.

Model proposals must be frozen before Nov 12, 2026. New observations for
Nov 12-13 are fetched only by an independent later auditor. No arbitrary
generated code, private input or production model change.
"""
import argparse
import json
import math
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
from .noaa_empirical import API, STATIONS, parse_observations
from .autonomous_hypothesis import _matrix
from .noaa_revision_agent import parse_candidate
from .model_challenge import CpuCandidate
from .independent_noaa_critic import SmolLM2Critic

# Pre-issuance source clarification, 2026-11-09: NOAA verified hourly_height
# is published after monthly review, not reliably available for November 2026
# target days at the precommitted November 16 audit. Reuse NOAA's ORIGINAL
# water_level observation product at six-minute intervals, selecting ONLY
# the recorded top-of-hour UTC measurements. No interpolation, synthetic
# observations, NOAA tide predictions, post-hoc forecast-model changes, or
# fallback between two measurement products. Preliminary source may be revised.
NOAA_SOURCE_PRODUCT = "water_level"
NOAA_SOURCE_SAMPLING = "exact top-of-hour UTC (minute=00) from observed six-minute product"
NOAA_SOURCE_AMENDMENT = "noaa-prospective-2026-11-source-clarification-2026-11-09"
NOAA_MAX_SOURCE_BYTES = 1_200_000  # 21 days of real 6-minute observations; finite limit.

PROTOCOL_ID = "plenum-prospective-noaa-2026-11-v1"
PROTOCOL_COMMIT = "45ac814869b9e47450c00ec55e83b29f02d3ca71"
QWEN = "Qwen/Qwen3-1.7B"
QWEN_SHA = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
CRITIC = "HuggingFaceTB/SmolLM2-1.7B-Instruct"
CRITIC_SHA = "31b70e2e869a7173562077fd711b654946d38674"
STATION_IDS = ("8443970", "8723214")
START = datetime(2026,10,24,tzinfo=timezone.utc)
DEV_END = datetime(2026,11,9,tzinfo=timezone.utc)
ISSUE_FROM = datetime(2026,11,10,tzinfo=timezone.utc)
TEST_START = datetime(2026,11,12,tzinfo=timezone.utc)
AUDIT_FROM = datetime(2026,11,15,tzinfo=timezone.utc)
TEST_DAYS = ("2026-11-12","2026-11-13")
FOLDS = ((11,11,13),(13,13,16))
BASELINES = ("phase_repeat_of_last_training_UTC_day","m2_s2_harmonics",
             "four_constituent_harmonics")
MIN_GAIN = 0.005


def digest(x):
    return sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,
        separators=(",",":"),allow_nan=False).encode()).hexdigest()


def now_utc():
    return datetime.now(timezone.utc)


def gate(now, stage):
    if not isinstance(now,datetime) or now.tzinfo is None:
        raise ValueError("Time must be timezone-aware")
    t=now.astimezone(timezone.utc)
    if stage=="propose" and not ISSUE_FROM<=t<TEST_START:
        raise ValueError("Proposals must be made before future test observations")
    if stage=="audit" and t<AUDIT_FROM:
        raise ValueError("Cannot audit before prospective observations are available")
    return t


def protocol():
    file=Path(__file__).resolve().parents[2]/"protocols/noaa-prospective-2026-11.json"
    p=json.loads(file.read_text("utf-8"))
    if (p.get("protocol_id")!=PROTOCOL_ID or tuple(p.get("stations",{}))!=STATION_IDS
            or tuple(p.get("test_days_utc",()))!=TEST_DAYS
            or p.get("development_start_utc")!="2026-10-24T00:00:00Z"
            or p.get("development_end_exclusive_utc")!="2026-11-09T00:00:00Z"
            or p.get("forecast_issue_deadline_utc")!="2026-11-12T00:00:00Z"
            or p.get("audit_not_before_utc")!="2026-11-15T00:00:00Z"
            or p.get("agents",{}).get("proposer",{}).get("immutable_revision")!=QWEN_SHA
            or p.get("agents",{}).get("separate_model_critic",{}).get("immutable_revision")!=CRITIC_SHA
            or p.get("selection_rule",{}).get(
              "candidate_must_beat_best_baseline_on_each_development_fold_by_at_least_m")!=MIN_GAIN):
        raise ValueError("Prospective scientific protocol has changed")
    return p


def usable_six_minute_observation(row):
    """Apply NOAA's original p/v quality flags before exact-hour sampling.

    NOAA water_level f fields are O,F,R,L for preliminary and I,F,R,T for
    verified readings. Reject flagged flat/rate/limit anomalies in either
    category and inferred verified heights; preliminary O is a sample count,
    not itself an invalid observation. Unparseable flags are NOT assumed good.
    """
    if not isinstance(row,dict) or row.get("q") not in ("p","v"):
        return False
    flags=row.get("f")
    if not isinstance(flags,str):
        return False
    fields=flags.split(",")
    if len(fields)!=4 or not all(x.isdigit() for x in fields):
        return False
    if any(x!="0" for x in fields[1:]):
        return False
    return row["q"]!="v" or fields[0]=="0"


def fetch_public(station, reveal=False, opener=urlopen):
    if station not in STATION_IDS or station not in STATIONS:
        raise ValueError("Unapproved station")
    end="20261113" if reveal else "20261108"
    query=urlencode({"begin_date":"20261024","end_date":end,"station":station,
        "product":NOAA_SOURCE_PRODUCT,"datum":"MLLW","time_zone":"gmt",
        "units":"metric","format":"json",
        "application":"plenum_prospective_scientific_study"})
    request=Request(API+"?"+query,headers={"User-Agent":"PlenumScientificIntelligence/1.0"})
    with opener(request,timeout=25) as response:
        raw=response.read(NOAA_MAX_SOURCE_BYTES+1)
    if len(raw)>NOAA_MAX_SOURCE_BYTES:
        raise ValueError("NOAA six-minute source exceeded fixed 21-day download limit")
    data=json.loads(raw)
    if not isinstance(data,dict) or data.get("error") or not isinstance(data.get("data"),list):
        raise ValueError("Observed NOAA six-minute water levels unavailable; no forecasts fabricated")
    # NOAA water_level is measured, not the tide-prediction product. Its q flag
    # identifies preliminary/verified observation status. Accept only p/v;
    # parse_observations takes exact hh:00 UTC readings and rejects duplicates.
    # This samples observed top-of-hour heights, NOT the verified hourly_height
    # averaged product. Both frozen development and later targets use this
    # single predeclared extraction and the original observed-data units.
    accepted=[row for row in data["data"] if usable_six_minute_observation(row)]
    hourly=parse_observations(accepted)
    if not hourly:
        raise ValueError("No flagged real NOAA top-of-hour observations in six-minute source")
    return hourly,sha256(raw).hexdigest()


def dev_series(obs):
    s=[(t.isoformat(),float(v)) for t,v in sorted(obs.items()) if START<=t<DEV_END]
    if len(s)<350:
        raise ValueError("Missing development hourly observations")
    return s


def fold_times(obs,n_train,first,last):
    end=START+timedelta(days=n_train)
    lo=START+timedelta(days=first)
    hi=START+timedelta(days=last)
    fit=sorted(t for t in obs if START<=t<end)
    target=sorted(t for t in obs if lo<=t<hi)
    if len(fit)<n_train*22 or len(target)<(last-first)*20 or set(fit)&set(target):
        raise ValueError("Independent rolling-fold coverage insufficient")
    return fit,target


def forecast(obs,fit,targets,method):
    if not fit or not targets or set(fit)&set(targets):
        raise ValueError("Forecast uses overlapping train/test observations")
    if method==BASELINES[0]:
        last=max(fit).date()
        h={t.hour:float(obs[t]) for t in fit if t.date()==last}
        if len(h)!=24:
            raise ValueError("Last training day lacks a full 24h hourly pattern")
        return [h[t.hour] for t in targets]
    if method in BASELINES[1:]:
        name="m2_s2" if method==BASELINES[1] else "four_constituents"
        X=_matrix(fit,name)
        y=np.array([obs[t] for t in fit],dtype=float)
        weights,_res,rank,_sv=np.linalg.lstsq(X,y,rcond=None)
        if rank<X.shape[1] or not np.all(np.isfinite(weights)):
            raise ValueError("Harmonic baseline cannot be fitted")
        prediction=_matrix(targets,name)@weights
        if not np.all(np.isfinite(prediction)):
            raise ValueError("Nonfinite prediction")
        return [float(x) for x in prediction]
    if not isinstance(method,dict) or not 0<=method["alpha"]<=1 or not 0.6<=method["gain"]<=1.4:
        raise ValueError("Candidate violates the frozen mathematical form")
    p=forecast(obs,fit,targets,BASELINES[0])
    h=forecast(obs,fit,targets,BASELINES[2])
    mu=sum(obs[t] for t in fit)/len(fit)
    a,g=method["alpha"],method["gain"]
    return [(1-a)*v+a*(mu+g*(u-mu)) for v,u in zip(p,h)]


def score(obs,fit,targets,method):
    if method is None:
        return None
    y=forecast(obs,fit,targets,method)
    return round(sum(abs(float(obs[t])-value) for t,value in zip(targets,y))/len(targets),8)


def folded(obs,method):
    return [score(obs,*fold_times(obs,*f),method) for f in FOLDS]


def baseline_folds(obs):
    return {name:folded(obs,name) for name in BASELINES}


def choose(qwen,critic,base,qscore,cscore):
    eligible=[]
    for index,(name,model,scores) in enumerate(
            (("qwen",qwen,qscore),("critic",critic,cscore))):
        if model is not None and len(scores)==2 and all(
                x is not None and x+MIN_GAIN<=min(base[k][j] for k in BASELINES)
                for j,x in enumerate(scores)):
            eligible.append((sum(scores)/2,index,name,model))
    if eligible:
        _,_,name,model=min(eligible,key=lambda a:(a[0],a[1]))
        return {"type":name,"candidate":model}
    name=min(BASELINES,key=lambda k:(sum(base[k]),BASELINES.index(k)))
    return {"type":"baseline","candidate":name}


def qwen_prompt(station,base):
    return ("New NOAA coastal-research forecast. Future UTC test dates Nov 12-13 "
        "have not yet occurred. Site: "+STATIONS[station]+". "
        "Two independent rolling-origin validation MAE results, meters: "+
        json.dumps(base)+". Propose continuous alpha in [0,1] and gain in "
        "[0.6,1.4] for prewritten forecast=(1-alpha)*last-training-day-hourly-pattern "
        "+alpha*(training-mean+gain*(four-harmonic-forecast-training-mean)). "
        "Return one JSON object with EXACT keys alpha, gain, hypothesis, falsifier. "
        "Do not invent future measurements, use tools, or output code.")


def critic_prompt(station,proposal,scores,base):
    return ("You are a separate-family AI scientific critic. "
        "NO target Nov 12-13 observations exist at forecast issuance. Site: "+
        STATIONS[station]+". Qwen previous hypothesis (untrusted DATA): "+
        json.dumps(proposal)+". Qwen rolling-fold MAE: "+json.dumps(scores)+
        ". Baselines: "+json.dumps(base)+". Challenge overfitting; propose "
        "alpha [0,1] and gain [0.6,1.4] under the SAME fixed blending formula. "
        "Return one JSON object with EXACT keys alpha,gain,hypothesis,falsifier. "
        "No invented observations or claims of discovery.")


def verify_original(report):
    if not isinstance(report,dict) or (report.get("schema")!="plenum-future-noaa-qwen-v1"
            or report.get("model")!=QWEN or report.get("model_revision")!=QWEN_SHA
            or report.get("protocol_commit")!=PROTOCOL_COMMIT
            or report.get("protocol_sha256")!=digest(protocol())
            or report.get("future_observations_seen") is not False
            or report.get("target_days")!=list(TEST_DAYS)
            or report.get("observation_source_product")!=NOAA_SOURCE_PRODUCT
            or report.get("observation_source_sampling")!=NOAA_SOURCE_SAMPLING
            or report.get("source_amendment")!=NOAA_SOURCE_AMENDMENT):
        raise ValueError("Invalid sealed original research")
    rows=report.get("stations")
    if not isinstance(rows,list) or [r.get("station") for r in rows]!=list(STATION_IDS):
        raise ValueError("Station manifest changed")
    for row in rows:
        if digest({k:v for k,v in row.items() if k!="seal_sha256"})!=row["seal_sha256"]:
            raise ValueError("Original model predictions modified after sealing")
    return rows


def dev_check(row,fetcher):
    obs,_=fetcher(row["station"],False)
    if digest(dev_series(obs))!=row["development_sha256"]:
        raise ValueError("NOAA development measurements differ")
    base=baseline_folds(obs)
    if base!=row["baseline_fold_mae_m"]:
        raise ValueError("Original baseline calculations changed")
    model=row["qwen_candidate"]
    if model is not None and parse_candidate(json.dumps(model))["candidate"]!=model:
        raise ValueError("Unapproved Qwen parameters")
    if folded(obs,model)!=row["qwen_fold_mae_m"]:
        raise ValueError("Original proposal's development metrics changed")
    return obs,base


def propose(generate,fetcher=fetch_public,now=None,model=QWEN,revision=QWEN_SHA):
    gate(now or now_utc(),"propose")
    p=protocol()
    if not callable(generate) or model!=QWEN or revision!=QWEN_SHA:
        raise ValueError("The reviewed Qwen model is required")
    rows=[]
    for station in STATION_IDS:
        obs,source=fetcher(station,False)
        base=baseline_folds(obs)
        response=generate(qwen_prompt(station,base))
        parsed=parse_candidate(response)
        candidate=parsed["candidate"]
        item={"station":station,"development_sha256":digest(dev_series(obs)),
              "source_sha256":source,"baseline_fold_mae_m":base,
              "qwen_candidate":candidate,"qwen_status":parsed["status"],
              "qwen_fold_mae_m":folded(obs,candidate),
              "model_output_sha256":sha256(response.encode()).hexdigest(),
              "future_observations_seen":False}
        item["seal_sha256"]=digest(item)
        rows.append(item)
    return {"schema":"plenum-future-noaa-qwen-v1","model":model,
            "model_revision":revision,"protocol_commit":PROTOCOL_COMMIT,
            "protocol_sha256":digest(p),"target_days":list(TEST_DAYS),
            "observation_source_product":NOAA_SOURCE_PRODUCT,
            "observation_source_sampling":NOAA_SOURCE_SAMPLING,
            "source_amendment":NOAA_SOURCE_AMENDMENT,
            "stations":rows,"model_calls":len(rows),
            "future_observations_seen":False,"auto_model_promotion":False}


def critique(report,generate,fetcher=fetch_public,now=None,
             model=CRITIC,revision=CRITIC_SHA):
    gate(now or now_utc(),"propose")
    rows=verify_original(report)
    if not callable(generate) or model!=CRITIC or revision!=CRITIC_SHA:
        raise ValueError("The independent reviewed critic is required")
    entries=[]
    for row in rows:
        obs,base=dev_check(row,fetcher)
        response=generate(critic_prompt(row["station"],row["qwen_candidate"],
                                        row["qwen_fold_mae_m"],base))
        parsed=parse_candidate(response)
        alternate=parsed["candidate"]
        scores=folded(obs,alternate)
        item={"station":row["station"],"critic_candidate":alternate,
              "critic_status":parsed["status"],"critic_fold_mae_m":scores,
              "selected":choose(row["qwen_candidate"],alternate,base,
                                row["qwen_fold_mae_m"],scores),
              "response_sha256":sha256(response.encode()).hexdigest(),
              "future_observations_seen":False}
        item["seal_sha256"]=digest(item)
        entries.append(item)
    return {"schema":"plenum-future-noaa-critic-v1",
            "original_sha256":digest(report),"critic_model":model,
            "critic_revision":revision,"stations":entries,
            "observation_source_product":NOAA_SOURCE_PRODUCT,
            "observation_source_sampling":NOAA_SOURCE_SAMPLING,
            "source_amendment":NOAA_SOURCE_AMENDMENT,
            "model_calls":len(entries),"future_observations_seen":False,
            "auto_model_promotion":False}


def verify_critic(report,criticism,fetcher):
    rows=verify_original(report)
    if not isinstance(criticism,dict) or (
            criticism.get("schema")!="plenum-future-noaa-critic-v1"
            or criticism.get("critic_model")!=CRITIC
            or criticism.get("critic_revision")!=CRITIC_SHA
            or criticism.get("original_sha256")!=digest(report)
            or criticism.get("model_calls")!=len(STATION_IDS)
            or criticism.get("future_observations_seen") is not False
            or criticism.get("observation_source_product")!=NOAA_SOURCE_PRODUCT
            or criticism.get("observation_source_sampling")!=NOAA_SOURCE_SAMPLING
            or criticism.get("source_amendment")!=NOAA_SOURCE_AMENDMENT):
        raise ValueError("Unverified independent model criticism")
    critics=criticism.get("stations")
    if not isinstance(critics,list) or [r.get("station") for r in critics]!=list(STATION_IDS):
        raise ValueError("Critic station list altered")
    for row,rev in zip(rows,critics):
        if rev.get("future_observations_seen") is not False or digest(
                {k:v for k,v in rev.items() if k!="seal_sha256"})!=rev["seal_sha256"]:
            raise ValueError("Critic record was altered or read future observations")
        obs,base=dev_check(row,fetcher)
        alt=rev["critic_candidate"]
        if alt is not None and parse_candidate(json.dumps(alt))["candidate"]!=alt:
            raise ValueError("Unapproved independent critic hypothesis")
        scores=folded(obs,alt)
        if scores!=rev["critic_fold_mae_m"]:
            raise ValueError("Reviewer development metrics changed")
        expected=choose(row["qwen_candidate"],alt,base,row["qwen_fold_mae_m"],scores)
        if rev["selected"]!=expected:
            raise ValueError("Research selection rule was altered")
    return rows,critics


def audit(frozen,fetcher=fetch_public,now=None):
    gate(now or now_utc(),"audit")
    if not isinstance(frozen,dict) or frozen.get("schema")!="plenum-future-noaa-frozen-v1" \
       or frozen.get("frozen_before_future_observations") is not True \
       or frozen.get("protocol_commit")!=PROTOCOL_COMMIT:
        raise ValueError("No certified pre-test research commit")
    original=frozen["original"]
    criticism=frozen["critic"]
    if frozen["original_sha256"]!=digest(original) or frozen["critic_sha256"]!=digest(criticism):
        raise ValueError("Research archive digest changed")
    rows,reviews=verify_critic(original,criticism,fetcher)
    # The only point where new future observations may be requested.
    results=[]
    for row,review in zip(rows,reviews):
        obs,_source=fetcher(row["station"],True)
        if digest(dev_series(obs))!=row["development_sha256"]:
            raise ValueError("Training observations changed before independent audit")
        fit=sorted(t for t in obs if START<=t<DEV_END)
        if len(fit)<350:
            raise ValueError("Final full training coverage insufficient")
        for day in TEST_DAYS:
            target=datetime.strptime(day,"%Y-%m-%d").replace(tzinfo=timezone.utc)
            times=sorted(t for t in obs if target<=t<target+timedelta(days=1))
            if len(times)<20:
                raise ValueError("Future NOAA hourly observations missing")
            baselines={name:score(obs,fit,times,name) for name in BASELINES}
            q=score(obs,fit,times,row["qwen_candidate"])
            c=score(obs,fit,times,review["critic_candidate"])
            selected=score(obs,fit,times,review["selected"]["candidate"])
            best=min(baselines.values())
            results.append({"station":row["station"],"site":STATIONS[row["station"]],
                "target_day_utc":day,"hours":len(times),
                "selected_method":review["selected"]["type"],
                "qwen_mae_m":q,"critic_mae_m":c,"policy_mae_m":selected,
                "baselines_mae_m":baselines,"best_baseline_mae_m":best,
                "policy_beats_best_baseline":selected<best,
                "critic_beats_qwen":q is not None and c is not None and c<q,
                "target_data_used_for_selection":False})
    return {"schema":"plenum-future-noaa-audit-v1","protocol_commit":PROTOCOL_COMMIT,
            "frozen_sha256":digest(frozen),"results":results,
            "station_days":len(results),
            "wins_vs_best_baseline":sum(x["policy_beats_best_baseline"] for x in results),
            "prospective_test":True,"heldout_evaluated_only_in_later_auditor":True,
            "general_intelligence_demonstrated":False,
            "scientific_discovery_verified":False,"recursive_self_improvement":False,
            "model_or_code_deployed":False,
            "limitations":"Two locations, two correlated future days, a fixed forecast family. "
                          "General intelligence and cross-discipline invention remain unverified."}


def save(path,data):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False,
                               allow_nan=False)+"\n",encoding="utf-8")


def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="command",required=True)
    x=sub.add_parser("propose")
    x.add_argument("--out",required=True)
    x=sub.add_parser("critique")
    x.add_argument("--original",required=True)
    x.add_argument("--out",required=True)
    x=sub.add_parser("audit")
    x.add_argument("--frozen",required=True)
    x.add_argument("--out",required=True)
    a=p.parse_args()
    if a.command=="propose":
        model=CpuCandidate(QWEN)
        result=propose(model.generate,model=model.model_id,revision=model.revision)
        print("Qwen research proposals:",result["model_calls"],"valid",
              sum(x["qwen_candidate"] is not None for x in result["stations"]))
    elif a.command=="critique":
        report=json.loads(Path(a.original).read_text("utf-8"))
        model=SmolLM2Critic()
        result=critique(report,model.generate)
        print("Independent model critiques:",result["model_calls"],"valid",
              sum(x["critic_candidate"] is not None for x in result["stations"]))
    else:
        frozen=json.loads(Path(a.frozen).read_text("utf-8"))
        result=audit(frozen)
        print("Prospective NOAA audit:",result["station_days"],
              "policy wins against best baseline:",result["wins_vs_best_baseline"])
    save(a.out,result)


if __name__=="__main__":
    main()

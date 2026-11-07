"""USGS modern Water Data API: bounded daily stream-discharge study.

This module provides *scientific instruments*, not an AGI claim.
Uses the current OGC Water Data API rather than deprecated NWIS WaterServices.
Input dates, sites, parameter and response count are allowlisted.
"""
from datetime import date, timedelta
from hashlib import sha256
import json
import math
from statistics import mean
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "https://api.waterdata.usgs.gov/ogcapi/v1/collections/daily/items"
SITES = {
    "01646500": "Potomac River near Washington DC, Little Falls",
    "01491000": "Choptank River near Greensboro MD",
}
PARAMETER = "00060"  # discharge, cubic feet per second
STATISTIC = "00003"  # daily mean
FIRST = date(2026, 10, 1)
DEVELOPMENT_LAST = date(2026, 11, 4)
HOLDOUT_LAST = date(2026, 11, 13)
HOLDOUT_DAYS = (date(2026, 11, 12), date(2026, 11, 13))
FOLDS = ((date(2026, 10, 24), (date(2026, 11, 1),date(2026, 11, 2))),
         (date(2026, 10, 26), (date(2026, 11, 3),date(2026, 11, 4))))
BASELINES = ("last_day", "last_week_mean", "damped_log_trend")
MAX_PAYLOAD = 2_000_000


def canonical_digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                    ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def query_url(site, include_holdout=False):
    if site not in SITES:
        raise ValueError("Monitoring station not approved")
    last = HOLDOUT_LAST if include_holdout else DEVELOPMENT_LAST
    params = {
        "f":"json", "monitoring_location_id":"USGS-"+site,
        "parameter_code":PARAMETER, "statistic_id":STATISTIC,
        "time":FIRST.isoformat()+"/"+last.isoformat(),
        "limit":500, "skipGeometry":"true",
    }
    return API+"?"+urlencode(params)


def parse_daily(payload, site, include_holdout=False):
    if site not in SITES or not isinstance(payload,dict):
        raise ValueError("Unapproved USGS daily series")
    features=payload.get("features")
    if payload.get("type")!="FeatureCollection" or not isinstance(features,list):
        raise ValueError("Invalid modern USGS response")
    if not 20<=len(features)<=500:
        raise ValueError("Incomplete or excessive USGS records")
    if any(link.get("rel")=="next" for link in payload.get("links",[])
           if isinstance(link,dict)):
        raise ValueError("USGS response is paginated; refuse incomplete measurements")
    obs={}
    statuses=set()
    for feature in features:
        p=feature.get("properties") if isinstance(feature,dict) else None
        if not isinstance(p,dict) or (p.get("monitoring_location_id")!="USGS-"+site
           or p.get("parameter_code")!=PARAMETER or p.get("statistic_id")!=STATISTIC
           or p.get("unit_of_measure")!="ft^3/s"):
            raise ValueError("Unexpected USGS site, parameter, statistic or units")
        try:
            day=date.fromisoformat(p["time"][:10])
            y=float(p["value"])
        except (TypeError,KeyError,ValueError) as exc:
            raise ValueError("Missing USGS daily measurement") from exc
        limit=HOLDOUT_LAST if include_holdout else DEVELOPMENT_LAST
        if not FIRST<=day<=limit or not math.isfinite(y) or not 0<y<10_000_000:
            raise ValueError("Invalid observation day or flow")
        if day in obs:
            raise ValueError("Multiple time series or duplicate daily measurements")
        obs[day]=y
        statuses.add(p.get("approval_status","Unknown"))
    if len(obs)<27:
        raise ValueError("Too few daily discharge observations")
    return obs,sorted(str(x) for x in statuses)


def fetch_daily(site, include_holdout=False, opener=urlopen):
    request=Request(query_url(site,include_holdout),
                    headers={"User-Agent":"PlenumScientificIntelligence/1.0 public-hydrology-research"})
    with opener(request,timeout=30) as response:
        raw=response.read(MAX_PAYLOAD+1)
    if len(raw)>MAX_PAYLOAD:
        raise ValueError("USGS measurement response exceeded cap")
    data=json.loads(raw)
    obs,statuses=parse_daily(data,site,include_holdout)
    return obs, {"source":"USGS Water Data API v1 daily discharge",
                 "url":query_url(site,include_holdout),
                 "response_sha256":sha256(raw).hexdigest(),
                 "statuses":statuses, "parameter_code":PARAMETER,
                 "statistic_id":STATISTIC, "unit":"ft^3/s"}


def development_digest(obs):
    items=[(day.isoformat(),value) for day,value in sorted(obs.items())
           if FIRST<=day<=DEVELOPMENT_LAST]
    if len(items)<27:
        raise ValueError("Insufficient preregistered discharge observations")
    return canonical_digest(items)


def _last_values(obs,train_end):
    days=[d for d in sorted(obs) if FIRST<=d<=train_end]
    if len(days)<20 or days[-1]!=train_end:
        raise ValueError("Training data missing latest approved day")
    if any((train_end-timedelta(days=k)) not in obs for k in range(14)):
        raise ValueError("Missing complete last 14 training days")
    return days


def _trend(obs,train_end,target):
    t=[train_end-timedelta(days=k) for k in range(13,-1,-1)]
    ln=[math.log(obs[day]) for day in t]
    avg=mean(ln)
    ybar=mean(range(14))
    slope=sum((i-ybar)*(v-avg) for i,v in enumerate(ln))/sum((i-ybar)**2 for i in range(14))
    slope=max(-0.05,min(0.05,slope))
    horizon=(target-train_end).days
    return obs[train_end]*math.exp(max(-1.0,min(1.0,slope*horizon)))


def predict(obs,train_end,day,method):
    if not isinstance(train_end,date) or not isinstance(day,date) or day<=train_end:
        raise ValueError("Only chronological future prediction is allowed")
    _last_values(obs,train_end)
    recent=[obs[train_end-timedelta(days=i)] for i in range(7)]
    last=obs[train_end]
    weekly=mean(recent)
    trend=_trend(obs,train_end,day)
    if method==BASELINES[0]:
        return last
    if method==BASELINES[1]:
        return weekly
    if method==BASELINES[2]:
        return trend
    if (not isinstance(method,dict)
            or not 0<=method.get("alpha",-1)<=1
            or not -0.05<=method.get("beta",1)<=0.05):
        raise ValueError("Candidate not in bounded parameter family")
    horizon=(day-train_end).days
    growth=math.exp(method["beta"]*horizon)
    return (1-method["alpha"])*weekly*growth+method["alpha"]*trend


def _error(obs,train_end,targets,method):
    if method is None:
        return None
    if any(t not in obs or t<=train_end for t in targets):
        raise ValueError("Measured evaluation dates unavailable")
    true=[obs[day] for day in targets]
    pred=[predict(obs,train_end,day,method) for day in targets]
    return round(sum(abs(a-b)/max(a,1.) for a,b in zip(true,pred))/len(targets),8)


def fold_scores(obs,model):
    return [_error(obs,train_end,targets,model) for train_end,targets in FOLDS]


def baseline_scores(obs):
    return {name:fold_scores(obs,name) for name in BASELINES}


def select(qwen,critic,base,q_scores,c_scores,margin=0.05):
    """Require relative-error gain on EACH preregistered development fold."""
    if not 0<=margin<=0.5:
        raise ValueError("Invalid preregistered margin")
    eligible=[]
    for order,(name,model,scores) in enumerate((
            ("qwen",qwen,q_scores),("critic",critic,c_scores))):
        if (model is not None and len(scores)==len(FOLDS)
              and all(s is not None and s <= (1-margin)*min(base[k][i]
                      for k in BASELINES) for i,s in enumerate(scores))):
            eligible.append((sum(scores)/len(scores),order,name,model))
    if eligible:
        _,_,name,model=min(eligible,key=lambda x:(x[0],x[1]))
        return {"source":name,"candidate":model}
    best=min(BASELINES,key=lambda n:(sum(base[n]),BASELINES.index(n)))
    return {"source":"baseline","candidate":best}

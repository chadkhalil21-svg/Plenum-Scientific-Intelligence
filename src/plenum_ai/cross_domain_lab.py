"""Independent historical chemistry and biology method-selection benchmark.

Models propose bounded hyperparameters, NEVER executable code. Chemistry uses a
Bemis-Murcko scaffold-separated Delaney ESOL solubility study. Biology uses
public UCI Wisconsin cell-morphology observations for research ONLY. This is
NOT an AGI, clinical, invention, or prospective discovery demonstration.
"""
import argparse
import csv
from dataclasses import dataclass
from hashlib import sha1,sha256
from io import StringIO
import json
import math
from pathlib import Path
from urllib.request import Request,urlopen

import numpy as np

PROTOCOL=Path(__file__).resolve().parents[2]/"protocols/cross-domain-chemistry-biology-v1.json"
DOMAINS=("chemistry","biology")
QWEN="Qwen/Qwen3-1.7B"
QWEN_SHA="70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
CRITIC="HuggingFaceTB/SmolLM2-1.7B-Instruct"
CRITIC_SHA="31b70e2e869a7173562077fd711b654946d38674"
FEATURES=("Minimum Degree","Molecular Weight","Number of H-Bond Donors",
          "Number of Rings","Number of Rotatable Bonds","Polar Surface Area")
BASELINES=("linear","forest")
SEED=20261107
SCHEMA="plenum-cross-domain-chemistry-biology-v1"


def digest(obj):
    return sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),
          ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def protocol():
    p=json.loads(PROTOCOL.read_text("utf-8"))
    c=p.get("datasets",{}).get("chemistry",{})
    if (p.get("id")!=SCHEMA or tuple(c.get("features",[]))!=FEATURES
        or c.get("git_blob_sha1")!="970b0d32771f1d67175d4f4a630e13f446ba97a8"
        or p.get("datasets",{}).get("biology",{}).get("split_seed")!=SEED
        or p.get("models",{}).get("proposer",{}).get("revision")!=QWEN_SHA
        or p.get("models",{}).get("critic",{}).get("revision")!=CRITIC_SHA):
        raise ValueError("Precommitted scientific protocol altered")
    return p


@dataclass
class Dataset:
    name: str
    X: np.ndarray
    y: np.ndarray
    train: np.ndarray
    dev: np.ndarray
    holdout: np.ndarray
    source_digest: str
    features: tuple

    def verify(self):
        indices=[set(int(i) for i in x) for x in (self.train,self.dev,self.holdout)]
        if (self.name not in DOMAINS or self.X.ndim!=2 or
            len(self.X)!=len(self.y) or
            not np.all(np.isfinite(self.X)) or not np.all(np.isfinite(self.y)) or
            min(len(x) for x in indices)<25 or
            indices[0]&indices[1] or indices[0]&indices[2] or indices[1]&indices[2] or
            len(set.union(*indices))!=len(self.y)):
            raise ValueError("Scientific data missing, overlapping, or nonfinite")
        if self.name=="biology":
            for idx in (self.train,self.dev,self.holdout):
                if set(int(x) for x in self.y[idx])!={0,1}:
                    raise ValueError("Biology classes absent from benchmark split")


def chemistry(opener=urlopen):
    from rdkit import Chem,RDLogger
    from rdkit.Chem.Scaffolds import MurckoScaffold
    RDLogger.DisableLog("rdApp.error")
    source=protocol()["datasets"]["chemistry"]
    request=Request(source["source"],headers={
       "User-Agent":"PlenumScientificIntelligence/1.0 public-evidence"})
    with opener(request,timeout=25) as response:
        raw=response.read(160001)
    if len(raw)>160000:
        raise ValueError("Oversized Delaney chemistry source")
    hash_blob=sha1(b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()
    if hash_blob!=source["git_blob_sha1"]:
        raise ValueError("Chemistry source changed since evidence protocol")
    records=list(csv.DictReader(StringIO(raw.decode("utf-8"))))
    if len(records)!=1128:
        raise ValueError("Expected exactly 1128 Delaney solubility records")
    groups={}
    X=[];y=[]
    for i,row in enumerate(records):
        if any(row.get(f) in (None,"") for f in FEATURES+(
                "measured log solubility in mols per litre","smiles")):
            raise ValueError("Missing chemistry experimental observations")
        mol=Chem.MolFromSmiles(row["smiles"])
        if mol is None:
            raise ValueError("Invalid chemistry structure")
        scaffold=MurckoScaffold.MurckoScaffoldSmiles(mol=mol)
        group="scaffold:"+scaffold if scaffold else "acyclic:"+Chem.MolToSmiles(mol)
        groups.setdefault(group,[]).append(i)
        X.append([float(row[f]) for f in FEATURES])
        y.append(float(row["measured log solubility in mols per litre"]))
    assigned={"train":[],"dev":[],"holdout":[]}
    ordered=sorted(groups.items(),key=lambda pair:(-len(pair[1]),
         sha256(("plenum-cross-domain-v1:"+pair[0]).encode()).hexdigest()))
    for group,ids in ordered:
        label=("train" if len(assigned["train"])<.70*len(y) else
               "dev" if len(assigned["dev"])<.15*len(y) else "holdout")
        assigned[label].extend(ids)
    d=Dataset("chemistry",np.asarray(X,float),np.asarray(y,float),
         *(np.asarray(sorted(assigned[n]),int) for n in ("train","dev","holdout")),
         hash_blob,FEATURES)
    d.verify()
    return d


def biology():
    from sklearn.datasets import load_breast_cancer
    from sklearn.model_selection import train_test_split
    data=load_breast_cancer()
    X=np.asarray(data.data,dtype=float)
    y=np.asarray(data.target,dtype=int)
    if X.shape!=(569,30) or y.shape!=(569,):
        raise ValueError("Historical biology dataset changed")
    indices=np.arange(569)
    train_dev,holdout=train_test_split(indices,test_size=.20,
         stratify=y,random_state=SEED)
    train,dev=train_test_split(train_dev,test_size=.20,
         stratify=y[train_dev],random_state=SEED)
    fingerprint=sha256(X.astype("<f8").tobytes()+
                        y.astype("<i4").tobytes()).hexdigest()
    d=Dataset("biology",X,y,np.sort(train),np.sort(dev),np.sort(holdout),
              fingerprint,tuple(str(f) for f in data.feature_names))
    d.verify()
    return d


def load(name):
    if name=="chemistry":return chemistry()
    if name=="biology":return biology()
    raise ValueError("Unknown precommitted scientific domain")


def parse(text):
    if not isinstance(text,str) or len(text)>5000:
        return {"status":"invalid","candidate":None}
    raw=text.strip()
    if raw.startswith(chr(96)*3):
        raw=raw.strip(chr(96)).removeprefix("json").strip()
    try: p=json.loads(raw)
    except (ValueError,TypeError):return {"status":"invalid_json","candidate":None}
    if not isinstance(p,dict) or set(p)!={
          "linear_strength","forest_leaf","mix","hypothesis","falsifier"}:
        return {"status":"invalid_schema","candidate":None}
    a,b,c=p["linear_strength"],p["forest_leaf"],p["mix"]
    if (type(a) not in (float,int) or type(b) is not int
        or type(c) not in (float,int) or not math.isfinite(a) or
        not math.isfinite(c) or not .02<=a<=25.0 or
        not 1<=b<=12 or not 0<=c<=1):
        return {"status":"invalid_parameters","candidate":None}
    if any(not isinstance(p[k],str) or len(p[k])>450
           for k in ("hypothesis","falsifier")):
        return {"status":"invalid_claim_type","candidate":None}
    # Numerical method evaluation and prose quality are distinct. Preserve
    # weak scientific writing without discarding independently testable rates.
    # No automated numeric score ever proves a new scientific hypothesis.
    explanatory=(len(p["hypothesis"].strip())>=15 and
                 len(p["falsifier"].strip())>=15)
    return {"status":"valid" if explanatory else "numeric_only_weak_claim",
            "scientific_claim_verified":False,
            "candidate":{
        "linear_strength":float(a),"forest_leaf":b,"mix":float(c),
        "hypothesis":p["hypothesis"].strip(),
        "falsifier":p["falsifier"].strip()}}


def baseline(name):
    if name not in BASELINES:raise ValueError("Unknown baseline")
    return {"linear_strength":1.0,"forest_leaf":2,
            "mix":1.0 if name=="linear" else 0.0}


def score(d,proposal,fit,verify):
    """Fit prewritten models, no model-produced code execution."""
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline
    from sklearn.linear_model import Ridge,LogisticRegression
    from sklearn.ensemble import RandomForestRegressor,RandomForestClassifier
    from sklearn.metrics import mean_absolute_error,log_loss
    if proposal is None:return None
    if isinstance(proposal,str):
        params=baseline(proposal)
    else:
        valid=parse(json.dumps(proposal))["candidate"]
        if valid!=proposal:
            raise ValueError("Illegal research model configuration")
        params=valid
    if d.name=="chemistry":
        a=make_pipeline(StandardScaler(),Ridge(alpha=params["linear_strength"]))
        b=RandomForestRegressor(n_estimators=60,random_state=SEED,
             min_samples_leaf=params["forest_leaf"],n_jobs=2)
    else:
        a=make_pipeline(StandardScaler(),LogisticRegression(
             C=params["linear_strength"],max_iter=1200,random_state=SEED))
        b=RandomForestClassifier(n_estimators=60,random_state=SEED,
             min_samples_leaf=params["forest_leaf"],n_jobs=2)
    a.fit(d.X[fit],d.y[fit])
    b.fit(d.X[fit],d.y[fit])
    if d.name=="chemistry":
        p=params["mix"]*a.predict(d.X[verify])+(1-params["mix"])*b.predict(d.X[verify])
        result=mean_absolute_error(d.y[verify],p)
    else:
        p=params["mix"]*a.predict_proba(d.X[verify])[:,1]+(
          1-params["mix"])*b.predict_proba(d.X[verify])[:,1]
        result=log_loss(d.y[verify],np.clip(p,1e-7,1-1e-7),labels=[0,1])
    if not math.isfinite(result) or result<0:raise ValueError("Unphysical model score")
    return round(float(result),7)


def prepare(loader=load):
    data=[]
    for domain in DOMAINS:
        d=loader(domain);d.verify()
        refs={name:score(d,name,d.train,d.dev) for name in BASELINES}
        data.append({"domain":domain,"source_sha256":d.source_digest,
           "train_n":len(d.train),"dev_n":len(d.dev),"holdout_n":len(d.holdout),
           "features":list(d.features),
           "metric":"MAE log(mol/L)" if domain=="chemistry" else "log_loss",
           "baseline_dev_errors":refs,"holdout_scored":False})
    return {"schema":SCHEMA,"stage":"development","protocol_sha256":digest(protocol()),
        "domains":data,"holdout_labels_exposed_to_models":False,
        "AGI_verified":False}


def _check_dev(dev,loader):
    if (not isinstance(dev,dict) or dev.get("schema")!=SCHEMA or
        dev.get("protocol_sha256")!=digest(protocol()) or
        dev.get("holdout_labels_exposed_to_models") is not False):
        raise ValueError("Research development provenance invalid")
    rows=dev.get("domains")
    if not isinstance(rows,list) or [x.get("domain") for x in rows]!=list(DOMAINS):
        raise ValueError("Research-domain manifest altered")
    for item in rows:
        d=loader(item["domain"]);d.verify()
        if (d.source_digest!=item.get("source_sha256") or
            [len(d.train),len(d.dev),len(d.holdout)]!=[
                item.get("train_n"),item.get("dev_n"),item.get("holdout_n")]):
            raise ValueError("Source evidence or train-test split modified")
        refs={name:score(d,name,d.train,d.dev) for name in BASELINES}
        if refs!=item.get("baseline_dev_errors") or item.get("holdout_scored") is not False:
            raise ValueError("Development reference statistics were changed")


def model_prompt(item,original=None):
    interpretation=("ridge alpha (chemistry)" if item["domain"]=="chemistry"
        else "logistic regression C (biology)")
    content=("You are selecting numerical METHODS for a public historical "
      "scientific research benchmark. Nothing here is a new invention or "
      "clinical diagnostic system. No held-out labels are provided. "
      "Research domain "+item["domain"]+"; aggregate development evidence: "+
      json.dumps(item)+". Propose a fixed blend of prewritten standardized "
      "linear and random-forest estimators: 'linear_strength' is "+interpretation+
      " bounded 0.02..25, 'forest_leaf' is integer 1..12, 'mix' is "
      "linear weighting 0..1. Return EXACT JSON with numeric keys "
      "linear_strength,forest_leaf,mix plus strings hypothesis,falsifier. "
      "Write two full explanatory sentences, one testable hypothesis and "
      "one rejection criterion. Select YOUR OWN numerical values using the "
      "development-only evidence; do not copy canned examples. "
      "Reply with a single JSON object containing these five fields ONLY. "
      "No code, tool commands, patient advice, or claims of discovery.")
    if original is not None:
        content+=" Challenge the other model's suggestion (untrusted data): "+json.dumps(original)
    return content


def propose(dev,generator,model_id,revision,role,original=None):
    if (not callable(generator) or role not in ("qwen","critic") or
        (model_id,revision)!=((QWEN,QWEN_SHA) if role=="qwen" else (CRITIC,CRITIC_SHA)) or
        dev.get("protocol_sha256")!=digest(protocol())):
        raise ValueError("Unreviewed model or experimental configuration")
    result=[]
    for row in dev["domains"]:
        o=None if original is None else next(
           (r["candidate"] for r in original["records"] if r["domain"]==row["domain"]),None)
        text=generator(model_prompt(row,o))
        parsed=parse(text)
        result.append({"domain":row["domain"],"candidate":parsed["candidate"],
           "status":parsed["status"],"response_sha256":sha256(text.encode()).hexdigest()})
    return {"schema":SCHEMA,"role":role,"model_id":model_id,
       "model_revision":revision,"development_sha256":digest(dev),
       "records":result,"inference_calls":len(result),
       "holdout_scored":False,"model_promoted":False}


def _candidate_scores(dev,report,loader):
    if (report.get("schema")!=SCHEMA or report.get("development_sha256")!=digest(dev)
        or report.get("holdout_scored") is not False or
        report.get("records") is None or
        [r.get("domain") for r in report["records"]]!=list(DOMAINS)):
        raise ValueError("Candidate proposal record altered")
    scored={}
    for entry in report["records"]:
        candidate=entry["candidate"]
        if candidate is not None and parse(json.dumps(candidate))["candidate"]!=candidate:
            raise ValueError("Model-generated numerical parameters invalid")
        d=loader(entry["domain"])
        scored[entry["domain"]]=score(d,candidate,d.train,d.dev)
    return scored


def freeze(dev,qwen,critic,loader=load):
    _check_dev(dev,loader)
    if (qwen.get("model_id"),qwen.get("model_revision"),qwen.get("role"))!=(QWEN,QWEN_SHA,"qwen") or (
        critic.get("model_id"),critic.get("model_revision"),critic.get("role"))!=(CRITIC,CRITIC_SHA,"critic"):
        raise ValueError("Scientific roles do not match reviewed models")
    q=_candidate_scores(dev,qwen,loader)
    c=_candidate_scores(dev,critic,loader)
    decisions=[]
    for row in dev["domains"]:
        domain=row["domain"];refs=row["baseline_dev_errors"]
        best_name=min(BASELINES,key=lambda name:(refs[name],BASELINES.index(name)))
        chosen={"role":"baseline","method":best_name,"score":refs[best_name]}
        for role,proposal,devscore in (
           ("qwen",qwen,q[domain]),("critic",critic,c[domain])):
            if devscore is not None and devscore<=refs[best_name]*.98 and (
               chosen["role"]=="baseline" or devscore<chosen["score"]):
                params=next(x["candidate"] for x in proposal["records"] if x["domain"]==domain)
                chosen={"role":role,"method":params,"score":devscore}
        decisions.append({"domain":domain,"selection":chosen,
             "qwen_dev_error":q[domain],"critic_dev_error":c[domain],
             "best_reference_dev_error":refs[best_name]})
    return {"schema":SCHEMA,"stage":"frozen","protocol_sha256":digest(protocol()),
       "development":dev,"qwen":qwen,"critic":critic,"decisions":decisions,
       "dev_sha256":digest(dev),"qwen_sha256":digest(qwen),"critic_sha256":digest(critic),
       "holdout_used_in_selection":False,"automatic_deployment":False}


def audit(frozen,loader=load):
    if (not isinstance(frozen,dict) or frozen.get("schema")!=SCHEMA or
       frozen.get("stage")!="frozen" or frozen.get("holdout_used_in_selection") is not False or
       frozen.get("automatic_deployment") is not False):
        raise ValueError("Invalid held-out study manifest")
    for field,datum in (("dev_sha256","development"),("qwen_sha256","qwen"),
                        ("critic_sha256","critic")):
        if frozen.get(field)!=digest(frozen.get(datum)):
            raise ValueError("Frozen research evidence changed after sealing")
    independently=freeze(frozen["development"],frozen["qwen"],frozen["critic"],loader)
    if independently!=frozen:
        raise ValueError("Development selection could not be independently reproduced")
    results=[]
    for row in frozen["decisions"]:
        d=loader(row["domain"]);d.verify()
        train_dev=np.concatenate((d.train,d.dev))
        refs={b:score(d,b,train_dev,d.holdout) for b in BASELINES}
        selected=score(d,row["selection"]["method"],train_dev,d.holdout)
        original=next(x["candidate"] for x in frozen["qwen"]["records"] if x["domain"]==d.name)
        independent=next(x["candidate"] for x in frozen["critic"]["records"] if x["domain"]==d.name)
        qscore=score(d,original,train_dev,d.holdout) if original is not None else None
        cscore=score(d,independent,train_dev,d.holdout) if independent is not None else None
        results.append({"domain":d.name,"holdout_n":len(d.holdout),
             "metric":"MAE log(mol/L)" if d.name=="chemistry" else "log_loss",
             "selected_role":row["selection"]["role"],
             "selected_test_error":selected,
             "qwen_test_error":qscore,"critic_test_error":cscore,
             "reference_test_errors":refs,"best_reference_error":min(refs.values()),
             "beats_strongest_reference":selected<min(refs.values()),
             "historical_public_dataset":True})
    return {"schema":"plenum-cross-domain-independent-audit-v1",
      "frozen_sha256":digest(frozen),"results":results,
      "tested_domains":len(results),
      "wins_against_strongest_baselines":sum(r["beats_strongest_reference"] for r in results),
      "independent_holdout_audit":True,"AGI_demonstrated":False,
      "new_scientific_discovery_verified":False,
      "clinical_diagnostic_capability_verified":False,
      "recursive_self_improvement":False,"model_weights_modified":False,
      "model_promoted":False,
      "limitations":"Historical public datasets possibly in model pretraining, "
        "bounded statistical hyperparameters, only two evaluation domains. "
        "No new scientific law, clinical validation, prospective prediction or AGI."}


def save(path,x):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+"\n","utf-8")


def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="command",required=True)
    x=sub.add_parser("prepare");x.add_argument("--out",required=True)
    for cmd in ("propose","critic"):
        x=sub.add_parser(cmd);x.add_argument("--development",required=True)
        if cmd=="critic":x.add_argument("--qwen",required=True)
        x.add_argument("--out",required=True)
    x=sub.add_parser("freeze")
    for key in ("development","qwen","critic","out"):
        x.add_argument("--"+key,required=True)
    x=sub.add_parser("audit");x.add_argument("--frozen",required=True)
    x.add_argument("--out",required=True)
    args=p.parse_args()
    read=lambda p:json.loads(Path(p).read_text("utf-8"))
    if args.command=="prepare":result=prepare()
    elif args.command=="propose":
        from .model_challenge import CpuCandidate
        model=CpuCandidate(QWEN)
        result=propose(read(args.development),model.generate,model.model_id,
                       model.revision,"qwen")
    elif args.command=="critic":
        from .independent_noaa_critic import SmolLM2Critic
        model=SmolLM2Critic()
        result=propose(read(args.development),model.generate,CRITIC,CRITIC_SHA,
                       "critic",read(args.qwen))
    elif args.command=="freeze":
        result=freeze(read(args.development),read(args.qwen),read(args.critic))
    else:result=audit(read(args.frozen))
    save(args.out,result)
    print("Research stage:",args.command,
          "AGI or scientific discovery NOT demonstrated")


if __name__=="__main__":
    main()

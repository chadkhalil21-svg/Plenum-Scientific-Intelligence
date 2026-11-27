"""Bounded paired comparison using real prior 4B receipts; no 4B replay.

Reuse scikit-learn's KNeighborsClassifier, the classifier used by upstream
LLMRouter KNNRouter. Avoid its heavyweight provider and embedding stack.
This is a tiny diagnostic, never sufficient for production router admission.
"""
import hashlib
import itertools
import json
import os
import sys
import time
import zipfile
from pathlib import Path
from importlib.metadata import version
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"prometheus_gepa"))
from optimize_planner import corpus, unique, SEED
import model_plan as mp
import variable_mission as vm
from checkpoint_store import exclusive
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import KNeighborsClassifier

ARCHIVE_SHA="f6571bb878ecb45cf3fd52f13d0a16c3e98df5ebc91653d66d32b471d090fd9f"
MODEL="qwen3.5:9b-q4_K_M"
PREFIX="56671c2ab938"
CALLS={"a":5,"b":6,"c":4,"d":1,"e":2,"f":3,"g":18,"h":19,"i":20}

def decoded(raw_hash, keys):
    matches={}
    for order in itertools.permutations(sorted(keys)):
        for values in itertools.product((False,True),repeat=len(order)):
            obj=dict(zip(order,values))
            texts=[json.dumps(obj,separators=s) for s in ((",",":"),(", ",": "),(",",": "),(", ",":"))]
            texts.extend(json.dumps(obj,indent=n) for n in (1,2,4))
            for raw in texts:
                for pre in (""," ","\n"):
                    for post in (""," ","\n","\n\n"):
                        candidate=pre+raw+post
                        if mp.digest(candidate)==raw_hash:
                            matches[mp.digest(obj)]=obj
    if len(matches)!=1:
        raise ValueError("Archived response cannot be uniquely reconstructed")
    return next(iter(matches.values()))

def prior(archive, groups):
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=ARCHIVE_SHA:
        raise ValueError("Unexpected original archive")
    result={}
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None or len(z.namelist())!=len(set(z.namelist())):
            raise ValueError("Invalid original archive")
        def read(name):
            return json.loads(z.read(name),object_pairs_hook=unique)
        binding=read("binding.json")
        if binding["corpus_sha256"]!=mp.digest(groups) or binding["paid_inference"] is not False:
            raise ValueError("Original corpus mismatch")
        outcome=read("outcome.json")
        for split,items in groups.items():
            for item in items:
                key=item["id"]
                i=CALLS[key]
                reservation=read(f"call-{i:02d}.reserved.json")
                row=read(f"call-{i:02d}.result.json")
                req=vm.request(item["mission"])
                if (reservation["request_sha256"]!=mp.digest(req) or reservation["stage"]!="selection"
                    or reservation["paid_inference"] is not False or reservation["model_digest"]!=binding["model_digest"]
                    or any(row[k]!=v for k,v in reservation.items())):
                    raise ValueError("Original request mismatch")
                selection=decoded(row["response_sha256"],item["mission"]["authorized_inputs"])
                vm.graph(item["mission"],selection)
                score=int(selection==item["expected"])
                if split!="train":
                    old=outcome[("validation" if split=="val" else "test")+"_baseline"][key]
                    if old!={"selection":selection,"score":float(score)}:
                        raise ValueError("Original score mismatch")
                result[key]={"selection":selection,"score":score,"response_sha256":row["response_sha256"],
                             "request_sha256":reservation["request_sha256"]}
    return result

def main():
    if os.getenv("GITHUB_ACTIONS")!="true" or version("scikit-learn")!="1.6.1":
        raise PermissionError("Pinned isolated runner only")
    for k in ("OPENAI_API_KEY","ANTHROPIC_API_KEY","GOOGLE_API_KEY","AZURE_OPENAI_API_KEY","HF_TOKEN","OLLAMA_API_KEY"):
        if os.getenv(k):
            raise PermissionError("External credentials prohibited")
    archive,root=map(Path,sys.argv[1:])
    root.mkdir(mode=0o700,exist_ok=False)
    groups=corpus()
    previous=prior(archive,groups)
    tags=mp.read_json("/api/tags")
    found=[r.get("digest") for r in tags["models"] if r.get("name")==MODEL]
    if len(found)!=1 or not isinstance(found[0],str):
        raise ValueError("Pinned 9B absent")
    md=found[0]
    raw=md.removeprefix("sha256:")
    if len(raw)!=64 or not raw.startswith(PREFIX) or any(c not in "0123456789abcdef" for c in raw):
        raise ValueError("Unexpected 9B digest")
    exclusive(root/"binding.json",{"source_archive_sha256":ARCHIVE_SHA,"corpus_sha256":mp.digest(groups),
             "model_digest":md,"paid_inference":False,"sklearn":"1.6.1","original_4b_replayed":False})
    pairs={}
    seen=set()
    for split,items in groups.items():
        for item in items:
            key=item["id"]
            req=vm.request(item["mission"])
            req["model"]=MODEL
            h=mp.digest(req)
            if h in seen or h==previous[key]["request_sha256"]:
                raise ValueError("Repeated request")
            seen.add(h)
            identity={"case":key,"split":split,"request_sha256":h,"model_digest":md,"paid_inference":False}
            exclusive(root/(key+".reserved.json"),identity)
            started=time.monotonic()
            reply=mp.read_json("/api/chat",req,timeout=180)
            elapsed=round(time.monotonic()-started,3)
            if reply.get("model")!=MODEL or reply.get("done") is not True or reply.get("done_reason")!="stop":
                raise ValueError("Incomplete 9B response")
            raw_response=reply["message"]["content"]
            if not isinstance(raw_response,str) or len(raw_response)>2000:
                raise ValueError("Invalid response")
            n,p=reply.get("eval_count"),reply.get("prompt_eval_count")
            if type(n) is not int or not 0<n<=req["options"]["num_predict"] or type(p) is not int or not 0<p<=req["options"]["num_ctx"]:
                raise ValueError("Invalid inference counters")
            try:
                answer=json.loads(raw_response,object_pairs_hook=unique)
                vm.graph(item["mission"],answer)
            except (ValueError,TypeError,KeyError):
                answer=None
            score=int(answer==item["expected"])
            row={**identity,"selection":answer,"score":score,"response_sha256":mp.digest(raw_response),
                 "eval_count":n,"prompt_eval_count":p,"seconds":elapsed}
            exclusive(root/(key+".result.json"),row)
            pairs[key]={"split":split,"4b":previous[key],"9b":row}
    # Reuse the actual upstream KNN classifier with local lexical vectors.
    # Fit on train+validation only; held-out scores never determine routing.
    train=groups["train"]+groups["val"]
    test=groups["test"]
    def features(item):
        return item["mission"]["objective"]+" capabilities "+" ".join(sorted(item["mission"]["authorized_inputs"]))
    v=TfidfVectorizer(ngram_range=(1,2),lowercase=True)
    x=v.fit_transform([features(i) for i in train])
    labels=["9b" if pairs[i["id"]]["9b"]["score"]>pairs[i["id"]]["4b"]["score"] else "4b" for i in train]
    knn=KNeighborsClassifier(n_neighbors=1,metric="cosine",algorithm="brute")
    knn.fit(x,labels)
    routes=knn.predict(v.transform([features(i) for i in test])).tolist()
    scored={i["id"]:{"route":r,"4b":pairs[i["id"]]["4b"]["score"],"9b":pairs[i["id"]]["9b"]["score"],
                       "routed_score":pairs[i["id"]][r]["score"]} for i,r in zip(test,routes)}
    totals={k:sum(r[k] for r in scored.values()) for k in ("4b","9b","routed_score")}
    exclusive(root/"outcome.json",{"paired_results":pairs,"held_out":scored,"held_out_totals":totals,
              "training_labels":labels,"new_9b_calls":len(seen),"4b_calls_replayed":0,"paid_inference":False,
              "production_routing_admitted":False,"general_autonomy_verified":False,
              "method":"LLMRouter KNN classifier dependency, local TF-IDF; not full LLMRouter installation"})
if __name__=="__main__":
    main()

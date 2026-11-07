"""Paired reasoning-method comparison, with an independent deterministic auditor.

The source questions and all reference answers come from an EXISTING frozen
math/science/arithmetic-program generator. No unrestricted generated code.
Runs a pinned existing 1.7B model and an optional pinned 4-bit 4B model.
"""
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import time

from . import agi_capability_lab as lab

SCHEMA="plenum-reasoning-method-ablation-v1"
AUDIT_SCHEMA="plenum-reasoning-method-independent-audit-v1"
PROTOCOL=Path(__file__).resolve().parents[2]/"protocols/reasoning-method-ablation-v1.json"
QWEN_17="Qwen/Qwen3-1.7B"
QWEN_4="Qwen/Qwen3-4B-Instruct-2507"
MODEL_REVISIONS={
    QWEN_17:"70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",
    QWEN_4:"cdbee75f17c01a7cc42f958dc650907174af0554",
}
GGUF_REPO="unsloth/Qwen3-4B-Instruct-2507-GGUF"
GGUF_REVISION="75818336d16b082f8427aeac9d13afb6e7b983d9"
GGUF_FILE="Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
MODES=("baseline","verify")
MAX_OUTPUT_CHARS=4000


def digest(obj):
    return sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),
             ensure_ascii=False,allow_nan=False).encode("utf-8")).hexdigest()


def protocol():
    p=json.loads(PROTOCOL.read_text("utf-8"))
    models=p.get("models",[])
    if (p.get("schema")!=SCHEMA
        or [m.get("id") for m in models]!=list(MODEL_REVISIONS)
        or [m.get("revision") for m in models]!=list(MODEL_REVISIONS.values())
        or [m.get("key") for m in p.get("prompt_conditions",[])]!=list(MODES)
        or p.get("quantized_4b",{}).get("repository")!=GGUF_REPO
        or p["quantized_4b"].get("revision")!=GGUF_REVISION
        or p["quantized_4b"].get("file")!=GGUF_FILE):
        raise ValueError("Precommitted model or evaluation protocol changed")
    return p


def prepare(seed):
    protocol()
    manifest=lab.prepare(seed)
    return {"schema":SCHEMA,"protocol_sha256":digest(protocol()),
      "task_manifest":manifest,"manifest_sha256":lab.digest(manifest),
      "question_count":len(manifest["tasks"]),
      "modes":list(MODES),"answer_key_exposed":False,
      "AGI_demonstrated":False,"automatic_model_promotion":False}


def _check_prepared(prepared):
    if not isinstance(prepared,dict) or prepared!=prepare(prepared["task_manifest"]["seed"]):
        raise ValueError("Prepared benchmark questions/protocol changed")
    return prepared["task_manifest"]


def prompt_for(task,mode):
    if mode not in MODES:raise ValueError("Unknown prompt condition")
    if mode=="baseline":return task["prompt"]
    return (task["prompt"]+
      "\nBefore the final response, check the arithmetic and units. "
      "For arithmetic programs, check that your operations implement the "
      "full function on unseen inputs, not merely the examples. "
      "Return only the requested JSON value or operations, without "
      "an explanation, Markdown, invented observations or sample answers.")


def normalize(raw):
    """Narrow FORMAT-only correction: whole-response JSON fence, never infer numbers."""
    if not isinstance(raw,str) or len(raw)>MAX_OUTPUT_CHARS:
        return raw,"unusable"
    s=raw.strip()
    if s.startswith("{"):
        return s,"raw"
    m=re.fullmatch(r"`{3}(?:json)?\s*(\{[\s\S]*?\})\s*`{3}",s,flags=re.I)
    if m:
        return m.group(1),"entire_response_fenced_json"
    return raw,"unrecognized"


def _runtime(model):
    if model==QWEN_17:
        from .model_challenge import CpuCandidate
        runtime=CpuCandidate(model)
        if runtime.revision!=MODEL_REVISIONS[model]:
            raise ValueError("Existing model revision not pinned")
        def generate(prompt):
            batch=runtime._inputs(prompt)
            with runtime.torch.inference_mode():
                output=runtime.model.generate(
                    **batch, do_sample=False, max_new_tokens=220,
                    pad_token_id=runtime.tokenizer.eos_token_id)
            return runtime.tokenizer.decode(
                output[0][batch["input_ids"].shape[1]:],
                skip_special_tokens=True).strip()
        return generate,{"engine":"transformers-bfloat16",
            "model_source":model,"weights_revision":runtime.revision}
    if model==QWEN_4:
        from huggingface_hub import hf_hub_download
        from llama_cpp import Llama
        import os
        path=hf_hub_download(repo_id=GGUF_REPO,filename=GGUF_FILE,
                             revision=GGUF_REVISION)
        # No arbitrary local paths or external model execution.
        engine=Llama(model_path=path,n_ctx=1600,n_threads=2,
                     n_gpu_layers=0,verbose=False)
        def generate(prompt):
            answer=engine.create_chat_completion(
                messages=[{"role":"user","content":prompt}],
                max_tokens=220,temperature=0.0,top_p=1.0)
            return answer["choices"][0]["message"]["content"]
        return generate,{"engine":"llama-cpp-q4-k-m",
            "model_source":GGUF_REPO,"weights_revision":GGUF_REVISION,
            "base_model_revision":MODEL_REVISIONS[model],
            "quantized":True}
    raise ValueError("Unreviewed model")


def propose(prepared,model_id,generator,engine_metadata):
    manifest=_check_prepared(prepared)
    if model_id not in MODEL_REVISIONS or not callable(generator):
        raise ValueError("Unapproved model")
    if not isinstance(engine_metadata,dict) or engine_metadata.get("model_source") not in (model_id,GGUF_REPO):
        raise ValueError("Missing engine/model provenance")
    if engine_metadata.get("weights_revision") not in (MODEL_REVISIONS[QWEN_17],GGUF_REVISION):
        raise ValueError("Unpinned weights")
    if model_id==QWEN_17 and engine_metadata.get("weights_revision")!=MODEL_REVISIONS[model_id]:
        raise ValueError("Incorrect baseline weights")
    if model_id==QWEN_4 and engine_metadata.get("weights_revision")!=GGUF_REVISION:
        raise ValueError("Incorrect quantized weights")
    started=time.monotonic()
    results=[]
    for mode in MODES:
        for task in manifest["tasks"]:
            t0=time.monotonic()
            raw=generator(prompt_for(task,mode))
            seconds=round(time.monotonic()-t0,4)
            if not isinstance(raw,str):
                raise ValueError("Model output must be original text")
            # Keep original output bounded; oversized is recorded as failure.
            if len(raw)>MAX_OUTPUT_CHARS:
                payload=None
                hashvalue=sha256(raw.encode()).hexdigest()
            else:
                payload=raw
                hashvalue=sha256(raw.encode()).hexdigest()
            results.append({"mode":mode,"task_id":task["id"],
              "raw_response":payload,"response_sha256":hashvalue,
              "oversized":payload is None,"inference_seconds":seconds})
    return {"schema":SCHEMA,"model_id":model_id,
       "model_revision":MODEL_REVISIONS[model_id],
       "engine":engine_metadata,"protocol_sha256":digest(protocol()),
       "prepared_sha256":digest(prepared),
       "results":results,"model_calls":len(results),
       "elapsed_seconds":round(time.monotonic()-started,4),
       "model_saw_gold_answers":False,"model_saw_program_holdouts":False,
       "AGI_demonstrated":False,"model_promoted":False}


def _check_result(prepared,report,model_id):
    if (not isinstance(report,dict) or report.get("schema")!=SCHEMA
        or report.get("model_id")!=model_id
        or report.get("model_revision")!=MODEL_REVISIONS[model_id]
        or report.get("protocol_sha256")!=digest(protocol())
        or report.get("prepared_sha256")!=digest(prepared)
        or report.get("model_saw_gold_answers") is not False
        or report.get("model_saw_program_holdouts") is not False
        or report.get("AGI_demonstrated") is not False
        or report.get("model_promoted") is not False):
        raise ValueError("Unapproved model report")
    metadata=report.get("engine",{})
    if (metadata.get("weights_revision") !=
       (MODEL_REVISIONS[QWEN_17] if model_id==QWEN_17 else GGUF_REVISION)):
        raise ValueError("Unexpected model checkpoint")
    expected=[(m,t["id"]) for m in MODES for t in prepared["task_manifest"]["tasks"]]
    records=report.get("results")
    if not isinstance(records,list) or [(x.get("mode"),x.get("task_id")) for x in records]!=expected:
        raise ValueError("Missing or reordered model outputs")
    if report.get("model_calls")!=len(expected):
        raise ValueError("Model call count altered")
    for rec in records:
        text=rec.get("raw_response")
        if (not isinstance(rec.get("response_sha256"),str)
            or (text is None)!=(rec.get("oversized") is True)
            or (text is not None and (not isinstance(text,str)
              or len(text)>MAX_OUTPUT_CHARS
              or sha256(text.encode()).hexdigest()!=rec["response_sha256"]))
            or type(rec.get("inference_seconds")) not in (int,float)
            or not math.isfinite(rec["inference_seconds"])
            or not 0<=rec["inference_seconds"]<=3600):
            raise ValueError("Corrupted model response")
    if type(report.get("elapsed_seconds")) not in (int,float) or not math.isfinite(report["elapsed_seconds"]) or report["elapsed_seconds"]<0:
        raise ValueError("Invalid inference timing")


def audit(prepared,reports):
    manifest=_check_prepared(prepared)
    if not isinstance(reports,dict) or set(reports)!=set(MODEL_REVISIONS):
        raise ValueError("Both the old and stronger model are required")
    for k,v in reports.items():_check_result(prepared,v,k)
    details={}
    for model,report in reports.items():
        scores={}
        for mode in MODES:
            records=[r for r in report["results"] if r["mode"]==mode]
            checked=[]
            for task,raw in zip(manifest["tasks"],records):
                source=raw["raw_response"]
                strict=lab._evaluate(task,source,manifest["seed"])
                normalized,fmt=normalize(source)
                scored=lab._evaluate(task,normalized,manifest["seed"])
                checked.append({"task":task["id"],"family":task["family"],
                  "format_normalization":fmt,
                  "strict_schema_valid":strict["status"]=="valid",
                  "normalized_schema_valid":scored["status"]=="valid",
                  "strict_correct":strict["correct"],
                  "normalized_correct":scored["correct"],
                  "hidden_program_cases_passed":scored["hidden_program_cases_passed"],
                  "hidden_program_cases":scored["hidden_program_cases"],
                  "inference_seconds":raw["inference_seconds"]})
            scores[mode]={
                "attempted":len(checked),
                "strict_schema_valid":sum(x["strict_schema_valid"] for x in checked),
                "normalized_schema_valid":sum(x["normalized_schema_valid"] for x in checked),
                "strict_correct":sum(x["strict_correct"] for x in checked),
                "normalized_correct":sum(x["normalized_correct"] for x in checked),
                "model_seconds":round(sum(x["inference_seconds"] for x in checked),4),
                "domain_correct":{f:sum(x["normalized_correct"] for x in checked if x["family"]==f) for f in lab.FAMILIES},
                "tasks":checked}
        details[model]={"engine":report["engine"],"conditions":scores,
                       "total_model_calls":report["model_calls"],
                       "total_model_seconds":report["elapsed_seconds"]}
    return {"schema":AUDIT_SCHEMA,
            "protocol_sha256":digest(protocol()),
            "prepared_sha256":digest(prepared),
            "model_report_sha256":{k:digest(v) for k,v in reports.items()},
            "models":details,"task_count_per_condition":len(manifest["tasks"]),
            "arithmetic_program_inputs_excluded_from_model_prompts":True,
            "independent_deterministic_scoring":True,
            "unrestricted_generated_code_executed":False,
            "automatic_model_promotion":False,
            "AGI_demonstrated":False,
            "scientific_invention_verified":False,
            "limitations":"Only 6 seeded textbook-style tasks in each of two prompt conditions; public task templates, quantization differs, and format normalization is strict. No general intelligence or scientific invention inference."}


def save(path,value):
    p=Path(path)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")


def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("prepare")
    a.add_argument("--seed",type=int,required=True)
    a.add_argument("--out",required=True)
    a=sub.add_parser("propose")
    a.add_argument("--prepared",required=True)
    a.add_argument("--model",choices=list(MODEL_REVISIONS),required=True)
    a.add_argument("--out",required=True)
    a=sub.add_parser("audit")
    a.add_argument("--prepared",required=True)
    a.add_argument("--baseline",required=True)
    a.add_argument("--stronger",required=True)
    a.add_argument("--out",required=True)
    args=p.parse_args()
    if args.cmd=="prepare":
        record=prepare(args.seed)
    elif args.cmd=="propose":
        prepared=json.loads(Path(args.prepared).read_text())
        generate,meta=_runtime(args.model)
        record=propose(prepared,args.model,generate,meta)
        print("Measured",record["model_calls"],"calls from",record["model_id"],
              "seconds",record["elapsed_seconds"])
    else:
        prepared=json.loads(Path(args.prepared).read_text())
        baseline=json.loads(Path(args.baseline).read_text())
        stronger=json.loads(Path(args.stronger).read_text())
        record=audit(prepared,{QWEN_17:baseline,QWEN_4:stronger})
        for model,s in record["models"].items():
            for mode,metrics in s["conditions"].items():
                print(model,mode,"correct",metrics["normalized_correct"],
                      "/",metrics["attempted"],"raw JSON",metrics["strict_schema_valid"],
                      "recovered JSON",metrics["normalized_schema_valid"],
                      "seconds",metrics["model_seconds"])
    save(args.out,record)


if __name__=="__main__":
    main()

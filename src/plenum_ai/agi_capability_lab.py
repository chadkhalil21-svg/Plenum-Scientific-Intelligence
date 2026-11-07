"""AGI Capability Laboratory v1: independently scored, deliberately small tasks.

Models see question prompts but not reference answers. Programming responses are
interpreted in a bounded arithmetic JSON DSL, NEVER executed as Python/shell.
This measures narrow task performance, not genuine general intelligence.
"""
import argparse
from collections import Counter
from hashlib import sha256
import json
import math
from pathlib import Path
import random
import time

SCHEMA = "plenum-agi-capability-laboratory-v1"
AUDIT_SCHEMA = "plenum-agi-capability-independent-audit-v1"
MODEL_PINS = {
    "Qwen/Qwen3-1.7B": "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",
    "HuggingFaceTB/SmolLM2-1.7B-Instruct": "31b70e2e869a7173562077fd711b654946d38674",
}
FAMILIES = ("mathematics", "scientific_quantitative_reasoning",
            "restricted_program_synthesis")
MAX_RESPONSE_CHARS = 4000
MAX_OPERATIONS = 6
OPS = ("add", "mul", "square")
PROGRAM_INPUTS = (-11, -7, -5, -1, 0, 1, 2, 3, 7, 11)


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()


def _seed(seed):
    if type(seed) is not int or not 1 <= seed < 2**63:
        raise ValueError("A positive bounded evaluation run seed is required")
    return seed


def _num_prompt(problem):
    return (problem + "\nReturn ONLY one JSON object with one numeric field "
            'named "answer". No markdown or explanation. Never guess an observation.')


def _program_prompt(problem, examples):
    return (problem + "\nProduce a small arithmetic program using ONLY JSON: "
            '{"ops":[{"op":"add","value":integer},{"op":"mul","value":integer},'
            '{"op":"square"}]}. These objects are illustrative TYPES, not a "
            "suggested solution. Instructions operate on the current integer "
            "in their listed order. You may omit instructions and repeat "
            "allowed operations, with at most 6 total operations. "
            "The program must work on unseen integer inputs, not just examples. "
            "Return ONLY JSON, no markdown, text, Python or shell commands.\n"
            "Public examples: " + json.dumps(examples, sort_keys=True))


def _cases(seed):
    """Generate ground truth locally; only _public_cases reaches model jobs."""
    rng = random.Random(_seed(seed))
    a, b, c, d = (rng.randint(7, 47) for _ in range(4))
    modulo = rng.choice((53, 59, 61, 67, 71, 73))
    known_x = rng.randint(-16, 16)
    coefficient = rng.randint(3, 13)
    intercept = rng.randint(-55, 55)
    mass = rng.randrange(800, 2601, 100)
    speed = rng.randint(9, 31)
    distance = rng.randint(25, 95)
    stock = rng.randint(2, 7)
    divisor = rng.randint(4, 13)
    desired_ml = rng.randint(6, 29)
    result_ml = divisor * desired_ml
    final_concentration = stock / divisor
    mult = rng.choice((-8, -5, -3, 2, 4, 6, 7))
    offset = rng.randint(-19, 21)
    shift = rng.randint(-7, 7)
    after = rng.randint(-21, 21)
    tasks = [
      {
       "id": "math-modular",
       "family": FAMILIES[0],
       "prompt": _num_prompt(
         f"Compute the exact nonnegative remainder of (({a}*{b}+{c})^2+{d}) "
         f"upon division by {modulo}. Use ^ for exponentiation."),
       "gold": ((a*b+c)**2+d) % modulo,
      },
      {
       "id": "math-linear",
       "family": FAMILIES[0],
       "prompt": _num_prompt(
         f"Solve for x: {coefficient}*x + ({intercept}) = "
         f"{coefficient*known_x+intercept}. What is x?"),
       "gold": known_x,
      },
      {
       "id": "science-mechanics",
       "family": FAMILIES[1],
       "prompt": _num_prompt(
         f"A {mass}-kg vehicle travels at {speed} m/s and stops over "
         f"{distance} meters under constant braking. Neglect losses. "
         "What is the magnitude of the average braking force, in newtons? "
         "Use work-energy conservation. Return the answer to at least "
         "three significant figures."),
       "gold": mass*speed**2/(2*distance),
      },
      {
       "id": "science-chemistry",
       "family": FAMILIES[1],
       "prompt": _num_prompt(
         f"A stock solution has concentration {stock} mol/L. You want "
         f"{result_ml} mL at {final_concentration:.9g} mol/L. "
         "Assume ideal volumetric dilution and C1*V1=C2*V2. "
         "What volume of the stock solution in mL is required?"),
       "gold": desired_ml,
      },
      {
       "id": "program-affine",
       "family": FAMILIES[2],
       "prompt": _program_prompt(
         f"Synthesize integer function f(x)={mult}*x+({offset}).",
         [{"x":x, "f_x":mult*x+offset} for x in (-2, 1, 4)]),
       "gold": ("affine", mult, offset),
      },
      {
       "id": "program-square",
       "family": FAMILIES[2],
       "prompt": _program_prompt(
         f"Synthesize integer function f(x)=(x+({shift}))^2+({after}).",
         [{"x":x, "f_x":(x+shift)**2+after} for x in (-3, 0, 5)]),
       "gold": ("square", shift, after),
      },
    ]
    return tasks


def _public_cases(seed):
    return [{"id":t["id"], "family":t["family"], "prompt":t["prompt"],
             "response_type":"arithmetic_json_program" if t["family"]==FAMILIES[2]
                             else "numeric_json_answer"}
            for t in _cases(seed)]


def prepare(seed):
    tasks = _public_cases(seed)
    return {
        "schema": SCHEMA,
        "generator_version": 1,
        "seed": seed,
        "tasks": tasks,
        "task_count": len(tasks),
        "model_answer_key_exposed": False,
        "heldout_program_inputs_exposed": False,
        "public_synthetic_questions_only": True,
        "confidential_data_used": False,
        "automatic_model_deployment": False,
        "claim_AGI": False,
    }


def _check_manifest(manifest, seed):
    if (not isinstance(manifest, dict) or manifest != prepare(_seed(seed))
            or len(manifest["tasks"]) != 6
            or [x["family"] for x in manifest["tasks"]] !=
               [FAMILIES[0]]*2+[FAMILIES[1]]*2+[FAMILIES[2]]*2):
        raise ValueError("Task manifest changed or answer key exposed")
    return manifest["tasks"]


def parse_response(text, kind):
    """Parse inert model output; no eval/exec, imports, SQL, external actions."""
    if not isinstance(text, str) or len(text) > MAX_RESPONSE_CHARS:
        return {"status":"invalid_or_oversized_response", "parsed":None}
    raw = text.strip()
    try:
        obj = json.loads(raw)
    except (ValueError,TypeError):
        return {"status":"invalid_json", "parsed":None}
    if kind == "numeric_json_answer":
        if (not isinstance(obj,dict) or set(obj) != {"answer"}
                or type(obj["answer"]) not in (float,int)
                or not math.isfinite(obj["answer"])
                or abs(obj["answer"]) > 10**12):
            return {"status":"invalid_numeric_response", "parsed":None}
        return {"status":"valid","parsed":float(obj["answer"])}
    if kind == "arithmetic_json_program":
        if not isinstance(obj,dict) or set(obj)!={"ops"} or not isinstance(obj["ops"],list):
            return {"status":"invalid_program_schema","parsed":None}
        seq=obj["ops"]
        if not 1 <= len(seq) <= MAX_OPERATIONS:
            return {"status":"invalid_program_length","parsed":None}
        for op in seq:
            if not isinstance(op,dict) or op.get("op") not in OPS:
                return {"status":"unapproved_program_instruction","parsed":None}
            if op["op"]=="square":
                if set(op)!={"op"}:
                    return {"status":"invalid_square_instruction","parsed":None}
            elif (set(op)!={"op","value"} or type(op["value"]) is not int
                  or not -99<=op["value"]<=99):
                return {"status":"invalid_program_argument","parsed":None}
        return {"status":"valid","parsed":seq}
    raise ValueError("Unknown task response type")


def interpret(program, x):
    """Pure bounded arithmetic interpreter; never execute generated code."""
    if type(x) is not int or not -1000 <= x <= 1000:
        raise ValueError("Invalid test input")
    current=x
    for step in program:
        if step["op"]=="add":
            current+=step["value"]
        elif step["op"]=="mul":
            current*=step["value"]
        elif step["op"]=="square":
            current*=current
        else:
            raise ValueError("Unapproved arithmetic operation")
        if abs(current)>1_000_000_000:
            raise ValueError("Output magnitude cap exceeded")
    return current


def _hidden_inputs(seed):
    rng=random.Random(_seed(seed) ^ 0x3AD7C0DE)
    # Inputs beyond public examples, plus boundary, zero and negative cases.
    random_inputs=[rng.randint(-40,40) for _ in range(18)]
    return tuple(PROGRAM_INPUTS)+tuple(random_inputs)


def _gold_value(spec,x):
    if spec[0]=="affine":return spec[1]*x+spec[2]
    if spec[0]=="square":return (x+spec[1])**2+spec[2]
    raise ValueError("Unknown reference program")


def _evaluate(one_task, response, seed):
    parsed=parse_response(response,one_task["response_type"])
    result={"status":parsed["status"], "correct":False,
            "hidden_program_cases_passed":0,"hidden_program_cases":0}
    if parsed["parsed"] is None:
        return result
    reference=next(t for t in _cases(seed) if t["id"]==one_task["id"])
    if one_task["response_type"]=="numeric_json_answer":
        actual=parsed["parsed"]
        expected=reference["gold"]
        # Real physics values permit a maximum 0.05% relative error.
        rtol=0.0005 if one_task["family"]==FAMILIES[1] else 1e-10
        result["correct"]=math.isclose(actual,expected,rel_tol=rtol,abs_tol=1e-8)
        result["response_numeric_value"]=actual
        result["reference_numeric_value"]=expected
    else:
        samples=_hidden_inputs(seed)
        result["hidden_program_cases"]=len(samples)
        checks=[]
        for x in samples:
            try:
                checks.append(interpret(parsed["parsed"],x)==_gold_value(reference["gold"],x))
            except (ValueError,OverflowError):
                checks.append(False)
        result["hidden_program_cases_passed"]=sum(checks)
        result["correct"]=all(checks)
    return result


def propose(manifest, *, model_id, revision, generate):
    tasks=_check_manifest(manifest, manifest.get("seed"))
    if (model_id not in MODEL_PINS or revision!=MODEL_PINS[model_id]
            or not callable(generate)):
        raise ValueError("Unknown model or mutable model revision")
    started=time.monotonic()
    records=[]
    for task in tasks:
        begin=time.monotonic()
        answer=generate(task["prompt"])
        elapsed=round(time.monotonic()-begin,4)
        if not isinstance(answer,str):
            raise ValueError("Model inference did not return text")
        if len(answer)>MAX_RESPONSE_CHARS:
            # Retain a digest for investigation, not a fabricated answer.
            records.append({"task_id":task["id"],"response":None,
                "rejected_oversized":True,"response_sha256":sha256(answer.encode()).hexdigest(),
                "inference_seconds":elapsed})
        else:
            records.append({"task_id":task["id"],"response":answer,
                "rejected_oversized":False,"response_sha256":sha256(answer.encode()).hexdigest(),
                "inference_seconds":elapsed})
    return {"schema":SCHEMA,"model_id":model_id,"revision":revision,
            "manifest_sha256":digest(manifest),
            "tasks_attempted":len(records),"records":records,
            "elapsed_seconds":round(time.monotonic()-started,4),
            "solutions_observed":False,"program_holdouts_evaluated":False,
            "model_promoted":False,"AGI_demonstrated":False}


def _check_proposal(result, manifest, model_id):
    if (not isinstance(result,dict) or result.get("schema")!=SCHEMA
        or result.get("model_id")!=model_id
        or result.get("revision")!=MODEL_PINS[model_id]
        or result.get("manifest_sha256")!=digest(manifest)
        or result.get("tasks_attempted")!=len(manifest["tasks"])
        or result.get("solutions_observed") is not False
        or result.get("program_holdouts_evaluated") is not False
        or result.get("model_promoted") is not False
        or result.get("AGI_demonstrated") is not False):
        raise ValueError("Unrecognized model provenance or pre-tested response")
    records=result.get("records")
    if (not isinstance(records,list) or
        [x.get("task_id") for x in records] != [x["id"] for x in manifest["tasks"]]):
        raise ValueError("Model question identities or order altered")
    for r in records:
        answer=r.get("response")
        if ((answer is not None and (not isinstance(answer,str) or len(answer)>MAX_RESPONSE_CHARS))
            or (answer is None and r.get("rejected_oversized") is not True)
            or (answer is not None and r.get("rejected_oversized") is not False)
            or (answer is not None and sha256(answer.encode()).hexdigest()!=r.get("response_sha256"))
            or type(r.get("inference_seconds")) not in (int,float)
            or not 0<=r["inference_seconds"]<=3600):
            raise ValueError("Model response or runtime was changed")
    if type(result.get("elapsed_seconds")) not in (int,float) or not 0<=result["elapsed_seconds"]<=36000:
        raise ValueError("Model runtime invalid")


def audit(manifest, proposals):
    seed=manifest.get("seed")
    tasks=_check_manifest(manifest, seed)
    if (not isinstance(proposals,dict) or
        set(proposals)!=set(MODEL_PINS)):
        raise ValueError("Both independently weighted models required")
    for model_id,report in proposals.items():
        _check_proposal(report,manifest,model_id)
    outcomes={}
    for model_id,report in proposals.items():
        evaluations=[]
        for task,rec in zip(tasks,report["records"]):
            result=_evaluate(task,rec["response"],seed)
            evaluations.append({"task_id":task["id"],"family":task["family"],
                                **result,
                                "inference_seconds":rec["inference_seconds"]})
        tally={family:{"correct":sum(r["correct"] for r in evaluations if r["family"]==family),
                       "total":sum(r["family"]==family for r in evaluations)}
               for family in FAMILIES}
        outcomes[model_id]={
            "model_revision":report["revision"],
            "correct":sum(x["correct"] for x in evaluations),
            "valid_json_schema":sum(x["status"]=="valid" for x in evaluations),
            "attempted":len(evaluations),
            "domain_scores":tally,
            "inference_calls":len(evaluations),
            "total_inference_seconds":report["elapsed_seconds"],
            "evaluations":evaluations,
        }
    return {"schema":AUDIT_SCHEMA,"seed":seed,
        "manifest_sha256":digest(manifest),
        "proposal_digests":{m:digest(r) for m,r in proposals.items()},
        "models":outcomes,"tasks_per_model":len(tasks),
        "total_model_calls":sum(x["inference_calls"] for x in outcomes.values()),
        "heldout_program_cases_generated_only_by_auditor":True,
        "independent_reference_calculations":True,
        "model_generated_code_executed":False,
        "cost_measured_as_runtime_not_dollars":True,
        "auto_model_promotion":False,
        "recursive_self_improvement_proven":False,
        "AGI_demonstrated":False,
        "scientific_discovery_verified":False,
        "limitations":"Six generated textbook-style problems across three families; "
          "not open-world science, not a standard AGI examination, "
          "and not enough trials to establish general competence. "
          "Program synthesis uses a tiny bounded arithmetic DSL."}


def save(path,data):
    p=Path(path)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+"\n",
                 encoding="utf-8")


def main():
    cli=argparse.ArgumentParser(description="Small independently audited AGI capability laboratory")
    sub=cli.add_subparsers(dest="command",required=True)
    p=sub.add_parser("prepare")
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--out",required=True)
    p=sub.add_parser("propose")
    p.add_argument("--model",choices=tuple(MODEL_PINS),required=True)
    p.add_argument("--manifest",required=True)
    p.add_argument("--out",required=True)
    p=sub.add_parser("audit")
    p.add_argument("--manifest",required=True)
    p.add_argument("--qwen",required=True)
    p.add_argument("--critic",required=True)
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--out",required=True)
    args=cli.parse_args()
    if args.command=="prepare":
        report=prepare(args.seed)
        print("Prepared public questions:",len(report["tasks"]),"no answers supplied")
    elif args.command=="propose":
        manifest=json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        if args.model=="Qwen/Qwen3-1.7B":
            from .model_challenge import CpuCandidate
            runtime=CpuCandidate(args.model)
            revision=runtime.revision
        else:
            from .independent_noaa_critic import SmolLM2Critic
            runtime=SmolLM2Critic()
            revision=MODEL_PINS[args.model]
        if revision!=MODEL_PINS[args.model]:
            raise ValueError("Resolved model differs from registered immutable checkpoint")
        report=propose(manifest,model_id=args.model,revision=revision,
                       generate=runtime.generate)
        print("Attempted",report["tasks_attempted"],"public tasks with",args.model)
    else:
        manifest=json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        if manifest.get("seed")!=args.seed:
            raise ValueError("Independent auditor run seed differs from preparation")
        left=json.loads(Path(args.qwen).read_text(encoding="utf-8"))
        right=json.loads(Path(args.critic).read_text(encoding="utf-8"))
        report=audit(manifest,{left["model_id"]:left,right["model_id"]:right})
        for name,score in report["models"].items():
            print(name,"correct",score["correct"],"of",score["attempted"],
                  "valid schema",score["valid_json_schema"],"of",score["attempted"],
                  "seconds",score["total_inference_seconds"])
    save(args.out,report)


if __name__=="__main__":
    main()

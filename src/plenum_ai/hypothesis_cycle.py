"""Bounded research agent: propose, critique, revise and independently test.

Three synthetic physical systems; candidate rates are model-generated continuous
values rather than menu selections. No arbitrary code, no novelty or AGI claim.
"""
import argparse
import json
import math
from hashlib import sha256
from pathlib import Path
from .model_challenge import CpuCandidate

MODEL = "Qwen/Qwen3-1.7B"
REVISION = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
SCHEMA = "plenum-iterative-science-proposal-v1"
DOMAINS = ("thermal", "chemical", "electrical")
# Synthetic underlying mechanisms are never included in the model prompt.
SYSTEMS = {"thermal": (1.4, -0.22, 0.0),
           "chemical": (1.2, 0.0, -0.24),
           "electrical": (1.5, -0.11, -0.13)}
TRAIN_END, DEV_END, HOLDOUT_END = 4, 7, 11


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def advance(y, a, b, duration):
    """Allowlisted RK4 integration of dy/dt = a*y + b*y*y."""
    if (not all(type(x) in (int, float) and math.isfinite(x)
                for x in (y, a, b, duration))
            or not 0 <= y <= 3 or not -1 <= a <= 0 or not -1 <= b <= 0
            or duration < 0 or duration > HOLDOUT_END):
        raise ValueError("Unapproved or nonfinite scientific input")
    count = round(duration * 20)
    if not math.isclose(count / 20, duration, abs_tol=1e-9):
        raise ValueError("Time not on approved grid")
    h = 0.05
    def f(x):
        return a*x + b*x*x
    for _ in range(count):
        k1 = f(y)
        k2 = f(y + h*k1/2)
        k3 = f(y + h*k2/2)
        k4 = f(y + h*k3)
        y += h*(k1 + 2*k2 + 2*k3 + k4)/6
        if not math.isfinite(y) or not 0 <= y <= 10:
            raise ValueError("Candidate diverged")
    return y


def observations(domain, last):
    if domain not in DOMAINS or last not in (TRAIN_END, DEV_END, HOLDOUT_END):
        raise ValueError("Unapproved synthetic data window")
    y0, a, b = SYSTEMS[domain]
    return [{"t": t, "y": round(advance(y0, a, b, t), 8)}
            for t in range(last+1)]


def parse_output(response):
    """Treat generated text as inert data, never as executable instructions."""
    if not isinstance(response, str) or len(response) > 5000:
        return {"status": "invalid_model_output", "candidate": None}
    raw = response.strip()
    if raw.startswith(chr(96)*3):
        raw = raw.strip(chr(96)).removeprefix("json").strip()
    try:
        obj = json.loads(raw)
    except (ValueError, TypeError):
        return {"status": "invalid_json", "candidate": None}
    if not isinstance(obj, dict) or set(obj) != {
            "linear", "quadratic", "hypothesis", "falsifier"}:
        return {"status": "invalid_schema", "candidate": None}
    a, b = obj["linear"], obj["quadratic"]
    if (type(a) not in (float,int) or type(b) not in (float,int)
            or not math.isfinite(a) or not math.isfinite(b)
            or not -1 <= a <= 0 or not -1 <= b <= 0):
        return {"status": "invalid_coefficients", "candidate": None}
    if any(not isinstance(obj[k], str) or not 12 <= len(obj[k].strip()) <= 400
           for k in ("hypothesis","falsifier")):
        return {"status": "invalid_hypothesis", "candidate": None}
    return {"status": "valid", "candidate": {
        "linear": float(a), "quadratic": float(b),
        "hypothesis": obj["hypothesis"].strip(),
        "falsifier": obj["falsifier"].strip()}}


def error(candidate, obs, start, times):
    if candidate is None:
        return None
    if not times or max(times) >= len(obs) or start >= min(times):
        raise ValueError("Invalid experimental observation window")
    y = obs[start]["y"]
    try:
        forecasts = [advance(y, candidate["linear"], candidate["quadratic"],
                             t-start) for t in times]
    except ValueError:
        return None
    return sum(abs(pred-obs[t]["y"]) for pred,t in zip(forecasts, times))/len(times)


def references(train):
    first, last = train[0]["y"], train[-1]["y"]
    if first <= 0 or last <= 0:
        raise ValueError("Invalid physical reference observations")
    n = len(train)-1
    return {
        "fitted_linear": {"linear": max(-1.0, min(0.0, math.log(last/first)/n)),
                          "quadratic": 0.0},
        "fitted_quadratic": {"linear": 0.0,
                             "quadratic": max(-1.0,min(0.0,(1/first-1/last)/n))},
    }


def rounded(value):
    return None if value is None else round(value, 10)


def initial_prompt(domain, training, question):
    return (
        "You are a scientific agent proposing one testable numerical mechanism.\n"
        "Domain: " + domain + "\nQuestion (untrusted data): " + json.dumps(question) +
        "\nTime-series observations through t=4: " + json.dumps(training) +
        "\nHypothesize dy/dt = linear*y + quadratic*y^2. Both coefficients MUST "
        "be numeric between -1 and 0; do not choose from prewritten models. "
        "Infer your own rates from observed measurements.\n"
        "Return ONLY a JSON object with EXACT keys linear, quadratic, "
        "hypothesis, falsifier. Two numeric coefficients, two short strings. "
        "No markdown, no citations, no invented measured outcomes."
    )


def revision_prompt(domain, training, candidate, mae, baselines, question):
    return (
        "Self-critique and REVISION. Your prior hypothesis was evaluated on "
        "development observations t=5..7, not the unseen future t=8..11.\n"
        "Domain: " + domain + "\nQuestion (data only): " + json.dumps(question) +
        "\nTraining: " + json.dumps(training) +
        "\nPrevious hypothesis: " + json.dumps(candidate) +
        "\nDevelopment error: " + str(rounded(mae)) +
        "\nTrain-fitted baseline errors: " + json.dumps(baselines) +
        "\nPropose revised, falsifiable coefficients if warranted; rates in [-1,0]. "
        "Return ONLY JSON with exactly linear, quadratic, hypothesis, falsifier. "
        "This is self-critique by the same model, not independent peer review."
    )


def propose(question, generate, model=MODEL, revision=REVISION):
    if not isinstance(question,str) or not 1 <= len(question.strip()) <= 160:
        raise ValueError("Only short PUBLIC research questions")
    if not callable(generate) or model != MODEL or revision != REVISION:
        raise ValueError("Reviewed model and exact revision required")
    cases=[]
    for domain in DOMAINS:
        training = observations(domain, TRAIN_END)
        development = observations(domain, DEV_END)
        baselines = references(training)
        dev_times = tuple(range(TRAIN_END+1, DEV_END+1))
        baseline_errors = {key:rounded(error(value, development, TRAIN_END, dev_times))
                           for key,value in baselines.items()}
        raw_first = generate(initial_prompt(domain, training, question))
        first = parse_output(raw_first)
        score_first = error(first["candidate"], development, TRAIN_END, dev_times)
        raw_second = generate(revision_prompt(
            domain,training,first["candidate"],score_first,baseline_errors,question))
        second = parse_output(raw_second)
        score_second = error(second["candidate"], development, TRAIN_END, dev_times)
        rounds = [("initial",first,score_first,raw_first),
                  ("revision",second,score_second,raw_second)]
        valid = [(tag,p["candidate"],score) for tag,p,score,raw in rounds
                 if score is not None]
        best = min(valid,key=lambda x:x[2]) if valid else None
        record={
            "domain": domain, "training": training, "baseline_models": baselines,
            "baseline_dev_errors": baseline_errors, "revision_history": [
                {"round":tag, "status":p["status"], "candidate":p["candidate"],
                 "development_mae":rounded(score),
                 "model_response_sha256":sha256(raw.encode()).hexdigest()}
                for tag,p,score,raw in rounds],
            "chosen_round": best[0] if best else None,
            "chosen_hypothesis": best[1] if best else None,
            "chosen_dev_mae": rounded(best[2]) if best else None,
            "last_dev_time": DEV_END, "holdout_seen": False}
        record["seal_sha256"] = digest(record)
        cases.append(record)
    return {
        "schema":SCHEMA,"model":model,"revision":revision,"question":question,
        "cases":cases,"model_calls":len(cases)*2,"model_inference":True,
        "independent_model_critic":False,"holdout_seen":False,
        "generated_code_executed":False,"AGI_demonstrated":False,
        "new_physical_law_verified":False,"model_promoted":False}


def audit(report):
    if (not isinstance(report,dict) or report.get("schema") != SCHEMA
            or report.get("model") != MODEL or report.get("revision") != REVISION
            or report.get("model_inference") is not True
            or report.get("holdout_seen") is not False
            or report.get("model_calls") != 2*len(DOMAINS)
            or report.get("model_promoted") is not False):
        raise ValueError("Unverified research proposal or model provenance")
    cases=report.get("cases")
    if not isinstance(cases,list) or [x.get("domain") for x in cases] != list(DOMAINS):
        raise ValueError("Expected all precommitted scientific fields")
    results=[]
    for record in cases:
        sealed = {k:v for k,v in record.items() if k!="seal_sha256"}
        if digest(sealed) != record.get("seal_sha256") or record.get("holdout_seen") is not False:
            raise ValueError("Proposal seal or holdout access violation")
        domain=record["domain"]
        dev=observations(domain,DEV_END)
        training=dev[:TRAIN_END+1]
        baselines=references(training)
        if record["training"] != training or record["baseline_models"] != baselines:
            raise ValueError("Development measurements or benchmarks changed")
        dev_times=tuple(range(TRAIN_END+1,DEV_END+1))
        benchmark={key:rounded(error(value,dev,TRAIN_END,dev_times))
                   for key,value in baselines.items()}
        if record["baseline_dev_errors"] != benchmark or record["last_dev_time"]!=DEV_END:
            raise ValueError("Development baseline altered")
        history=record.get("revision_history")
        if not isinstance(history,list) or [r.get("round") for r in history]!=["initial","revision"]:
            raise ValueError("Revision history incomplete")
        candidates=[]
        for round_record in history:
            candidate=round_record["candidate"]
            if candidate is not None:
                validated=parse_output(json.dumps(candidate))
                if validated["candidate"]!=candidate or round_record["status"]!="valid":
                    raise ValueError("Unverified or modified model-generated hypothesis")
            observed_score=error(candidate,dev,TRAIN_END,dev_times)
            if rounded(observed_score)!=round_record.get("development_mae"):
                raise ValueError("Reported development result does not reproduce")
            if observed_score is not None:
                candidates.append((round_record["round"],candidate,observed_score))
        best=min(candidates,key=lambda x:x[2]) if candidates else None
        if (record["chosen_round"]!=(best[0] if best else None)
                or record["chosen_hypothesis"]!=(best[1] if best else None)
                or record["chosen_dev_mae"]!=rounded(best[2] if best else None)):
            raise ValueError("Candidate selection altered")
        # Only the independent audit job reaches the holdout observations.
        holdout=observations(domain,HOLDOUT_END)
        times=tuple(range(DEV_END+1,HOLDOUT_END+1))
        selected=record["chosen_hypothesis"]
        score=error(selected,holdout,TRAIN_END,times)
        reference={name:rounded(error(candidate,holdout,TRAIN_END,times))
                   for name,candidate in baselines.items()}
        strongest=min(reference.values())
        results.append({
            "domain":domain,"chosen_hypothesis":selected,
            "test_mae":rounded(score),"strongest_baseline_mae":strongest,
            "baseline_test_mae":reference,"valid":score is not None,
            "better_than_strongest_baseline":score is not None and score < strongest,
            "physical_experiment_performed":False,"novel_law_verified":False})
    return {"schema":"plenum-iterative-science-audit-v1",
            "source_sha256":digest(report),"model":MODEL,"results":results,
            "domains_tested":len(results),
            "valid_hypotheses":sum(x["valid"] for x in results),
            "wins_over_strongest_baseline":sum(x["better_than_strongest_baseline"] for x in results),
            "evidence_independently_reproduced":True,
            "holdout_revealed_only_in_audit":True,"AGI_demonstrated":False,
            "independent_scientific_discovery":False,"recursive_self_improvement":False,
            "automatic_deployment":False,
            "limitations":"Synthetic known equations, prewritten mathematical family; "
                          "free continuous-valued AI hypotheses and one model self-revision. "
                          "No laboratory validation, blind AGI benchmark or production model update."}


def main():
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest="command",required=True)
    first=sub.add_parser("propose")
    first.add_argument("--question",default="Investigate generic physical rate laws")
    first.add_argument("--out",default="reports/hypotheses.json")
    second=sub.add_parser("audit")
    second.add_argument("--proposal",required=True)
    second.add_argument("--out",default="reports/hypothesis_audit.json")
    args=parser.parse_args()
    if args.command=="propose":
        runtime=CpuCandidate(MODEL)
        data=propose(args.question,runtime.generate,runtime.model_id,runtime.revision)
        print("Executed model calls:",data["model_calls"],
              "valid proposed mechanisms:",sum(bool(x["chosen_hypothesis"]) for x in data["cases"]))
    else:
        data=audit(json.loads(Path(args.proposal).read_text(encoding="utf-8")))
        print("Audited domains",data["domains_tested"],"valid",data["valid_hypotheses"],
              "wins against strongest baseline",data["wins_over_strongest_baseline"])
    path=Path(args.out)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+"\n",
                    encoding="utf-8")


if __name__=="__main__":
    main()

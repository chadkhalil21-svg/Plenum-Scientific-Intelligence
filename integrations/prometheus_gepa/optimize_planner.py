"""Bounded upstream GEPA qualification on the original Minister planner.

No owner mission is replayed. Only public synthetic capability selections are
scored. Existing authority, graph validation and tool execution remain unchanged.
"""
import json
import os
import sys
from pathlib import Path
from importlib.metadata import version
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "paperclip"))
import model_plan as mp
import variable_mission as vm
from checkpoint_store import exclusive
from gepa import optimize
from gepa.core.adapter import EvaluationBatch

VERSION = "0.1.4"
MAX_CALLS = 32
SEED = {"guidance": "Preserve the original objective and authorization boundaries."}
INPUTS = {"stations": ["8723214"], "bibliography": ["10.1145/3442188.3445922"],
          "thermal": {"initial_kelvin": 352, "ambient_kelvin": 297, "rate": .04, "duration": 18},
          "commercial": True}
# New disjoint synthetic cases, not the SkillOpt corpus or owner assignments.
CASES = (
    ("train", "a", "Estimate the temperature after cooling and confirm the DOI record.", ["thermal","bibliography"]),
    ("train", "b", "Check the station identifier and whether the public American Rider site responds.", ["stations","commercial"]),
    ("train", "c", "Establish the literature metadata alone, without a numerical forecast.", ["bibliography"]),
    ("val", "d", "Determine the NOAA station coordinates and predict the final cooling temperature.", ["stations","thermal"]),
    ("val", "e", "Assess the public endpoint and identify the cited scholarly publication.", ["commercial","bibliography"]),
    ("val", "f", "Calculate only the final temperature and independently check the calculation.", ["thermal"]),
    ("test", "g", "Confirm the station location and the published citation, with no website assessment.", ["stations","bibliography"]),
    ("test", "h", "Prepare a brief about public service availability and the projected temperature.", ["commercial","thermal"]),
    ("test", "i", "Identify only the NOAA station metadata and confirm it independently.", ["stations"]),
)

def corpus():
    groups = {"train": [], "val": [], "test": []}
    for split, key, objective, required in CASES:
        mission = vm.validate({"objective": objective, "authorized_inputs": INPUTS})
        groups[split].append({"id": key, "mission": mission,
                              "expected": {k: k in required for k in sorted(INPUTS)}})
    return groups

def unique(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError("Duplicate field")
        out[k] = v
    return out

class Local:
    def __init__(self, root, md):
        self.root, self.md, self.cache = root, md, {}
        self.calls = 0
        self.reflections = 0

    def infer(self, request, stage):
        digest = mp.digest(request)
        if digest in self.cache:
            return self.cache[digest]
        if self.calls >= MAX_CALLS:
            raise RuntimeError("Local inference ceiling")
        self.calls += 1
        label = f"call-{self.calls:02d}"
        row = {"stage": stage, "request_sha256": digest,
               "model_digest": self.md, "paid_inference": False}
        exclusive(self.root / (label + ".reserved.json"), row)
        reply = mp.read_json("/api/chat", request, timeout=180)
        raw = reply.get("message", {}).get("content")
        n = reply.get("eval_count")
        p = reply.get("prompt_eval_count")
        if (reply.get("model") != mp.MODEL or reply.get("done") is not True
                or reply.get("done_reason") != "stop" or not isinstance(raw, str)
                or not raw.strip() or len(raw) > 12000
                or type(n) is not int or not 0 < n <= request["options"]["num_predict"]
                or type(p) is not int or not 0 < p <= request["options"]["num_ctx"]):
            raise ValueError("Incomplete model reply")
        exclusive(self.root / (label + ".result.json"), {**row,
                  "response_sha256": mp.digest(raw), "eval_count": n, "prompt_eval_count": p})
        self.cache[digest] = raw
        self.reflections += int(stage == "reflection")
        return raw

    def reflect(self, prompt):
        if not isinstance(prompt, str) or len(prompt) > 20000:
            raise ValueError("Reflection prompt bound")
        req = {"model": mp.MODEL, "stream": False, "think": False,
               "options": {"temperature": 0, "num_ctx": 4096, "num_predict": 768},
               "messages": [{"role": "system", "content":
                   "Improve only reusable advisory capability-selection guidance. Preserve existing authority and output schema. Never encode specific answers or expand scope."},
                   {"role": "user", "content": prompt}]}
        return self.infer(req, "reflection")

class Adapter:
    def __init__(self, local):
        self.local = local

    def evaluate(self, batch, candidate, capture_traces=False):
        if set(candidate) != {"guidance"} or not isinstance(candidate["guidance"], str) or len(candidate["guidance"]) > 2500:
            raise ValueError("Candidate scope")
        outputs, scores, traces = [], [], []
        for item in batch:
            req = vm.request(item["mission"])
            if candidate != SEED:
                req["messages"][0]["content"] += " Advisory planning guidance only: " + candidate["guidance"]
            raw = self.local.infer(req, "selection")
            try:
                selected = json.loads(raw, object_pairs_hook=unique)
                vm.graph(item["mission"], selected)
                score = float(selected == item["expected"])
            except (ValueError, TypeError, KeyError):
                score = 0.0
                selected = None
            outputs.append(selected)
            scores.append(score)
            traces.append({"Inputs": {"objective": item["mission"]["objective"],
                         "available_capabilities": sorted(INPUTS)},
                           "Generated Outputs": selected,
                           "Feedback": "Exact required selection: " + json.dumps(item["expected"], sort_keys=True)})
        return EvaluationBatch(outputs=outputs, scores=scores,
                               trajectories=traces if capture_traces else None)

    def make_reflective_dataset(self, candidate, eval_batch, components_to_update):
        if components_to_update != ["guidance"]:
            raise ValueError("Unknown optimization component")
        return {"guidance": eval_batch.trajectories}

def main():
    if os.getenv("GITHUB_ACTIONS") != "true" or version("gepa") != VERSION:
        raise PermissionError("Pinned public development runner only")
    for key in ("OPENAI_API_KEY","ANTHROPIC_API_KEY","GOOGLE_API_KEY","AZURE_OPENAI_API_KEY","HF_TOKEN","OLLAMA_API_KEY"):
        if os.getenv(key):
            raise PermissionError("External credential prohibited")
    root = Path(sys.argv[1])
    root.mkdir(mode=0o700, exist_ok=False)
    groups = corpus()
    md = mp.check_local_model()
    exclusive(root / "binding.json", {"model_digest": md, "gepa": VERSION,
              "corpus_sha256": mp.digest(groups), "paid_inference": False,
              "synthetic_development_only": True})
    local = Local(root, md)
    adapter = Adapter(local)
    result = optimize(seed_candidate=SEED, trainset=groups["train"], valset=groups["val"],
                      adapter=adapter, reflection_lm=local.reflect,
                      max_metric_calls=18, reflection_minibatch_size=2,
                      use_merge=False, seed=0, raise_on_exception=True)
    best = result.best_candidate
    def grade(split, candidate):
        rows = groups[split]
        run = adapter.evaluate(rows, candidate)
        return {row["id"]: {"selection": output, "score": score}
                for row, output, score in zip(rows, run.outputs, run.scores)}
    base_val, best_val = grade("val", SEED), grade("val", best)
    base_test, best_test = grade("test", SEED), grade("test", best)
    def total(rows):
        return sum(r["score"] for r in rows.values())
    improved = (best != SEED and local.reflections > 0
                and total(best_val) > total(base_val) and total(best_test) > total(base_test)
                and all(best_test[k]["score"] >= base_test[k]["score"] for k in base_test))
    exclusive(root / "outcome.json", {"validation_baseline": base_val, "validation_candidate": best_val,
              "test_baseline": base_test, "test_candidate": best_test, "candidate_improved": improved,
              "candidate_changed": best != SEED, "model_calls": local.calls,
              "reflection_calls": local.reflections, "model_calls_replayed": 0, "paid_inference": False,
              "automatic_adoption": False, "general_autonomy_verified": False})
    if improved:
        exclusive(root / "candidate.json", best)

if __name__ == "__main__":
    main()

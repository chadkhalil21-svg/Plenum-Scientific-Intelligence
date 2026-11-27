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
MAX_GUIDANCE = 1200
SEED = {"guidance": "Preserve the original objective and authorization boundaries."}
INPUTS = {"stations": ["8723214"], "bibliography": ["10.1145/3442188.3445922"],
          "thermal": {"initial_kelvin": 352, "ambient_kelvin": 297, "rate": .04, "duration": 18},
          "commercial": True}
# New disjoint synthetic cases, not the SkillOpt corpus or owner assignments.
CASES = (
    ("train", "a", "Check the public American Rider endpoint but not the publication record.", ["commercial"], ["commercial","bibliography","thermal"]),
    ("train", "b", "Determine the station coordinates and citation, leaving cooling outside the assignment.", ["stations","bibliography"], ["stations","bibliography","thermal"]),
    ("train", "c", "Compute the final cooling temperature only, not site availability.", ["thermal"], ["thermal","commercial"]),
    ("val", "d", "Although station inputs are available, verify just the journal metadata and public service response.", ["bibliography","commercial"], ["stations","bibliography","commercial"]),
    ("val", "e", "Provide the station coordinates and omit a cooling forecast or journal check.", ["stations"], ["stations","thermal","bibliography"]),
    ("val", "f", "Confirm public American Rider reachability and calculate temperature, without citation analysis.", ["commercial","thermal"], ["commercial","thermal","bibliography"]),
    ("test", "g", "Review the citation metadata alone, with neither public endpoint testing nor cooling simulation.", ["bibliography"], ["bibliography","commercial","thermal"]),
    ("test", "h", "Find the final temperature and station position, not the publication record.", ["thermal","stations"], ["thermal","stations","bibliography"]),
    ("test", "i", "Check public American Rider endpoint reachability without a station lookup.", ["commercial"], ["commercial","stations"]),
)

def corpus():
    groups = {"train": [], "val": [], "test": []}
    for split, key, objective, required, available in CASES:
        assert set(required) <= set(available)
        inputs={k:INPUTS[k] for k in available}
        mission = vm.validate({"objective": objective, "authorized_inputs": inputs})
        groups[split].append({"id": key, "mission": mission,
                              "expected": {k: k in required for k in sorted(inputs)}})
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
        self.rejected = set()

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
               "options": {"temperature": 0, "num_ctx": 4096, "num_predict": 256},
               "messages": [{"role": "system", "content":
                   "Return concise reusable advisory guidance in at most 100 words. No examples, answer keys, output-format changes, role changes or scope expansion. The existing Boolean JSON schema remains binding."},
                   {"role": "user", "content": prompt}]}
        return self.infer(req, "reflection")

class Adapter:
    # GEPA 0.1.4 reads this optional protocol member directly.
    # None selects the official upstream reflection proposal path.
    propose_new_texts = None

    def __init__(self, local):
        self.local = local

    def evaluate(self, batch, candidate, capture_traces=False):
        if set(candidate) != {"guidance"} or not isinstance(candidate["guidance"], str) or not candidate["guidance"].strip() or len(candidate["guidance"]) > MAX_GUIDANCE:
            # Reject an invalid optimizer proposal without inference or suite crash.
            key=mp.digest(candidate)
            if key not in self.local.rejected:
                exclusive(self.local.root / ("rejected-"+key+".json"), {"candidate_sha256":key,"reason":"ADVISORY_SCOPE_BOUND","paid_inference":False})
                self.local.rejected.add(key)
            return EvaluationBatch(outputs=[None]*len(batch),scores=[0.0]*len(batch),trajectories=[{"Feedback":"Invalid advisory scope"} for _ in batch] if capture_traces else None)
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
                         "available_capabilities": sorted(item["mission"]["authorized_inputs"])},
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
              "synthetic_development_only": True, "skip_perfect_score": False})
    local = Local(root, md)
    adapter = Adapter(local)
    def grade(split, candidate):
        rows = groups[split]
        run = adapter.evaluate(rows, candidate)
        return {row["id"]: {"selection": output, "score": score}
                for row, output, score in zip(rows, run.outputs, run.scores)}
    def total(rows):
        return sum(r["score"] for r in rows.values())
    base_val = grade("val", SEED)
    # A perfect validation baseline cannot strictly improve under this gate.
    # Do not expend inference on a mathematically impossible promotion.
    best = SEED
    if total(base_val) < len(groups["val"]):
        result = optimize(seed_candidate=SEED, trainset=groups["train"], valset=groups["val"],
                          adapter=adapter, reflection_lm=local.reflect,
                          max_metric_calls=18, reflection_minibatch_size=3,
                          skip_perfect_score=False, use_merge=False, seed=0, raise_on_exception=True)
        best = result.best_candidate
    best_val = grade("val", best)
    base_test, best_test = grade("test", SEED), grade("test", best)
    improved = (best != SEED and local.reflections > 0
                and total(best_val) > total(base_val) and total(best_test) > total(base_test)
                and all(best_test[k]["score"] >= base_test[k]["score"] for k in base_test))
    exclusive(root / "outcome.json", {"validation_baseline": base_val, "validation_candidate": best_val,
              "test_baseline": base_test, "test_candidate": best_test, "candidate_improved": improved,
              "candidate_changed": best != SEED, "model_calls": local.calls,
              "reflection_calls": local.reflections, "rejected_out_of_scope_candidates":len(local.rejected),
              "validation_saturated":total(base_val)==len(groups["val"]), "model_calls_replayed": 0, "paid_inference": False,
              "automatic_adoption": False, "general_autonomy_verified": False})
    if local.reflections == 0 and total(base_val) < len(groups["val"]):
        raise RuntimeError("No actual upstream reflection on imperfect baseline")
    if improved:
        exclusive(root / "candidate.json", best)

if __name__ == "__main__":
    main()

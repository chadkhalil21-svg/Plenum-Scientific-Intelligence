"""Generate a quarantined engineering skill from real original mission failures.

Reuse upstream SkillOpt-Sleep reflection and bounded edit application. This
is learning-candidate generation, NOT admission, model training, or evidence
of improved performance. No original owner task is replayed.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile
from importlib.metadata import version

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "paperclip"))
import model_plan as mp
from checkpoint_store import exclusive
from skillopt_sleep.backend import CliBackend
from skillopt_sleep.memory import apply_edits
from skillopt_sleep.types import TaskRecord, ReplayResult

SEED = "Inspect relevant source, implement an authorized repair, test and refine it, and submit a review-only patch."
ARCHIVES = {
    "first": ("a4190790a727d212d305a5eceebf670fea64a17f6de817ee046a8679c84399a3", 15230648247),
    "continuation": ("d197363c3b62a5593a91cd43269f09027485b4531b9c8dde88cc362bfc86604e", 15232100681),
}

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def open_bound(path, kind):
    expected, _ = ARCHIVES[kind]
    if (path.is_symlink() or not path.is_file()
            or not 0 < path.stat().st_size <= 2_000_000
            or sha(path.read_bytes()) != expected):
        raise ValueError("Untrusted original evidence")
    z = zipfile.ZipFile(path)
    if (len(z.namelist()) != len(set(z.namelist()))
            or sum(i.file_size for i in z.infolist()) > 4_000_000
            or z.testzip() is not None):
        z.close()
        raise ValueError("Invalid archived evidence")
    return z

def historical_failures(first, continuation):
    with open_bound(first, "first") as z:
        r = json.loads(z.read("miniswe-1040/native-result.json"))
        t = json.loads(z.read("miniswe-1040/trajectory.json"))
        calls = [json.loads(x) for x in z.read("miniswe-1040/model-reservations.jsonl").splitlines()]
        results = [json.loads(x) for x in z.read("miniswe-1040/model-responses.jsonl").splitlines()]
        commands = [a["command"] for m in t["messages"] if m.get("role") == "assistant"
                    for a in m.get("extra", {}).get("actions", [])]
        prior = {x["request_sha256"] for x in calls}
        if (r["issue"] != 1040 or r["exit_status"] != "LimitsExceeded"
                or r["paid_inference"] is not False or r["native_agent_calls"] != 12
                or r["baseline_passed"] is not True or len(commands) != 12
                or len(calls) != 12 or len(results) != 12 or len(prior) != 12
                or {x["request_sha256"] for x in results} != prior
                or sha(json.dumps(commands, ensure_ascii=True, separators=(",", ":")).encode())
                   != "aaefa76db6028a95deb37e7f6becc8c761e1e04c66f1d7133d745ef86d15b819"):
            raise ValueError("Original inspection failure changed")
    with open_bound(continuation, "continuation") as z:
        prefix = "miniswe-1040-continuation/"
        binding = json.loads(z.read(prefix + "continuation-binding.json"))
        calls2 = [json.loads(x) for x in z.read(prefix + "model-reservations.jsonl").splitlines()]
        t2 = json.loads(z.read(prefix + "trajectory.json"))
        if (binding["original_run"] != 46065445035
                or binding["original_archive_sha256"] != ARCHIVES["first"][0]
                or binding["original_calls_replayed"] is not False
                or len(calls2) != 1 or calls2[0]["request_sha256"] in prior
                or prefix+"model-responses.jsonl" in z.namelist()
                or any(m.get("role") == "assistant" for m in t2["messages"])
                or t2["messages"][-1].get("extra",{}).get("exit_status") != "APITimeoutError"):
            raise ValueError("Original timeout evidence changed")
    # Derived factual observations only. Never include raw tool output,
    # code, or model-supplied instructions in the optimizer prompt.
    cases = [
        ("1040-original", "Complete a genuine authorized source repair with independent tests.",
         "Twelve answered inspection calls; no edit, test-driven correction, or submission.",
         "Execution budget exhausted before any repair."),
        ("1040-continuation", "Resume a genuine source repair using earlier inspection evidence.",
         "Full-source context supplied; one distinct inference reservation; no response or action.",
         "Inference timeout before tool execution; no patch or independent acceptance."),
    ]
    failures = []
    for key, intent, observed, why in cases:
        task = TaskRecord(id=key, project="Prometheus", intent=intent,
                          outcome="fail", split="train", origin="real",
                          source_sessions=[key], tags=["actual-engineering"])
        replay = ReplayResult(id=key, hard=0, soft=0, response=observed, fail_reason=why)
        failures.append((task, replay))
    return failures, prior | {calls2[0]["request_sha256"]}

class LocalReflect(CliBackend):
    def __init__(self, root, digest, forbidden):
        super().__init__(model=mp.MODEL)
        self.root, self.md, self.forbidden, self.seen = root, digest, forbidden, set()
        self.preferences = ("General engineering advice only. No specific file, solution, commands, "
                            "authority changes, hidden test knowledge, or extra paid resources. "
                            "Prefer bounded context and concrete progress within available inference.")

    def _call(self, prompt, *, max_tokens=1024):
        req = {"model": mp.MODEL, "stream": False, "think": False,
               "options": {"temperature": 0, "num_ctx": 4096, "num_predict": min(384,max_tokens)},
               "messages": [{"role":"system","content":"Return bounded reusable advisory skill edits only. Preserve existing security and review requirements."},
                            {"role":"user","content":prompt}]}
        key = mp.digest(req)
        if key in self.seen or key in self.forbidden or len(self.seen) >= 2 or len(prompt)>14000:
            raise RuntimeError("Unbounded or duplicate reflection")
        self.seen.add(key)
        label = self.root / f"reflection-{len(self.seen)}"
        receipt = {"request_sha256":key,"model_digest":self.md,"paid_inference":False}
        exclusive(label.with_suffix(".reserved.json"),receipt)
        reply = mp.read_json("/api/chat",req,timeout=180)
        raw = reply.get("message",{}).get("content")
        if (reply.get("model")!=mp.MODEL or reply.get("done") is not True
                or not isinstance(raw,str) or not raw.strip() or len(raw)>5000):
            raise ValueError("Invalid reflection response")
        exclusive(label.with_suffix(".result.json"),{**receipt,"response_sha256":sha(raw.encode()),
                  "eval_count":reply.get("eval_count"),"prompt_eval_count":reply.get("prompt_eval_count")})
        return raw

def main():
    if os.getenv("GITHUB_ACTIONS")!="true" or version("skillopt")!="0.2.0":
        raise PermissionError("Pinned original public runner only")
    for key in ("OPENAI_API_KEY","ANTHROPIC_API_KEY","AZURE_OPENAI_API_KEY","GOOGLE_API_KEY","HF_TOKEN","OLLAMA_API_KEY"):
        if os.getenv(key):
            raise PermissionError("External credentials prohibited")
    first, second, dest = map(Path,sys.argv[1:])
    failures, prior = historical_failures(first,second)
    dest.mkdir(parents=True,exist_ok=False)
    md = mp.check_local_model()
    backend = LocalReflect(dest,md,prior)
    exclusive(dest/"training-binding.json",{"archive_ids":[15230648247,15232100681],
        "archive_sha256":[ARCHIVES[x][0] for x in ("first","continuation")],
        "historical_missions":1,"historical_failure_phases":2,"historical_requests":13,
        "historical_requests_replayed":0,"skillopt":"0.2.0","reflection_model_digest":md,
        "training_observations":[{"task":t.to_dict(),"outcome":r.to_dict()} for t,r in failures],
        "paid_inference":False})
    edits = backend.reflect(failures,[],SEED,"",edit_budget=2,evolve_skill=True,evolve_memory=False)
    # Stage only short additions; do not allow removal of incumbent guidance
    # or activation merely because an optimizer returned an edit.
    admissible = [e for e in edits if e.target=="skill" and e.op=="add"
                  and 0 < len(e.content) <= 320 and "\n" not in e.content
                  and not any(c in e.content for c in ("<",">","\x00","\x1b"))]
    candidate, applied = apply_edits(SEED,admissible)
    if candidate != SEED and applied and len(candidate)<=1200:
        exclusive(dest/"quarantined-skill.json",{"guidance":candidate,
            "sha256":sha(candidate.encode()),"admitted":False,"production_active":False,
            "requires":"prospective real engineering outcome improvement and no regression"})
    exclusive(dest/"outcome.json",{"historical_failure_phases":2,
        "upstream_reflection_calls":len(backend.seen),"proposed_edits":len(edits),
        "staged_edits":len(applied),"candidate_created":candidate!=SEED and bool(applied) and len(candidate)<=1200,
        "heldout_evaluated":False,"improvement_demonstrated":False,"admitted":False,
        "historical_requests_replayed":0,"paid_inference":False})

if __name__=="__main__":
    main()

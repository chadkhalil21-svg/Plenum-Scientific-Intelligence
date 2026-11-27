"""Independent native Magentic proof reader; no SDK, inference or provider calls."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"paperclip"))
import model_plan as mp
import variable_mission as vm
from checkpoint_store import checked

MODEL = "qwen3.5:9b-q4_K_M"
MODEL_PREFIX = "56671c2ab938"
VERSIONS = {
    "agent-framework-core": "1.26.0",
    "agent-framework-orchestrations": "1.4.2",
    "agent-framework-openai": "1.18.2",
    "openai": "3.60.0",
    "httpx2": "2.16.2",
}
MAX_CALLS = 12

def verify_native_plan(root, mission, commitment, identity):
    """Read the actual multi-call planning proof, not a fabricated 4B receipt."""
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Unsafe native planner evidence")
    binding = checked(root / "binding.json", {})
    md = binding.get("model_digest")
    if not isinstance(md, str):
        raise ValueError("Missing model digest")
    raw = md.removeprefix("sha256:")
    if len(raw) != 64 or not raw.startswith(MODEL_PREFIX) or any(c not in "0123456789abcdef" for c in raw):
        raise ValueError("Unexpected native model digest")
    if binding != {"mission_sha256":mp.digest(mission),"model_digest":md,
                   "versions":VERSIONS,"paid_inference":False,"native_identity":identity}:
        raise ValueError("Native planner binding changed")
    row = checked(root / "accepted-plan.json", {})
    selection = row["selection"]
    vm.graph(mission, selection)
    if mp.digest(sorted(k for k,v in selection.items() if v)) != commitment:
        raise ValueError("Native objective commitment changed")
    n = row["model_calls"]
    if type(n) is not int or not 1 <= n <= MAX_CALLS or row != {
        "selection":selection,"model_calls":n,"model_calls_replayed":0,
        "paid_inference":False,"model_digest":md}:
        raise ValueError("Native planner result changed")
    hashes = set()
    expected = {"binding.json","accepted-plan.json"}
    for i in range(1,n+1):
        name = f"call-{i:02d}.reserved.json"
        expected.add(name)
        call = checked(root / name,{})
        h = call.get("request_sha256")
        if not isinstance(h,str) or len(h)!=64 or any(c not in "0123456789abcdef" for c in h) or h in hashes or call != {
            "request_sha256":h,"model_digest":md,"paid_inference":False}:
            raise ValueError("Native inference reservation changed")
        hashes.add(h)
    if {p.name for p in root.iterdir()} != expected:
        raise ValueError("Unexpected native planning evidence")
    return row


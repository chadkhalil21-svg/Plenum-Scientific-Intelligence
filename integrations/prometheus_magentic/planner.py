"""Candidate Microsoft Magentic planner for the ORIGINAL Minister.
Uses official Agent Framework orchestration, existing local model and contract graph.
No new workforce, provider credentials, arbitrary tools, or external write authority.
"""
import asyncio
import json
import os
import sys
import httpx2 as httpx
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "paperclip"))
import model_plan as mp
import variable_mission as vm
from checkpoint_store import exclusive, checked
from plenum_ai.chief_contract_plan import run_contract, check_contract_result

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
BASE = "http://127.0.0.1:11434/v1/"


def strict():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise PermissionError("Authorized public development runner only")
    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AZURE_OPENAI_API_KEY",
                "GOOGLE_API_KEY", "OLLAMA_API_KEY", "HF_TOKEN", "LANGSMITH_API_KEY"):
        if os.getenv(key):
            raise PermissionError("External provider credentials prohibited")
    os.environ["AGENT_FRAMEWORK_TELEMETRY_ENABLED"] = "false"
    os.environ["AGENT_FRAMEWORK_USER_AGENT_DISABLED"] = "true"
    if {k: version(k) for k in VERSIONS} != VERSIONS:
        raise ValueError("Unreviewed framework version")


def model_digest():
    tags = mp.read_json("/api/tags")
    found = [r.get("digest") for r in tags.get("models", []) if r.get("name") == MODEL]
    if len(found) != 1 or not isinstance(found[0], str):
        raise ValueError("Existing stronger local model unavailable")
    raw = found[0].removeprefix("sha256:")
    if len(raw) != 64 or any(c not in "0123456789abcdef" for c in raw) or not raw.startswith(MODEL_PREFIX):
        raise ValueError("Unexpected model digest")
    return found[0]


class Guard(httpx.AsyncBaseTransport):
    """Bound the actual SDK transport; reserve before inference, never resend."""
    def __init__(self, root, md):
        self.root, self.md, self.seen = root, md, set()
        self.transport = httpx.AsyncHTTPTransport(retries=0, trust_env=False)

    async def aclose(self):
        await self.transport.aclose()

    async def handle_async_request(self, request):
        if str(request.url) != BASE + "chat/completions" or request.method != "POST":
            raise PermissionError("Only local chat completion is authorized")
        raw = await request.aread()
        if len(raw) > 100_000:
            raise ValueError("Request too large")
        payload = json.loads(raw)
        if payload.get("model") != MODEL or payload.get("tools") or payload.get("functions"):
            raise PermissionError("Model or tool scope changed")
        # The upstream orchestrator owns planning, progress and replanning.
        # Bound local generation, not its choice of specialist.
        requested = payload.pop("max_completion_tokens", None) or payload.get("max_tokens") or 1024
        if type(requested) is not int or requested < 1:
            raise ValueError("Invalid requested token bound")
        payload["max_tokens"] = min(requested, 1024)
        payload["reasoning_effort"] = "none"
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        digest = sha256(raw).hexdigest()
        if digest in self.seen or len(self.seen) >= MAX_CALLS:
            raise PermissionError("Duplicate request or mission inference ceiling")
        exclusive(self.root / f"call-{len(self.seen)+1:02d}.reserved.json",
                  {"request_sha256":digest, "model_digest":self.md, "paid_inference":False})
        self.seen.add(digest)
        # Forward exactly the reserved bytes, with no redirects or retries.
        headers = request.headers.copy()
        headers["Content-Length"] = str(len(raw))
        forwarded = httpx.Request(request.method, request.url, headers=headers,
                                  content=raw, extensions=request.extensions)
        return await self.transport.handle_async_request(forwarded)


def parse_selection(text, mission):
    def unique(pairs):
        out = {}
        for k, v in pairs:
            if k in out:
                raise ValueError("Duplicate final selection")
            out[k] = v
        return out
    if not isinstance(text, str) or len(text) > 2000:
        raise ValueError("Invalid final selection")
    selection = json.loads(text, object_pairs_hook=unique)
    vm.graph(mission, selection)
    return selection


async def plan(root, mission, commitment, native_identity=None):
    """Official MagenticBuilder chooses specialists, maintains progress and replans."""
    strict()
    vm.validate(mission)
    from agent_framework import Agent
    from agent_framework.orchestrations import MagenticBuilder
    from agent_framework.openai import OpenAIChatCompletionClient
    from openai import AsyncOpenAI
    md = model_digest()
    root.mkdir(mode=0o700, parents=False, exist_ok=False)
    exclusive(root / "binding.json", {"mission_sha256":mp.digest(mission),
        "model_digest":md, "versions":VERSIONS, "paid_inference":False,
        **({"native_identity":native_identity} if native_identity is not None else {})})
    guard = Guard(root, md)
    async with httpx.AsyncClient(trust_env=False, follow_redirects=False,
                                 timeout=httpx.Timeout(240.0, connect=10.0), transport=guard) as transport:
        async with AsyncOpenAI(base_url=BASE, api_key="local-no-secret", max_retries=0,
                               http_client=transport, timeout=240.0) as sdk:
            client = OpenAIChatCompletionClient(model=MODEL, async_client=sdk)
            researcher = Agent(client=client, name="research",
                description="Reviews source and evidence requirements.",
                instructions="Identify all required evidence capabilities and their dependencies. No external calls or invented facts.")
            engineer = Agent(client=client, name="engineering",
                description="Reviews computation, constraints and verification requirements.",
                instructions="Identify required computation and independent checks. Review omissions and unnecessary actions.")
            manager = Agent(client=client, name="minister",
                description="Original Minister's upstream planning engine.",
                instructions="Choose only necessary authorized capabilities. The final response is exactly the complete Boolean JSON object, no prose or fences. Do not claim execution before tools run.")
            workflow = MagenticBuilder(participants=[researcher, engineer],
                manager_agent=manager, max_round_count=4, max_stall_count=1,
                max_reset_count=1).build()
            scope = json.loads(vm.request(mission)["messages"][1]["content"])
            schema = vm.request(mission)["format"]
            task = json.dumps({"mission":scope, "required_final_schema":schema,
                               "planning_constraint":"Use concise specialist findings and a compact final plan; avoid unnecessary discussion."},
                              sort_keys=True)
            outcome = await asyncio.wait_for(workflow.run(task), timeout=840)
            outputs = outcome.get_outputs()
            if len(outputs) != 1:
                raise ValueError("Unexpected Magentic terminal output")
            output = outputs[0]
            text = output if isinstance(output, str) else getattr(output, "text", None)
            selection = parse_selection(text, mission)
    if mp.digest(sorted(k for k, v in selection.items() if v)) != commitment:
        raise ValueError("Independent objective commitment rejected Magentic plan")
    exclusive(root / "accepted-plan.json", {"selection":selection,
        "model_calls":len(guard.seen), "model_calls_replayed":0,
        "paid_inference":False, "model_digest":md})
    return selection


def verify_native_plan(root, mission, commitment, identity):
    """Read the actual multi-call planning proof, not a fabricated 4B receipt."""
    strict()
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

def execute_native_plan(root, mission, commitment, identity):
    asyncio.run(plan(root, mission, commitment, native_identity=identity))
    return verify_native_plan(root, mission, commitment, identity)


def execute(root, mission, commitment):
    """Use existing original contract workers; no new tool implementation."""
    selection = asyncio.run(plan(root, mission, commitment))
    scope, graph = vm.graph(mission, selection)
    results = {}
    for node in graph:
        tool = node["id"]
        deps = node["depends_on"]
        inputs = {k:results[k] for k in deps}
        exclusive(root / (tool+".reserved.json"),
                  {"tool":tool, "input_sha256":mp.digest(inputs)})
        result = run_contract(tool, scope, inputs)
        check_contract_result(tool, scope, inputs, result)
        exclusive(root / (tool+".result.json"), {"result":result,
                  "result_sha256":mp.digest(result)})
        results[tool] = result
    exclusive(root / "outcome.json", {"mission_sha256":mp.digest(mission),
        "selected_capabilities":selection, "verified_contracts":len(results),
        "report_sha256":mp.digest(results["evidence_report"]),
        "paid_inference":False, "production_integrated":False,
        "general_autonomy_verified":False})


def verify(root, mission, commitment):
    """Independently reopen every contract and reservation without model/provider calls."""
    strict()
    def load(name):
        p = root / name
        if p.is_symlink() or not p.is_file() or p.stat().st_size > 2_000_000:
            raise ValueError("Unsafe receipt")
        return json.loads(p.read_text())
    binding = load("binding.json")
    md = binding.get("model_digest")
    if (binding != {"mission_sha256":mp.digest(mission),"model_digest":md,
                    "versions":VERSIONS,"paid_inference":False}
            or not isinstance(md,str) or not md.removeprefix("sha256:").startswith(MODEL_PREFIX)):
        raise ValueError("Mission binding changed")
    plan = load("accepted-plan.json")
    selection = plan["selection"]
    if mp.digest(sorted(k for k,v in selection.items() if v)) != commitment:
        raise ValueError("Selection commitment changed")
    scope, graph = vm.graph(mission, selection)
    n=plan["model_calls"]
    if type(n) is not int or not 1 <= n <= MAX_CALLS or plan != {
        "selection":selection,"model_calls":n,"model_calls_replayed":0,
        "paid_inference":False,"model_digest":md}:
        raise ValueError("Plan receipt changed")
    hashes=set()
    files={"binding.json","accepted-plan.json","outcome.json"}
    for i in range(1,n+1):
        name=f"call-{i:02d}.reserved.json";files.add(name)
        row=load(name);h=row.get("request_sha256")
        if not isinstance(h,str) or len(h)!=64 or h in hashes or row != {
                "request_sha256":h,"model_digest":md,"paid_inference":False}:
            raise ValueError("Inference reservation changed")
        hashes.add(h)
    results={}
    for node in graph:
        tool=node["id"];inputs={k:results[k] for k in node["depends_on"]}
        reservation=tool+".reserved.json";receipt=tool+".result.json"
        files.update((reservation,receipt))
        if load(reservation)!={"tool":tool,"input_sha256":mp.digest(inputs)}:
            raise ValueError("Contract reservation changed")
        row=load(receipt);result=row["result"]
        if row!={"result":result,"result_sha256":mp.digest(result)}:
            raise ValueError("Contract result changed")
        check_contract_result(tool,scope,inputs,result)
        results[tool]=result
    expected={"mission_sha256":mp.digest(mission),"selected_capabilities":selection,
        "verified_contracts":len(results),"report_sha256":mp.digest(results["evidence_report"]),
        "paid_inference":False,"production_integrated":False,"general_autonomy_verified":False}
    if load("outcome.json")!=expected or {p.name for p in root.iterdir()}!=files:
        raise ValueError("Outcome or archive changed")
    print(json.dumps({**expected,"independent_readback":True,"model_calls":n},sort_keys=True))


def main():
    # A useful new public evidence objective, not an additional production queue.
    # Distinct DOI evidence from two original published cattle studies.
    mission = {
        "objective":"Review both scholarly DOI records for the evidence report and independently read back the publication metadata.",
        "authorized_inputs":{
            "bibliography":["10.1371/journal.pone.0247820","10.1093/jas/skae109"],
            "thermal":{"initial_kelvin":330,"ambient_kelvin":298,"rate":0.03,"duration":15},
        },
    }
    phase, path = sys.argv[1:]
    if phase == "run":
        execute(Path(path), mission, mp.digest(["bibliography"]))
    elif phase == "verify":
        verify(Path(path), mission, mp.digest(["bibliography"]))
    else:
        raise ValueError("Unknown phase")


if __name__ == "__main__":
    main()

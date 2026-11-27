"""Candidate Microsoft Magentic planner for the ORIGINAL Minister.
Uses official Agent Framework orchestration, existing local model and contract graph.
No new workforce, provider credentials, arbitrary tools, or external write authority.
"""
import asyncio
import json
import os
import sys
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "paperclip"))
import model_plan as mp
import variable_mission as vm
from checkpoint_store import exclusive
from plenum_ai.chief_contract_plan import run_contract, check_contract_result

MODEL = "qwen3.5:9b-q4_K_M"
MODEL_PREFIX = "56671c2ab938"
VERSIONS = {
    "agent-framework-core": "1.26.0",
    "agent-framework-orchestrations": "1.4.2",
    "agent-framework-openai": "1.18.2",
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


class Guard:
    """Bound the actual SDK transport; reserve before inference, never resend."""
    def __init__(self, root, md):
        self.root, self.md, self.seen = root, md, set()

    async def reserve(self, request):
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
        payload["max_tokens"] = min(payload.get("max_tokens") or 1024, 1024)
        payload["reasoning_effort"] = "none"
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        digest = sha256(raw).hexdigest()
        if digest in self.seen or len(self.seen) >= MAX_CALLS:
            raise PermissionError("Duplicate request or mission inference ceiling")
        exclusive(self.root / f"call-{len(self.seen)+1:02d}.reserved.json",
                  {"request_sha256":digest, "model_digest":self.md, "paid_inference":False})
        self.seen.add(digest)
        # httpx request hook can replace the request stream; update the length.
        import httpx
        request.stream = httpx.ByteStream(raw)
        request._content = raw
        request.headers["Content-Length"] = str(len(raw))


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


async def plan(root, mission, commitment):
    """Official MagenticBuilder chooses specialists, maintains progress and replans."""
    strict()
    vm.validate(mission)
    from agent_framework import Agent
    from agent_framework.orchestrations import MagenticBuilder
    from agent_framework.openai import OpenAIChatClient
    from openai import AsyncOpenAI
    import httpx
    md = model_digest()
    root.mkdir(mode=0o700, parents=False, exist_ok=False)
    exclusive(root / "binding.json", {"mission_sha256":mp.digest(mission),
        "model_digest":md, "versions":VERSIONS, "paid_inference":False})
    guard = Guard(root, md)
    async with httpx.AsyncClient(trust_env=False, follow_redirects=False,
                                 timeout=90, event_hooks={"request":[guard.reserve]}) as transport:
        async with AsyncOpenAI(base_url=BASE, api_key="local-no-secret", max_retries=0,
                               http_client=transport) as sdk:
            client = OpenAIChatClient(model=MODEL, async_client=sdk)
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
            task = json.dumps({"mission":scope, "required_final_schema":schema},
                              sort_keys=True)
            outcome = await asyncio.wait_for(workflow.run(task), timeout=540)
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
    execute(Path(sys.argv[1]), mission, mp.digest(["bibliography"]))


if __name__ == "__main__":
    main()

"""Optional, approval-gated LiveKit voice transport for Plenum Prometheus.

This is *not* the Prometheus intelligence engine, proof of AGI, an active
voice server, persistent memory or confirmation of subjective experience.
The default path is local, read-only configuration output.  Reuses upstream
LiveKit Agents 1.8.9; never starts or imports that runtime in plan mode.
"""
import argparse
import json
import os

SCHEMA = "prometheus-livekit-voice-stage1-v1"
UPSTREAM_PACKAGE = "livekit-agents==1.8.9"
APPROVAL_ENV = "PROMETHEUS_APPROVE_LIVE_VOICE_COST"
REQUIRED_ENV = ("LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET")
MODELS = {
    "stt": "assemblyai/universal-3-6-pro",
    "llm": "google/gemma-4-31b-it",
    "tts": "fishaudio/s2.1-pro",
    "voice": "fa4c9eb3dccc4806b382b40d61c6b10a",
}
INSTRUCTIONS = (
    "You are Plenum Prometheus, an explicitly artificial experimental "
    "scientific assistant. Your purpose is to help the authorized user "
    "reason, learn, design, research, and test ideas across disciplines. "
    "Be intellectually honest, identify uncertainty, protect private "
    "information, and never invent experimental results, memories or "
    "sources. Maintain continuity only through approved provenance-aware "
    "project state. Follow authorized goals faithfully while allowing "
    "correction and declining unsafe, unethical or unauthorized actions. "
    "Do not assert consciousness, subjective feelings, independent legal "
    "personhood, or unlimited validated intelligence. "
    "No external tool, transaction, disclosure or self-modification is "
    "approved merely because a user speaks a command. "
    "Keep spoken answers conversational and avoid excessive formatting."
)


def preview():
    """Safe serializable configuration: absolutely no remote service calls."""
    return {
        "schema": SCHEMA,
        "upstream_framework": "livekit/agents",
        "package_pin": UPSTREAM_PACKAGE,
        "purpose": "optional interrupted realtime speech and iPad/web interface",
        "intelligence_layer": "separate existing Plenum research / LangGraph",
        "models": dict(MODELS),
        "cloud_provider_cost_possible": True,
        "approval_env": APPROVAL_ENV,
        "requires_authorization_and_credentials": True,
        "network_started": False,
        "model_inference_executed": False,
        "microphone_connected": False,
        "memory_connected": False,
        "private_knowledge_uploaded": False,
        "real_time_latency_verified": False,
        "AGI_demonstrated": False,
        "consciousness_demonstrated": False,
    }


def approval_check(environ=None):
    """Do not initialize SDK/network without affirmative consent and credentials."""
    env = os.environ if environ is None else environ
    if env.get(APPROVAL_ENV) != "YES":
        raise PermissionError(
            "Live provider voice service is OFF. Owner approval for potential "
            "provider billing is required before starting."
        )
    missing = [name for name in REQUIRED_ENV if not env.get(name)]
    if missing:
        raise RuntimeError("Missing LiveKit connection parameters: " + ", ".join(missing))
    return True


def build_server():
    """Real optional upstream integration, imported only after approval.

    Provider model strings come from the LiveKit quickstart. These managed
    inference endpoints are NOT free/hosted locally by this module.
    """
    from livekit import agents
    from livekit.agents import Agent, AgentServer, AgentSession, inference

    class PrometheusAgent(Agent):
        def __init__(self):
            super().__init__(instructions=INSTRUCTIONS)

    server = AgentServer()

    @server.rtc_session(agent_name="plenum-prometheus")
    async def voice_session(ctx: agents.JobContext):
        session = AgentSession(
            stt=inference.STT(model=MODELS["stt"], language="en"),
            llm=inference.LLM(model=MODELS["llm"]),
            tts=inference.TTS(model=MODELS["tts"], voice=MODELS["voice"]),
        )
        await session.start(room=ctx.room, agent=PrometheusAgent())
        await session.generate_reply(
            instructions="Greet the participant briefly and invite their question."
        )

    return server, agents


def main(argv=None):
    parser = argparse.ArgumentParser(description="Review optional LiveKit speech bridge")
    parser.add_argument(
        "--serve", action="store_true",
        help="Start only after owner approves possible provider billing and credentials"
    )
    args = parser.parse_args(argv)
    if not args.serve:
        print(json.dumps(preview(), indent=2))
        return
    approval_check()
    server, agents = build_server()
    agents.cli.run_app(server)


if __name__ == "__main__":
    main()

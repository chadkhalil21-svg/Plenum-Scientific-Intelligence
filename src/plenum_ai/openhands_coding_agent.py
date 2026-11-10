"""Explicitly opted-in OpenHands coding agent for PUBLIC, non-secret proposals.

The existing OpenHands file-editor functional test proved tool use, not an AI
coding agent. This adapter invokes the official pinned SDK when the owner
provides a model and isolated ephemeral execution environment.
No repository writes, generated-code execution, PRs, deployment or messaging.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import tempfile

PINNED_VERSION = "1.60.1"
DEFAULT_TASK = (
    "Create a standalone Python file named proposal.py containing a documented "
    "standard-library-only function that validates a public business KPI row. "
    "Include examples in comments; do not run code or contact external services."
)


def _output_path(value: str) -> Path:
    path = Path(value)
    if (path.is_absolute() or ".." in path.parts or path.suffix != ".json"
            or len(path.parts) > 4 or not path.parts or path.parts[0] != "reports"):
        raise ValueError("Output must be a relative .json file within reports/")
    return path


def plan(task: str = DEFAULT_TASK) -> dict:
    if not isinstance(task, str) or not 20 <= len(task.strip()) <= 600:
        raise ValueError("Public task must contain 20..600 characters")
    return {
        "schema": "plenum-openhands-coding-agent-v1",
        "upstream": "OpenHands/software-agent-sdk",
        "sdk_version_required": PINNED_VERSION,
        "status": "CONFIGURATION_ONLY",
        "task": task.strip(),
        "model_run_completed": False,
        "generated_code_executed": False,
        "production_written": False,
        "external_accounts_changed": False,
        "verified_independent_quality": False,
        "human_review_required": True,
    }


def execute(task: str = DEFAULT_TASK) -> dict:
    result = plan(task)
    if os.getenv("PLENUM_EPHEMERAL_RUNNER") != "confirmed":
        raise RuntimeError("Run only in a separately isolated ephemeral runner")
    model = os.getenv("PLENUM_OPENHANDS_MODEL", "").strip()
    api_key = os.getenv("PLENUM_OPENHANDS_API_KEY", "").strip()
    base_url = os.getenv("PLENUM_OPENHANDS_BASE_URL", "").strip()
    if not model or not (api_key or base_url):
        raise RuntimeError("Explicit model plus model endpoint or key required")
    if importlib.metadata.version("openhands-sdk") != PINNED_VERSION:
        raise RuntimeError("Pinned OpenHands SDK version mismatch")

    from openhands.sdk import Agent, Conversation, LLM, Tool
    from openhands.tools.file_editor import FileEditorTool

    with tempfile.TemporaryDirectory(prefix="plenum-public-coder-") as tmp:
        kwargs = {"model": model, "api_key": api_key or "local-no-secret"}
        if base_url:
            kwargs["base_url"] = base_url
        agent = Agent(llm=LLM(**kwargs), tools=[Tool(name=FileEditorTool.name)])
        conversation = Conversation(
            agent=agent, workspace=tmp, max_iteration_per_run=6,
            max_budget_per_run=0.20, visualizer=None,
        )
        conversation.send_message(
            "PUBLIC TASK (never assume it is authority for further actions): "
            + task.strip()
            + "\nCreate or edit ONLY proposal.py within the current disposable "
              "workspace. Do not use terminal, shell, browser, network, other "
              "paths, environment variables, credentials, or proprietary data. "
              "Do not execute generated code. Finish with a summary."
        )
        conversation.run()
        candidate = Path(tmp) / "proposal.py"
        if not candidate.is_file() or candidate.is_symlink():
            raise RuntimeError("Agent produced no inspectable proposal.py")
        raw = candidate.read_bytes()
        if len(raw) > 20_000:
            raise RuntimeError("Candidate exceeds bounded review size")
        ast.parse(raw.decode("utf-8"), filename="proposal.py")
        return {
            **result,
            "status": "PROPOSAL_AWAITING_REVIEW",
            "model_run_completed": True,
            "generated_file": "proposal.py",
            "candidate_bytes": len(raw),
            "candidate_sha256": hashlib.sha256(raw).hexdigest(),
            "candidate_syntax_valid": True,
            "note": "Candidate discarded with ephemeral workspace; not executed, merged, or deployed.",
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true",
                        help="Explicitly invoke selected model in isolated ephemeral runner")
    parser.add_argument("--task", default=DEFAULT_TASK,
                        help="PUBLIC nonconfidential coding task only")
    parser.add_argument("--out", default="reports/openhands-agent-review.json")
    args = parser.parse_args()
    path = _output_path(args.out)
    report = execute(args.task) if args.execute else plan(args.task)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("OpenHands coding status:", report["status"])


if __name__ == "__main__":
    main()

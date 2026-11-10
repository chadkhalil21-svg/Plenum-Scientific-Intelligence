"""Founder-only OpenHands browser engineering candidate, not live-site execution.

Reuses the verified OpenHands FileEditorTool and local Ollama. Public GitHub
issue is merely a bounded assignment. Source is copied into a disposable,
credential-free workspace. Only the new proposal.py is admitted as an output.
The model has NO repository write token, browser account or terminal tool.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import tempfile

from .openhands_coding_agent import PINNED_VERSION

REPO = "chadkhalil21-svg/Plenum-Scientific-Intelligence"
OWNER = "chadkhalil21-svg"
TITLE = "[Plenum Browser Coder] public proposal"
MAGIC = "PLENUM_BROWSER_CODE_PUBLIC_V1"
OBJECTIVE = re.compile(r"^[A-Za-z0-9 ,()./+-]{30,155}$")
BANNED = (
    "password", "credential", "token", "confidential", "private key",
    "api key", "billing", "payment", "customer", "patent", "deploy",
)
SOURCES = (
    "services/computer_browser/owner_navigation.py",
    "services/computer_browser/owner_task_loop.py",
    "services/computer_browser/browser_actions.py",
)
LIMIT = 22_000


def _require_implemented_candidate(raw: bytes) -> None:
    """Generic independent source-quality floor, NOT a behavioral test.

    The first real OpenHands browser task produced two functions containing
    only 'pass' yet passed Python AST. Refuse all no-op stubs, fake ellipsis
    implementations and source with no functional return. A human/independent
    task-specific verifier must STILL establish actual correctness.
    """
    tree = ast.parse(raw.decode("utf-8"), filename="proposal.py")
    funcs = [x for x in ast.walk(tree)
             if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if not funcs:
        raise ValueError("No implemented Python functions")
    if any(isinstance(x, ast.Pass) for x in ast.walk(tree)):
        raise ValueError("Unimplemented pass statement in source")
    if any(isinstance(x, ast.Constant) and x.value is Ellipsis
           for x in ast.walk(tree)):
        raise ValueError("Placeholder ellipsis in source")
    if any(isinstance(x, ast.Raise) and isinstance(x.exc, ast.Call)
           and isinstance(x.exc.func, ast.Name)
           and x.exc.func.id == "NotImplementedError"
           for x in ast.walk(tree)):
        raise ValueError("NotImplementedError placeholder in source")
    if not any(isinstance(x, ast.Return) and x.value is not None
               for x in ast.walk(tree)):
        raise ValueError("Source provides no returned result")
    if any(isinstance(x, ast.Call) and isinstance(x.func, ast.Name)
           and x.func.id in {"eval", "exec", "__import__"}
           for x in ast.walk(tree)):
        raise PermissionError("Dynamic evaluation is outside source proposal scope")



def local_coder_llm_options() -> dict:
    """Pinned official SDK model config for non-thinking Ollama coder weights.

    SDK 1.60.1 defaults reasoning_effort='high', which LiteLLM translated
    into Ollama's unsupported think=true on qwen2.5-coder:7b. Use the SDK's
    existing documented capability overrides, not a proxy rewrite.
    """
    return {
        "model": "ollama/qwen2.5-coder:7b",
        "api_key": "local-no-secret",
        "base_url": "http://127.0.0.1:11434",
        "reasoning_effort": None,
        "capability_overrides": {
            "supports_reasoning_effort": False,
            "thinking_mode": "none",
        },
        "enable_encrypted_reasoning": False,
    }


def parse_issue(event: dict) -> dict:
    issue = event.get("issue") or {}
    if (
        event.get("action") != "opened"
        or (event.get("repository") or {}).get("full_name") != REPO
        or (issue.get("user") or {}).get("login") != OWNER
        or issue.get("title") != TITLE
        or type(issue.get("number")) is not int
        or not 1 <= issue["number"] <= 999_999_999
    ):
        raise PermissionError("Not an original founder public coding assignment")
    body = issue.get("body")
    lines = body.splitlines() if isinstance(body, str) else []
    if len(lines) != 2 or lines[0] != MAGIC or not lines[1].startswith("objective: "):
        raise ValueError("Use exact two-line founder public coding task")
    objective = lines[1][11:]
    if not OBJECTIVE.fullmatch(objective) or any(x in objective.lower() for x in BANNED):
        raise PermissionError("Only bounded, non-sensitive public code proposals")
    return {
        "schema": "plenum-owner-browser-code-proposal-v1",
        "issue": issue["number"],
        "objective": objective,
        "output_kind": "REVIEW_ONLY_SOURCE",
        "production_writes_authorized": False,
    }


def _out_dir(issue_number: int) -> Path:
    if type(issue_number) is not int or not 1 <= issue_number <= 999_999_999:
        raise ValueError("Invalid founder issue")
    return Path("reports") / "browser-agent" / ("issue-" + str(issue_number))


def run(event: dict, *, execute: bool = False) -> dict:
    task = parse_issue(event)
    output = _out_dir(task["issue"])
    output.mkdir(parents=True, exist_ok=True)
    receipt = {
        **task,
        "model_executed": False,
        "source_candidate_syntax_verified": False,
        "production_written": False,
        "external_account_actions": False,
        "independent_behavior_verified": False,
        "candidate_review_required": True,
        "status": "PREFLIGHT_ONLY",
    }
    if not execute:
        (output / "result.json").write_text(json.dumps(receipt, indent=2) + "\n")
        return receipt
    if (
        os.getenv("PLENUM_EPHEMERAL_RUNNER") != "confirmed"
        or os.getenv("PLENUM_OPENHANDS_MODEL") != "ollama/qwen2.5-coder:7b"
        or os.getenv("PLENUM_OPENHANDS_BASE_URL") != "http://127.0.0.1:11434"
        or importlib.metadata.version("openhands-sdk") != PINNED_VERSION
    ):
        raise PermissionError("Pinned local model and ephemeral OpenHands required")
    from openhands.sdk import Agent, Conversation, LLM, Tool
    from openhands.tools.file_editor import FileEditorTool

    with tempfile.TemporaryDirectory(prefix="plenum-browser-code-") as temp:
        root = Path(temp)
        trusted = {}
        for name in SOURCES:
            src = Path(name)
            if not src.is_file() or src.stat().st_size > 50_000:
                raise FileNotFoundError("Original browser source missing or oversized")
            original = src.read_bytes()
            dest = root / src.name
            dest.write_bytes(original)
            trusted[dest.name] = hashlib.sha256(original).hexdigest()
        agent = Agent(
            llm=LLM(**local_coder_llm_options()),
            tools=[Tool(name=FileEditorTool.name)],
        )
        conversation = Conversation(
            agent=agent, workspace=temp, max_iteration_per_run=4,
            max_budget_per_run=0.20, visualizer=None,
        )
        instructions = (
            "A founder asked for this PUBLIC browser code improvement: "
            + task["objective"]
            + "\nInspect the existing owner_navigation.py, owner_task_loop.py "
              "and browser_actions.py from this isolated workspace with "
              "FileEditorTool. These are READ-ONLY references. Create ONLY "
              "proposal.py, a standalone Python draft helper compatible with "
              "the existing engine. Do not create or modify any other file. "
              "Do not use terminal, shell, network, browser, system secrets "
              "or any production website. Never claim the code ran, was "
              "integrated, or passed a live login. No unapproved writes. "
              "Implement genuine functions with meaningful return values, NOT "
              "pass, ellipsis, TODO or NotImplementedError placeholders. "
              "Include at least two short expected-input and expected-output "
              "examples in comments for independent review. "
              "Finish after writing proposal.py."
        )
        conversation.send_message(instructions)
        candidate = root / "proposal.py"
        for attempt in range(2):
            conversation.run()
            if candidate.is_symlink():
                raise PermissionError("Symlink output forbidden")
            if candidate.is_file():
                raw = candidate.read_bytes()
                if not 80 <= len(raw) <= LIMIT:
                    raise ValueError("Candidate must be bounded nonempty Python")
                try:
                    _require_implemented_candidate(raw)
                    break
                except (UnicodeDecodeError, SyntaxError, ValueError):
                    if attempt:
                        raise RuntimeError("Agent could not repair syntax")
                    conversation.send_message(
                        "Independent review found invalid syntax or no-op placeholder functions. "
                        "Repair proposal.py only, without executing code."
                    )
            elif attempt:
                raise RuntimeError("Agent failed to produce source candidate")
            else:
                conversation.send_message(
                    "The requested proposal.py is missing. Create it now "
                    "with FileEditorTool; no other edits or actions."
                )
        for name, digest in trusted.items():
            if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
                raise PermissionError("Reference browser source was modified")
        if any(p.name not in set(trusted) | {"proposal.py"} for p in root.iterdir()):
            raise PermissionError("Unexpected model-written workspace files")
        (output / "proposal.py").write_bytes(raw)
        receipt.update({
            "status": "SOURCE_PROPOSAL_AWAITING_REVIEW",
            "model_executed": True,
            "source_candidate_syntax_verified": True,
            "candidate_sha256": hashlib.sha256(raw).hexdigest(),
            "candidate_bytes": len(raw),
            "repair_rounds": attempt,
            "note": "Actual FileEditor model code candidate, not a deployed feature.",
        })
    (output / "result.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--event", required=True)
    p.add_argument("--execute", action="store_true")
    args = p.parse_args()
    event = json.loads(Path(args.event).read_text())
    result = run(event, execute=args.execute)
    print("Browser coder status:", result["status"])


if __name__ == "__main__":
    main()

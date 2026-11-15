"""Explicitly opted-in OpenHands coding agent for PUBLIC, non-secret proposals.

The existing OpenHands file-editor functional test proved tool use, not an AI
coding agent. This adapter invokes the official pinned SDK when the owner
provides a model and isolated ephemeral execution environment.
No repository writes, generated-code execution, PRs, deployment or messaging.
"""
from __future__ import annotations

import argparse
import ast
import difflib
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import tempfile

PINNED_VERSION = "1.60.1"
ORIGINAL_FREE_CODING_ENDPOINT = "https://plenum-public-wake.chadkhalil21.workers.dev/ai/v1"


def original_free_retry_options(model: str, base_url: str) -> dict:
    """Use pinned upstream OpenHands retry settings, not another retry wrapper.

    A genuine original job #733 repeatedly retried a deterministic local
    daily-budget 429. One call is enough for this exact Free model endpoint.
    Other model/provider retry behavior remains unchanged.
    """
    if (model == "openai/glm-4.7-flash"
            and base_url == ORIGINAL_FREE_CODING_ENDPOINT):
        return {"num_retries": 1}
    return {}


OWNER = "chadkhalil21-svg"
REPO = "chadkhalil21-svg/Plenum-Scientific-Intelligence"
REPAIR_TITLE = "[Plenum OpenHands] public repair"
REPAIR_MARKER = "PLENUM_OPENHANDS_PUBLIC_REPAIR_V1"
LOCAL_REPAIR_MARKER = "PLENUM_AIDER_LOCAL_PUBLIC_REPAIR_V1"
LOCAL_ENGINE = "aider_local_ollama"
# Official amd64 v0.86.0 image manifest (not a mutable latest tag).
AIDER_IMAGE = "paulgauthier/aider@sha256:cfdc43ebd4ff163f7ef5f1803b069fa80abbd95e981d165495d459d3edcc356c"
LOCAL_MODEL = "qwen2.5-coder:7b"
LOCAL_MAX_SOURCE_BYTES = 12_000  # Whole-file output on 4 CPU free runner.
GEMINI_ENGINE = "gemini_free_openhands"
GEMINI_MODEL = "gemini/gemini-3.5-flash-lite"
# Owner verified the sole existing Default Gemini Project's Free tier and no
# enabled billing in authenticated AI Studio on 15 Nov 2026. Never infer this
# from key presence; any later tier/key change requires re-verification.
GEMINI_FREE_APPROVAL = "owner-verified-default-gemini-project-free-2026-11-15"
REVIEW_REPORT = Path("reports/openhands-agent-review.json")
CLOUD_FAILURE_REPORT = Path("reports/openhands-cloud-failure.json")
GEMINI_RESERVATION = Path("reports/openhands-gemini-fallback-reservation.json")
GEMINI_EXECUTION = Path("reports/openhands-gemini-fallback-execution.json")
CLOUD_FAILURES = {
    "BLOCKED_ORIGINAL_DAILY_FREE_AI_CAP": "LOCAL_DURABLE_OBJECT_DAILY_BUDGET",
    "BLOCKED_ORIGINAL_CLOUD_NO_REVIEWABLE_PATCH": "ORIGINAL_ENGINE_NO_REVIEWABLE_PATCH",
    "BLOCKED_ORIGINAL_CLOUD_TRANSPORT": "ORIGINAL_ENGINE_TRANSPORT",
}


class NoReviewableProposalError(RuntimeError):
    """An authorized model ran but produced no usable source, not a security failure."""


def _public_source(source_file: str) -> tuple[bytes, str]:
    """Bound a proposed edit to one already-public Python module."""
    import re
    if (not isinstance(source_file, str)
            or not re.fullmatch(r"src/plenum_ai/[a-z][a-z0-9_]{1,64}\.py", source_file)
            or any(term in Path(source_file).name for term in
                   ("secret", "credential", "token", "password", "browser", "auth", "billing", "stripe"))):
        raise PermissionError("Only one reviewed public Python source module")
    path = Path(source_file)
    if path.is_symlink() or not path.is_file():
        raise PermissionError("Expected regular public source in original checkout")
    if not path.resolve().is_relative_to(Path.cwd().resolve() / "src" / "plenum_ai"):
        raise PermissionError("Public source escaped original checkout")
    raw = path.read_bytes()
    if not 1 <= len(raw) <= 40_000:
        raise ValueError("Source module exceeds bounded review limit")
    raw.decode("utf-8")
    return raw, hashlib.sha256(raw).hexdigest()


def parse_owner_repair_event(event: dict) -> dict:
    """Owner-only, one-file public repair; no trust in model-generated instructions."""
    import re
    issue = event.get("issue") or {}
    if (event.get("action") != "opened"
            or (event.get("repository") or {}).get("full_name") != REPO
            or (issue.get("user") or {}).get("login") != OWNER
            or issue.get("title") != REPAIR_TITLE
            or not isinstance(issue.get("number"), int)
            or not 0 < issue["number"] < 10**9):
        raise PermissionError("Only original owner public repair issues")
    body = issue.get("body")
    lines = body.splitlines() if isinstance(body, str) else []
    if (len(lines) != 3 or lines[0] not in (REPAIR_MARKER, LOCAL_REPAIR_MARKER)
            or not lines[1].startswith("file: ")
            or not lines[2].startswith("objective: ")):
        raise ValueError("Exact three-line original public repair contract required")
    source_file, objective = lines[1][6:], lines[2][11:]
    if (not 25 <= len(objective) <= 200 or objective != objective.strip()
            or not re.fullmatch(r"[A-Za-z0-9 .,()/+'-]+", objective)
            or any(term in objective.lower() for term in
                   ("secret", "credential", "password", "token", "private",
                    "customer", "deploy", "publish", "bypass", "billing", "payment"))):
        raise PermissionError("Only bounded public review-only objectives")
    _, sha = _public_source(source_file)
    return {"issue_number": issue["number"], "task": objective,
            "source_file": source_file, "source_sha256": sha,
            "review_only": True, "auto_merge": False, "paid_api_authorized": False,
            **({"engine": LOCAL_ENGINE} if lines[0] == LOCAL_REPAIR_MARKER else {})}


def _review_output_path(value: str, *, source_file: str | None) -> Path:
    import re
    if (not isinstance(value, str) or not re.fullmatch(
            r"reports/openhands-review/(?:proposal\.py|issue-[0-9]{1,9}\.patch)", value)):
        raise ValueError("Only review artifacts beneath reports/openhands-review")
    path = Path(value)
    if (source_file is None) != (path.suffix == ".py"):
        raise ValueError("Source repairs require a patch; standalone proposals require Python")
    root = Path.cwd().resolve()
    base = root / "reports" / "openhands-review"
    if path.exists() or path.is_symlink() or base.is_symlink():
        raise PermissionError("Never overwrite an existing or linked review artifact")
    if not path.parent.resolve().is_relative_to(base):
        raise PermissionError("Review artifact path escaped original workspace")
    return path


def _fallback_binding(event: dict, receipt_path: Path, *, run_id: str,
                      run_attempt: str) -> dict:
    """Validate actual original cloud failure and one exact owner/source/run binding."""
    import re
    owner = parse_owner_repair_event(event)
    if (owner.get("engine") or not re.fullmatch(r"[1-9][0-9]{0,12}", run_id)
            or run_attempt != "1"):
        raise PermissionError("Only first original cloud issue attempt may fail over")
    if (receipt_path.is_symlink() or not receipt_path.is_file()
            or receipt_path.stat().st_size > 64_000):
        raise PermissionError("No bounded original cloud failure receipt")
    raw = receipt_path.read_bytes()
    receipt = json.loads(raw)
    if (not isinstance(receipt, dict)
            or receipt.get("schema") != "plenum-openhands-coding-agent-v1"
            or receipt.get("upstream") != "OpenHands/software-agent-sdk"
            or receipt.get("status") not in CLOUD_FAILURES
            or receipt.get("failure_category") != CLOUD_FAILURES[receipt["status"]]
            or receipt.get("task") != owner["task"]
            or receipt.get("source_file") != owner["source_file"]
            or receipt.get("source_sha256") != owner["source_sha256"]
            or receipt.get("origin_issue_number") != owner["issue_number"]
            or receipt.get("origin_run_id") != run_id
            or receipt.get("origin_run_attempt") != run_attempt
            or any(receipt.get(key) is not False for key in (
                "candidate_persisted", "model_run_completed", "generated_code_executed",
                "production_written", "external_accounts_changed", "retry_same_day_authorized"))
            or receipt.get("no_paid_fallback") is not True
            or receipt.get("candidate_artifact") is not None):
        raise PermissionError("Original cloud receipt does not authorize Gemini fallback")
    # Do not start another agent if any original candidate exists, even if
    # report claims otherwise; do not weaken the original review path.
    _review_output_path(f"reports/openhands-review/issue-{owner['issue_number']}.patch",
                        source_file=owner["source_file"])
    return {"schema": "plenum-original-gemini-fallback-v1",
            "origin_issue_number": owner["issue_number"], "origin_run_id": run_id,
            "origin_run_attempt": run_attempt, "source_sha256": owner["source_sha256"],
            "cloud_receipt_sha256": hashlib.sha256(raw).hexdigest(),
            "cloud_attempt_status": receipt["status"], "gemini_fallback_attempted": True,
            "fallback_engine": GEMINI_ENGINE, "fallback_model": GEMINI_MODEL,
            "free_project_approval": GEMINI_FREE_APPROVAL}


def reserve_gemini_fallback(event: dict, *, run_id: str, run_attempt: str) -> bool:
    """Reserve the single approved same-job Gemini route before key access."""
    try:
        if os.getenv("PLENUM_GEMINI_FREE_PROJECT_APPROVAL") != GEMINI_FREE_APPROVAL:
            return False
        if any(p.exists() or p.is_symlink() for p in
               (CLOUD_FAILURE_REPORT, GEMINI_RESERVATION, GEMINI_EXECUTION)):
            return False
        bound = _fallback_binding(event, REVIEW_REPORT, run_id=run_id, run_attempt=run_attempt)
        with CLOUD_FAILURE_REPORT.open("xb") as dst:
            dst.write(REVIEW_REPORT.read_bytes())
        with GEMINI_RESERVATION.open("x", encoding="utf-8") as dst:
            json.dump(bound, dst, indent=2)
        return True
    except (OSError, ValueError, PermissionError, TypeError, KeyError):
        return False


def consume_gemini_fallback(event: dict, *, run_id: str, run_attempt: str) -> dict:
    """A reservation authorizes one Gemini engineering attempt; never retry it."""
    if os.getenv("PLENUM_GEMINI_FREE_PROJECT_APPROVAL") != GEMINI_FREE_APPROVAL:
        raise PermissionError("Gemini Free project approval unavailable")
    bound = _fallback_binding(event, CLOUD_FAILURE_REPORT, run_id=run_id, run_attempt=run_attempt)
    if (GEMINI_RESERVATION.is_symlink() or not GEMINI_RESERVATION.is_file()
            or GEMINI_RESERVATION.stat().st_size > 16_000
            or json.loads(GEMINI_RESERVATION.read_text()) != bound
            or GEMINI_EXECUTION.exists() or GEMINI_EXECUTION.is_symlink()):
        raise PermissionError("No unused exact original Gemini fallback reservation")
    with GEMINI_EXECUTION.open("x", encoding="utf-8") as dst:
        json.dump(bound, dst, indent=2)
    return bound


DEFAULT_TASK = (
    "Create a standalone Python file named proposal.py containing a documented "
    "standard-library-only function that validates a public business KPI row. "
    "Include examples in comments; do not run code or contact external services."
)


def _candidate_byte_limit(original_bytes: bytes | None) -> int:
    """A source repair may retain the full reviewed source plus a bounded edit."""
    if original_bytes is None:
        return 20_000
    return min(45_000, max(20_000, len(original_bytes) + 5_000))


def _output_path(value: str) -> Path:
    path = Path(value)
    if (path.is_absolute() or ".." in path.parts or path.suffix != ".json"
            or len(path.parts) > 4 or not path.parts or path.parts[0] != "reports"):
        raise ValueError("Output must be a relative .json file within reports/")
    return path


def plan(task: str = DEFAULT_TASK, *, source_file: str | None = None) -> dict:
    if not isinstance(task, str) or not 20 <= len(task.strip()) <= 600:
        raise ValueError("Public task must contain 20..600 characters")
    source_sha = _public_source(source_file)[1] if source_file is not None else None
    return {
        "schema": "plenum-openhands-coding-agent-v1",
        "upstream": "OpenHands/software-agent-sdk",
        "sdk_version_required": PINNED_VERSION,
        "status": "CONFIGURATION_ONLY",
        "task": task.strip(),
        "source_file": source_file,
        "source_sha256": source_sha,
        "candidate_persisted": False,
        "model_run_completed": False,
        "generated_code_executed": False,
        "production_written": False,
        "external_accounts_changed": False,
        "verified_independent_quality": False,
        "human_review_required": True,
    }


def _candidate_report(result: dict, original: bytes | None, raw: bytes,
                      source_file: str | None, artifact: Path | None,
                      attempt: int) -> dict:
    if original is not None and raw == original:
        raise NoReviewableProposalError("Coder did not modify the original source copy")
    saved = None
    artifact_bytes = b""
    if artifact is not None:
        artifact.parent.mkdir(parents=True, exist_ok=True)
        if original is None:
            artifact_bytes = raw
        else:
            artifact_bytes = "".join(difflib.unified_diff(
                original.decode("utf-8").splitlines(keepends=True),
                raw.decode("utf-8").splitlines(keepends=True),
                fromfile="a/" + source_file, tofile="b/" + source_file,
            )).encode("utf-8")
            if not artifact_bytes or len(artifact_bytes) > 80_000:
                raise RuntimeError("Proposed change lacks a bounded unified diff")
        with artifact.open("xb") as destination:
            destination.write(artifact_bytes)
        saved = artifact.as_posix()
    return {
        **result,
        "status": "PROPOSAL_AWAITING_REVIEW",
        "candidate_persisted": saved is not None,
        "candidate_artifact": saved,
        "candidate_artifact_sha256": (
            hashlib.sha256(artifact_bytes).hexdigest() if saved else None),
        "model_run_completed": True,
        "generated_file": "proposal.py",
        "candidate_bytes": len(raw),
        "candidate_sha256": hashlib.sha256(raw).hexdigest(),
        "candidate_syntax_valid": True,
        "repair_passes": attempt,
        "note": ("AST pass only: artifact saved for independent human review, not deployed."
                 if saved else "Independent AST check passed. Candidate discarded; never executed or deployed."),
    }


def local_plan(task: str, *, source_file: str) -> dict:
    if len(_public_source(source_file)[0]) > LOCAL_MAX_SOURCE_BYTES:
        raise PermissionError("Source too large for bounded CPU whole-file local coding")
    result = plan(task, source_file=source_file)
    result.pop("sdk_version_required")
    return {**result, "upstream": "Aider-AI/aider", "engine": LOCAL_ENGINE,
            "aider_image": AIDER_IMAGE, "local_model": LOCAL_MODEL,
            "cloud_inference_used": False, "paid_api_authorized": False}


def gemini_plan(task: str, *, source_file: str) -> dict:
    return {**plan(task, source_file=source_file), "engine": GEMINI_ENGINE,
            "model": GEMINI_MODEL, "provider": "Google AI Studio Gemini Developer API",
            "free_project_approval": GEMINI_FREE_APPROVAL, "paid_api_authorized": False,
            "max_model_iterations": 4, "max_output_tokens_per_completion": 4096,
            "provider_retries": 0}


def _register_proposal_editor() -> str:
    """Reuse the pinned upstream editor but enforce one private temporary file.

    Upstream FileEditor workspace_root is a cwd hint, not a read boundary.
    Its allowed_edits_files also permits arbitrary views, so every command
    must pass our lexical path and regular-file check before delegation.
    """
    from openhands.sdk.tool import register_tool
    from openhands.tools.file_editor import FileEditorTool
    from openhands.tools.file_editor.definition import FileEditorObservation
    from openhands.tools.file_editor.impl import FileEditorExecutor

    class ProposalOnlyExecutor(FileEditorExecutor):
        def __init__(self, *, workspace_root):
            super().__init__(workspace_root=workspace_root)
            self._proposal = Path(workspace_root).resolve(strict=True) / "proposal.py"

        def __call__(self, action, conversation=None):
            supplied = Path(action.path)
            if (not supplied.is_absolute() or ".." in supplied.parts
                    or supplied != self._proposal or self._proposal.is_symlink()
                    or self._proposal.parent.resolve() != self._proposal.parent
                    or (self._proposal.exists() and not self._proposal.is_file())):
                return FileEditorObservation.from_text(
                    command=action.command, is_error=True,
                    text="Only the disposable public proposal.py file is permitted.")
            return super().__call__(action, conversation)

    class ProposalOnlyFileEditorTool(FileEditorTool):
        @classmethod
        def create(cls, conv_state):
            return [tool.set_executor(ProposalOnlyExecutor(
                workspace_root=conv_state.workspace.working_dir))
                for tool in super().create(conv_state)]

    register_tool(ProposalOnlyFileEditorTool.name, ProposalOnlyFileEditorTool)
    return ProposalOnlyFileEditorTool.name


def execute_local(task: str, *, source_file: str, candidate_out: str) -> dict:
    """Run official Aider noninteractively, with only a public source copy mounted.

    The existing Actions job supplies an internal Docker network connected only
    to the already-downloaded local Ollama server. No credentials are forwarded.
    The same independent, networkless patch gate remains mandatory.
    """
    result = local_plan(task, source_file=source_file)
    artifact = _review_output_path(candidate_out, source_file=source_file)
    if os.getenv("PLENUM_EPHEMERAL_RUNNER") != "confirmed":
        raise RuntimeError("Run only in a separately isolated ephemeral runner")
    original, _ = _public_source(source_file)
    with tempfile.TemporaryDirectory(prefix="plenum-aider-public-") as tmp:
        candidate = Path(tmp) / "proposal.py"
        candidate.write_bytes(original)
        command = [
            "docker", "run", "--rm", "--pull=never", "--network=plenum-coding-isolated",
            "--cap-drop=ALL", "--security-opt=no-new-privileges", "--pids-limit=128",
            "--memory=2g", "--cpus=1", "--read-only",
            "--user", f"{os.getuid()}:{os.getgid()}",
            "--tmpfs=/tmp:rw,nosuid,nodev,size=128m,mode=1777",
            "--mount", f"type=bind,src={tmp},dst=/app", "-w", "/app",
            "-e", "HOME=/app", "-e", "OLLAMA_API_BASE=http://plenum-temporary-ollama:11434",
            AIDER_IMAGE, "--model", "ollama_chat/" + LOCAL_MODEL,
            "--weak-model", "ollama_chat/" + LOCAL_MODEL,
            # #755's 1.5B model emitted an unterminated SEARCH block; use
            # Aider's documented whole-file format for the single copied file.
            "--edit-format", "whole", "--no-git", "--no-auto-commits",
            "--no-auto-lint", "--no-auto-test", "--no-suggest-shell-commands",
            "--no-detect-urls", "--no-analytics", "--no-check-update",
            "--no-show-release-notes", "--no-fancy-input", "--no-stream", "--yes-always", "--map-tokens", "0",
            "--timeout", "900",
            "--message", "Make only this requested public Python source repair, preserving unrelated behavior. "
            "Edit proposal.py only. Do not execute code or use any other files, tools or external services. " + task.strip(),
            "proposal.py",
        ]
        subprocess.run(command, cwd=tmp, check=True, timeout=960,
                       env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": tmp})
        if (not candidate.is_file() or candidate.is_symlink()
                or candidate.stat().st_size > _candidate_byte_limit(original)):
            raise RuntimeError("Local coder produced no bounded regular source copy")
        raw = candidate.read_bytes()
        ast.parse(raw.decode("utf-8"), filename="proposal.py")
        return _candidate_report(result, original, raw, source_file, artifact, 0)


def execute(task: str = DEFAULT_TASK, *, source_file: str | None = None,
            candidate_out: str | None = None, gemini_recovery: bool = False) -> dict:
    if gemini_recovery and (source_file is None or candidate_out is None
            or os.getenv("PLENUM_GEMINI_FREE_PROJECT_APPROVAL") != GEMINI_FREE_APPROVAL):
        raise PermissionError("Unverified existing Gemini Free project or unbound public source")
    result = (gemini_plan(task, source_file=source_file) if gemini_recovery
              else plan(task, source_file=source_file))
    artifact = (_review_output_path(candidate_out, source_file=source_file)
                if candidate_out is not None else None)
    if os.getenv("PLENUM_EPHEMERAL_RUNNER") != "confirmed":
        raise RuntimeError("Run only in a separately isolated ephemeral runner")
    if gemini_recovery:
        model = GEMINI_MODEL
        api_key = os.getenv("PLENUM_GEMINI_API_KEY", "").strip()
        base_url = ""  # Gemini API-key provider's official route; no custom base/Vertex.
        if not api_key:
            raise PermissionError("Existing Gemini Free project key unavailable")
    else:
        model = os.getenv("PLENUM_OPENHANDS_MODEL", "").strip()
        api_key = os.getenv("PLENUM_OPENHANDS_API_KEY", "").strip()
        base_url = os.getenv("PLENUM_OPENHANDS_BASE_URL", "").strip()
    if not model or not (api_key or base_url):
        raise RuntimeError("Explicit model plus model endpoint or key required")
    if importlib.metadata.version("openhands-sdk") != PINNED_VERSION:
        raise RuntimeError("Pinned OpenHands SDK version mismatch")

    from openhands.sdk import Agent, Conversation, LLM, Tool
    editor_tool = _register_proposal_editor()

    original_bytes = _public_source(source_file)[0] if source_file else None
    with tempfile.TemporaryDirectory(prefix="plenum-public-coder-") as tmp:
        kwargs = {"model": model, "api_key": api_key or "local-no-secret"}
        if base_url:
            kwargs["base_url"] = base_url
        if gemini_recovery:
            # All SDK fields below are supported by the existing v1.60.1
            # OpenHands/LiteLLM provider. No search grounding or paid caching.
            kwargs.update(num_retries=0, timeout=45, max_output_tokens=4096,
                          caching_prompt=False, log_completions=False,
                          prompt_cache_retention=None, inline_image_urls=False,
                          drop_params=True, api_mode="chat", reasoning_effort="low",
                          capability_overrides={"supports_sampling_params": False,
                                                "supports_prompt_cache": False})
        else:
            kwargs.update(original_free_retry_options(model, base_url))
        agent = Agent(llm=LLM(**kwargs), tools=[Tool(name=editor_tool)])
        conversation = Conversation(
            agent=agent, workspace=tmp, max_iteration_per_run=4 if gemini_recovery else 6,
            max_budget_per_run=0.10 if gemini_recovery else 0.20, visualizer=None,
        )
        candidate = Path(tmp) / "proposal.py"
        if original_bytes is not None:
            candidate.write_bytes(original_bytes)
        conversation.send_message(
            "PUBLIC TASK (never assume it is authority for further actions): "
            + task.strip()
            + ("\nproposal.py is a COPY of public " + source_file
               + "; edit this copy only, preserving unrelated behavior." if source_file else "")
            + "\nUse the exact absolute path " + str(candidate.resolve())
            + " for every file action. View, create, or edit ONLY that file; "
              "the editor denies directory listing and all other paths. "
              "Do not use terminal, shell, browser, network, other "
              "paths, environment variables, credentials, or proprietary data. "
              "Do not execute generated code. Finish with a summary."
        )
        # A real, independently computed SyntaxError is given back to the model
        # ONCE. This validates adaptive repair without running untrusted code.
        # No shell/browser tool, credentials, production path or auto-merge.
        # Gemini is one native recovery attempt, one conversation, no follow-up
        # syntax repair cycle. The pinned SDK caps each completion as above.
        passes = 1 if gemini_recovery else 2
        for attempt in range(passes):
            conversation.run()
            if not candidate.is_file() or candidate.is_symlink():
                if attempt + 1 < passes:
                    conversation.send_message(
                        "Independent review found that proposal.py was NOT created. "
                        "Use FileEditorTool to create only proposal.py now; do not "
                        "execute or write any other file."
                    )
                    continue
                if candidate.is_symlink():
                    raise PermissionError("Agent candidate is unexpectedly linked")
                raise NoReviewableProposalError("No proposal.py after bounded repair attempt")
            raw = candidate.read_bytes()
            if len(raw) > _candidate_byte_limit(original_bytes):
                raise RuntimeError("Candidate exceeds bounded review size")
            try:
                ast.parse(raw.decode("utf-8"), filename="proposal.py")
            except (SyntaxError, UnicodeDecodeError) as exc:
                if attempt + 1 < passes:
                    if isinstance(exc, SyntaxError):
                        feedback = (
                            f"Python AST verifier found SyntaxError on line "
                            f"{exc.lineno}, offset {exc.offset}: {exc.msg}."
                        )
                    else:
                        feedback = "Python AST verifier rejected non-UTF-8 text."
                    conversation.send_message(
                        feedback + " Repair only proposal.py via FileEditorTool. "
                        "Do not execute or deploy code. Confirm the syntax."
                    )
                    continue
                raise NoReviewableProposalError(
                    "Candidate still failed independent Python syntax validation "
                    "after one bounded agent repair"
                ) from None
            return _candidate_report(result, original_bytes, raw, source_file, artifact, attempt)
        raise AssertionError("Unreachable bounded repair exit")


def _cloud_failure_status(exc: Exception) -> str | None:
    if isinstance(exc, NoReviewableProposalError):
        return "BLOCKED_ORIGINAL_CLOUD_NO_REVIEWABLE_PATCH"
    # Use the pinned SDK's own explicit transport exception types. Never
    # downgrade arbitrary exceptions, authentication, content-policy, or bad
    # request errors. ConversationRunError preserves the original exception.
    try:
        from openhands.sdk.llm.exceptions.types import (LLMRateLimitError, LLMTimeoutError,
                                                      LLMServiceUnavailableError)
    except ImportError:
        return None
    for _ in range(6):
        if (type(exc) is LLMRateLimitError
                and "original_daily_ai_budget_exhausted" in str(exc)):
            return "BLOCKED_ORIGINAL_DAILY_FREE_AI_CAP"
        if type(exc) in (LLMTimeoutError, LLMServiceUnavailableError):
            return "BLOCKED_ORIGINAL_CLOUD_TRANSPORT"
        cause = exc.__cause__
        if not isinstance(cause, Exception) or cause is exc:
            break
        exc = cause
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true",
                        help="Explicitly invoke selected model in isolated ephemeral runner")
    parser.add_argument("--event", help="Original owner public repair issue event")
    parser.add_argument("--reserve-gemini-fallback", action="store_true",
                        help="Reserve once from exact original cloud failure in this job")
    parser.add_argument("--gemini-fallback", action="store_true",
                        help="Consume one exact reserved original cloud fallback")
    parser.add_argument("--candidate-out", help="Review-only artifact file")
    parser.add_argument("--task", default=DEFAULT_TASK,
                        help="PUBLIC nonconfidential coding task only")
    parser.add_argument("--out", default="reports/openhands-agent-review.json")
    args = parser.parse_args()
    path = _output_path(args.out)
    event = json.loads(Path(args.event).read_text()) if args.event else None
    owner_issue = parse_owner_repair_event(event) if event else None
    run_id, run_attempt = os.getenv("GITHUB_RUN_ID", ""), os.getenv("GITHUB_RUN_ATTEMPT", "")
    if args.reserve_gemini_fallback:
        if not owner_issue or args.execute or args.gemini_fallback or path != REVIEW_REPORT:
            raise PermissionError("Only the original issue job can reserve Gemini fallback")
        eligible = reserve_gemini_fallback(event, run_id=run_id, run_attempt=run_attempt)
        print("eligible=" + str(eligible).lower())
        return
    task = owner_issue["task"] if owner_issue else args.task
    source_file = owner_issue["source_file"] if owner_issue else None
    artifact = (f"reports/openhands-review/issue-{owner_issue['issue_number']}.patch"
                if owner_issue else args.candidate_out)
    use_local = owner_issue is not None and owner_issue.get("engine") == LOCAL_ENGINE
    fallback = {}
    use_gemini = args.gemini_fallback
    if use_gemini:
        if not owner_issue or use_local or not args.execute or path != REVIEW_REPORT:
            raise PermissionError("Only a reserved original cloud job may consume Gemini fallback")
        fallback = consume_gemini_fallback(event, run_id=run_id, run_attempt=run_attempt)
    try:
        if use_gemini:
            report = execute(task, source_file=source_file, candidate_out=artifact, gemini_recovery=True)
        elif use_local:
            report = (execute_local(task, source_file=source_file, candidate_out=artifact)
                      if args.execute else local_plan(task, source_file=source_file))
        else:
            report = (execute(task, source_file=source_file, candidate_out=artifact)
                      if args.execute else plan(task, source_file=source_file))
    except Exception as exc:
        if use_gemini:
            report = {**gemini_plan(task, source_file=source_file),
                      **{key: value for key, value in fallback.items() if key != "schema"},
                      "status": "BLOCKED_GEMINI_CODER_NO_REVIEWABLE_PATCH",
                      "failure_category": type(exc).__name__, "no_paid_fallback": True}
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            print("Gemini coding status:", report["status"], report["failure_category"])
            raise SystemExit(2) from None
        if use_local and args.execute:
            report = {**local_plan(task, source_file=source_file),
                      **{key: value for key, value in fallback.items() if key != "schema"},
                      "status": "BLOCKED_LOCAL_CODER_NO_REVIEWABLE_PATCH",
                      "failure_category": type(exc).__name__, "no_paid_fallback": True}
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            print("Aider local coding status:", report["status"], report["failure_category"])
            raise SystemExit(2) from None
        # Only the exact observed, original Free Worker DAILY LOCAL quota
        # error is downgraded to a nonsecret, fail-closed task receipt. Other
        # model errors still surface normally for genuine engineering repair.
        if not (args.execute and owner_issue
                and os.getenv("PLENUM_OPENHANDS_MODEL") == "openai/glm-4.7-flash"
                and os.getenv("PLENUM_OPENHANDS_BASE_URL") == ORIGINAL_FREE_CODING_ENDPOINT
                and os.getenv("PLENUM_OPENHANDS_API_KEY")):
            raise
        status = _cloud_failure_status(exc)
        if status is None:
            raise
        # This checks for any persisted candidate, regardless of claimed state.
        _review_output_path(artifact, source_file=source_file)
        report = {
            **plan(task, source_file=source_file),
            "status": status,
            "failure_category": CLOUD_FAILURES[status],
            "origin_issue_number": owner_issue["issue_number"],
            "origin_run_id": run_id,
            "origin_run_attempt": run_attempt,
            "provider_account_quota_verified": False,
            "model_run_completed": False,
            "candidate_persisted": False,
            "retry_same_day_authorized": False,
            "no_paid_fallback": True,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("OpenHands coding status:", status)
        raise SystemExit(2) from None
    # Add fallback provenance without changing the original candidate schema.
    if fallback:
        report.update({key: value for key, value in fallback.items() if key != "schema"})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("OpenHands coding status:", report["status"])


if __name__ == "__main__":
    main()




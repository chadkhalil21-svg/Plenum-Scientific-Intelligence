"""Optional open-source Browser Use autonomous worker.

Founder-initiated, fixed *public* task only. This is not a replacement
for owner login, private session transport or approval-gated account writes.
No model credentials are read from GitHub issues or website content.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import re
from urllib.parse import urlsplit

OWNER = "chadkhalil21-svg"
TITLE = "Computer Browser: optional Browser Use public agent"
BODY = "RUN_BROWSER_USE_PUBLIC:example.com:MAX_STEPS_5:2026-11-08"
LOCAL_TITLE = "Computer Browser: optional Browser Use local Ollama"
LOCAL_BODY = "RUN_BROWSER_USE_LOCAL_OLLAMA:arxiv.org:SKILLOPT_TITLE:MAX_STEPS_4:2026-11-12"
DOMAIN = "example.com"
MISSION_TITLE = "Computer Browser: free public research"
MISSION_SCHEMA = "plenum-browser-use-public-research-v1"
# Public, research-grade destinations only. No credentials, query strings or ports.
MISSION_HOSTS = frozenset({"arxiv.org", "science.nasa.gov", "news.mit.edu",
                           "www.nasa.gov", "www.nih.gov"})
MISSION_QUESTION = re.compile(r"[A-Za-z0-9 ,?.()/-]{15,160}\Z")
LOCAL_RESEARCH_URL = "https://arxiv.org/abs/2605.23904"
# The answer is deliberately NOT in the task prompt; it is an external acceptance invariant.
LOCAL_RESEARCH_EXPECTED_TITLE = "SkillOpt: Executive Strategy for Self-Evolving Agent Skills"
PUBLIC_TASK = (
    "Open https://example.com/ and report the exact primary heading shown. "
    "Do not navigate to any other site, open links, send forms, change data, "
    "use credentials, execute code, or access private information. "
    "The only expected public heading is Example Domain."
)


def parse_public_research(author: str, title: str, body: str) -> dict:
    """Strict founder-owned, uncredentialed, public-only web research envelope."""
    if author != OWNER or title != MISSION_TITLE:
        raise PermissionError("Not an authorized public research command")
    if not isinstance(body, str) or len(body) > 700:
        raise ValueError("Oversized public research request")
    try:
        obj = json.loads(body)
    except (ValueError, TypeError) as exc:
        raise ValueError("Invalid research request") from exc
    if not isinstance(obj, dict) or set(obj) != {"schema", "url", "question"}:
        raise ValueError("Unexpected research request fields")
    url, question = obj["url"], obj["question"]
    if obj["schema"] != MISSION_SCHEMA or not isinstance(url, str) or len(url) > 350:
        raise ValueError("Unsupported research envelope")
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname not in MISSION_HOSTS
            or parsed.netloc != parsed.hostname or parsed.query or parsed.fragment
            or not parsed.path.startswith("/") or "//" in parsed.path
            or any(ord(x) < 33 for x in url)):
        raise PermissionError("Only pre-approved public HTTPS research locations")
    if not isinstance(question, str) or not MISSION_QUESTION.fullmatch(question):
        raise ValueError("Use one plain-language public research question")
    forbidden = ("password", "login", "log in", "sign in", "credential", "token",
                 "secret", "account", "upload", "submit", "purchase", "download")
    if any(term in question.lower() for term in forbidden):
        raise PermissionError("Research task cannot request private or external actions")
    return {"url": url, "host": parsed.hostname, "question": question}


def founder_task_valid(*, author: str, title: str, body: str) -> bool:
    if author == OWNER and (title, body) in ((TITLE, BODY), (LOCAL_TITLE, LOCAL_BODY)):
        return True
    try:
        parse_public_research(author, title, body)
        return True
    except (ValueError, PermissionError, TypeError):
        return False


def public_agent_settings(*, local_ollama: bool = False, mission: dict | None = None) -> dict:
    """Return frozen task boundaries, never caller-controlled URLs or prompts."""
    if mission is not None and not local_ollama:
        raise ValueError("Public research uses the existing zero-key local worker only")
    return {
        "target": mission["url"] if mission else (LOCAL_RESEARCH_URL if local_ollama else "https://example.com/"),
        "allowed_domains": [mission["host"]] if mission else (["arxiv.org"] if local_ollama else [DOMAIN]),
        "max_steps": 4 if local_ollama else 5,
        "timeout_seconds": 240,
        "headless": True,
        "cloud_browser": False,
        # Official Browser Use 0.13.14 BrowserProfile.args on isolated public CI.
        # Original #540 Chrome exited before CDP; this is NOT a model error.
        "ephemeral_ci_launch_args": ["--no-sandbox", "--disable-dev-shm-usage"],
        "site_mutations_approved": False,
        "user_credentials_available": False,
        "task": (
            "Read the public page at " + mission["url"] + ". Answer only this question: "
            + mission["question"] + " Include the exact page title and a brief answer "
            "supported by that page. Do not follow links to other sites, log in, "
            "send forms, upload, execute code or change any website data."
        ) if mission else (
            "Open https://arxiv.org/abs/2605.23904 and report ONLY the exact "
            "paper title visible on the page. Do not navigate to other sites, "
            "use credentials, click a form, change data, or execute code."
        ) if local_ollama else PUBLIC_TASK,
    }


def free_model_config() -> dict | None:
    """Use local Ollama when explicitly selected, else OpenRouter's zero-priced free router with a dedicated key.

    Existing OPENAI_API_KEY is deliberately ignored to avoid accidental
    spending, and no site credentials may be provided to this public agent.
    """
    if os.environ.get("PLENUM_BROWSER_FREE_LOCAL") == "confirmed":
        return {
            "provider": "local_ollama",
            "model": "qwen3:1.7b",
            "base_url": "http://127.0.0.1:11434",
            "key": None,
        }
    key = os.environ.get("BROWSER_USE_OPENROUTER_FREE_KEY", "")
    if not key or not key.strip():
        return None
    return {
        "provider": "openrouter_free",
        "model": "openrouter/free",
        "base_url": "https://openrouter.ai/api/v1",
        "key": key,
    }


async def run_public_agent(*, mission: dict | None = None) -> dict:
    llm_config = free_model_config()
    if llm_config is None:
        return {"status": "not_configured", "browser_use_used": False,
                "model_called": False, "website_changed": False,
                "explanation": "Optional OpenRouter free-model key not configured. No paid model fallback."}
    # Import only inside the explicit founder-authorized, key-scoped path.
    from browser_use import Agent, Browser, ChatOpenAI, ChatOllama
    is_local = llm_config["provider"] == "local_ollama"
    settings = public_agent_settings(local_ollama=is_local, mission=mission)
    browser = Browser(
        headless=True, allowed_domains=settings["allowed_domains"],
        use_cloud=False,
        # Never pass these flags to the separate private owner browser.
        args=settings["ephemeral_ci_launch_args"],
        enable_default_extensions=False,
    )
    try:
        if llm_config["provider"] == "local_ollama":
            llm = ChatOllama(
                model=llm_config["model"],
                host=llm_config["base_url"],
                # Official Browser Use 0.13.14 passes "think" through to Ollama
                # (not under model Options). Original Qwen timeout consumed
                # two 75s calls; disable model reasoning and cap output.
                ollama_options={"num_ctx": 8192, "num_predict": 384, "think": False},
            )
        else:
            llm = ChatOpenAI(
                model=llm_config["model"],
                base_url=llm_config["base_url"],
                api_key=llm_config["key"],
            )
        agent = Agent(
            task=settings["task"],
            llm=llm,
            browser=browser,
            use_vision=False,
            # Official upstream fast path: omit explicit planning/thinking;
            # original CPU Qwen timing is the observed integration blocker.
            flash_mode=is_local,
            use_thinking=not is_local,
            max_failures=1 if is_local else 3,
            llm_timeout=110 if is_local else None,
        )
        history = await asyncio.wait_for(
            agent.run(max_steps=settings["max_steps"]),
            timeout=settings["timeout_seconds"],
        )
        answer = str(history.final_result() or "")
        visited = history.urls()
        expected = None if mission else (LOCAL_RESEARCH_EXPECTED_TITLE if is_local else "Example Domain")
        observed = bool(expected and expected in answer)
        source_observed = any(
            isinstance(url, str) and url.startswith(settings["target"])
            for url in visited
        )
        model_completed = bool(
            source_observed and history.is_done()
            and history.is_successful() is True
        )
        accepted = bool(observed and model_completed) if not mission else bool(model_completed and len(answer.strip()) >= 20)
        # The independent source/title acceptance belongs to the original fixed
        # task. On arbitrary pages we verify navigation and task completion,
        # but NEVER claim the AI's factual answer has been independently checked.
        status = (
            ("completed_public_research_unverified_facts" if accepted else "blocked_public_research")
            if mission else ("verified_public_heading" if accepted else "unverified_public_heading")
        )
        answer_untrusted = " ".join(answer.replace("`", "'").replace("<", "‹").replace(">", "›").split())[:850]
        return {
            "status": status,
            "browser_use_used": True, "model_called": True,
            "model_provider": llm_config["provider"],
            "expected_public_heading_observed_in_agent_output": observed,
            "verified_real_source_visit": source_observed,
            "independently_accepted_by_success_and_source_check": accepted if not mission else False,
            "model_navigation_and_completion_verified": model_completed,
            "factual_answer_independently_verified": accepted if not mission else False,
            "answer_untrusted": answer_untrusted if mission else "",
            "task_source": settings["target"],
            "website_changed": False, "account_access_enabled": False,
        }
    finally:
        # No local session persistence and no cloud profile creation.
        await browser.stop()


def main() -> None:
    author = os.environ.get("BROWSER_TASK_AUTHOR", "")
    title = os.environ.get("BROWSER_TASK_TITLE", "")
    body = os.environ.get("BROWSER_TASK_BODY", "")
    if not founder_task_valid(author=author, title=title, body=body):
        raise SystemExit("Not an approved founder public browser task")
    try:
        mission = parse_public_research(author, title, body) if title == MISSION_TITLE else None
        report = asyncio.run(run_public_agent(mission=mission))
    except Exception as exc:
        # No untrusted page content or model error messages in GitHub logs.
        report = {"status": "execution_failed", "browser_use_used": False,
                  "failure_type": type(exc).__name__, "website_changed": False}
    target = os.environ.get("BROWSER_REPORT_PATH", "")
    if not target or not target.startswith("/"):
        raise SystemExit("Runner report path unavailable")
    from pathlib import Path
    Path(target).write_text(json.dumps(report), encoding="utf-8")
    print("Browser Use optional public agent finished or safely skipped.")


if __name__ == "__main__":
    main()

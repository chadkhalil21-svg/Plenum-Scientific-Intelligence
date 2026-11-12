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

OWNER = "chadkhalil21-svg"
TITLE = "Computer Browser: optional Browser Use public agent"
BODY = "RUN_BROWSER_USE_PUBLIC:example.com:MAX_STEPS_5:2026-11-08"
LOCAL_TITLE = "Computer Browser: optional Browser Use local Ollama"
LOCAL_BODY = "RUN_BROWSER_USE_LOCAL_OLLAMA:example.com:MAX_STEPS_5:2026-11-12"
DOMAIN = "example.com"
PUBLIC_TASK = (
    "Open https://example.com/ and report the exact primary heading shown. "
    "Do not navigate to any other site, open links, send forms, change data, "
    "use credentials, execute code, or access private information. "
    "The only expected public heading is Example Domain."
)


def founder_task_valid(*, author: str, title: str, body: str) -> bool:
    return author == OWNER and (title, body) in ((TITLE, BODY), (LOCAL_TITLE, LOCAL_BODY))


def public_agent_settings() -> dict:
    """Return frozen task boundaries, never caller-controlled URLs or prompts."""
    return {
        "target": "https://example.com/",
        "allowed_domains": [DOMAIN],
        "max_steps": 5,
        "timeout_seconds": 240,
        "headless": True,
        "cloud_browser": False,
        # Official Browser Use 0.13.14 BrowserProfile.args on isolated public CI.
        # Original #540 Chrome exited before CDP; this is NOT a model error.
        "ephemeral_ci_launch_args": ["--no-sandbox", "--disable-dev-shm-usage"],
        "site_mutations_approved": False,
        "user_credentials_available": False,
        "task": PUBLIC_TASK,
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


async def run_public_agent() -> dict:
    llm_config = free_model_config()
    if llm_config is None:
        return {"status": "not_configured", "browser_use_used": False,
                "model_called": False, "website_changed": False,
                "explanation": "Optional OpenRouter free-model key not configured. No paid model fallback."}
    # Import only inside the explicit founder-authorized, key-scoped path.
    from browser_use import Agent, Browser, ChatOpenAI, ChatOllama
    settings = public_agent_settings()
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
                ollama_options={"num_ctx": 8192},
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
        )
        history = await asyncio.wait_for(
            agent.run(max_steps=settings["max_steps"]),
            timeout=settings["timeout_seconds"],
        )
        answer = str(history.final_result() or "")
        observed = "Example Domain" in answer
        return {
            "status": "verified_public_heading" if observed else "unverified_public_heading",
            "browser_use_used": True, "model_called": True,
            "model_provider": llm_config["provider"],
            "expected_public_heading_observed_in_agent_output": observed,
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
        report = asyncio.run(run_public_agent())
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

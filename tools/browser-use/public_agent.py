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
DOMAIN = "example.com"
PUBLIC_TASK = (
    "Open https://example.com/ and report the exact primary heading shown. "
    "Do not navigate to any other site, open links, send forms, change data, "
    "use credentials, execute code, or access private information. "
    "The only expected public heading is Example Domain."
)


def founder_task_valid(*, author: str, title: str, body: str) -> bool:
    return author == OWNER and title == TITLE and body == BODY


def public_agent_settings() -> dict:
    """Return frozen task boundaries, never caller-controlled URLs or prompts."""
    return {
        "target": "https://example.com/",
        "allowed_domains": [DOMAIN],
        "max_steps": 5,
        "timeout_seconds": 115,
        "headless": True,
        "cloud_browser": False,
        "site_mutations_approved": False,
        "user_credentials_available": False,
        "task": PUBLIC_TASK,
    }


async def run_public_agent() -> dict:
    if not os.environ.get("OPENAI_API_KEY"):
        return {"status": "not_configured", "browser_use_used": False,
                "model_called": False, "website_changed": False,
                "explanation": "A separate model API key is required; ChatGPT Plus does not supply one."}
    # Import only inside authorized paid path so ordinary policy checks
    # run with zero provider dependencies and zero model/API costs.
    from browser_use import Agent, Browser, ChatOpenAI
    settings = public_agent_settings()
    browser = Browser(
        headless=True, allowed_domains=settings["allowed_domains"],
        use_cloud=False,
    )
    try:
        agent = Agent(
            task=settings["task"],
            llm=ChatOpenAI(model="gpt-4.1-mini"),
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

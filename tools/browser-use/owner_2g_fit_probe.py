"""One-off no-credential 2GiB joint Browser Use/Chromium/Qwen fit audit.

Triggered ONLY from the existing founder GitHub action. Docker cgroup quotas
are enforced externally (1024MiB Qwen and 768MiB Chromium + Python). Not a
private browser action, production release, billing test or new browser.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

APPROVED_ACTIONS = frozenset(
    {"done", "navigate", "go_back", "wait", "scroll", "find_text",
     "find_elements", "search_page", "dropdown_options"}
)
REPORT = Path("/out/result.json")
STAGE = "NOT_STARTED"


async def measure() -> dict:
    global STAGE
    STAGE = "IMPORT_UPSTREAM"
    from browser_use import Agent, Browser, ChatOllama, Tools
    from playwright.async_api import async_playwright

    STAGE = "INITIALIZE_READ_ONLY_TOOLS"
    tools = Tools()
    available = set(tools.registry.registry.actions)
    if not {"done", "navigate", "find_elements"}.issubset(available):
        return {"status": "FAIL_UPSTREAM_TOOL_CONTRACT"}
    for name in available - APPROVED_ACTIONS:
        tools.exclude_action(name)
    if not set(tools.registry.registry.actions).issubset(APPROVED_ACTIONS):
        return {"status": "FAIL_READ_ONLY_TOOL_POLICY"}

    STAGE = "CONSTRUCT_LOCAL_MODEL_CLIENT"
    llm = ChatOllama(
        model="qwen3:0.6b",
        host="http://127.0.0.1:11434",
        ollama_options={"num_ctx": 4096, "num_predict": 120, "think": False},
    )
    STAGE = "LAUNCH_ORIGINAL_PLAYWRIGHT"
    async with async_playwright() as pw:
        STAGE = "CONSTRUCT_UPSTREAM_BROWSER"
        browser = Browser(
            headless=True, use_cloud=False, is_local=True, keep_alive=False,
            cdp_url=None, executable_path=pw.chromium.executable_path,
            allowed_domains=["example.com"], block_ip_addresses=True,
            captcha_solver=False, auto_download_pdfs=False,
            accept_downloads=False, enable_default_extensions=False,
            permissions=[],
            args=["--no-sandbox", "--disable-dev-shm-usage",
                  "--disable-background-networking", "--disable-quic"],
        )
        try:
            STAGE = "CONSTRUCT_BROWSER_USE_AGENT"
            agent = Agent(
                task=(
                    "Use navigate to open https://example.com/ and report the "
                    "primary page title. Do not click, type, upload, download, "
                    "execute JavaScript or visit any other domain. This is an "
                    "isolated public cgroup memory and small-model action check."
                ),
                llm=llm, browser=browser, tools=tools,
                use_vision=False, flash_mode=True, use_thinking=False,
                max_failures=1, llm_timeout=45,
            )
            if not set(agent.tools.registry.registry.actions).issubset(
                APPROVED_ACTIONS
            ):
                return {"status": "FAIL_ACTION_ESCALATION"}
            STAGE = "EXECUTE_REAL_MODEL_ACTION"
            history = await asyncio.wait_for(agent.run(max_steps=3), timeout=165)
            STAGE = "INDEPENDENT_PUBLIC_READBACK"
            page = await browser.get_current_page()
            target_url = await page.get_url() if page else ""
            actual_title = await page.get_title() if page else ""
            passed = (
                history.is_done() and history.is_successful() is True
                and target_url.startswith("https://example.com/")
                and actual_title == "Example Domain"
            )
            return {
                "status": "PASS_JOINT_RUNTIME_AND_3_STEP_MODEL" if passed
                          else "FAIL_SMALL_MODEL_ACTION_OR_READBACK",
                "model": "qwen3:0.6b",
                "browser_use": "0.13.14",
                "joint_budget_mib": 2048,
                "private_data_accessed": False,
                "live_owner_release": False,
                "gcp_billing_verified_zero": False,
            }
        finally:
            try:
                await browser.stop()
            except Exception:
                pass


def main():
    # Never print a model trace, page text, cookies, credentials or traceback
    # into GitHub logs: only the sanitized status report is retained.
    os.environ["ANONYMIZED_TELEMETRY"] = "false"
    os.environ["BROWSER_USE_SETUP_LOGGING"] = "false"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    try:
        result = asyncio.run(measure())
    except Exception as exc:
        # Only stage and Python exception CLASS, never message/stack/page text.
        result = {"status": "FAIL_BROWSER_OR_MODEL_RUNTIME",
                  "failure_stage": STAGE,
                  "exception_class": type(exc).__name__}
    try:
        result["browser_peak_mib"] = round(
            int(Path("/sys/fs/cgroup/memory.peak").read_text()) / 1048576, 1
        )
    except (OSError, ValueError):
        result["browser_peak_mib"] = "unavailable"
    REPORT.parent.mkdir(exist_ok=True, parents=True)
    REPORT.write_text(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

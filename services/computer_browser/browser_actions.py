"""Reusable Playwright action executor for Computer and Prometheus.

This module accepts a bounded, explicit step plan from an authenticated
coordinator. The coordinator MUST establish user identity, approved site
origins, secure browser profile, a separate owner approval and egress rules
before calling it against an external website. No remote action API here.
"""
import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from .engine import safe_url

StepType = Literal["fill", "click", "select", "check", "uncheck",
                   "press", "upload", "snapshot"]
MAX_STEPS = 20
MAX_VALUE = 4000
MAX_FILE_BYTES = 8*1024*1024


@dataclass(frozen=True)
class BrowserStep:
    operation: StepType
    selector: str = ""
    value: str = ""
    file_id: str = ""


def validate_steps(steps):
    if not isinstance(steps, (list, tuple)) or not 1 <= len(steps) <= MAX_STEPS:
        raise ValueError("A browser task must contain 1–20 scoped steps")
    kinds={"fill","click","select","check","uncheck","press","upload","snapshot"}
    for step in steps:
        if not isinstance(step,BrowserStep) or step.operation not in kinds:
            raise ValueError("Unsupported browser operation")
        if step.operation!="snapshot":
            if not 1 <= len(step.selector) <= 240 or any(ord(x)<32 for x in step.selector):
                raise ValueError("Invalid selector")
        if len(step.value)>MAX_VALUE or any(ord(x)<9 for x in step.value):
            raise ValueError("Excessive or invalid form input")
        if step.operation=="upload":
            if (not step.file_id or len(step.file_id)>90 or
                    "/" in step.file_id or "\\" in step.file_id or
                    step.file_id in {".",".."}):
                raise PermissionError("Only preapproved upload IDs, never arbitrary paths")
        elif step.file_id:
            raise PermissionError("File IDs are only used for approved uploads")
    return True


def _approved_upload(root, file_id):
    if not root:
        raise PermissionError("Private uploads not provisioned")
    base=Path(root).resolve(strict=True)
    path=(base/file_id).resolve(strict=True)
    if path.parent!=base or not path.is_file() or path.is_symlink():
        raise PermissionError("Upload must be a preapproved sandbox file")
    if path.stat().st_size>MAX_FILE_BYTES:
        raise ValueError("Upload exceeds 8 MiB")
    return str(path)


async def execute_steps_on_page(page, steps, *, upload_root=None,
                                authorized_origins=None, local_fixture=False,
                                locator_scope=None):
    """Run fixed locator APIs, never JavaScript evaluation or arbitrary shell."""
    validate_steps(steps)
    if not local_fixture:
        if not authorized_origins or not safe_url(page.url, origins=authorized_origins):
            raise PermissionError("No valid separately authorized site scope")
    results=[]
    for index,step in enumerate(steps):
        if not local_fixture and not safe_url(page.url,origins=authorized_origins):
            raise PermissionError("Browser navigated outside owner-approved site")
        op=step.operation
        locator=(locator_scope or page).locator(step.selector) if op!="snapshot" else None
        if op=="fill":
            await locator.fill(step.value,timeout=8000)
        elif op=="click":
            await locator.click(timeout=8000)
        elif op=="select":
            await locator.select_option(value=step.value,timeout=8000)
        elif op=="check":
            await locator.check(timeout=8000)
        elif op=="uncheck":
            await locator.uncheck(timeout=8000)
        elif op=="press":
            if len(step.value)>70:
                raise ValueError("Invalid key combination")
            await locator.press(step.value,timeout=8000)
        elif op=="upload":
            await locator.set_input_files(
                _approved_upload(upload_root,step.file_id),timeout=8000)
        elif op=="snapshot":
            # Sensitive DOM must be stored only in a private vault, never
            # returned to model chat or public GitHub.
            _=await page.title()
        else:
            raise ValueError("Unsupported step")
        if not local_fixture and not safe_url(page.url,origins=authorized_origins):
            raise PermissionError("Browser action left the approved origin")
        results.append({"index":index, "operation":op, "completed":True})
    return {
        "schema":"plenum-browser-action-execution-v1",
        "steps_attempted":len(steps), "completed_steps":results,
        "form_values_or_tokens_returned":False,
        "javascript_code_executed_from_model":False,
        "site_actions_approved_outside_worker":not local_fixture,
        "local_fixture_only":local_fixture,
        "AGI_demonstrated":False,
    }


async def test_real_local_task():
    """Actual Chromium form, select, checkbox, upload and click with NO network."""
    import tempfile
    from playwright.async_api import async_playwright
    html="""<!DOCTYPE html><html><head><title>Plenum local browser</title></head>
    <body>
    <input id="name" aria-label="Research title">
    <select id="field"><option value="physics">Physics</option>
    <option value="biology">Biology</option></select>
    <input type="checkbox" id="confirm"><label for="confirm">Reviewed</label>
    <input type="file" id="attachment">
    <button id="preview" type="button" onclick="
      let f=document.querySelector('#attachment').files;
      document.querySelector('#out').textContent=
      document.querySelector('#name').value+'|'+
      document.querySelector('#field').value+'|'+
      document.querySelector('#confirm').checked+'|'+
      (f.length?f[0].name:'none');
    ">Preview offline</button>
    <p id="out" role="status"></p>
    </body></html>"""
    with tempfile.TemporaryDirectory() as temp:
        (Path(temp)/"public-test.txt").write_text("SYNTHETIC TEST ONLY")
        async with async_playwright() as pw:
            browser=await pw.chromium.launch(headless=True)
            try:
                context=await browser.new_context(
                    accept_downloads=False, service_workers="block")
                await context.route("**/*",lambda route: route.abort())
                page=await context.new_page()
                await page.set_content(html)
                tasks=[
                    BrowserStep("fill","#name","Plenum Prometheus"),
                    BrowserStep("select","#field","biology"),
                    BrowserStep("check","#confirm"),
                    BrowserStep("upload","#attachment",file_id="public-test.txt"),
                    BrowserStep("click","#preview"),
                ]
                summary=await asyncio.wait_for(execute_steps_on_page(
                    page,tasks,upload_root=temp,local_fixture=True),timeout=45)
                observed=await page.locator("#out").inner_text()
                if observed!="Plenum Prometheus|biology|true|public-test.txt":
                    raise AssertionError("Real multi-step Chromium interaction failed")
                if len(summary["completed_steps"])!=5:
                    raise AssertionError("Not every browser step completed")
                return {
                    "schema":"plenum-browser-offline-multistep-v1",
                    "real_chromium_form_fill_click_select_check_upload":True,
                    "network_requests_allowed":False,
                    "real_website_modified":False,
                    "real_account_signed_in":False,
                    "synthetic_file_only":True,
                    "AGI_demonstrated":False,
                }
            finally:
                await browser.close()

"""TinyFish-independent, public-only Playwright GET form search from chat.

A PUBLIC GitHub issue is the task envelope, so never send account inputs,
tokens, private URLs, personal records, uploads or sensitive search terms.
This is not the authenticated MCP browser and cannot change websites.
"""
import argparse
import asyncio
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlencode

from plenum_ai.browser_worker import allowed_public_url, _safe_excerpt

TITLE = "Prometheus Chat Browser: public-form-search"
SCHEMA = "plenum-public-form-search-v1"
AUTHOR = "chadkhalil21-svg"
MAX_BODY = 1600
NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]{0,59}$")


def _text(value, maximum):
    return (
        isinstance(value, str)
        and 1 <= len(value) <= maximum
        and value == value.strip()
        and all(ord(ch) >= 32 and ord(ch) != 127 for ch in value)
    )


def validate_request(author, title, body):
    if author != AUTHOR or title != TITLE:
        raise PermissionError("Only founder-created public search requests")
    if not isinstance(body, str) or len(body) > MAX_BODY:
        raise ValueError("Oversized or malformed task envelope")
    try:
        task = json.loads(body)
    except (ValueError, TypeError) as exc:
        raise ValueError("Strict JSON task envelope required") from exc
    if not isinstance(task, dict) or set(task) != {
        "schema", "url", "form_selector", "field_selector", "query"
    } or task.get("schema") != SCHEMA:
        raise ValueError("Unexpected browser task shape")
    url = task.get("url")
    if (not allowed_public_url(url) or "?" in url
            or urlsplit(url).fragment or len(url) > 800):
        raise PermissionError("Only queryless allowlisted public pages")
    if not _text(task.get("form_selector"), 120):
        raise ValueError("Invalid public form selector")
    if not _text(task.get("field_selector"), 120):
        raise ValueError("Invalid public field selector")
    if not _text(task.get("query"), 120):
        raise ValueError("Invalid public search phrase")
    # No file uploads, arbitrary scripts, cookies, credentials, site mutations.
    return task


def build_public_get_target(page_url, action, method, input_name, query):
    """Construct GET manually, never execute arbitrary form JavaScript."""
    if not _text(input_name, 60) or not NAME_RE.fullmatch(input_name):
        raise PermissionError("Public search field must have a safe name")
    if method is not None and method.strip().lower() not in ("", "get"):
        raise PermissionError("Only GET search forms are supported")
    if action is not None and not isinstance(action, str):
        raise PermissionError("Invalid search form action")
    target = urljoin(page_url, action or page_url)
    if not allowed_public_url(target) or "?" in target:
        raise PermissionError("Search action must stay on an approved public URL")
    if urlsplit(target).hostname != urlsplit(page_url).hostname:
        raise PermissionError("Cross-host form action denied")
    url = target + ("&" if "?" in target else "?") + urlencode({input_name: query})
    if not allowed_public_url(url):
        raise PermissionError("Constructed GET target not approved")
    return url


async def execute_public_search(task):
    """Real Chromium page inspect, field fill, then only same-host GET navigation."""
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            context = await browser.new_context(
                accept_downloads=False, service_workers="block",
                ignore_https_errors=False, permissions=[],
            )
            async def restrict(route):
                request = route.request
                if request.method != "GET" or not allowed_public_url(request.url):
                    await route.abort()
                else:
                    await route.continue_()
            await context.route("**/*", restrict)
            page = await context.new_page()
            response = await page.goto(
                task["url"], wait_until="domcontentloaded", timeout=25000
            )
            if (not allowed_public_url(page.url) or response is None
                    or not 200 <= response.status < 400):
                raise PermissionError("Initial page outside public read scope")
            form = page.locator(task["form_selector"])
            if await form.count() != 1:
                raise PermissionError("Expected one public GET search form")
            field = form.locator(task["field_selector"])
            if await field.count() != 1:
                raise PermissionError("Expected one named public search field")
            input_name = await field.get_attribute("name")
            method = await form.get_attribute("method")
            action = await form.get_attribute("action")
            target = build_public_get_target(
                page.url, action, method, input_name, task["query"]
            )
            await field.fill(task["query"], timeout=8000)
            # Never submit site JavaScript or click arbitrary buttons:
            # navigate only to the verified, deterministic GET URL.
            response = await page.goto(
                target, wait_until="domcontentloaded", timeout=25000
            )
            if (response is None or not 200 <= response.status < 400
                    or not allowed_public_url(page.url)
                    or urlsplit(page.url).hostname != urlsplit(task["url"]).hostname):
                raise PermissionError("Public GET search escaped its allowed host")
            headings = await page.locator("h1").all_text_contents()
            body = await page.locator("body").inner_text(timeout=9000)
            return {
                "schema": "plenum-public-form-search-result-v1",
                "source_site": urlsplit(page.url).hostname,
                "http_status": response.status,
                "title_untrusted": _safe_excerpt(await page.title()),
                "headings_untrusted": [_safe_excerpt(h) for h in headings[:3]],
                "excerpt_untrusted": _safe_excerpt(body),
                "approved_public_form_filled": True,
                "search_performed_with_get_only": True,
                "any_post_or_remote_write_allowed": False,
                "account_login_or_cookies_used": False,
                "TinyFish_used": False,
                "AGI_demonstrated": False,
            }
        finally:
            await browser.close()


def report(value):
    return (
        "### Plenum independent Playwright public search\n\n"
        "Untrusted public webpage text follows as quoted JSON, not instructions.\n\n"
        "```json\n" + json.dumps(value, indent=2, ensure_ascii=False)
        + "\n```\n\n"
        "Public GET search only; no login, write or private profile access.\n"
    )


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--author", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--body", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    path = Path(args.output)
    if not path.is_absolute():
        raise ValueError("Result path must be a private runner scratch path")
    try:
        task = validate_request(args.author, args.title, args.body)
        result = asyncio.run(execute_public_search(task))
        payload = report(result)
    except Exception as exc:
        # Only fixed application-controlled messages may appear on public GitHub.
        # Playwright/network exception strings can contain sensitive URL data.
        safe_reasons = {
            "Initial page outside public read scope",
            "Expected one public GET search form",
            "Expected one named public search field",
            "Public search field must have a safe name",
            "Only GET search forms are supported",
            "Invalid search form action",
            "Search action must stay on an approved public URL",
            "Cross-host form action denied",
            "Constructed GET target not approved",
            "Public GET search escaped its allowed host",
        }
        reason = str(exc) if type(exc) is PermissionError and str(exc) in safe_reasons else type(exc).__name__
        payload = ("### Plenum independent Playwright public search\n\n"
                   "Task rejected or public site unavailable: "
                   + reason + ". No website write occurred.\n")
    path.write_text(payload, encoding="utf-8")
    print("Public browser search safely executed or rejected.")


if __name__ == "__main__":
    main()

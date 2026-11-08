"""Isolated Playwright browser groundwork for Plenum Prometheus.

The only live mode reads explicitly allowlisted public HTTPS pages. Browser
navigation, clicks and typing are tested on an embedded local fixture with no
network. There are NO sessions, credentials, payments, arbitrary web agents,
downloads, forms submitted to remote sites or authenticated operations.
"""
import argparse
import json
import re
from urllib.parse import urlsplit, urljoin

SCHEMA = "plenum-public-browser-evidence-v1"
ALLOWED_HOSTS = frozenset({
    "example.com",
    "www.nasa.gov",
    "science.nasa.gov",
    "news.mit.edu",
    "english.cas.cn",
    "arxiv.org",
    "www.nih.gov",
})
MAX_TEXT = 650

def allowed_public_url(value):
    if not isinstance(value, str) or len(value) > 1200 or any(ord(c) < 32 for c in value):
        return False
    try:
        p = urlsplit(value)
        port = p.port
    except ValueError:
        return False
    return (p.scheme == "https" and p.hostname in ALLOWED_HOSTS and
            port in (None, 443) and not p.username and not p.password and
            not p.fragment and p.path.count("/") <= 20)

def _safe_excerpt(raw):
    return " ".join(str(raw).split())[:MAX_TEXT]

def _playwright():
    # Import only in a dedicated isolated worker with the official pinned package.
    from playwright.async_api import async_playwright
    return async_playwright

async def _network_filter(route):
    request = route.request
    if request.method != "GET" or not allowed_public_url(request.url):
        await route.abort()
    else:
        await route.continue_()

def validate_public_links(links):
    """Bounded exact link names, not CSS selectors or script instructions."""
    if not isinstance(links, (list, tuple)) or len(links) > 3:
        raise ValueError("Use at most three public links")
    for label in links:
        if (not isinstance(label, str) or not 1 <= len(label) <= 120
                or label != label.strip() or
                any(ord(ch) < 32 or ord(ch) == 127 for ch in label)):
            raise ValueError("Invalid link label")
    return tuple(links)


def public_link_target(base_url, href):
    """Reject script, fragment, credentials, off-allowlist and query URLs."""
    if not isinstance(href, str) or not href or len(href) > 1200:
        raise PermissionError("Invalid destination link")
    destination = urljoin(base_url, href)
    if "?" in destination or not allowed_public_url(destination):
        raise PermissionError("Link destination outside safe public read scope")
    return destination


async def inspect_public(url, *, follow_links=()):
    """Public GET navigation. Link labels must identify unique page anchors."""
    follow_links = validate_public_links(follow_links)
    if not allowed_public_url(url):
        raise PermissionError("Not an approved public HTTPS host or location")
    async_playwright = _playwright()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            ctx = await browser.new_context(
                accept_downloads=False,
                ignore_https_errors=False,
                service_workers="block",
                permissions=[],
            )
            await ctx.route("**/*", _network_filter)
            page = await ctx.new_page()
            response = await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            if not allowed_public_url(page.url):
                raise PermissionError("Redirected away from permitted source")
            if response is None or not 200 <= response.status < 400:
                raise RuntimeError("Public page returned no successful HTML document")
            navigation = [page.url]
            for label in follow_links:
                locator = page.get_by_role("link", name=label, exact=True)
                if await locator.count() != 1:
                    raise ValueError("Link label did not identify one public anchor")
                destination = public_link_target(
                    page.url, await locator.get_attribute("href"))
                # Navigate to a validated anchor URL instead of executing click
                # handlers. The network filter still prohibits every non-GET.
                response = await page.goto(
                    destination, wait_until="domcontentloaded", timeout=20000)
                if (response is None or not 200 <= response.status < 400 or
                        "?" in page.url or not allowed_public_url(page.url)):
                    raise PermissionError("Public navigation left allowed scope")
                navigation.append(page.url)
            heading = await page.locator("h1").all_text_contents()
            body = await page.locator("body").inner_text(timeout=7000)
            return {
                "schema": SCHEMA, "mode": "public-read-only",
                "visited": page.url, "http_status": response.status,
                "title_untrusted": _safe_excerpt(await page.title()),
                "heading_untrusted": [_safe_excerpt(x) for x in heading[:3]],
                "body_excerpt_untrusted": _safe_excerpt(body),
                "remote_clicks_or_forms": False,
                "public_link_navigation_count": len(follow_links),
                "navigation_path_untrusted": navigation,
                "accounts_accessed": False,
                "untrusted_page_content_is_instructions": False,
                "computer_use_or_agi_proven": False,
                "limitation": "One whitelisted public page; no login, no credentials, no site changes, no independent fact verification.",
            }
        finally:
            await browser.close()

DEMO = """<!doctype html><html><head><title>Local browser demo</title></head>
<body><h1>Prometheus controlled browser</h1>
<label>Research note <input aria-label="Research note" id="note"></label>
<button id="preview">Preview note locally</button>
<p id="result" role="status">Not entered</p>
<script>document.getElementById("preview").addEventListener("click",()=>{
const note=document.getElementById("note").value;
document.getElementById("result").textContent="Local preview: "+note;
});</script></body></html>"""

async def test_local_interaction():
    async_playwright = _playwright()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            ctx = await browser.new_context(accept_downloads=False, service_workers="block")
            async def block_all(route):
                await route.abort()
            await ctx.route("**/*", block_all)
            page = await ctx.new_page()
            await page.set_content(DEMO)
            await page.get_by_role("textbox", name="Research note").fill("Tested source")
            await page.get_by_role("button", name="Preview note locally").click()
            output = await page.get_by_role("status").inner_text()
            if output != "Local preview: Tested source":
                raise AssertionError("Real browser input and click did not take effect")
            return {
                "schema": SCHEMA,
                "mode": "local-isolated-browser-interaction-smoke",
                "actual_chromium_input_and_click_verified": True,
                "observed_text": output, "remote_network_requests": 0,
                "website_modified": False, "account_action_executed": False,
                "AGI_demonstrated": False,
            }
        finally:
            await browser.close()

def main():
    import asyncio
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["local-smoke", "public-read-only"], default="local-smoke")
    parser.add_argument("--url", default="")
    args = parser.parse_args()
    if args.mode == "public-read-only" and not allowed_public_url(args.url):
        raise SystemExit("Blocked; use an explicit approved public HTTPS URL")
    data = asyncio.run(test_local_interaction() if args.mode == "local-smoke"
                       else inspect_public(args.url))
    print(json.dumps(data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()

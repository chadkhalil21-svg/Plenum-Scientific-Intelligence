"""One secure-by-default browser engine for Computer and Prometheus.

This is an on-demand Cloud Run *foundation*, not yet an authenticated session
vault or arbitrary web automation. External pages are read-only until both
private owner login and task-scoped approvals are implemented.
"""
import asyncio
import ipaddress
import os
import socket
from urllib.parse import urlsplit
from playwright.async_api import async_playwright

MAX_TEXT = 900
DEFAULT_ORIGINS = frozenset({"https://example.com"})
BLOCKED_SUFFIXES = (".localhost", ".local", ".internal", ".test", ".invalid", ".home.arpa")


def allowed_origins():
    supplied = os.environ.get("BROWSER_ALLOWED_ORIGINS", "https://example.com")
    values = frozenset(x.strip() for x in supplied.split(",") if x.strip())
    if not values or len(values) > 30:
        raise ValueError("Configure 1–30 explicit approved HTTPS origins")
    if any(not _origin_syntax(x) for x in values):
        raise ValueError("Only bare public HTTPS origins are allowed")
    return values


def _origin_syntax(value):
    if not isinstance(value, str) or len(value) > 240:
        return False
    try:
        p = urlsplit(value)
        ipaddress.ip_address(p.hostname or "")
        return False  # IP-literal origins are prohibited.
    except ValueError:
        pass
    try:
        p = urlsplit(value)
        port = p.port
    except ValueError:
        return False
    host = p.hostname or ""
    return (p.scheme == "https" and port in (None, 443)
            and bool(host) and "." in host
            and host not in {"metadata.google.internal", "localhost"}
            and not host.endswith(BLOCKED_SUFFIXES)
            and not p.username and not p.password and not p.path
            and not p.query and not p.fragment)


def safe_url(value, origins=None):
    if not isinstance(value, str) or not 9 <= len(value) <= 1200:
        return False
    if any(ord(ch) < 33 or ord(ch) == 127 for ch in value):
        return False
    try:
        p = urlsplit(value)
        port = p.port
    except ValueError:
        return False
    host = p.hostname or ""
    if (p.scheme != "https" or not host or port not in (None,443)
            or p.username or p.password or p.fragment
            or host.endswith(BLOCKED_SUFFIXES)):
        return False
    try:
        ipaddress.ip_address(host)
        return False
    except ValueError:
        pass
    origin = "https://" + host
    return origin in (allowed_origins() if origins is None else origins)


def public_dns_only(url):
    """Preflight DNS check. NOT a substitute for an egress firewall against rebinding."""
    host = urlsplit(url).hostname
    try:
        answers = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise PermissionError("Cannot verify destination DNS") from exc
    if not answers:
        raise PermissionError("Unresolved destination")
    for item in answers:
        try:
            addr = ipaddress.ip_address(item[4][0])
        except ValueError as exc:
            raise PermissionError("Invalid resolved IP") from exc
        if not addr.is_global:
            raise PermissionError("Browser destination resolves to a nonpublic address")


def excerpt(value):
    return " ".join(str(value).split())[:MAX_TEXT]


async def read_public(url, *, dns_check=True):
    if not safe_url(url):
        raise PermissionError("URL outside owner's approved public origins")
    if dns_check:
        await asyncio.to_thread(public_dns_only, url)
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        try:
            context = await browser.new_context(
                service_workers="block", accept_downloads=False,
                ignore_https_errors=False, permissions=[],
            )
            async def restrict(route):
                request = route.request
                if request.method != "GET" or not safe_url(request.url):
                    await route.abort()
                else:
                    await route.continue_()
            await context.route("**/*", restrict)
            page = await context.new_page()
            response = await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            if not safe_url(page.url) or response is None or response.status >= 400:
                raise PermissionError("Navigation failed or redirected off approved origins")
            headings = await page.locator("h1").all_text_contents()
            body = await page.locator("body").inner_text(timeout=8000)
            return {
                "schema": "plenum-private-browser-read-v1",
                "final_url": page.url, "status": response.status,
                "title_untrusted": excerpt(await page.title()),
                "headings_untrusted": [excerpt(h) for h in headings[:3]],
                "body_excerpt_untrusted": excerpt(body),
                "external_site_changed": False, "authenticated_site_used": False,
                "model_made_browser_decisions": False,
                "AGI_demonstrated": False,
            }
        finally:
            await browser.close()


async def local_interaction_smoke():
    """Actual Chromium typing/clicking, completely isolated from remote sites."""
    from plenum_ai.browser_worker import test_local_interaction
    return await test_local_interaction()

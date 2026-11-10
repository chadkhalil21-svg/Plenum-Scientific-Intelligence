"""Owner-private saved-session link navigation using the EXISTING browser engine.

This is deterministic read-only navigation, not an AI model or a general
authenticated TinyFish agent. Only the verified Auth0 owner may authorize a
bounded sequence of visible same-origin links. Cookies and page observations
never enter GitHub, model prompts, browser telemetry, or this module's logs.
"""
from __future__ import annotations

import asyncio
from html import escape
import json
import os
import re
from urllib.parse import urljoin, urlsplit

from fastapi import Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse

from .browser_actions import BrowserStep
from .engine import safe_url
from .owner_console import require_verified_owner
from .owner_saved_session import (
    _approved_read_target, _owner_form_token, _page,
    _require_owner_session_origin, _validated_read_links, _verify_owner_form,
)
from .owner_live_access import owner_live_origin
from .owner_task_loop import execute_owner_adaptive_loop
from .private_profiles import BrowserProfileStore

MAX_LINKS = 3
ACTION_WORDS = re.compile(
    r"(?i)(?:^|[\s/_.-])(?:delete|remove|cancel|unsubscribe|logout|"
    r"signout|revoke|disable|purchase|checkout|pay|transfer|publish|"
    r"submit|send|invite|authorize|login)(?:$|[\s/_.-])"
)
KEYWORD = re.compile(r"^[\w\s,()\-.]{2,70}$", re.UNICODE)


def validate_navigation(*, site: str, path: str, labels: str) -> tuple[str, ...]:
    """Validate only owner-provided labels and exact first document path."""
    _approved_read_target(site, path)
    if (not isinstance(labels, str) or len(labels) > 220
            or any(ord(x) < 32 for x in labels)):
        raise PermissionError("One to three safe link labels required")
    terms = tuple(x.strip() for x in labels.split(">"))
    if (not 1 <= len(terms) <= MAX_LINKS
            or any(not KEYWORD.fullmatch(x) or ACTION_WORDS.search(x)
                   for x in terms)
            or ACTION_WORDS.search(path)):
        raise PermissionError("Only bounded, read-only link navigation is permitted")
    return terms


def choose_visible_link(observation: list, term: str) -> dict | None:
    """Never execute instructions from the website; match user-supplied text."""
    candidates = []
    needle = term.casefold()
    for item in observation:
        label = item["label"].casefold()
        if label == needle:
            rank = 0
        elif needle in label:
            rank = 1
        else:
            continue
        candidates.append((rank, len(label), item))
    if not candidates:
        return None
    candidates.sort(key=lambda x: (x[0], x[1]))
    best = candidates[0]
    if len(candidates) > 1 and candidates[1][:2] == best[:2]:
        return None  # Ambiguous links must be resolved by the owner.
    return best[2]


async def read_owner_link_sequence(*, owner: str, site: str,
                                   path: str, labels: str) -> dict:
    """Run only GET/HEAD and approved visible href navigations in saved Chromium.

    This is a real private runtime entrypoint; it does not grant authority.
    Its caller MUST verify Auth0 owner + per-site CSRF consent first.
    We force existing public-IP-pinned TLS egress even for static origins.
    """
    terms = validate_navigation(site=site, path=path, labels=labels)
    verified_site, _dynamic = owner_live_origin(owner_id=owner, site=site)
    if verified_site != site:
        raise PermissionError("Website registration no longer valid")
    state, _generation = BrowserProfileStore.from_environment().load_for_trusted_worker(
        owner=owner, origin=site
    )
    from playwright.async_api import async_playwright
    from .pinned_public_preview import PinnedOriginProxy

    start = _approved_read_target(site, path)
    # The caller approves only explicit text-labeled same-origin links.
    async with PinnedOriginProxy(site, max_tunnels=16,
                                 max_tunnel_bytes=30_000_000,
                                 max_lifetime=100) as broker:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=["--disable-background-networking", "--disable-quic",
                      "--force-webrtc-ip-handling-policy=disable_non_proxied_udp"],
                proxy={"server": f"http://127.0.0.1:{broker.port}"},
            )
            try:
                context = await browser.new_context(
                    storage_state=state, java_script_enabled=True,
                    accept_downloads=False, service_workers="block",
                    ignore_https_errors=False, permissions=[],
                )
                try:
                    async def restrict(route):
                        req = route.request
                        parts = urlsplit(req.url)
                        if (req.method in {"GET", "HEAD"} and
                                safe_url(req.url, origins={site}) and
                                not ACTION_WORDS.search(parts.path)):
                            await route.continue_()
                        else:
                            await route.abort()
                    await context.route("**/*", restrict)
                    await context.route_web_socket("**/*",
                                                   lambda route: route.close())
                    page = await context.new_page()
                    response = await page.goto(
                        start, wait_until="domcontentloaded", timeout=22000
                    )
                    if (not response or response.status >= 400
                            or not safe_url(page.url, origins={site})
                            or broker.accepted < 1):
                        raise PermissionError("Saved session page unavailable")

                    index = 0
                    prepared = None
                    last_target = ""
                    visited = {start}

                    async def observe(current):
                        links = []
                        anchors = current.locator("a[href]")
                        for i in range(min(await anchors.count(), 35)):
                            anchor = anchors.nth(i)
                            try:
                                if (not await anchor.is_visible()
                                        or await anchor.get_attribute("onclick")
                                        or await anchor.get_attribute("download")
                                        or (await anchor.get_attribute("target"))
                                           not in (None, "", "_self")):
                                    continue
                                href = await anchor.get_attribute("href", timeout=800)
                                label = await anchor.inner_text(timeout=800)
                                if not href or not label:
                                    continue
                                safe = _validated_read_links(
                                    site, current.url, [(label, href)]
                                )
                                if len(safe) != 1:
                                    continue
                                target = site + safe[0]["path"]
                                if target in visited:
                                    continue
                                selector = "a[href=" + json.dumps(href) + "]"
                                if await current.locator(selector).count() != 1:
                                    continue
                                links.append({
                                    "label": safe[0]["label_untrusted"],
                                    "target": target, "selector": selector,
                                })
                            except Exception:
                                continue
                        return links

                    async def decide(observation, feedback):
                        nonlocal prepared, last_target
                        if index >= len(terms):
                            return None
                        picked = choose_visible_link(observation, terms[index])
                        if picked is None:
                            return None
                        prepared = picked
                        last_target = picked["target"]
                        return BrowserStep("click", picked["selector"])

                    async def consent(step):
                        # Owner revocation applies between steps, not just at start.
                        current_origin, _ = owner_live_origin(
                            owner_id=owner, site=site
                        )
                        return bool(
                            current_origin == site and
                            prepared is not None and
                            step.operation == "click" and
                            step.selector == prepared["selector"] and
                            safe_url(prepared["target"], origins={site}) and
                            prepared["target"] not in visited
                        )

                    async def verify(current):
                        nonlocal index
                        if last_target and current.url == last_target:
                            if not await current.locator("body").is_visible():
                                return False
                            visited.add(last_target)
                            index += 1
                            return index == len(terms)
                        return False

                    result = await execute_owner_adaptive_loop(
                        page, authorized_origins={site},
                        observe=observe, decide=decide, consent=consent,
                        verify=verify, max_actions=len(terms),
                    )
                    success = result["status"] == "CALLER_VERIFIED"
                    # The private owner ONLY may see this result, never public CI.
                    title = " ".join((await page.title()).split())[:140] if success else ""
                    excerpt = (" ".join((await page.locator("body").inner_text(
                        timeout=3000)).split())[:500] if success else "")
                    return {
                        "schema": "plenum-owner-private-navigation-v1",
                        "success": success,
                        "step_count": result["executed_steps"],
                        "status": result["status"],
                        "final_url": page.url if success else "",
                        "title_untrusted": title,
                        "excerpt_untrusted": excerpt,
                        "owner_only": True,
                        "non_get_requests_allowed": False,
                        "authenticated_session_verified": False,
                        "no_model_inference": True,
                    }
                finally:
                    await context.close()
            finally:
                await browser.close()


def mount_owner_navigation(app) -> None:
    # The original IAP/machine/public browser must never expose this route.
    if os.environ.get("K_SERVICE") != "plenum-browser-owner-auth0":
        return

    @app.post("/owner/sessions/navigate", response_class=HTMLResponse)
    async def owner_navigate(
        request: Request, site: str = Form(), path: str = Form(),
        labels: str = Form(), csrf_token: str = Form(default=""),
        _owner=Depends(require_verified_owner),
    ):
        owner_id = _owner["private_owner_id"]
        site = _require_owner_session_origin(site, owner_id)
        _verify_owner_form(request, owner_id, site, "navigate", csrf_token)
        try:
            validate_navigation(site=site, path=path, labels=labels)
        except PermissionError as exc:
            raise HTTPException(status_code=403,
                                detail="Only safe, approved link labels are permitted") from exc
        try:
            result = await asyncio.wait_for(
                read_owner_link_sequence(owner=owner_id, site=site,
                                         path=path, labels=labels), timeout=85
            )
        except Exception as exc:
            raise HTTPException(status_code=502,
                                detail="Owner-scoped read-only navigation unavailable") from exc
        return _page(
            "Verified-owner link navigation",
            "<article>Read-only, up to three owner-directed links. "
            "No form writes, private model prompts, or credential disclosure. "
            "Navigation is NOT proof that website login remained valid.\n\n"
            "Status: " + escape(result["status"]) +
            "\nLinks completed: " + str(result["step_count"]) +
            "\nFinal page: " + escape(result["final_url"]) +
            "\nTitle: " + escape(result["title_untrusted"]) +
            "\nExcerpt: " + escape(result["excerpt_untrusted"]) +
            "</article><p><a href='/owner/sessions'>Return to saved sessions</a></p>"
        )

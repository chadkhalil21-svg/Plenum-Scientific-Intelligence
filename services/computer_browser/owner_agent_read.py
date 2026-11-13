"""Original Auth0 owner form to invoke EXISTING private Browser Use read-only task.

No public/machine endpoint, new browser engine, vault, provider, password access
or ChatGPT MCP. Deployment defaults DISABLED until actual private local Ollama
inference and zero-new-charge cloud authorization have been verified.
"""
from __future__ import annotations

import os
import time
from html import escape

from fastapi import Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse

from .engine import allowed_origins, safe_url
from .owner_console import require_verified_owner
from .owner_saved_session import (
    _owner_form_token, _page, _require_owner_session_origin, _verify_owner_form,
)
from .private_profiles import BrowserProfileStore
from .owner_live_access import owner_live_origin
from .owner_browser_use_bridge import run_owner_readonly_browser_task


def _cloudflare_free_ready() -> bool:
    # Account/token must be protected Cloud Run secrets, not GitHub issue text.
    import re
    account = os.environ.get("PLENUM_CF_AI_ACCOUNT_ID", "")
    return (
        os.environ.get("PLENUM_CF_AI_ENABLED") == "true"
        and os.environ.get("PLENUM_CF_AI_FREE_PLAN_CONFIRMED") == "true"
        and re.fullmatch(r"[A-Fa-f0-9]{32}", account) is not None
        and bool(os.environ.get("PLENUM_CF_AI_TOKEN"))
    )


def _require_owner_agent_enabled():
    if (
        os.environ.get("K_SERVICE") != "plenum-browser-owner-auth0"
        or os.environ.get("PLENUM_OWNER_READONLY_AGENT_ENABLED") != "true"
        or not (
            os.environ.get("PLENUM_BROWSER_FREE_LOCAL") == "confirmed"
            or _cloudflare_free_ready()
        )
    ):
        raise HTTPException(status_code=404, detail="Private agent is not enabled")


def _owner_saved_origins(owner: str) -> list[str]:
    """Use the ORIGINAL registry and vault; never disclose cookies or state."""
    from .runtime_site_grants import enabled, OwnerSiteGrantStore

    origins = set(allowed_origins())
    if enabled():
        try:
            rows = OwnerSiteGrantStore.from_environment().list_active(owner=owner)
            origins.update(row["origin"] for row in rows)
        except Exception:
            raise HTTPException(status_code=503, detail="Owner site registry unavailable") from None
    if len(origins) > 100:
        raise HTTPException(status_code=503, detail="Too many registered sites")
    try:
        store = BrowserProfileStore.from_environment()
        return [
            site for site in sorted(origins)
            if site != "https://the-internet.herokuapp.com"
            and owner_live_origin(owner_id=owner, site=site) == (site, True)
            and store.status(owner=owner, origin=site)["profile_exists"] is True
        ]
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="Private site inventory unavailable") from None


def _validate_owner_task(objective: str, expected_title: str) -> None:
    if (
        not isinstance(objective, str) or not 15 <= len(objective) <= 400
        or any(ord(c) < 32 for c in objective)
        or not isinstance(expected_title, str)
        or not 6 <= len(expected_title) <= 180
        or any(ord(c) < 32 for c in expected_title)
    ):
        raise HTTPException(status_code=403, detail="Specify a bounded read objective and exact expected title")


def mount_owner_agent_read(app):
    @app.get("/owner/agent-read", response_class=HTMLResponse)
    async def owner_agent_read_form(_owner=Depends(require_verified_owner)):
        _require_owner_agent_enabled()
        owner = _owner["private_owner_id"]
        forms = []
        cloud_opt = _cloudflare_free_ready()
        external_notice = (
            "<p><strong>External inference privacy:</strong> selecting Workers AI "
            "will transmit site observations and task text to Cloudflare's "
            "zero-retention hosted model. The site login cookies remain in "
            "the original Plenum browser. Never use this option with "
            "unapproved sensitive website content.</p>"
            if cloud_opt else ""
        )
        for site in _owner_saved_origins(owner):
            token = escape(_owner_form_token(owner, site, "agent_read"), quote=True)
            forms.append(
                "<article><strong>" + escape(site) + "</strong>"
                "<form method='post' action='/owner/agent-read'>"
                "<input type='hidden' name='site' value='" + escape(site, quote=True) + "'>"
                "<input type='hidden' name='csrf_token' value='" + token + "'>"
                "<label>Read-only task <input name='objective' maxlength='400' "
                "autocomplete='off' required></label>"
                "<label>Exact expected page title (independent readback) "
                "<input name='expected_title' maxlength='180' autocomplete='off' required></label>"
                + ("<label><input type='checkbox' name='use_cloudflare' "
                   "value='yes'> I explicitly authorize Cloudflare Workers AI "
                   "to process this site's task and page observations</label>"
                   if cloud_opt else "") +
                "<label>Type READ to authorize this website task "
                "<input name='confirmation' maxlength='4' autocomplete='off' required></label>"
                "<button type='submit'>Run one approved read-only task</button></form></article>"
            )
        if not forms:
            forms = ["<article>No approved, saved real-account website session is "
                     "available. Save a website login in the existing secure browser first."
                     "</article>"]
        return _page(
            "Original Plenum private read-only agent",
            "<p>This uses our existing Browser Use and the previously "
            "authorized inference provider. Navigation and inspection only; "
            "no click, form submission, uploading, password entry, new "
            "account, purchases or permissions changes. This page does not "
            "establish that a website login remains valid.</p>"
            + external_notice + "".join(forms),
        )

    @app.post("/owner/agent-read", response_class=HTMLResponse)
    async def run_approved_read(
        request: Request,
        site: str = Form(),
        objective: str = Form(),
        expected_title: str = Form(),
        confirmation: str = Form(),
        csrf_token: str = Form(default=""),
        use_cloudflare: str = Form(default=""),
        _owner=Depends(require_verified_owner),
    ):
        _require_owner_agent_enabled()
        owner = _owner["private_owner_id"]
        site = _require_owner_session_origin(site, owner)
        _verify_owner_form(request, owner, site, "agent_read", csrf_token)
        if confirmation != "READ":
            raise HTTPException(status_code=403, detail="Exact owner approval required")
        if use_cloudflare not in ("", "yes"):
            raise HTTPException(status_code=403, detail="Inference selection invalid")
        external = use_cloudflare == "yes"
        if (external and not _cloudflare_free_ready()) or (
            not external and os.environ.get("PLENUM_BROWSER_FREE_LOCAL") != "confirmed"
        ):
            raise HTTPException(status_code=403, detail="Selected inference not authorized")
        _validate_owner_task(objective, expected_title)
        if not safe_url(site, origins={site}) or site not in _owner_saved_origins(owner):
            raise HTTPException(status_code=403, detail="Original saved owner session missing")
        import asyncio
        from playwright.async_api import async_playwright
        from .pinned_public_preview import PinnedOriginProxy

        deadline = time.time() + 180

        async def approved(request_owner, requested_site, requested_objective):
            return (
                request_owner == owner and requested_site == site
                and requested_objective == objective and time.time() < deadline
            )

        async def verified(history, browser):
            # This is independent of the model's claimed task completion.
            # It is a narrow expected TITLE check, NOT a verified login or
            # proof of a consequential provider-side action.
            page = await browser.get_current_page()
            if page is None:
                return False
            current = await page.get_url()
            title = await page.get_title()
            return safe_url(current, origins={site}) and title == expected_title

        try:
            async with PinnedOriginProxy(
                site, max_tunnels=16, max_tunnel_bytes=30_000_000,
                max_lifetime=250,
            ) as broker:
                async with async_playwright() as pw:
                    outcome = await run_owner_readonly_browser_task(
                        verified_owner=_owner, website_origin=site,
                        objective=objective,
                        owner_proxy_url=f"http://127.0.0.1:{broker.port}",
                        existing_chromium_executable=pw.chromium.executable_path,
                        approval_callback=approved, independent_verify=verified,
                        approval_expires_at=deadline, max_steps=6,
                        external_inference_consent=external,
                    )
        except HTTPException:
            raise
        except Exception:
            # Never disclose site text, cookies, local model output or GCS.
            raise HTTPException(status_code=503, detail="Private read-only agent unavailable") from None

        status = outcome.get("status")
        if status not in {
            "INDEPENDENTLY_VERIFIED_BY_TRUSTED_CALLER",
            "BLOCKED_NOT_INDEPENDENTLY_VERIFIED",
            "BLOCKED_PRIVATE_AGENT_EXECUTION",
        }:
            status = "BLOCKED_PRIVATE_AGENT_EXECUTION"
        return _page(
            "Original private browser result",
            "<article>Task status: " + escape(status)
            + "\nWebsite: " + escape(site)
            + "\nIndependent check: exact owner-provided page title only."
            + "\nInference route: " + ("owner-approved Cloudflare Workers AI" if external else "local")
            + "\nNo credentials, private page text or AI responses are shared."
            + "\nAccount login and three meaningful private actions remain "
              "unverified until separate provider-specific evidence is obtained."
            + "</article><p><a href='/owner/agent-read'>Back to private agent</a></p>",
        )

"""Verified-owner session status, readback and revocation.

Uses the existing signed Google IAP owner identity and encrypted GCS profile
vault. No credentials or decrypted Playwright state reach ChatGPT or GitHub.
No remote site modification, uploads, or account actions are accepted here.
"""
import asyncio
import os
from html import escape
from urllib.parse import urlsplit

from fastapi import Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse

from .engine import _origin_syntax, allowed_origins, safe_url, public_dns_only
from .owner_console import require_verified_owner
from .private_profiles import BrowserProfileStore

_HEADERS = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; "
                               "form-action 'self'; frame-ancestors 'none'; base-uri 'none'",
}


def _require_allowed_origin(site):
    if (not _origin_syntax(site)
            or site not in allowed_origins()
            or urlsplit(site).path not in ("", "/")):
        raise HTTPException(status_code=403, detail="Website origin not approved")
    return site


def _require_same_origin(request):
    """No unsigned header can authorize the owner; IAP dependency is separate."""
    origin = os.environ.get("BROWSER_PUBLIC_ORIGIN", "")
    if (not origin.startswith("https://")
            or not _origin_syntax(origin)
            or request.headers.get("origin") != origin):
        raise HTTPException(status_code=403, detail="Same-origin owner action required")


def _page(title, body):
    return HTMLResponse(
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>Computer · Private Website Sessions</title>"
        "<style>body{font:16px system-ui;max-width:720px;margin:32px auto;"
        "padding:0 18px;line-height:1.6}input,button{font:inherit;padding:9px}"
        "input{min-width:60%}article{border:1px solid #8888;padding:16px;"
        "border-radius:10px;white-space:pre-wrap;overflow-wrap:anywhere}"
        "button{cursor:pointer}small{opacity:.75}</style></head>"
        "<body><h1>" + escape(title) + "</h1>" + body
        + "<p><a href='/owner'>Return to Computer</a></p></body></html>",
        headers=_HEADINGS(),
    )


def _HEADINGS():
    # Avoid caching even intermediate signed-owner screen responses.
    return dict(_HEADERS)


def safe_session_preview_url(site):
    """Use one audited login-protected demo fixture, never arbitrary paths."""
    if site=="https://the-internet.herokuapp.com":
        return site+"/secure"
    return site+"/"


async def read_saved_site(*, site, owner):
    """Decrypt only inside the trusted server and restore only one owner/site."""
    store = BrowserProfileStore.from_environment()
    state, _generation = store.load_for_trusted_worker(owner=owner, origin=site)
    await asyncio.to_thread(public_dns_only, site)
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            context = await browser.new_context(
                storage_state=state, accept_downloads=False,
                ignore_https_errors=False, service_workers="block",
                permissions=[],
            )
            try:
                async def constrain(route):
                    req = route.request
                    if req.method in ("GET", "HEAD") and safe_url(req.url, origins={site}):
                        await route.continue_()
                    else:
                        await route.abort()
                await context.route("**/*", constrain)
                page = await context.new_page()
                resp = await page.goto(safe_session_preview_url(site), timeout=20000,
                                       wait_until="domcontentloaded")
                if not safe_url(page.url, origins={site}) or resp is None or resp.status >= 400:
                    raise PermissionError("Saved session preview left allowed origin")
                title = " ".join((await page.title()).split())[:160]
                body = " ".join((await page.locator("body").inner_text(
                    timeout=7000)).split())[:1200]
                # An ordinary HTTP 200 login page is not an authenticated
                # restore proof. Only the specific public demo fixture has
                # a trustworthy narrow success check.
                demo_restored=(site=="https://the-internet.herokuapp.com"
                    and urlsplit(page.url).path=="/secure"
                    and "Logged in as" in body
                    and "Secure Area" in body)
                return {"title":title,"body":body,
                        "site":site,"http_status":resp.status,
                        "demo_authenticated_restored":demo_restored}
            finally:
                await context.close()
        finally:
            await browser.close()


def mount_owner_saved_session(app):
    @app.get("/owner/sessions", response_class=HTMLResponse)
    async def owner_sessions(_owner=Depends(require_verified_owner)):
        origins = sorted(allowed_origins())
        if (not os.environ.get("BROWSER_PROFILE_BUCKET")
                or not os.environ.get("BROWSER_SESSION_KEY")):
            return _page("Session vault not yet provisioned",
                         "<article>The browser session storage is not configured. "
                         "No website accounts are accessible.</article>")
        rows = []
        store = BrowserProfileStore.from_environment()
        for site in origins:
            try:
                exists = bool(store.status(
                    owner=_owner["private_owner_id"], origin=site)["profile_exists"])
            except Exception:
                exists = None
            label = ("Saved encrypted profile exists" if exists is True
                     else "No saved profile" if exists is False
                     else "Unable to check saved profile securely")
            rows.append(
                "<article><strong>" + escape(site) + "</strong> · "
                + escape(label) +
                ("<p>Retry after the storage service is available.</p></article>"
                 if exists is None else
                "<form method='post' action='/owner/sessions/preview'>")
                "<input type='hidden' name='site' value='" + escape(site, quote=True) + "'>"
                "<button type='submit'>Preview saved session (read only)</button>"
                "</form>"
                "<form method='post' action='/owner/sessions/revoke'>"
                "<input type='hidden' name='site' value='" + escape(site, quote=True) + "'>"
                "<label>Type REVOKE to delete saved session "
                "<input name='confirmation' autocomplete='off' maxlength='6'></label>"
                "<button type='submit'>Revoke session</button></form></article>"
            )
        return _page("Saved website sessions", "".join(rows))

    @app.post("/owner/sessions/preview", response_class=HTMLResponse)
    async def owner_preview_session(
        request: Request,
        site: str = Form(),
        _owner=Depends(require_verified_owner),
    ):
        _require_same_origin(request)
        site = _require_allowed_origin(site)
        try:
            result = await asyncio.wait_for(read_saved_site(
                site=site, owner=_owner["private_owner_id"]), timeout=45)
        except Exception as exc:
            raise HTTPException(
                status_code=502, detail="Saved website preview unavailable"
            ) from exc
        demo=(site=="https://the-internet.herokuapp.com")
        verification=("<strong>Demo login restoration verified.</strong>"
                      if result.get("demo_authenticated_restored")
                      else "<strong>Demo login restoration NOT verified.</strong>"
                      if demo else
                      "<strong>Session preview is read-only; login status is not proven.</strong>")
        return _page("Owner-only saved-session preview",
                     "<small>Website state was loaded from the owner-scoped "
                     "encrypted profile. No credentials are sent to ChatGPT.</small>"
                     "<article>"+verification+"\n"
                     + "<strong>" + escape(result["title"]) + "</strong>\n"
                     + escape(result["site"]) + "\n\n"
                     + escape(result["body"]) + "</article>")

    @app.post("/owner/sessions/revoke", response_class=HTMLResponse)
    async def owner_revoke_session(
        request: Request,
        site: str = Form(),
        confirmation: str = Form(),
        _owner=Depends(require_verified_owner),
    ):
        _require_same_origin(request)
        site = _require_allowed_origin(site)
        if confirmation != "REVOKE":
            raise HTTPException(status_code=403, detail="Explicit revoke confirmation required")
        try:
            store = BrowserProfileStore.from_environment()
            owner = _owner["private_owner_id"]
            generation = store.current_generation(owner=owner, origin=site)
            if generation is not None:
                store.revoke(owner=owner, origin=site, expected_generation=generation)
        except Exception as exc:
            raise HTTPException(status_code=502, detail="Session revocation unavailable") from exc
        return _page("Saved website session revoked",
                     "<article>The selected encrypted profile is no longer stored. "
                     "This does not log out other devices.</article>")

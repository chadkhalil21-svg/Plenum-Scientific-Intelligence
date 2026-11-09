"""Verified-owner session status, readback and revocation.

Uses the existing signed Google IAP owner identity and encrypted GCS profile
vault. No credentials or decrypted Playwright state reach ChatGPT or GitHub.
No remote site modification, uploads, or account actions are accepted here.
"""
import asyncio
import hashlib
import hmac
import os
import re
import secrets
import time
from html import escape
from urllib.parse import urlsplit

from fastapi import Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse

from .engine import _origin_syntax, allowed_origins, safe_url, public_dns_only
from .owner_console import require_verified_owner
from .private_profiles import BrowserProfileStore

PUBLIC_DEMO_ORIGIN = "https://the-internet.herokuapp.com"

_HEADERS = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    # HTML form POST with Referrer-Policy:no-referrer serializes Origin:null
    # under the Fetch standard. That conflicts with our same-origin CSRF guard.
    # "same-origin" sends Referer only internally and never to external sites;
    # no cookies, bearer values or CSRF tokens are present in this page URL.
    "Referrer-Policy": "same-origin",
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; "
                               "form-action 'self'; frame-ancestors 'none'; base-uri 'none'",
}


def _require_allowed_origin(site):
    if (not _origin_syntax(site)
            or site not in allowed_origins()
            or urlsplit(site).path not in ("", "/")):
        raise HTTPException(status_code=403, detail="Website origin not approved")
    return site


def _owner_form_secret(owner_id):
    """Derive exact-owner CSRF MAC key using standard-library SHA-256 only."""
    secret=os.environ.get("COMPUTER_BROWSER_TOKEN","")
    if len(secret)<32 or not isinstance(owner_id,str) or not 1<=len(owner_id)<=80:
        raise HTTPException(status_code=503,detail="Private owner form unavailable")
    return hmac.digest(secret.encode(),("plenum.owner.form.v1:"+owner_id).encode(),"sha256")


def _owner_form_mac(owner_id, site, action, issued_hex, nonce):
    scope="v1:"+issued_hex+":"+nonce+":"+action+":"+site
    return hmac.digest(_owner_form_secret(owner_id),scope.encode(),"sha256").hex()


def _owner_form_token(owner_id, site, action):
    """Short-lived exact-owner/site/action CSRF token; no account data inside."""
    if action not in ("preview","revoke","demo_refresh"):
        raise ValueError("Unrecognized owner form action")
    issued=f"{int(time.time()):08x}"
    nonce=secrets.token_hex(8)
    signature=_owner_form_mac(owner_id,site,action,issued,nonce)
    return "v1."+issued+"."+nonce+"."+signature


def _verify_owner_form(request, owner_id, site, action, token):
    """Support iPad forms which omit Origin, without accepting forged POSTs.

    Origin, Referer and Fetch Metadata, when present, MUST be same origin.
    Missing headers are permitted only with a verified owner-bound CSRF token,
    since Referrer-Policy:no-referrer is required for private account pages.
    """
    origin=os.environ.get("BROWSER_PUBLIC_ORIGIN","")
    if not origin.startswith("https://") or not _origin_syntax(origin):
        raise HTTPException(status_code=403,detail="Same-origin owner action required")
    supplied=request.headers.get("origin")
    if supplied is not None and supplied!=origin:
        raise HTTPException(status_code=403,detail="Same-origin owner action required")
    referer=request.headers.get("referer")
    if referer:
        try:
            p=urlsplit(referer)
            ref_origin=f"{p.scheme}://{p.netloc}"
        except ValueError:
            ref_origin=""
        if ref_origin!=origin:
            raise HTTPException(status_code=403,detail="Same-origin owner action required")
    fetch_site=request.headers.get("sec-fetch-site")
    if fetch_site is not None and fetch_site!="same-origin":
        raise HTTPException(status_code=403,detail="Same-origin owner action required")
    if not isinstance(token,str) or len(token)>1000 or not token:
        raise HTTPException(status_code=403,detail="Owner form verification required")
    match=re.fullmatch(r"v1[.]([0-9a-f]{8,10})[.]([0-9a-f]{16})[.]([0-9a-f]{64})",token)
    if match is None or action not in ("preview","revoke","demo_refresh"):
        raise HTTPException(status_code=403,detail="Owner form verification required")
    issued_hex,nonce,signature=match.groups()
    now=int(time.time())
    issued=int(issued_hex,16)
    if issued>now+10 or now-issued>1800:
        raise HTTPException(status_code=403,detail="Owner form verification required")
    expected=_owner_form_mac(owner_id,site,action,issued_hex,nonce)
    if not hmac.compare_digest(signature,expected):
        raise HTTPException(status_code=403,detail="Owner form verification required")


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
    if site==PUBLIC_DEMO_ORIGIN:
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
                demo_restored=(site==PUBLIC_DEMO_ORIGIN
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


async def _public_demo_login_snapshot(browser, *, fixture_route=None):
    """Get session state for ONLY the public Sauce Labs test account.

    Never opens a user-supplied destination or reads private credentials.
    Production routes are limited to exact approved demo HTTPS origin.
    """
    from .private_login import filter_site_storage
    demo=PUBLIC_DEMO_ORIGIN
    context=await browser.new_context(
        accept_downloads=False,ignore_https_errors=False,
        service_workers="block",permissions=[])
    try:
        async def restrict(route):
            request=route.request
            if (request.method not in ("GET","HEAD","POST","OPTIONS")
                    or not safe_url(request.url,origins={demo})):
                await route.abort()
            elif fixture_route is not None:
                await fixture_route(route)
            else:
                await route.continue_()
        await context.route("**/*",restrict)
        page=await context.new_page()
        await page.goto(demo+"/login",wait_until="domcontentloaded",timeout=25000)
        # These demonstration credentials are intentionally published by
        # Sauce Labs in their public source, not supplied by the user.
        await page.locator("#username").fill("tomsmith")
        await page.locator("#password").fill("SuperSecretPassword!")
        await page.locator("button[type=submit]").click(timeout=12000)
        await page.wait_for_url(demo+"/secure",timeout=15000)
        body=" ".join((await page.locator("body").inner_text(timeout=7000)).split())
        if not ("Secure Area" in body and "Logged in as tomsmith" in body):
            return None
        state=filter_site_storage(await context.storage_state(),demo)
        if not state["cookies"]:
            return None
        return state
    finally:
        await context.close()


async def _refresh_and_verify_public_demo(owner):
    """One owner-authorized demo-only login, encrypted write and fresh restore."""
    demo=PUBLIC_DEMO_ORIGIN
    _require_allowed_origin(demo)
    await asyncio.to_thread(public_dns_only,demo)
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(headless=True)
        try:
            state=await _public_demo_login_snapshot(browser)
        finally:
            await browser.close()
    if state is None:
        return "demo_login_not_verified"
    from .private_login import _persist_encrypted_site_profile
    await asyncio.to_thread(_persist_encrypted_site_profile,
                            owner_id=owner,origin=demo,state=state)
    result=await read_saved_site(site=demo,owner=owner)
    if result.get("demo_authenticated_restored") is True:
        return "verified"
    return "saved_but_not_restored"


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
            base="<article><strong>"+escape(site)+"</strong> · "+escape(label)
            if exists is None:
                rows.append(base+"<p>Retry after the storage service is available.</p></article>")
                continue
            preview_token=escape(_owner_form_token(_owner["private_owner_id"],site,"preview"),quote=True)
            revoke_token=escape(_owner_form_token(_owner["private_owner_id"],site,"revoke"),quote=True)
            demo_refresh_form=(
                "<form method='post' action='/owner/sessions/demo-refresh'>"
                "<input type='hidden' name='csrf_token' value='"
                + escape(_owner_form_token(_owner["private_owner_id"],site,
                                           "demo_refresh"),quote=True)
                + "'><button type='submit'>Refresh and verify public demo login</button>"
                "</form>"
                if site==PUBLIC_DEMO_ORIGIN else "")
            rows.append(
                base+
                "<form method='post' action='/owner/sessions/preview'>"
                "<input type='hidden' name='site' value='" + escape(site, quote=True) + "'>"
                "<input type='hidden' name='csrf_token' value='" + preview_token + "'>"
                "<button type='submit'>Preview saved session (read only)</button>"
                "</form>"
                "<form method='post' action='/owner/sessions/revoke'>"
                "<input type='hidden' name='site' value='" + escape(site, quote=True) + "'>"
                "<input type='hidden' name='csrf_token' value='" + revoke_token + "'>"
                "<label>Type REVOKE to delete saved session "
                "<input name='confirmation' autocomplete='off' maxlength='6'></label>"
                "<button type='submit'>Revoke session</button></form>"
                + demo_refresh_form + "</article>"
            )
        return _page("Saved website sessions", "".join(rows))

    @app.post("/owner/sessions/preview", response_class=HTMLResponse)
    async def owner_preview_session(
        request: Request,
        site: str = Form(),
        csrf_token: str = Form(default=""),
        _owner=Depends(require_verified_owner),
    ):
        site = _require_allowed_origin(site)
        _verify_owner_form(request,_owner["private_owner_id"],site,"preview",csrf_token)
        try:
            result = await asyncio.wait_for(read_saved_site(
                site=site, owner=_owner["private_owner_id"]), timeout=45)
        except Exception as exc:
            raise HTTPException(
                status_code=502, detail="Saved website preview unavailable"
            ) from exc
        demo=(site==PUBLIC_DEMO_ORIGIN)
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

    @app.post("/owner/sessions/demo-refresh", response_class=HTMLResponse)
    async def owner_refresh_public_demo(
        request: Request,
        csrf_token: str = Form(default=""),
        _owner=Depends(require_verified_owner),
    ):
        """Explicit owner click refreshes only a published demo account."""
        demo=PUBLIC_DEMO_ORIGIN
        _require_allowed_origin(demo)
        _verify_owner_form(request,_owner["private_owner_id"],demo,
                           "demo_refresh",csrf_token)
        try:
            result=await asyncio.wait_for(_refresh_and_verify_public_demo(
                _owner["private_owner_id"]),timeout=90)
        except Exception as exc:
            raise HTTPException(status_code=502,
                detail="Public demo session refresh unavailable; private profiles not disclosed") from exc
        if result=="verified":
            return _page("Public demo session independently verified",
                "<article><strong>Demo login restoration verified.</strong> "
                "The published demonstration account was logged in afresh, "
                "its website state saved in owner-scoped encrypted storage, "
                "and an independent read-only Chromium session reached "
                "the protected demo Secure Area. "
                "This does not authorize other websites or connect ChatGPT actions."
                "</article>")
        if result=="demo_login_not_verified":
            return _page("Public demo website login unavailable",
                "<article>The published demonstration login did not succeed, "
                "so no replacement website session was saved. "
                "The existing saved profile was not changed.</article>")
        return _page("Public demo session saved but not restored",
            "<article>The demonstration login state was saved, "
            "but the public website did not accept it in an independent "
            "read-only Chromium session. Do not treat it as a valid login."
            "</article>")

    @app.post("/owner/sessions/revoke", response_class=HTMLResponse)
    async def owner_revoke_session(
        request: Request,
        site: str = Form(),
        confirmation: str = Form(),
        csrf_token: str = Form(default=""),
        _owner=Depends(require_verified_owner),
    ):
        site = _require_allowed_origin(site)
        _verify_owner_form(request,_owner["private_owner_id"],site,"revoke",csrf_token)
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

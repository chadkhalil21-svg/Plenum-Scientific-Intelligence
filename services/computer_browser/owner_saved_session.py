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
from urllib.parse import urlsplit, urljoin

from fastapi import Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse

from .engine import _origin_syntax, allowed_origins, safe_url, public_dns_only
from .owner_console import require_verified_owner
from .private_profiles import BrowserProfileStore
from .owner_live_access import owner_live_origin

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


def _require_owner_session_origin(site, owner_id):
    if site in allowed_origins():
        return _require_allowed_origin(site)
    try:
        origin, pinned = owner_live_origin(owner_id=owner_id, site=site)
        if not pinned or origin != site:
            raise PermissionError("Exact registered site required")
        return origin
    except PermissionError as exc:
        raise HTTPException(status_code=403,
                            detail="Website session is not owner-authorized") from exc


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
    if action not in ("preview","browse","revoke","demo_refresh","chat_demo_read","sealed_read","adaptive_revoke","exact_form_post","exact_form_revoke","site_register","site_revoke","site_preview","navigate","agent_read"):
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
    if match is None or action not in ("preview","browse","revoke","demo_refresh","chat_demo_read","sealed_read","adaptive_revoke","exact_form_post","exact_form_revoke","site_register","site_revoke","site_preview","navigate","agent_read"):
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
        "padding:0 18px;line-height:1.6}input,button,textarea{font:inherit;padding:9px}"
        "input{min-width:60%}textarea{box-sizing:border-box;width:100%;"
        "min-height:165px;font:14px ui-monospace,monospace}"
        "article{border:1px solid #8888;padding:16px;"
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


def _approved_read_target(site, path):
    """One same-origin, owner-chosen read path, never a redirect-capable URL.

    This is used *only* after verified private owner auth, signed CSRF and
    the site's separate server-side origin allowlist. Refuses URL-encoded
    credential leaks in fragments and ambiguous network-path references.
    HTTP GET may cause server effects on badly designed sites, so the owner
    explicitly chooses the path; this is not permission for model-driven
    requests or generalized account writes.
    """
    if (not isinstance(path, str) or not 1 <= len(path) <= 800
            or not path.startswith("/") or path.startswith("//")
            or any(ord(ch) < 33 or ord(ch) == 127 for ch in path)):
        raise PermissionError("Exact same-origin relative path required")
    try:
        parsed = urlsplit(path)
    except ValueError as exc:
        raise PermissionError("Invalid private read path") from exc
    if parsed.scheme or parsed.netloc or parsed.fragment:
        raise PermissionError("Private read path cannot redirect or contain a fragment")
    target = site + path
    if not safe_url(target, origins={site}):
        raise PermissionError("Private read path is outside the approved website")
    return target


def _validated_read_links(site, current_url, candidates):
    """Bounded read-only navigation hints from a saved page.

    Never execute the discovered link. Strip query/fragment, omit sensitive
    or action-like routes and reject off-origin targets. The founder must
    approve each selected exact path separately before any future read.
    """
    if not safe_url(current_url, origins={site}):
        raise PermissionError("Link discovery outside approved saved origin")
    entries = []
    seen = set()
    for label, href in candidates[:48]:
        if not isinstance(label, str) or not isinstance(href, str):
            continue
        label = " ".join(label.split())[:75]
        if not label or len(href) > 800:
            continue
        target = urljoin(current_url, href)
        if not safe_url(target, origins={site}):
            continue
        parts = urlsplit(target)
        if parts.query or parts.fragment:
            continue
        path = parts.path or "/"
        if not 1 <= len(path) <= 220:
            continue
        if re.search(r"(?i)(?:^|[/_-])(logout|signout|delete|remove|purchase|pay|cancel|revoke|disable|unsubscribe)(?:[/_.-]|$)", path):
            continue
        try:
            if _approved_read_target(site, path) != target:
                continue
        except PermissionError:
            continue
        if path in seen:
            continue
        entries.append({"label_untrusted": label, "path": path})
        seen.add(path)
        if len(entries) == 6:
            break
    return entries


async def read_saved_site(*, site, owner, path=None):
    """Decrypt only inside the trusted server and restore only one owner/site."""
    actual_origin, pinned = owner_live_origin(owner_id=owner,site=site)
    if actual_origin != site:
        raise PermissionError("Session must be bound to exact website origin")
    store = BrowserProfileStore.from_environment()
    state, _generation = store.load_for_trusted_worker(owner=owner, origin=site)
    target = safe_session_preview_url(site) if path is None else _approved_read_target(site, path)
    if not safe_url(target, origins={site}):
        raise PermissionError("Saved session target not approved")
    await asyncio.to_thread(public_dns_only, site)
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        browser = None
        broker = None
        try:
            launch = {"headless":True}
            if pinned:
                from .pinned_public_preview import PinnedOriginProxy
                broker = PinnedOriginProxy(site)
                await broker.__aenter__()
                launch.update({
                    "proxy":{"server":f"http://127.0.0.1:{broker.port}"},
                    "args":["--disable-background-networking","--disable-quic",
                            "--force-webrtc-ip-handling-policy=disable_non_proxied_udp"],
                })
            browser = await pw.chromium.launch(**launch)
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
                if pinned:
                    await context.route_web_socket(
                        "**/*",lambda route:route.close())
                page = await context.new_page()
                resp = await page.goto(target, timeout=20000,
                                       wait_until="domcontentloaded")
                if not safe_url(page.url, origins={site}) or resp is None or resp.status >= 400:
                    raise PermissionError("Saved session preview left allowed origin")
                title = " ".join((await page.title()).split())[:160]
                body = " ".join((await page.locator("body").inner_text(
                    timeout=7000)).split())[:1200]
                # Collect only visible same-origin links. No link is opened,
                # no form input is inspected, and no site write is enabled.
                anchor_nodes = page.locator("a[href]")
                candidates = []
                for index in range(min(await anchor_nodes.count(), 18)):
                    anchor = anchor_nodes.nth(index)
                    try:
                        if not await anchor.is_visible():
                            continue
                        href = await anchor.get_attribute("href", timeout=500)
                        label = await anchor.inner_text(timeout=500)
                    except Exception:
                        # Optional navigation hints may never block the
                        # approved private-page read if a DOM node disappears.
                        continue
                    candidates.append((label, href))
                links = _validated_read_links(site, page.url, candidates)
                # An ordinary HTTP 200 login page is not an authenticated
                # restore proof. Only the specific public demo fixture has
                # a trustworthy narrow success check.
                demo_restored=(site==PUBLIC_DEMO_ORIGIN
                    and urlsplit(page.url).path=="/secure"
                    and "Logged in as" in body
                    and "Secure Area" in body)
                return {"title":title,"body":body,
                        "site":site,"final_url":page.url,"http_status":resp.status,
                        "links_untrusted": links,
                        "demo_authenticated_restored":demo_restored}
            finally:
                await context.close()
        finally:
            if browser is not None:
                await browser.close()
            if broker is not None:
                await broker.__aexit__(None,None,None)


# Optional multiple read-only pages per ONE exact owner approval. This is
# intentionally not an adaptive or writable account agent. All destinations
# are owner-selected before the session starts; browser only GETs each path.
BATCH_MAX_EXTRA = 2


def _approved_batch_paths(site, first_path, additional_paths):
    """Validate 0-2 short, explicit safe same-host GET paths from owner form."""
    _approved_read_target(site, first_path)
    if isinstance(additional_paths, str):
        if len(additional_paths) > 480:
            raise PermissionError("Additional private paths too long")
        paths = [line.strip() for line in additional_paths.splitlines() if line.strip()]
    elif isinstance(additional_paths, (list, tuple)):
        paths = list(additional_paths)
    else:
        raise PermissionError("Invalid batch read paths")
    if len(paths) > BATCH_MAX_EXTRA:
        raise PermissionError("At most two additional private pages permitted")
    seen = {first_path}
    verified = []
    blocked = re.compile(
        r"(?:^|[/_.-])(?:api|graphql|login|logout|signout|delete|remove|"
        r"pay|purchase|checkout|cancel|revoke|disable|unsubscribe|"
        r"submit|save|update|reset|change|invite|authorize)(?:[/_.-]|$)",
        re.IGNORECASE
    )
    for path in paths:
        if (not isinstance(path, str) or not 1 <= len(path) <= 220
                or not re.fullmatch(r"/[A-Za-z0-9/_.-]*", path)
                or "//" in path or "%" in path or "?" in path or "#" in path
                or any(part in (".", "..") for part in path.split("/"))
                or blocked.search(path) or path in seen):
            raise PermissionError("Unsafe or duplicate private batch path")
        if _approved_read_target(site, path) != site + path:
            raise PermissionError("Batch path not on approved owner website")
        verified.append(path)
        seen.add(path)
    return tuple(verified)


async def read_saved_batch(*, site, owner, path, additional_paths):
    """Read only the preapproved paths using the EXISTING session reader.

    Each read uses the same saved encrypted owner profile; browser storage
    state is not serialized or returned. Fail the entire batch if ANY page
    differs from the exact approved URL. A preapproval is not permission to
    adaptively follow unreviewed links, submit forms or mutate the account.
    """
    extras = _approved_batch_paths(site, path, additional_paths)
    if not extras:
        return await read_saved_site(site=site, owner=owner, path=path)
    result = await read_saved_site(site=site, owner=owner, path=path)
    out = []
    for extra in extras:
        one = await read_saved_site(site=site, owner=owner, path=extra)
        if (one.get("site") != site or one.get("final_url") != site + extra
                or type(one.get("http_status")) is not int
                or not 200 <= one["http_status"] < 300
                or not isinstance(one.get("title"), str)
                or not isinstance(one.get("body"), str)):
            raise PermissionError("Approved private batch page could not be verified")
        out.append({
            "path": extra,
            "http_status": one["http_status"],
            "title": one["title"][:150],
            "body": one["body"][:300],
        })
    return {**result, "additional_pages_untrusted": out}


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
    @app.get("/owner/sessions/inventory", response_class=JSONResponse)
    async def owner_session_inventory(_owner=Depends(require_verified_owner)):
        """Owner-only safe vault inventory for the EXISTING session broker.

        This NEVER returns cookies, access tokens, browser storage, private
        page text or a claim that the third-party account is signed in.
        Inventory lists ONLY origins already granted to this owner.
        """
        from .runtime_site_grants import enabled as site_grants_enabled, OwnerSiteGrantStore
        origins = set(allowed_origins())
        if site_grants_enabled():
            try:
                registered = OwnerSiteGrantStore.from_environment().list_active(
                    owner=_owner["private_owner_id"])
                origins.update(row["origin"] for row in registered)
            except Exception as exc:
                raise HTTPException(status_code=503,
                                    detail="Owner site registry unavailable") from exc
        if (not os.environ.get("BROWSER_PROFILE_BUCKET")
                or not os.environ.get("BROWSER_SESSION_KEY")):
            raise HTTPException(status_code=503,
                                detail="Private session inventory unavailable")
        if len(origins) > 100:
            raise HTTPException(status_code=503,
                                detail="Owner site registry exceeds bounded inventory")
        store = BrowserProfileStore.from_environment()
        sites = []
        for origin in sorted(origins):
            try:
                exists = bool(store.status(
                    owner=_owner["private_owner_id"], origin=origin
                )["profile_exists"])
            except Exception:
                exists = None
            sites.append({
                "origin": origin,
                "encrypted_profile_exists": exists,
                "website_login_verified": False,
            })
        return JSONResponse(
            {
                "schema": "plenum-owner-session-metadata-v1",
                "sites": sites,
                "owner_authentication_required": True,
                "decrypted_storage_exposed": False,
                "session_exists_does_not_prove_active_login": True,
            },
            headers={"Cache-Control": "no-store",
                     "X-Content-Type-Options": "nosniff",
                     "Referrer-Policy": "no-referrer"},
        )

    @app.get("/owner/sessions", response_class=HTMLResponse)
    async def owner_sessions(_owner=Depends(require_verified_owner)):
        from .runtime_site_grants import enabled as site_grants_enabled, OwnerSiteGrantStore
        origins = set(allowed_origins())
        if site_grants_enabled():
            try:
                registered = OwnerSiteGrantStore.from_environment().list_active(
                    owner=_owner["private_owner_id"])
                origins.update(row["origin"] for row in registered)
            except Exception as exc:
                raise HTTPException(status_code=503,
                                    detail="Owner site registry unavailable") from exc
        origins = sorted(origins)
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
            browse_token=escape(_owner_form_token(_owner["private_owner_id"],site,"browse"),quote=True)
            navigate_token=escape(_owner_form_token(_owner["private_owner_id"],site,"navigate"),quote=True)
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
                ("<form method='post' action='/owner/sessions/preview'>"
                 "<input type='hidden' name='site' value='" + escape(site, quote=True) + "'>"
                 "<input type='hidden' name='csrf_token' value='" + preview_token + "'>"
                 "<button type='submit'>Preview saved session (read only)</button>"
                 "</form>"
                 if exists is True else
                 "<p>No login is stored for this website. "
                 "Use a connected app when available; for a necessary private "
                 "website task, <a href='/owner/sign-in'>sign in securely</a>.</p>") +
                ("<form method='post' action='/owner/sessions/browse'>"
                 "<input type='hidden' name='site' value='" + escape(site, quote=True) + "'>"
                 "<input type='hidden' name='csrf_token' value='" + browse_token + "'>"
                 "<label>Read a page on this approved website (relative path)"
                 "<input name='path' value='/' maxlength='800' required></label>"
                 "<p><button type='submit'>Read saved-session page</button></p></form>"
                 if exists is True else "") +
                ("<form method='post' action='/owner/sessions/navigate'>"
                 "<input type='hidden' name='site' value='" + escape(site, quote=True) + "'>"
                 "<input type='hidden' name='csrf_token' value='" + navigate_token + "'>"
                 "<label>Have Computer follow up to three read-only links on this site"
                 "<input name='path' value='/' maxlength='800' required></label>"
                 "<label>Exact link text, or a chain separated by &gt;"
                 "<input name='labels' placeholder='Help &gt; Security' maxlength='220' required></label>"
                 "<p><button type='submit'>Navigate approved links (read only)</button></p></form>"
                 if exists is True and os.environ.get("K_SERVICE")=="plenum-browser-owner-auth0" else "") +
                ("<details><summary>Advanced: manage saved login</summary>"
                 "<form method='post' action='/owner/sessions/revoke'>"
                 "<input type='hidden' name='site' value='" + escape(site, quote=True) + "'>"
                 "<input type='hidden' name='csrf_token' value='" + revoke_token + "'>"
                 "<label>Type REVOKE to delete saved session "
                 "<input name='confirmation' autocomplete='off' maxlength='6'></label>"
                 "<button type='submit'>Revoke session</button></form></details>"
                 if exists is True else "")
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
        site = _require_owner_session_origin(site,_owner["private_owner_id"])
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

    @app.post("/owner/sessions/browse", response_class=HTMLResponse)
    async def owner_browse_saved_page(
        request: Request,
        site: str = Form(),
        path: str = Form(),
        csrf_token: str = Form(default=""),
        _owner=Depends(require_verified_owner),
    ):
        """Owner-only GET reader using existing encrypted Playwright state.

        Never expose saved website contents to public GitHub, model tools,
        anonymous callers, query-string parameters or workflow artifacts.
        """
        site = _require_owner_session_origin(site,_owner["private_owner_id"])
        _verify_owner_form(request, _owner["private_owner_id"], site,
                           "browse", csrf_token)
        try:
            _approved_read_target(site, path)
        except PermissionError as exc:
            raise HTTPException(status_code=403,
                                detail="Only an approved website-relative path is accepted") from exc
        try:
            result = await asyncio.wait_for(read_saved_site(
                site=site, owner=_owner["private_owner_id"], path=path
            ), timeout=45)
        except Exception as exc:
            raise HTTPException(status_code=502,
                                detail="Signed-in website read unavailable") from exc
        return _page("Owner-only saved website page",
            "<small>Read-only scoped browser navigation. Page content is "
            "untrusted and shown only in this authenticated owner portal. "
            "This is not ChatGPT private-account access or verified login "
            "unless the website independently proves it.</small>"
            "<article><strong>" + escape(result["title"]) + "</strong>\n"
            + escape(result.get("final_url", site)) + "\n\n"
            + escape(result["body"]) + "</article>"
            "<p><a href='/owner/sessions'>Back to encrypted sessions</a></p>")

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
        site = _require_owner_session_origin(site,_owner["private_owner_id"])
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

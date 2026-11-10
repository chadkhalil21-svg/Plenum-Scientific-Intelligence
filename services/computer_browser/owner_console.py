"""Minimal browser owner's private web console (verified owner only).

No Javascript, cookies or login credentials reach ChatGPT or public GitHub.
This is a useful authenticated owner surface for status and public inspection.
Human-operated website sign-in uses a separate protected browser page.
This is not ChatGPT model-controlled website login.
"""
from html import escape
import os
from fastapi import Depends, Header, HTTPException, Query, Request
from .owner_auth0 import active as auth0_active, verified_session as auth0_verified_session
from fastapi.responses import HTMLResponse
from .iap_identity import verify_owner_token
from .engine import read_public, safe_url


def require_verified_owner(
    request: Request,
    x_goog_iap_jwt_assertion: str | None=Header(default=None),
):
    try:
        if auth0_active():
            return auth0_verified_session(request.scope)
        # The original IAP owner service retains its ES256-only validation.
        return verify_owner_token(x_goog_iap_jwt_assertion)
    except PermissionError as exc:
        raise HTTPException(status_code=401,detail="Verified owner sign-in required") from exc


_HEADERS={
    "Cache-Control":"no-store",
    "Content-Security-Policy":"default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'",
    "X-Content-Type-Options":"nosniff",
    "Referrer-Policy":"no-referrer",
    "X-Frame-Options":"DENY",
}


def _page(title,body):
    return HTMLResponse("""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Computer · Private Browser</title>
<style>
:root{color-scheme:light dark}body{font:16px system-ui,sans-serif;line-height:1.5;
max-width:650px;margin:42px auto;padding:0 24px}
h1{font-size:28px}h2{font-size:19px}input{padding:10px;width:95%;font:inherit}
button{padding:10px 17px;font:inherit;cursor:pointer}article{padding:16px;
border:1px solid #8888;border-radius:12px;margin:18px 0;white-space:pre-wrap;
overflow-wrap:anywhere}small{opacity:.75}a{color:inherit}
</style></head><body><h1>Computer · Private Browser</h1>
<small>Owner-only verified sign-in · Plenum Prometheus</small>
<h2>"""+escape(title)+"</h2>"+body+"""<hr>
<small>Website logins and approvals remain private to the verified owner browser.
ChatGPT can request only the specific read or write operations already approved
and supported by the signed GitHub bridge. No unrestricted account access is granted.</small>
</body></html>""",headers=_HEADERS)


def mount_owner_console(app):
    @app.get("/owner",response_class=HTMLResponse)
    async def owner_home(_owner=Depends(require_verified_owner)):
        return _page("Connected as verified owner",
            """<article>Owner identity: verified.
Browser software: built and tested.
Private website login: owner-operated through the secure sign-in link.
Saved sessions: encrypted storage configured; saving is checked per site.
ChatGPT automation: available through the connected, signed GitHub bridge
for specifically approved read and write actions, NOT unrestricted account control.</article>
<h2>Sign in to an approved website</h2>
<p><a href="/owner/sign-in">Open secure website sign-in</a></p>
<h2>Existing saved website sessions</h2>
<p><a href="/owner/sessions">View, preview or revoke an approved session</a></p>
<p><small>On iPad, open the owner portal in Edge when possible. ChatGPT's
in-app browser may have separate sign-in cookies and ask you to log in again.</small></p>
<h2>Read an approved public website</h2>
<form method="get" action="/owner/public-preview">
<label for="url">Website address</label>
<input type="url" id="url" name="url" required
value="https://example.com/" maxlength="1200">
<p><button type="submit">Open public page</button></p></form>""" + (
                """<h2>One-time ChatGPT public-demo verification</h2>
<p><a href="/owner/chat-demo-approval">Approve one signed, read-only demo browser check</a></p>"""
                if (os.environ.get("K_SERVICE")=="plenum-browser-owner-auth0"
                    and os.environ.get("PLENUM_CHAT_RELAY_ENABLED")=="true")
                else "") + (
                """<h2>One-time encrypted chat read of approved saved website</h2>
<p><a href="/owner/chat-sealed-approval">Approve an encrypted one-page Computer read</a></p>"""
                if (os.environ.get("K_SERVICE")=="plenum-browser-owner-auth0"
                    and os.environ.get("PLENUM_SEALED_CHAT_READ_ENABLED")=="true")
                else "") + (
                """<h2>Authorize a new website</h2>
<p><a href="/owner/sites">Manage registered websites</a></p>
<small>Registration enables verified-owner sign-in for one pinned HTTPS
origin. ChatGPT browser actions, cross-site sign-in, and website writes remain
gated.</small>"""
                if (os.environ.get("K_SERVICE")=="plenum-browser-owner-auth0"
                    and os.environ.get("PLENUM_RUNTIME_SITE_GRANTS_ENABLED")=="true")
                else "") + (
                """<h2>Authenticated website actions · Write Approval</h2>
<p><a href="/owner/chat-exact-form">Review and approve one signed-in form submission</a></p>
<p><small>The Write Approval page includes a control to cancel a pending form approval.</small></p>
<small>A website must have an existing authorized saved login. Review the
exact form before approval. One native HTML form submission is supported;
payments, deletions, permission changes and unrestricted writes are not.</small>"""
                if (os.environ.get("K_SERVICE")=="plenum-browser-owner-auth0"
                    and os.environ.get("PLENUM_EXACT_OWNER_FORM_POST_ENABLED")=="true")
                else ""))

    @app.get("/owner/public-preview",response_class=HTMLResponse)
    async def owner_preview(url: str=Query(min_length=9,max_length=1200),
                            _owner=Depends(require_verified_owner)):
        if not safe_url(url):
            raise HTTPException(status_code=403,detail="Site not in approved public origins")
        try:
            result=await read_public(url)
        except Exception as exc:
            raise HTTPException(status_code=502,detail="Public browser read failed") from exc
        title=escape(result.get("title_untrusted",""))
        body=escape(result.get("body_excerpt_untrusted",""))
        final_url=escape(result.get("final_url",""))
        return _page("Verified public-page result",
            "<article><strong>"+title+"</strong>\n"
            +final_url+"\n\n"+body+"</article>"
            +'<p><a href="/owner">Back to Computer</a></p>')

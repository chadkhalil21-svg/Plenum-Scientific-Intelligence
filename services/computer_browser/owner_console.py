"""Minimal browser owner's private web console (IAP-verified, read-only).

No Javascript, cookies or login credentials reach ChatGPT or public GitHub.
This is a useful authenticated owner surface for status and public inspection.
One-time human-operated website sign-in uses a separate IAP-protected page.
This is not ChatGPT model-controlled website login.
"""
from html import escape
from fastapi import Depends, Header, HTTPException, Query
from fastapi.responses import HTMLResponse
from .iap_identity import verify_owner_token
from .engine import read_public, safe_url


def require_verified_owner(
    x_goog_iap_jwt_assertion: str | None=Header(default=None),
):
    try:
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
<small>Owner-only Google sign-in · Plenum Prometheus</small>
<h2>"""+escape(title)+"</h2>"+body+"""<hr>
<small>Private login is available only after the owner enables the site,
protected cloud storage and Google authentication. Computer cannot yet operate
private websites directly from ordinary ChatGPT messages.</small>
</body></html>""",headers=_HEADERS)


def mount_owner_console(app):
    @app.get("/owner",response_class=HTMLResponse)
    async def owner_home(_owner=Depends(require_verified_owner)):
        return _page("Connected as verified owner",
            """<article>Google identity: verified.
Browser software: built and tested.
Private website login: owner-operated only, after cloud deployment.
Saved sessions: encrypted cloud storage when connected and configured.
ChatGPT direct website interaction: not yet connected.</article>
<h2>Sign in to an approved website</h2>
<p><a href="/owner/sign-in">Open secure website sign-in</a></p>
<h2>Read an approved public website</h2>
<form method="get" action="/owner/public-preview">
<label for="url">Website address</label>
<input type="url" id="url" name="url" required
value="https://example.com/" maxlength="1200">
<p><button type="submit">Open public page</button></p></form>""")

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

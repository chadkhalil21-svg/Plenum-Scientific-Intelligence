"""Owner-approved public-demo-only GitHub ChatGPT relay (off by default).

Human Auth0 owner approves one short-lived read from a trusted web form.
One exact GitHub-signed OIDC workflow may consume it once, with no owner
identifier or private cookie supplied in the issue. The only response is a
secret-free boolean about a known PUBLIC demo website's saved session.

Not a generic browser, private account reader, write/submit or AGI endpoint.
"""
import asyncio
import os

from fastapi import Depends, Form, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from .github_oidc_read_policy import GitHubOIDCTokenVerifier, GitHubRelayIdentity
from .owner_chat_pairing import (
    approve_one_demo_read, consume_one_demo_read, require_enabled, FLAG,
)
from .owner_console import require_verified_owner
from .owner_saved_session import (
    _owner_form_token, _verify_owner_form, _page, PUBLIC_DEMO_ORIGIN,
    read_saved_site,
)

_READ_HEADERS={"Cache-Control":"no-store","X-Content-Type-Options":"nosniff"}


def mount_owner_chat_relay(app):
    # The original IAP owner browser and the IAM-only machine never mount
    # this route even when the flag is erroneously present.
    if (os.environ.get("K_SERVICE")!="plenum-browser-owner-auth0"
            or os.environ.get(FLAG)!="true"):
        return

    @app.get("/owner/chat-demo-approval", response_class=HTMLResponse)
    async def chat_demo_owner_approval_page(_owner=Depends(require_verified_owner)):
        try:
            require_enabled()
        except PermissionError as exc:
            raise HTTPException(status_code=404,detail="Chat demo read unavailable") from exc
        token=_owner_form_token(_owner["private_owner_id"],
                                PUBLIC_DEMO_ORIGIN,"chat_demo_read")
        return _page("Approve one read-only Computer task",
            "<article>This approves exactly ONE signed ChatGPT/GitHub workflow "
            "to verify the saved PUBLIC demonstration website login. The approval "
            "expires after 10 minutes. No website page, cookie, password, or "
            "private account information is sent to GitHub."
            "</article><form method='post' action='/owner/chat-demo-approval'>"
            "<input type='hidden' name='csrf_token' value='"+token+"'>"
            "<label>Type APPROVE <input name='confirmation' autocomplete='off' "
            "maxlength='7' required></label>"
            "<button type='submit'>Approve one public-demo read</button></form>")

    @app.post("/owner/chat-demo-approval", response_class=HTMLResponse)
    async def owner_approve_one_public_demo(
        request:Request,
        csrf_token:str=Form(default=""),
        confirmation:str=Form(default=""),
        _owner=Depends(require_verified_owner),
    ):
        try:
            require_enabled()
        except PermissionError as exc:
            raise HTTPException(status_code=404,detail="Chat demo read unavailable") from exc
        _verify_owner_form(request,_owner["private_owner_id"],
                           PUBLIC_DEMO_ORIGIN,"chat_demo_read",csrf_token)
        if confirmation!="APPROVE":
            raise HTTPException(status_code=403,detail="Exact owner approval required")
        try:
            result=await asyncio.to_thread(
                approve_one_demo_read,_owner["private_owner_id"])
        except Exception as exc:
            raise HTTPException(status_code=503,
                 detail="Unable to store signed demo read consent") from exc
        return _page("Single public-demo browser read approved",
            "<article>One read-only demonstration session check is authorized "
            "for up to 10 minutes. It cannot change websites or return cookies. "
            "A matching signed GitHub workflow may now run once."
            "</article><p><a href='/owner'>Return to Computer</a></p>")

    @app.post("/internal/chat-demo-read")
    async def signed_github_demo_read(
        authorization:str|None=Header(default=None),
    ):
        try:
            require_enabled()
            if (not isinstance(authorization,str)
                    or not authorization.startswith("Bearer ")):
                raise PermissionError("Missing signed OIDC workflow identity")
            token=authorization[7:]
            caller=GitHubOIDCTokenVerifier(
                GitHubRelayIdentity.from_environment()
            )
            caller.verify(token)
        except Exception as exc:
            raise HTTPException(status_code=401,
                 detail="Signed owner-bound workflow required") from exc
        try:
            owner=await asyncio.to_thread(consume_one_demo_read)
        except Exception as exc:
            raise HTTPException(status_code=403,
                 detail="One-time owner approval absent or expired") from exc
        try:
            result=await asyncio.wait_for(
                read_saved_site(site=PUBLIC_DEMO_ORIGIN,owner=owner),timeout=42)
            verified=(
                isinstance(result,dict)
                and result.get("site")==PUBLIC_DEMO_ORIGIN
                and result.get("http_status")==200
                and result.get("demo_authenticated_restored") is True
            )
        except Exception:
            verified=False
        # NEVER return raw page, cookies, profile blobs, token, owner ID,
        # exception, GCS object name, or model-supplied URL.
        return JSONResponse({
            "schema":"plenum-owner-paired-public-demo-read-v1",
            "demo_login_restored":bool(verified),
            "read_only":True,
            "website_modified":False,
            "private_contents_exposed":False,
            "approval_consumed":True,
        },headers=_READ_HEADERS)

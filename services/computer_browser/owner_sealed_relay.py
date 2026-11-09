"""Existing owner Auth0 portal + signed GitHub OIDC, one sealed private-page read.

The GitHub job specifies NO site, path, key, or page content. The owner
approves those only in this authenticated web portal. The response to the
signed job is ciphertext for a recipient-controlled ephemeral public key.
This is NOT a generic account-automation or unrestricted MCP endpoint.
"""
import asyncio
import os
from html import escape

from fastapi import Depends, Form, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from .engine import allowed_origins
from .github_oidc_read_policy import GitHubOIDCTokenVerifier, GitHubRelayIdentity
from .owner_console import require_verified_owner
from .owner_saved_session import (
    _owner_form_token, _verify_owner_form, _require_allowed_origin,
    _page, read_saved_site,
)
from .private_profiles import BrowserProfileStore
from .sealed_chat_read import (
    FLAG, require_enabled, approve_read, consume_read, seal_result,
)

_HEADERS = {"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}


def mount_owner_sealed_relay(app):
    if (os.environ.get("K_SERVICE") != "plenum-browser-owner-auth0"
            or os.environ.get(FLAG) != "true"):
        return

    @app.get("/owner/chat-sealed-approval", response_class=HTMLResponse)
    async def approve_page(_owner=Depends(require_verified_owner)):
        try:
            require_enabled()
            store = BrowserProfileStore.from_environment()
        except Exception as exc:
            raise HTTPException(status_code=503,
                                detail="Private owner read unavailable") from exc
        forms = []
        for site in sorted(allowed_origins()):
            try:
                exists = store.status(owner=_owner["private_owner_id"],
                                      origin=site).get("profile_exists") is True
            except Exception:
                exists = False
            if not exists:
                continue
            token = escape(_owner_form_token(_owner["private_owner_id"],
                                             site, "sealed_read"), quote=True)
            forms.append(
                "<article><strong>Site: " + escape(site) + "</strong>"
                "<p>Only you can authorize a one-time read of a page on this "
                "already approved and encrypted saved website session. "
                "A fresh recipient public key encrypts its bounded page text "
                "before GitHub receives anything. Keep the matching private "
                "key in your current conversation and never paste it here.</p>"
                "<form method='post' action='/owner/chat-sealed-approval'>"
                "<input type='hidden' name='site' value='" + escape(site, quote=True) + "'>"
                "<input type='hidden' name='csrf_token' value='" + token + "'>"
                "<label>Relative page path <input name='path' value='/' "
                "maxlength='800' autocomplete='off' required></label>"
                "<p><label>Recipient ephemeral public key "
                "<input name='recipient_public_key' maxlength='43' "
                "autocomplete='off' required></label></p>"
                "<p><label>Type APPROVE to share this one page privately "
                "<input name='confirmation' maxlength='7' "
                "autocomplete='off' required></label></p>"
                "<button type='submit'>Approve one encrypted page read</button>"
                "</form></article>"
            )
        if not forms:
            return _page("No eligible encrypted sessions",
                "<article>No approved saved website session is currently "
                "available for this owner. Do not send passwords or cookies "
                "to ChatGPT or GitHub.</article>")
        return _page("Approve one sealed Computer page read", "".join(forms))

    @app.post("/owner/chat-sealed-approval", response_class=HTMLResponse)
    async def approve_page_post(
        request: Request, site: str = Form(), path: str = Form(),
        recipient_public_key: str = Form(),
        csrf_token: str = Form(default=""),
        confirmation: str = Form(default=""),
        _owner=Depends(require_verified_owner),
    ):
        try:
            require_enabled()
            site = _require_allowed_origin(site)
            _verify_owner_form(request, _owner["private_owner_id"],
                               site, "sealed_read", csrf_token)
            if confirmation != "APPROVE":
                raise HTTPException(status_code=403,
                                    detail="Explicit owner approval required")
            result = await asyncio.to_thread(
                approve_read, _owner["private_owner_id"],
                site=site, path=path,
                recipient_public_key=recipient_public_key,
            )
        except HTTPException:
            raise
        except (ValueError, PermissionError) as exc:
            raise HTTPException(status_code=403,
                                detail="Scope or saved session was not approved") from exc
        except Exception as exc:
            raise HTTPException(status_code=503,
                                detail="Private owner consent unavailable") from exc
        return _page("One sealed private page read authorized",
            "<article>The exact approved site, path and recipient public key "
            "are sealed in the owner's existing private encrypted vault. "
            "One signed founder GitHub workflow may read only that page "
            "within " + str(result["expires_in_seconds"]) + " seconds. "
            "Only encrypted text may reach GitHub. No website changes, "
            "cookies, passwords, or private keys are shared.</article>")

    @app.post("/internal/chat-sealed-read")
    async def signed_sealed_page_read(
        authorization: str | None = Header(default=None),
    ):
        try:
            require_enabled()
            if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
                raise PermissionError("Missing signed workflow")
            verifier = GitHubOIDCTokenVerifier(
                GitHubRelayIdentity.from_environment(), sealed=True)
            verifier.verify(authorization[7:])
        except Exception as exc:
            raise HTTPException(status_code=401,
                                detail="Signed founder workflow required") from exc
        try:
            # Existing GCS atomic compare-and-delete is a mandatory first step.
            consent = await asyncio.to_thread(consume_read)
        except Exception as exc:
            raise HTTPException(status_code=403,
                                detail="Owner consent absent or expired") from exc
        try:
            result = await asyncio.wait_for(read_saved_site(
                site=consent["site"], owner=consent["owner"],
                path=consent["path"],
            ), timeout=43)
            encrypted = seal_result(consent, result)
        except Exception as exc:
            raise HTTPException(status_code=503,
                                detail="Owner-approved private read failed") from exc
        return JSONResponse(encrypted, headers=_HEADERS)

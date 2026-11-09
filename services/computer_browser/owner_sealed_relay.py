"""Existing owner Auth0 portal + signed GitHub OIDC, one sealed private-page read.

The GitHub job specifies NO site, path, key, or page content. The owner
approves those only in this authenticated web portal. The response to the
signed job is ciphertext for a recipient-controlled ephemeral public key.
This is NOT a generic account-automation or unrestricted MCP endpoint.
"""
import asyncio
import os
import re
from html import escape

from fastapi import Depends, Form, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from .engine import allowed_origins
from .github_oidc_read_policy import GitHubOIDCTokenVerifier, GitHubRelayIdentity
from .owner_console import require_verified_owner
from .owner_saved_session import (
    _owner_form_token, _verify_owner_form, _require_allowed_origin,
    _page, read_saved_site, read_saved_batch,
)
from .private_profiles import BrowserProfileStore
from .sealed_chat_read import (
    FLAG, require_enabled, approve_read, consume_read, seal_result,
)

from .owner_adaptive_session import (
    FLAG as ADAPTIVE_FLAG, MAX_FOLLOWS,
    require_enabled as require_adaptive, _safe_links,
    read_hardened_saved_site, begin_session, consume_follow, save_follow,
    revoke_session, require_pending,
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
            adaptive_option = (
                "<p><label><input type='checkbox' name='adaptive' value='read_only'>"
                "Allow up to THREE adaptive read-only same-site link follows "
                "within TEN minutes (no script execution, forms, submissions, "
                "downloads, account writes or arbitrary URLs). Every follow-up "
                "is still limited to a link on the previous approved page. "
                "</label></p>"
                if os.environ.get(ADAPTIVE_FLAG) == "true" else ""
            )
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
                "<p><label>Optional additional read-only paths (up to two, one "
                "per line; same website, no form submission) "
                "<textarea name='additional_paths' maxlength='480' rows='3'></textarea>"
                "</label></p>" + adaptive_option +
                "<p><label>Recipient ephemeral public key "
                "<input name='recipient_public_key' maxlength='43' "
                "autocomplete='off' required></label></p>"
                "<p><label>Type APPROVE to share this one page privately "
                "<input name='confirmation' maxlength='7' "
                "autocomplete='off' required></label></p>"
                "<button type='submit'>Approve one encrypted page read</button>"
                "</form></article>"
            )
        token_revoke = escape(_owner_form_token(
            _owner["private_owner_id"], "https://example.com", "adaptive_revoke"
        ), quote=True)
        revoke_form = (
            "<article><strong>End any active adaptive browsing session</strong>"
            "<form method='post' action='/owner/chat-adaptive-revoke'>"
            "<input type='hidden' name='csrf_token' value='" + token_revoke + "'>"
            "<label>Type REVOKE <input name='confirmation' maxlength='6' "
            "autocomplete='off' required></label>"
            "<button type='submit'>Revoke adaptive browser session</button>"
            "</form></article>"
        )
        if not forms:
            forms.append("<article>No approved saved website session is currently "
                         "available for this owner. Do not share credentials.</article>")
        return _page("Approve sealed Computer page reads",
                     "".join(forms) + revoke_form)

    @app.post("/owner/chat-sealed-approval", response_class=HTMLResponse)
    async def approve_page_post(
        request: Request, site: str = Form(), path: str = Form(),
        recipient_public_key: str = Form(),
        additional_paths: str = Form(default=""),
        adaptive: str = Form(default=""),
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
            if adaptive not in ("", "read_only"):
                raise HTTPException(status_code=403,
                                    detail="Unrecognized adaptive approval")
            if adaptive == "read_only" and additional_paths.strip():
                raise HTTPException(status_code=403,
                                    detail="Select either a fixed batch or adaptive read")
            params = {"site": site, "path": path,
                      "recipient_public_key": recipient_public_key}
            if additional_paths.strip():
                params["additional_paths"] = additional_paths
            if adaptive == "read_only":
                require_adaptive()
                params["adaptive"] = True
            result = await asyncio.to_thread(
                approve_read, _owner["private_owner_id"], **params
            )
        except HTTPException:
            raise
        except (ValueError, PermissionError) as exc:
            raise HTTPException(status_code=403,
                                detail="Scope or saved session was not approved") from exc
        except Exception as exc:
            raise HTTPException(status_code=503,
                                detail="Private owner consent unavailable") from exc
        description = (
            "One signed founder GitHub workflow may start the read-only site "
            "navigation session. The first and up to THREE later safe same-site "
            "links are bounded by ten minutes and encrypted to the same key. "
            if adaptive == "read_only" else
            "One signed founder workflow may read only the exact approved "
            "page(s) within ten minutes. "
        )
        return _page("One sealed private page read authorized",
            "<article>Owner-approved scope encrypted in existing private vault. "
            + description +
            "No website changes, credentials, cookies, or private keys "
            "are ever delivered to GitHub.</article>")

    @app.post("/owner/chat-adaptive-revoke", response_class=HTMLResponse)
    async def owner_revoke_adaptive(
        request: Request, csrf_token: str = Form(default=""),
        confirmation: str = Form(default=""),
        _owner=Depends(require_verified_owner),
    ):
        _verify_owner_form(request, _owner["private_owner_id"],
                           "https://example.com", "adaptive_revoke", csrf_token)
        if confirmation != "REVOKE":
            raise HTTPException(status_code=403, detail="Revocation must be explicit")
        try:
            was_active = await asyncio.to_thread(revoke_session)
        except Exception as exc:
            raise HTTPException(status_code=503,
                                detail="Unable to verify private session revocation") from exc
        return _page("Adaptive browser session ended",
                     "<article>Any active adaptive follow-up session has been "
                     "revoked; no saved login credentials were deleted.</article>")

    @app.post("/internal/chat-sealed-read")
    async def signed_sealed_page_read(
        authorization: str | None = Header(default=None),
        navigation: str | None = Header(default=None, alias="X-Plenum-Navigation"),
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
        if navigation is not None:
            # Only a signed founder workflow may follow an opaque link ID.
            # The public issue carries no account URL, path or private text.
            match = re.fullmatch(r"([0-9a-f]{32}):([1-6])", navigation)
            if match is None:
                raise HTTPException(status_code=403,
                                    detail="Invalid private navigation request")
            try:
                cursor = await asyncio.to_thread(
                    consume_follow, match.group(1), int(match.group(2))
                )
            except Exception as exc:
                raise HTTPException(status_code=403,
                                    detail="No matching owner-approved link") from exc
            try:
                result = await asyncio.wait_for(read_hardened_saved_site(
                    site=cursor["site"], owner=cursor["owner"],
                    path=cursor["path"],
                ), timeout=45)
                links = _safe_links(cursor["site"], cursor["path"], result)
                result = {**result, "links_untrusted": links}
                response_record = {
                    "site": cursor["site"], "path": cursor["path"],
                    "recipient_public_key": cursor["recipient_public_key"],
                    "adaptive_session_id": cursor["session_id"],
                    "adaptive_remaining": cursor["remaining"],
                }
                encrypted = seal_result(response_record, result)
                await asyncio.to_thread(save_follow, cursor, result)
                return JSONResponse(encrypted, headers=_HEADERS)
            except Exception as exc:
                raise HTTPException(status_code=503,
                                    detail="Encrypted adaptive navigation failed") from exc

        try:
            # The original GCS atomic compare-and-delete is mandatory.
            consent = await asyncio.to_thread(consume_read)
        except Exception as exc:
            raise HTTPException(status_code=403,
                                detail="Owner consent absent or expired") from exc
        try:
            if consent.get("schema") == "plenum-sealed-owner-adaptive-consent-v1":
                # Revocation must block the first read, not only follow-ups.
                await asyncio.to_thread(require_pending, consent)
                result = await asyncio.wait_for(read_hardened_saved_site(
                    site=consent["site"], owner=consent["owner"],
                    path=consent["path"],
                ), timeout=45)
                links = _safe_links(consent["site"], consent["path"], result)
                result = {**result, "links_untrusted": links}
                encrypted = seal_result(consent, result)
                await asyncio.to_thread(begin_session, consent, result)
            elif consent.get("additional_paths"):
                result = await asyncio.wait_for(read_saved_batch(
                    site=consent["site"], owner=consent["owner"],
                    path=consent["path"],
                    additional_paths=consent["additional_paths"],
                ), timeout=105)
                encrypted = seal_result(consent, result)
            else:
                result = await asyncio.wait_for(read_saved_site(
                    site=consent["site"], owner=consent["owner"],
                    path=consent["path"],
                ), timeout=43)
                encrypted = seal_result(consent, result)
        except Exception as exc:
            raise HTTPException(status_code=503,
                                detail="Owner-approved private read failed") from exc
        return JSONResponse(encrypted, headers=_HEADERS)

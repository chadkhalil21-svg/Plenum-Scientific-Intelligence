"""Separate managed Auth0 owner entrance for the existing Plenum browser.

Reuse Authlib OAuth/OIDC with Authorization Code + S256 PKCE; never implement
an identity provider or expose the IAP browser through a public route.
This module is active ONLY inside an explicitly separate Cloud Run service.
No website tokens or OAuth access/refresh tokens are stored in the browser cookie.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import time
from urllib.parse import urlsplit

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

SERVICE_NAME = "plenum-browser-owner-auth0"
ISSUER = "https://dev-8sylxsg44yh5kkhh.us.auth0.com/"
EXPIRES_SECONDS = 1800
REQUIRE_CLIENT_ID = re.compile(r"^[A-Za-z0-9_-]{10,160}$")


def active() -> bool:
    return os.environ.get("K_SERVICE") == SERVICE_NAME


def _config() -> tuple[str, str]:
    """Fail closed for disabled/unconfigured client or unauthenticated owner."""
    if not active():
        raise PermissionError("Auth0 owner gateway is not active in this service")
    client_id = os.environ.get("AUTH0_OWNER_CLIENT_ID", "")
    origin = os.environ.get("AUTH0_OWNER_PUBLIC_ORIGIN", "")
    try:
        parsed = urlsplit(origin)
        valid_origin = (
            parsed.scheme == "https"
            and parsed.port in (None, 443)
            and parsed.username is None
            and parsed.password is None
            and parsed.path == ""
            and not parsed.query and not parsed.fragment
            and bool(re.fullmatch(
                r"plenum-browser-owner-auth0-[a-z0-9.-]+[.]run[.]app",
                parsed.hostname or "",
            ))
            and not any(ord(ch) < 33 or ord(ch) == 127 for ch in origin)
        )
    except ValueError:
        valid_origin = False
    if not REQUIRE_CLIENT_ID.fullmatch(client_id) or not valid_origin:
        raise PermissionError("Owner OAuth application is not configured")
    return client_id, origin


def _verified_owner(claims: dict) -> dict:
    """Accept only Authlib-validated OIDC ID-token claims for this exact owner."""
    if not isinstance(claims, dict):
        raise PermissionError("Verified OIDC claims required")
    expected = os.environ.get("COMPUTER_OWNER_EMAIL", "").strip().lower()
    actual = claims.get("email")
    sub = claims.get("sub")
    if (not expected or expected.count("@") != 1
            or not isinstance(actual, str)
            or not hmac.compare_digest(actual.strip().lower(), expected)
            or claims.get("email_verified") is not True
            or not isinstance(sub, str) or not 8 <= len(sub) <= 240):
        raise PermissionError("Authorized verified owner account required")
    # An owner-sub variable is optional only for first enrollment; matching the
    # verified and exact owner email remains mandatory in all cases.
    pinned = os.environ.get("AUTH0_OWNER_SUB", "").strip()
    if pinned and not hmac.compare_digest(pinned, sub):
        raise PermissionError("Immutable owner identity did not match")
    issuer = claims.get("iss")
    if issuer != ISSUER:
        raise PermissionError("Untrusted owner identity issuer")
    return {
        "owner_verified": True,
        "principal": "authorized-owner",
        "private_owner_id": hashlib.sha256((ISSUER + sub).encode()).hexdigest(),
    }


def verified_session(scope) -> dict:
    """Verify Authlib-generated, signed, secure HTTP/WebSocket owner session."""
    if not active():
        raise PermissionError("Auth0 owner gateway inactive")
    session = scope.get("session")
    if not isinstance(session, dict):
        raise PermissionError("No owner session")
    record = session.get("plenum_auth0_owner_v1")
    if not isinstance(record, dict) or set(record) != {"owner", "iat", "exp"}:
        raise PermissionError("Owner session unavailable")
    now = int(time.time())
    iat, exp, owner_id = record["iat"], record["exp"], record["owner"]
    if (not isinstance(iat, int) or isinstance(iat, bool)
            or not isinstance(exp, int) or isinstance(exp, bool)
            or iat > now + 10 or exp <= now
            or not 0 < exp - iat <= EXPIRES_SECONDS
            or not isinstance(owner_id, str)
            or not re.fullmatch(r"[0-9a-f]{64}", owner_id)):
        raise PermissionError("Owner session expired")
    return {
        "owner_verified": True,
        "principal": "authorized-owner",
        "private_owner_id": owner_id,
    }


def _session_secret() -> str:
    """Use HKDF-like domain separation from existing 256-bit service secret.

    The derived signer does not reveal the secret used for server-side bearer
    validation. If the source secret is missing, this service cannot start.
    """
    raw = os.environ.get("COMPUTER_BROWSER_TOKEN", "")
    if len(raw) < 32:
        raise RuntimeError("Auth0 owner session key material unavailable")
    return hmac.digest(raw.encode(), b"plenum.browser.auth0.owner.cookie.v1", "sha256").hex()


def mount_auth0_owner(app) -> None:
    """Install a new *separate service* portal without changing the original IAP."""
    if not active():
        return
    from authlib.integrations.starlette_client import OAuth
    from starlette.middleware.sessions import SessionMiddleware

    app.add_middleware(
        SessionMiddleware,
        secret_key=_session_secret(),
        session_cookie="__Host-plenum_browser_owner",
        max_age=EXPIRES_SECONDS,
        same_site="lax",
        https_only=True,
        path="/",
    )
    # A missing client ID is intentionally allowed only for a locked bootstrap
    # health page. No login, authenticated browser state or bearer tool works.
    client_id = os.environ.get("AUTH0_OWNER_CLIENT_ID", "")
    oauth = OAuth()
    if REQUIRE_CLIENT_ID.fullmatch(client_id):
        oauth.register(
            name="plenum_auth0",
            client_id=client_id,
            client_secret=None,
            token_endpoint_auth_method="none",
            server_metadata_url=ISSUER + ".well-known/openid-configuration",
            client_kwargs={
                "scope": "openid profile email",
                "code_challenge_method": "S256",
            },
        )

    @app.get("/", response_class=HTMLResponse)
    async def auth0_home(request: Request):
        try:
            verified_session(request.scope)
            return RedirectResponse("/owner", status_code=303)
        except PermissionError:
            return HTMLResponse(
                "<!doctype html><title>Plenum Computer Browser</title>"
                "<h1>Plenum Computer Browser</h1>"
                "<p>Independent owner browser. Authentication required.</p>"
                '<p><a href="/auth0/login">Sign in securely with Auth0</a></p>',
                headers={"Cache-Control": "no-store",
                         "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'",
                         "X-Content-Type-Options": "nosniff"},
            )

    @app.get("/auth0/login")
    async def auth0_login(request: Request):
        try:
            _, origin = _config()
        except PermissionError as exc:
            raise HTTPException(status_code=503, detail="Owner login connection not yet configured") from exc
        if oauth.plenum_auth0 is None:
            raise HTTPException(status_code=503, detail="Owner login connection unavailable")
        # Authlib owns the state/nonce/PKCE exchange; callback is fixed, not
        # derived from untrusted Host/X-Forwarded-Host request headers.
        return await oauth.plenum_auth0.authorize_redirect(
            request, origin + "/auth0/callback"
        )

    @app.get("/auth0/callback")
    async def auth0_callback(request: Request):
        try:
            _config()
            if oauth.plenum_auth0 is None:
                raise PermissionError("Auth0 client unavailable")
            token = await oauth.plenum_auth0.authorize_access_token(request)
            # The validated OIDC id_token claims are returned in userinfo.
            # Never store the access token, ID token or refresh token in cookies.
            claims = token.get("userinfo")
            if not isinstance(claims, dict):
                raise PermissionError("Verified OIDC ID token unavailable")
            owner = _verified_owner(claims)
        except Exception:
            request.session.clear()
            # This is an authentication boundary; never print token/provider
            # details or raw query parameters in responses or application logs.
            raise HTTPException(status_code=403, detail="Owner login was not verified")
        now = int(time.time())
        request.session.clear()
        request.session["plenum_auth0_owner_v1"] = {
            "owner": owner["private_owner_id"],
            "iat": now,
            "exp": now + EXPIRES_SECONDS,
        }
        return RedirectResponse("/owner", status_code=303,
                                headers={"Cache-Control": "no-store"})

    @app.get("/auth0/logout")
    async def auth0_logout(request: Request):
        request.session.clear()
        return RedirectResponse("/", status_code=303,
                                headers={"Cache-Control": "no-store"})

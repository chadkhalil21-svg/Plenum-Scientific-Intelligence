"""Owner-verified self-service website origin registration.

Reuses the existing owner Auth0 session, signed CSRF tokens, encrypted
GCS vault and single-owner scope. Owner-only private sign-in now consumes active grants using the existing
pinned-public-IP CONNECT proxy; general model-controlled navigation does not.
The original BROWSER_ALLOWED_ORIGINS signed chat action policy remains intact. Never read this from untrusted web content,
GitHub issue instructions, or a model-generated request alone.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from html import escape

from fastapi import Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse

from .engine import public_dns_only
from .owner_approval import _origin as canonical_origin
from .owner_console import require_verified_owner
from .owner_saved_session import _owner_form_token, _verify_owner_form, _page
from .private_profiles import BrowserProfileStore

FLAG = "PLENUM_RUNTIME_SITE_GRANTS_ENABLED"
MAX_SITES = 30
TTL_SECONDS = 7 * 24 * 3600
REGISTRY_SCOPE = "site-registry-v1"
_SCHEMA = "plenum-owner-origin-grants-v1"


def enabled():
    return (os.environ.get("K_SERVICE") == "plenum-browser-owner-auth0"
            and os.environ.get(FLAG) == "true")


def _owner(owner_id: str) -> str:
    if (not isinstance(owner_id, str) or not 1 <= len(owner_id) <= 80
            or "/" in owner_id):
        raise PermissionError("Verified owner identity required")
    return owner_id


def normalize_origin(origin: str) -> str:
    """A bare, exact, public HTTPS DNS origin, no URL paths or subdomains implied."""
    if not isinstance(origin, str) or len(origin) > 240:
        raise PermissionError("Invalid website origin")
    try:
        canonical = canonical_origin(origin)
    except (ValueError, PermissionError) as exc:
        raise PermissionError("Website origin must be a public HTTPS domain") from exc
    if canonical != origin:
        raise PermissionError("Enter the exact canonical HTTPS origin, without path or query")
    return origin


class OwnerSiteGrantStore:
    """One encrypted owner-specific GCS index with CAS updates and 7-day expiry."""

    def __init__(self, *, bucket, key):
        from cryptography.fernet import Fernet
        self.bucket = bucket
        self.fernet = Fernet(key if isinstance(key, bytes) else key.encode())

    @classmethod
    def from_environment(cls):
        # Reuse the ORIGINAL private GCS bucket/public-access-prevention guard.
        store = BrowserProfileStore.from_environment()
        store._require_private_bucket()
        return cls(bucket=store.bucket, key=os.environ["BROWSER_SESSION_KEY"])

    def _blob(self, owner):
        prefix = hashlib.sha256(_owner(owner).encode()).hexdigest()
        return self.bucket.blob("browser-owner-site-grants/v1/" + prefix + ".sealed")

    def _read(self, owner):
        from cryptography.fernet import InvalidToken
        blob = self._blob(owner)
        if not blob.exists():
            return [], 0
        blob.reload()
        gen = int(blob.generation)
        ciphertext = blob.download_as_bytes(if_generation_match=gen)
        if not isinstance(ciphertext, bytes) or len(ciphertext) > 28000:
            raise PermissionError("Invalid private origin registry")
        try:
            data = json.loads(self.fernet.decrypt(ciphertext))
        except (InvalidToken, UnicodeError, ValueError, TypeError) as exc:
            raise PermissionError("Private origin registry could not be verified") from exc
        if (not isinstance(data, dict)
                or set(data) != {"schema", "owner", "origins"}
                or data["schema"] != _SCHEMA
                or data["owner"] != _owner(owner)
                or not isinstance(data["origins"], list)
                or len(data["origins"]) > MAX_SITES):
            raise PermissionError("Invalid owner registry")
        rows, seen = [], set()
        for item in data["origins"]:
            if (not isinstance(item, dict)
                    or set(item) != {"origin", "issued", "expires"}
                    or type(item["issued"]) is not int
                    or type(item["expires"]) is not int
                    or item["issued"] < 1
                    or not 0 < item["expires"] - item["issued"] <= TTL_SECONDS):
                raise PermissionError("Invalid site registration")
            canonical = normalize_origin(item["origin"])
            if canonical in seen:
                raise PermissionError("Duplicate registered website")
            seen.add(canonical)
            rows.append(item)
        return rows, gen

    def list_active(self, *, owner, now=None):
        t = int(time.time() if now is None else now)
        rows, _ = self._read(owner)
        return sorted((dict(row) for row in rows
                       if row["issued"] <= t < row["expires"]),
                      key=lambda row: row["origin"])

    def authorized(self, *, owner, origin, now=None):
        site = normalize_origin(origin)
        return any(x["origin"] == site for x in self.list_active(owner=owner, now=now))

    def _write(self, *, owner, rows, generation):
        if len(rows) > MAX_SITES:
            raise PermissionError("Maximum 30 registered sites")
        raw = json.dumps({
            "schema": _SCHEMA, "owner": _owner(owner), "origins": rows,
        }, sort_keys=True, separators=(",", ":")).encode()
        if len(raw) > 16000:
            raise PermissionError("Owner site registry too large")
        blob = self._blob(owner)
        blob.upload_from_string(self.fernet.encrypt(raw),
                                content_type="application/octet-stream",
                                if_generation_match=generation)

    def register(self, *, owner, origin, now=None):
        site = normalize_origin(origin)
        t = int(time.time() if now is None else now)
        rows, generation = self._read(owner)
        fresh = [x for x in rows if x["expires"] > t and x["origin"] != site]
        fresh.append({"origin": site, "issued": t, "expires": t + TTL_SECONDS})
        self._write(owner=owner, rows=fresh, generation=generation)
        return {"registered": True, "site": site,
                "expires_seconds": TTL_SECONDS,
                "browser_navigation_enabled": False}

    def revoke(self, *, owner, origin, now=None):
        site = normalize_origin(origin)
        t = int(time.time() if now is None else now)
        rows, generation = self._read(owner)
        fresh = [x for x in rows if x["expires"] > t and x["origin"] != site]
        if len(fresh) == len(rows) and all(x["expires"] > t for x in rows):
            return {"revoked": False, "site": site}
        self._write(owner=owner, rows=fresh, generation=generation)
        return {"revoked": True, "site": site}


def mount_runtime_site_grants(app):
    if not enabled():
        return

    @app.get("/owner/sites", response_class=HTMLResponse)
    async def list_sites(_owner=Depends(require_verified_owner)):
        owner_id = _owner["private_owner_id"]
        try:
            rows = OwnerSiteGrantStore.from_environment().list_active(owner=owner_id)
        except Exception as exc:
            raise HTTPException(status_code=503,
                                detail="Private website registration unavailable") from exc
        token = escape(_owner_form_token(owner_id, REGISTRY_SCOPE, "site_register"), quote=True)
        parts = [
            "<small>Only your verified owner session can register a site. "
            "Registration is encrypted, limited to exact public HTTPS origins "
            "and expires automatically after seven days. "
            "<strong>Registration enables only owner-operated private sign-in</strong> "
            "through an IP-pinned single-origin browser. ChatGPT account "
            "actions and cross-site sign-in remain separately gated.</small>",
            "<form method='post' action='/owner/sites/authorize'>"
            "<label>Website HTTPS origin (for example https://example.org)"
            "<input name='site' type='url' maxlength='240' autocomplete='off' required>"
            "</label><input type='hidden' name='csrf_token' value='" + token + "'>"
            "<label>Type AUTHORIZE to register this exact website"
            "<input name='confirmation' maxlength='9' required></label>"
            "<button type='submit'>Register owner-approved website</button></form>",
        ]
        for row in rows:
            origin = row["origin"]
            revoke = escape(_owner_form_token(owner_id, origin, "site_revoke"), quote=True)
            preview_token = escape(_owner_form_token(owner_id, origin, "site_preview"), quote=True)
            preview_enabled = os.environ.get("PLENUM_PINNED_PUBLIC_PREVIEW_ENABLED") == "true"
            preview_form = (
                "<form method='post' action='/owner/sites/preview'>"
                "<input type='hidden' name='site' value='" + escape(origin, quote=True) + "'>"
                "<input type='hidden' name='csrf_token' value='" + preview_token + "'>"
                "<label>Relative page to inspect (public HTML only)"
                "<input name='path' maxlength='800' value='/' required></label>"
                "<button type='submit'>Read public page securely</button></form>"
                if preview_enabled else "")
            parts.append(
                "<article><strong>" + escape(origin) + "</strong>"
                "<p>Registration active. Owner-only private sign-in is available "
                "through pinned Chromium. ChatGPT actions and website changes "
                "remain separately gated.</p>" + preview_form +
                "<form method='post' action='/owner/sites/revoke'>"
                "<input type='hidden' name='site' value='" + escape(origin, quote=True) + "'>"
                "<input type='hidden' name='csrf_token' value='" + revoke + "'>"
                "<label>Type REVOKE <input name='confirmation' maxlength='6' required></label>"
                "<button type='submit'>Revoke registration</button></form></article>"
            )
        return _page("Owner-authorized website registry", "".join(parts))

    @app.post("/owner/sites/preview", response_class=HTMLResponse)
    async def preview_registered_site(
        request: Request, site: str = Form(), path: str = Form(),
        csrf_token: str = Form(default=""),
        _owner=Depends(require_verified_owner),
    ):
        """Only owner-approved, read-only public HTML, never site credentials."""
        if os.environ.get("PLENUM_PINNED_PUBLIC_PREVIEW_ENABLED") != "true":
            raise HTTPException(status_code=404, detail="Public website preview unavailable")
        owner_id = _owner["private_owner_id"]
        site = normalize_origin(site)
        _verify_owner_form(request, owner_id, site, "site_preview", csrf_token)
        try:
            from .owner_saved_session import _approved_read_target
            _approved_read_target(site, path)
            from .pinned_public_preview import read_registered_public
            import asyncio
            result = await asyncio.wait_for(
                read_registered_public(owner=owner_id, site=site, path=path),
                timeout=52)
        except PermissionError as exc:
            raise HTTPException(status_code=403,
                                detail="Website read not owner-approved") from exc
        except Exception as exc:
            raise HTTPException(status_code=502,
                                detail="Approved public page read failed") from exc
        return _page(
            "Public registered website preview",
            "<article><strong>" + escape(result["title"]) + "</strong>\\n"
            + escape(result["final_url"]) + "\\n\\n"
            + escape(result["body"]) + "</article>"
            "<small>Fresh Chromium, no saved credentials, scripts, files or "
            "website changes. An actual signed-in website session and interactive "
            "task actions require separate owner approval and execution gates.</small>"
            "<p><a href='/owner/sites'>Manage registered websites</a></p>")

    @app.post("/owner/sites/authorize", response_class=HTMLResponse)
    async def authorize_site(request: Request, site: str = Form(),
                             csrf_token: str = Form(default=""),
                             confirmation: str = Form(default=""),
                             _owner=Depends(require_verified_owner)):
        owner_id = _owner["private_owner_id"]
        _verify_owner_form(request, owner_id, REGISTRY_SCOPE, "site_register", csrf_token)
        if confirmation != "AUTHORIZE":
            raise HTTPException(status_code=403, detail="Explicit owner confirmation required")
        try:
            site = normalize_origin(site)
            # Pre-registration DNS validation is defense in depth, NOT proof
            # of rebinding-safe browser egress. Hence navigation stays disabled.
            public_dns_only(site)
            result = OwnerSiteGrantStore.from_environment().register(
                owner=owner_id, origin=site)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail="Invalid or unsafe HTTPS origin") from exc
        except Exception as exc:
            raise HTTPException(status_code=503,
                                detail="Website registration unavailable") from exc
        return _page("Website registration saved",
            "<article>Owner-only website <strong>" + escape(result["site"]) +
            "</strong> was saved in the existing encrypted vault for seven days. "
            "Owner-only private Chromium may now open this exact website through "
            "its pinned-origin gateway. ChatGPT actions, cross-site sign-in "
            "and website changes are NOT authorized.</article>"
            "<p><a href='/owner/sites'>Manage registered sites</a></p>")

    @app.post("/owner/sites/revoke", response_class=HTMLResponse)
    async def revoke_site(request: Request, site: str = Form(),
                          csrf_token: str = Form(default=""),
                          confirmation: str = Form(default=""),
                          _owner=Depends(require_verified_owner)):
        owner_id = _owner["private_owner_id"]
        site = normalize_origin(site)
        _verify_owner_form(request, owner_id, site, "site_revoke", csrf_token)
        if confirmation != "REVOKE":
            raise HTTPException(status_code=403, detail="Explicit revocation required")
        try:
            result = OwnerSiteGrantStore.from_environment().revoke(
                owner=owner_id, origin=site)
        except Exception as exc:
            raise HTTPException(status_code=503,
                                detail="Website revocation unavailable") from exc
        return _page("Website registration revoked",
            "<article>Owner runtime registration for <strong>" +
            escape(result["site"]) + "</strong> is no longer active. "
            "This action does not change a separately preconfigured "
            "site allowlist or delete previously saved website credentials. "
            "Revoke a saved encrypted session separately under Saved Sessions.</article>"
            "<p><a href='/owner/sites'>Manage registered sites</a></p>")

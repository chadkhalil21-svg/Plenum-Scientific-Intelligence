"""Optional, owner-only Bitwarden Secrets Manager CLI adapter for Plenum Browser.

Use Bitwarden Secrets Manager *machine accounts*, NOT the owner's personal
password-manager CLI or an unlocked master vault. An account-specific machine
token can read only its assigned projects. This file creates NO public API,
ChatGPT tool, default CLI login, global secret cache or automatic submission.
Owner-signed grants and the original origin-pinned browser must be enforced by
the caller. The adapter is disabled by default pending that private wiring.
"""
from __future__ import annotations

import asyncio
import inspect
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from urllib.parse import urlsplit

from .engine import safe_url

_SECRET_ID = re.compile(
    r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$",
    re.IGNORECASE,
)


@dataclass(frozen=True, repr=False)
class OwnerCredentialGrant:
    """Prepared by a trusted, verified owner service, NEVER a model response."""

    owner_id: str
    origin: str
    secret_id: str
    username_selector: str
    password_selector: str
    expires_at: float


def _exact_origin(origin: str) -> str:
    if not isinstance(origin, str) or len(origin) > 253:
        raise PermissionError("Exact HTTPS website origin required")
    try:
        p = urlsplit(origin)
        if (p.scheme != "https" or not p.hostname or p.port is not None or
                p.username is not None or p.password is not None or
                p.path or p.query or p.fragment or
                origin != "https://" + p.hostname):
            raise PermissionError("Noncanonical website origin")
    except (TypeError, ValueError) as exc:
        raise PermissionError("Invalid website origin") from exc
    return origin


def _check_grant(grant: OwnerCredentialGrant, page_url: str) -> None:
    if not isinstance(grant, OwnerCredentialGrant) or not grant.owner_id:
        raise PermissionError("Verified owner grant is required")
    origin = _exact_origin(grant.origin)
    if not _SECRET_ID.fullmatch(grant.secret_id):
        raise PermissionError("Approved specific secret ID is required")
    if not isinstance(grant.expires_at, (float, int)) or not (
        time.time() < grant.expires_at <= time.time() + 600
    ):
        raise PermissionError("Short-lived owner authorization is required")
    for selector in (grant.username_selector, grant.password_selector):
        if (not isinstance(selector, str) or not 1 <= len(selector) <= 240
                or any(ord(char) < 32 for char in selector)):
            raise PermissionError("Exact reviewed browser fields are required")
    if grant.username_selector == grant.password_selector:
        raise PermissionError("Credential fields must be distinct")
    if not safe_url(page_url, origins={origin}):
        raise PermissionError("Website does not match owner grant")


def _read_machine_secret(grant: OwnerCredentialGrant, *, runner=subprocess.run):
    """Return ONLY to this trusted browser process; never log CLI output.

    Official CLI: bws secret get <uuid>. Its JSON 'value' is a separately
    created, exact-HTTPS-origin-bound JSON object with username and password.
    """
    if os.environ.get("PLENUM_BWS_OWNER_FILL_ENABLED") != "true":
        raise PermissionError("Bitwarden owner credential fill not enabled")
    token = os.environ.get("BWS_ACCESS_TOKEN", "")
    if not token:
        raise PermissionError("Bitwarden machine account is not connected")
    try:
        completed = runner(
            ["bws", "secret", "get", grant.secret_id],
            capture_output=True, text=True, check=False, timeout=15,
            shell=False,
            env={
                "BWS_ACCESS_TOKEN": token,
                "PATH": os.environ.get("PATH", ""),
                "HOME": os.environ.get("HOME", ""),
            },
        )
        if completed.returncode != 0 or len(completed.stdout) > 16384:
            raise ValueError("not available")
        wrapper = json.loads(completed.stdout)
        if (not isinstance(wrapper, dict) or wrapper.get("object") != "secret"
                or wrapper.get("id", "").lower() != grant.secret_id.lower()):
            raise ValueError("wrong secret")
        data = json.loads(wrapper["value"])
        if not isinstance(data, dict) or set(data) != {
            "origin", "username", "password"
        }:
            raise ValueError("unapproved secret shape")
        if _exact_origin(data["origin"]) != grant.origin:
            raise ValueError("different website")
        username, password = data["username"], data["password"]
        if (not isinstance(username, str) or not 1 <= len(username) <= 320
                or not isinstance(password, str) or not 1 <= len(password) <= 4096):
            raise ValueError("invalid credential")
        return username, password
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
            subprocess.SubprocessError) as exc:
        # Never stringify an exception or command output: it can contain
        # passwords, auth tokens or server-supplied private website content.
        raise PermissionError("Approved Bitwarden credential unavailable") from None


async def fill_owner_approved_login(
    page,
    grant: OwnerCredentialGrant,
    *,
    verify_owner_grant,
    runner=subprocess.run,
):
    """Fill a reviewed login form; DO NOT click login, save state or return secrets.

    This requires an existing verified owner approval callback implemented by
    the private owner service; it is NOT safe to invoke from model-controlled
    arguments or a public GitHub workflow. A plain True/boolean is not accepted
    as a verifier. Never pass the personal vault master password to this API.
    """
    if not callable(verify_owner_grant):
        raise PermissionError("Trusted owner authorization callback missing")
    _check_grant(grant, page.url)
    permitted = verify_owner_grant(grant)
    if inspect.isawaitable(permitted):
        permitted = await permitted
    if permitted is not True:
        raise PermissionError("Owner did not approve exact credential use")
    _check_grant(grant, page.url)

    name_field = page.locator(grant.username_selector)
    password_field = page.locator(grant.password_selector)
    if await name_field.count() != 1 or await password_field.count() != 1:
        raise PermissionError("Approved credential fields are not unique")
    if await password_field.get_attribute("type") != "password":
        raise PermissionError("Approved password selector is not a password input")

    username, password = await asyncio.to_thread(
        _read_machine_secret, grant, runner=runner
    )
    try:
        _check_grant(grant, page.url)
        await name_field.fill(username, timeout=8000)
        await password_field.fill(password, timeout=8000)
        _check_grant(grant, page.url)
    finally:
        # Python strings cannot be securely zeroized; keep their lifetime
        # restricted to this function, with no history/log/model output.
        del username, password

    return {
        "status": "FILLED_AWAITING_OWNER_SUBMISSION",
        "website": grant.origin,
        "password_or_session_exposed_to_model": False,
        "automatically_submitted": False,
        "website_login_verified": False,
    }

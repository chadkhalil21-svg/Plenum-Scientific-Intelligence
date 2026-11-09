"""One-time owner-approved bridge consent stored in existing encrypted GCS vault.

No ChatGPT, GitHub or website credential is stored in an issue. An owner must
first sign into the separate Auth0 browser portal and approve precisely one
public-demonstration verification. An authenticated GitHub workflow may then
consume that approval exactly once, atomically, before launching Chromium.

This module is inert unless the owner-only Cloud Run relay flag is enabled.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import time

APPROVAL_BLOB="browser-chat-read/v1/owner-once.sealed"
MAX_APPROVAL_SECONDS=600
SERVICE="plenum-browser-owner-auth0"
FLAG="PLENUM_CHAT_RELAY_ENABLED"
ACTION="read_public_demo_authentication_only"


def require_enabled():
    if (os.environ.get("K_SERVICE")!=SERVICE
            or os.environ.get(FLAG)!="true"
            or os.environ.get("AUTH0_OWNER_PUBLIC_ORIGIN")
               !="https://plenum-browser-owner-auth0-2lak3vl73q-ue.a.run.app"
            or not os.environ.get("BROWSER_PROFILE_BUCKET")
            or not os.environ.get("BROWSER_SESSION_KEY")
            or not os.environ.get("COMPUTER_BROWSER_TOKEN")
            or os.environ.get("BROWSER_ALLOWED_ORIGINS","").split(",").count(
                "https://the-internet.herokuapp.com")!=1):
        raise PermissionError("Owner-paired demo read is disabled")


def _store():
    require_enabled()
    from .private_profiles import BrowserProfileStore
    store=BrowserProfileStore.from_environment()
    store._require_private_bucket()
    return store


def _cipher():
    from cryptography.fernet import Fernet
    secret=os.environ.get("BROWSER_SESSION_KEY","")
    if not secret:
        raise PermissionError("Encrypted chat approval unavailable")
    return Fernet(secret.encode())


def _owner(owner_id):
    if not isinstance(owner_id,str) or not re.fullmatch(r"[0-9a-f]{64}",owner_id):
        raise PermissionError("Verified opaque owner identity required")
    return owner_id


def approve_one_demo_read(owner_id, *, now=None):
    """Replace only fixed pending consent; require verified owner in caller."""
    owner=_owner(owner_id)
    t=int(time.time() if now is None else now)
    blob=_store().bucket.blob(APPROVAL_BLOB)
    generation=0
    if blob.exists():
        blob.reload()
        generation=int(blob.generation)
    # Encrypted at rest with same independently provisioned browser vault key.
    sealed=_cipher().encrypt(json.dumps({
        "schema":"plenum-owner-demo-pair-v1",
        "owner":owner,
        "action":ACTION,
        "issued":t,
        "expires":t+MAX_APPROVAL_SECONDS,
        "nonce":secrets.token_hex(16),
    },separators=(",",":")).encode())
    blob.upload_from_string(
        sealed,
        content_type="application/octet-stream",
        if_generation_match=generation,
    )
    return {"approved_once":True,"ttl_seconds":MAX_APPROVAL_SECONDS}


def consume_one_demo_read(*, now=None):
    """Atomic object deletion enforces single use even with concurrent callers.

    The caller MUST have already verified GitHub's short-lived signed OIDC JWT.
    Returns opaque owner ID only to trusted server-local code, never to tools.
    """
    t=int(time.time() if now is None else now)
    blob=_store().bucket.blob(APPROVAL_BLOB)
    try:
        blob.reload()
        gen=int(blob.generation)
        sealed=blob.download_as_bytes(if_generation_match=gen)
        from cryptography.fernet import InvalidToken
        data=json.loads(_cipher().decrypt(sealed,ttl=MAX_APPROVAL_SECONDS))
        owner=_owner(data.get("owner"))
        if (data.get("schema")!="plenum-owner-demo-pair-v1"
                or data.get("action")!=ACTION
                or not isinstance(data.get("issued"),int)
                or not isinstance(data.get("expires"),int)
                or data["issued"]>t+10
                or not 0<data["expires"]-data["issued"]<=MAX_APPROVAL_SECONDS
                or data["expires"]<=t
                or not isinstance(data.get("nonce"),str)
                or not re.fullmatch(r"[0-9a-f]{32}",data["nonce"])):
            raise PermissionError("Owner demo authorization unavailable")
        # Consume BEFORE using the encrypted website session. A second
        # concurrent invocation with this same generation cannot succeed.
        blob.delete(if_generation_match=gen)
        return owner
    except Exception as exc:
        raise PermissionError("One-time owner demo approval absent or consumed") from exc

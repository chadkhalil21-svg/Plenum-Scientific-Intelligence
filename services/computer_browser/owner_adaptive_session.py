"""Short-lived, owner-approved adaptive READ-ONLY saved-site navigation.

This is an adapter to the EXISTING owner Auth0, encrypted GCS, GitHub OIDC,
recipient-only sealed results, and original Chromium saved session. The public
GitHub issue carries ONLY a random cursor and link index, never a URL, cookie,
site, login, private page or action plan. One owner consent permits at most
three follow-up reads of exact same-site links returned by a previous read.

No arbitrary URL requests, submissions, account changes, scripts, uploads,
file downloads, private network access, general action-agent, or site bypass.
"""
from __future__ import annotations

import json
import os
import re
import time

CURSOR_BLOB = "browser-chat-read/v3/owner-adaptive-cursor.sealed"
FLAG = "PLENUM_ADAPTIVE_OWNER_READ_ENABLED"
MAX_FOLLOWS = 3
TTL = 600
_ID = re.compile(r"[0-9a-f]{32}")


def require_enabled():
    from .sealed_chat_read import require_enabled as require_sealed
    require_sealed()
    if os.environ.get(FLAG) != "true":
        raise PermissionError("Adaptive private read is disabled")


def _validate_id(value):
    if not isinstance(value, str) or _ID.fullmatch(value) is None:
        raise PermissionError("Invalid owner browser cursor")
    return value


def _safe_links(site, path, result):
    """Restrict original read-only link hints to non-action paths.

    A link is only a candidate for another HTTPS GET. Never execute an
    arbitrary instruction or path supplied in page text.
    """
    from .owner_saved_session import _approved_batch_paths
    from .sealed_chat_read import _validate_intent
    if not isinstance(result, dict) or result.get("site") != site:
        raise PermissionError("Saved owner page mismatch")
    if (result.get("final_url") != site + path
            or type(result.get("http_status")) is not int
            or result["http_status"] != 200):
        raise PermissionError("Saved owner page URL mismatch")
    links = result.get("links_untrusted", [])
    if not isinstance(links, list) or len(links) > 6:
        raise PermissionError("Malformed navigation links")
    candidates = []
    seen = set()
    for link in links:
        if not isinstance(link, dict) or set(link) != {"label_untrusted", "path"}:
            raise PermissionError("Malformed navigation link")
        name, relative = link["label_untrusted"], link["path"]
        if (not isinstance(name, str) or not 1 <= len(name) <= 75
                or any(ord(c) < 32 for c in name)
                or not isinstance(relative, str)):
            continue
        try:
            _approved_batch_paths(site, path, [relative])
        except PermissionError:
            continue
        if relative in seen:
            continue
        candidates.append({"label_untrusted": name, "path": relative})
        seen.add(relative)
    return candidates


def _cursor_blob():
    from .sealed_chat_read import _store
    return _store().bucket.blob(CURSOR_BLOB)


def _cipher():
    from .sealed_chat_read import _cipher as existing_cipher
    return existing_cipher()


def _check_scope(record, now):
    from .sealed_chat_read import _validate_intent
    from .owner_chat_pairing import _owner
    if (not isinstance(record, dict)
            or set(record) != {"schema", "session_id", "owner", "site",
                                "path", "recipient_public_key", "issued",
                                "expires", "remaining", "links"}
            or record.get("schema") != "plenum-adaptive-read-cursor-v1"
            or not _ID.fullmatch(str(record.get("session_id", "")))
            or type(record.get("issued")) is not int
            or type(record.get("expires")) is not int
            or type(record.get("remaining")) is not int
            or not 0 <= record["remaining"] <= MAX_FOLLOWS
            or not 0 < record["expires"] - record["issued"] <= TTL
            or record["issued"] > now + 10
            or record["expires"] <= now
            or not isinstance(record.get("links"), list)
            or len(record["links"]) > 6):
        raise PermissionError("Expired or malformed browser navigation approval")
    _owner(record["owner"])
    _validate_intent(site=record["site"], path=record["path"],
                     recipient_public_key=record["recipient_public_key"])
    # Revalidate every proposed link against the current approved origin.
    _safe_links(record["site"], record["path"], {
        "site": record["site"],
        "final_url": record["site"] + record["path"],
        "http_status": 200,
        "links_untrusted": record["links"],
    })
    return record


def begin_session(consent, result, *, now=None):
    """After first exact owner-approved read, create a bounded cursor.

    Replaces only the existing previous owner cursor, never a browser
    credential. Storage is private/FERNET-encrypted with GCS CAS.
    """
    require_enabled()
    t = int(time.time() if now is None else now)
    from .sealed_chat_read import _validate_intent
    if (not isinstance(consent, dict)
            or consent.get("schema") != "plenum-sealed-owner-adaptive-consent-v1"
            or type(consent.get("issued")) is not int
            or type(consent.get("expires")) is not int
            or consent["expires"] <= t
            or consent["issued"] > t + 10
            or not 0 < consent["expires"] - consent["issued"] <= TTL):
        raise PermissionError("Owner adaptive approval missing or expired")
    session_id = _validate_id(consent.get("adaptive_session_id"))
    _validate_intent(site=consent.get("site"), path=consent.get("path"),
                     recipient_public_key=consent.get("recipient_public_key"))
    links = _safe_links(consent["site"], consent["path"], result)
    record = {
        "schema": "plenum-adaptive-read-cursor-v1",
        "session_id": session_id,
        "owner": consent["owner"],
        "site": consent["site"],
        "path": consent["path"],
        "recipient_public_key": consent["recipient_public_key"],
        "issued": consent["issued"],
        "expires": consent["expires"],
        "remaining": MAX_FOLLOWS,
        "links": links,
    }
    _check_scope(record, t)
    blob = _cursor_blob()
    generation = 0
    if blob.exists():
        blob.reload()
        generation = int(blob.generation)
    blob.upload_from_string(
        _cipher().encrypt(json.dumps(record, separators=(",", ":")).encode()),
        content_type="application/octet-stream",
        if_generation_match=generation,
    )
    return {"session_id": session_id, "remaining": MAX_FOLLOWS,
            "links_untrusted": links}


def consume_follow(session_id, link_index, *, now=None):
    """Signed OIDC workflow ONLY: one GCS CAS deletion before visiting link."""
    require_enabled()
    t = int(time.time() if now is None else now)
    _validate_id(session_id)
    if type(link_index) is not int or not 1 <= link_index <= 6:
        raise PermissionError("Invalid browser link number")
    blob = _cursor_blob()
    try:
        blob.reload()
        generation = int(blob.generation)
        sealed = blob.download_as_bytes(if_generation_match=generation)
        state = json.loads(_cipher().decrypt(sealed, ttl=TTL))
        _check_scope(state, t)
        if (state["session_id"] != session_id
                or state["remaining"] < 1
                or link_index > len(state["links"])):
            raise PermissionError("Unapproved browser link or expired scope")
        path = state["links"][link_index - 1]["path"]
        if path == state["path"]:
            raise PermissionError("Repeated private link navigation")
        blob.delete(if_generation_match=generation)
        return {**state, "path": path, "remaining": state["remaining"] - 1}
    except Exception as exc:
        raise PermissionError("Owner-approved browser link unavailable") from exc


def save_follow(cursor, result, *, now=None):
    """Update encrypted cursor after one successful exact private page."""
    require_enabled()
    t = int(time.time() if now is None else now)
    if not isinstance(cursor, dict):
        raise PermissionError("Invalid active browser cursor")
    links = _safe_links(cursor["site"], cursor["path"], result)
    if cursor.get("remaining", 0) < 1:
        return {"remaining": 0, "links_untrusted": links}
    state = {**cursor, "links": links}
    _check_scope(state, t)
    blob = _cursor_blob()
    # Previous generation was atomically consumed BEFORE the website read.
    # Fail closed if another browser workflow or an owner reset created it.
    blob.upload_from_string(
        _cipher().encrypt(json.dumps(state, separators=(",", ":")).encode()),
        content_type="application/octet-stream",
        if_generation_match=0,
    )
    return {"remaining": state["remaining"], "links_untrusted": links}


def revoke_session(*, now=None):
    """Trusted owner-authenticated portal ONLY, never a GitHub issue command."""
    require_enabled()
    blob = _cursor_blob()
    if not blob.exists():
        return False
    blob.reload()
    gen = int(blob.generation)
    blob.delete(if_generation_match=gen)
    return True

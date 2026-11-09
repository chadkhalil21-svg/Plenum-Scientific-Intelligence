"""One owner-consented, one-time, end-to-end encrypted private page read.

The existing signed GitHub workflow carries NO site, path, credential, cookie
or plaintext page data. Only the verified Auth0 owner portal chooses the exact
approved origin, relative read path and ephemeral recipient X25519 public key.
Existing encrypted GCS bucket provides 10-minute atomic consent. Server runs
the already established read-only Playwright session loader; only AES-GCM
ciphertext leaves the owner service. A private key is never accepted here.

No general model-driven browsing, uploading, account changes or site writes.
Feature is deliberately off unless separately enabled on owner Cloud Run.
"""
from __future__ import annotations

import base64
import json
import os
import re
import secrets
import time

from .engine import allowed_origins
from .owner_chat_pairing import _owner, _cipher, _store, require_enabled as require_demo_relay
from .private_profiles import BrowserProfileStore

FLAG = "PLENUM_SEALED_CHAT_READ_ENABLED"
APPROVAL_BLOB = "browser-chat-read/v2/owner-sealed-once.sealed"
TTL = 600
AAD = b"plenum-chat-private-page-v1"
HKDF_INFO = b"plenum-x25519-aes256-gcm-owner-page-v1"
_PUBLIC_KEY = re.compile(r"^[A-Za-z0-9_-]{43}$")


def require_enabled():
    require_demo_relay()
    if os.environ.get(FLAG) != "true":
        raise PermissionError("Private sealed chat read disabled")


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def parse_recipient(value: str):
    """Canonical unpadded X25519 public key, not a private/symmetric key."""
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
    if not isinstance(value, str) or _PUBLIC_KEY.fullmatch(value) is None:
        raise PermissionError("Valid ephemeral recipient public key required")
    try:
        raw = base64.urlsafe_b64decode(value + "=")
        if len(raw) != 32 or _b64(raw) != value:
            raise ValueError("Noncanonical X25519 recipient")
        return X25519PublicKey.from_public_bytes(raw)
    except (ValueError, TypeError) as exc:
        raise PermissionError("Invalid recipient public key") from exc


def _validate_intent(*, site, path, recipient_public_key):
    # Keep scientific CI independent of optional FastAPI/browser dependencies.
    from .owner_saved_session import _approved_read_target
    if not isinstance(site, str) or site not in allowed_origins():
        raise PermissionError("Owner website is not on the existing allowlist")
    _approved_read_target(site, path)
    parse_recipient(recipient_public_key)
    return True


def approve_read(owner_id: str, *, site: str, path: str,
                 recipient_public_key: str, now: int | None = None,
                 additional_paths: str = "", adaptive: bool = False):
    """Trusted owner UI only, after signed CSRF and exact confirmation."""
    require_enabled()
    owner = _owner(owner_id)
    _validate_intent(site=site, path=path,
                     recipient_public_key=recipient_public_key)
    if type(adaptive) is not bool:
        raise PermissionError("Invalid owner adaptive approval")
    from .owner_saved_session import _approved_batch_paths
    extras = _approved_batch_paths(site, path, additional_paths)
    if adaptive:
        if extras:
            raise PermissionError("Adaptive read and explicit batch are exclusive")
        from .owner_adaptive_session import require_enabled as require_adaptive
        require_adaptive()
        # A signed-in adaptive reader may only follow safe exact GET paths.
        _approved_batch_paths(site, "/__plenum_adaptive_start__", [path])
    store = BrowserProfileStore.from_environment()
    if store.status(owner=owner, origin=site).get("profile_exists") is not True:
        raise PermissionError("No saved owner session for approved website")
    t = int(time.time() if now is None else now)
    blob = _store().bucket.blob(APPROVAL_BLOB)
    generation = 0
    if blob.exists():
        blob.reload()
        generation = int(blob.generation)
    record = {
        "schema": "plenum-sealed-owner-consent-v1",
        "owner": owner, "site": site, "path": path,
        "recipient_public_key": recipient_public_key,
        "issued": t, "expires": t + TTL,
        "nonce": secrets.token_hex(16),
    }
    if extras:
        record["schema"] = "plenum-sealed-owner-batch-consent-v1"
        record["additional_paths"] = list(extras)
    if adaptive:
        record["schema"] = "plenum-sealed-owner-adaptive-consent-v1"
        record["adaptive_session_id"] = secrets.token_hex(16)
    blob.upload_from_string(
        _cipher().encrypt(json.dumps(record, separators=(",", ":")).encode()),
        content_type="application/octet-stream",
        if_generation_match=generation,
    )
    return {"approved_once": True, "expires_in_seconds": TTL}


def consume_read(*, now: int | None = None):
    """Call only AFTER signed GitHub OIDC workflow identity verification."""
    require_enabled()
    t = int(time.time() if now is None else now)
    blob = _store().bucket.blob(APPROVAL_BLOB)
    try:
        blob.reload()
        generation = int(blob.generation)
        sealed = blob.download_as_bytes(if_generation_match=generation)
        record = json.loads(_cipher().decrypt(sealed, ttl=TTL))
        if (not isinstance(record, dict)
                or (
                    (record.get("schema") == "plenum-sealed-owner-consent-v1"
                     and set(record) != {"schema", "owner", "site", "path",
                                         "recipient_public_key", "issued", "expires", "nonce"})
                    or
                    (record.get("schema") == "plenum-sealed-owner-batch-consent-v1"
                     and set(record) != {"schema", "owner", "site", "path",
                                         "recipient_public_key", "issued", "expires", "nonce",
                                         "additional_paths"})
                    or
                    (record.get("schema") == "plenum-sealed-owner-adaptive-consent-v1"
                     and set(record) != {"schema", "owner", "site", "path",
                                         "recipient_public_key", "issued", "expires", "nonce",
                                         "adaptive_session_id"})
                    or record.get("schema") not in {
                        "plenum-sealed-owner-consent-v1",
                        "plenum-sealed-owner-batch-consent-v1",
                        "plenum-sealed-owner-adaptive-consent-v1"
                    })
                or not isinstance(record["issued"], int)
                or isinstance(record["issued"], bool)
                or not isinstance(record["expires"], int)
                or isinstance(record["expires"], bool)
                or record["issued"] > t + 10
                or not 0 < record["expires"] - record["issued"] <= TTL
                or record["expires"] <= t
                or not isinstance(record["nonce"], str)
                or re.fullmatch(r"[0-9a-f]{32}", record["nonce"]) is None):
            raise PermissionError("Malformed or expired owner consent")
        _owner(record["owner"])
        _validate_intent(site=record["site"], path=record["path"],
                         recipient_public_key=record["recipient_public_key"])
        from .owner_saved_session import _approved_batch_paths
        if record.get("additional_paths") is not None:
            _approved_batch_paths(record["site"], record["path"],
                                  record["additional_paths"])
        if record.get("schema") == "plenum-sealed-owner-adaptive-consent-v1":
            from .owner_adaptive_session import _validate_id, require_enabled as require_adaptive
            require_adaptive()
            _validate_id(record.get("adaptive_session_id"))
            _approved_batch_paths(record["site"], "/__plenum_adaptive_start__",
                                  [record["path"]])
        # CAS deletion must succeed before any private website session is read.
        blob.delete(if_generation_match=generation)
        return record
    except Exception as exc:
        raise PermissionError("No unconsumed owner-approved private read") from exc


def seal_result(record: dict, result: dict):
    """Use recipient's public key, never publish an unencrypted private result.

    The plaintext is limited to bounded text already extracted by the audited
    read_saved_site() function. Never serialize Playwright storage state,
    cookies, request headers, DOM HTML, form values or arbitrary result fields.
    """
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes

    if (not isinstance(record, dict) or not isinstance(result, dict)
            or result.get("site") != record.get("site")
            or type(result.get("http_status")) is not int
            or not 200 <= result["http_status"] < 300):
        raise PermissionError("Owner private page read was not verified")
    # An HTTP 200 login page at the *same* origin is not the owner's
    # authorized destination. Fail closed for redirects to /login, /home,
    # different query strings, or any route not explicitly owner-approved.
    from .owner_saved_session import _approved_read_target, PUBLIC_DEMO_ORIGIN
    expected_url = _approved_read_target(record.get("site"), record.get("path"))
    if result.get("final_url") != expected_url:
        raise PermissionError("The browser did not read the exact approved page")
    # This published demo has an independent authenticated-login proof.
    # Other approved sites have no universal proof; do not infer one from 200.
    if (record.get("site") == PUBLIC_DEMO_ORIGIN
            and record.get("path") == "/secure"
            and result.get("demo_authenticated_restored") is not True):
        raise PermissionError("Published demo saved login was not restored")
    title = result.get("title")
    body = result.get("body")
    if not isinstance(title, str) or len(title) > 160 or not isinstance(body, str) or len(body) > 1200:
        raise PermissionError("Private page exceeds bounded read result")
    # Only validated navigation hints can enter the encrypted payload.
    # This is link discovery, never permission to follow links without a
    # fresh owner-approved exact path in a new one-shot consent.
    links = result.get("links_untrusted", [])
    if not isinstance(links, list) or len(links) > 6:
        raise PermissionError("Invalid private page link count")
    clean_links = []
    for link in links:
        if not isinstance(link, dict) or set(link) != {"label_untrusted", "path"}:
            raise PermissionError("Malformed private link")
        label, link_path = link["label_untrusted"], link["path"]
        if (not isinstance(label, str) or not 1 <= len(label) <= 75
                or any(ord(ch) < 32 for ch in label)
                or not isinstance(link_path, str) or len(link_path) > 220
                or "?" in link_path or "#" in link_path):
            raise PermissionError("Private link data rejected")
        _approved_read_target(record["site"], link_path)
        clean_links.append({"label_untrusted": label, "path": link_path})
    _validate_intent(site=record.get("site"), path=record.get("path"),
                     recipient_public_key=record.get("recipient_public_key"))
    # Allow multiple owner-specified read-only pages in a single consent,
    # but forbid an executor from adding even one unapproved page.
    from .owner_saved_session import _approved_batch_paths
    extras = _approved_batch_paths(record["site"], record["path"],
                                    record.get("additional_paths", []))
    raw_pages = result.get("additional_pages_untrusted", [])
    if (not isinstance(raw_pages, list) or len(raw_pages) != len(extras)):
        raise PermissionError("Unexpected private batch page count")
    safe_pages = []
    for expected, item in zip(extras, raw_pages):
        if (not isinstance(item, dict)
                or set(item) != {"path", "http_status", "title", "body"}
                or item.get("path") != expected
                or type(item.get("http_status")) is not int
                or not 200 <= item["http_status"] < 300
                or not isinstance(item.get("title"), str)
                or len(item["title"]) > 150
                or not isinstance(item.get("body"), str)
                or len(item["body"]) > 300):
            raise PermissionError("Unapproved or malformed private batch page")
        safe_pages.append(item)
    document = {
        "schema": "plenum-private-page-read-v1",
        "site": record["site"], "path": record["path"],
        "http_status": result["http_status"], "title": title, "body": body,
        "links_untrusted": clean_links,
        "additional_pages_untrusted": safe_pages,
        "model_did_not_execute_website_actions": True,
    }
    if record.get("adaptive_session_id") is not None:
        from .owner_adaptive_session import _validate_id, MAX_FOLLOWS
        _validate_id(record["adaptive_session_id"])
        left = record.get("adaptive_remaining", MAX_FOLLOWS)
        if type(left) is not int or not 0 <= left <= MAX_FOLLOWS:
            raise PermissionError("Invalid adaptive navigation budget")
        document["adaptive_navigation"] = {
            "session_id": record["adaptive_session_id"],
            "remaining_followups": left,
            "read_only": True,
            "requires_new_owner_approval_per_page": False,
        }
    plaintext = json.dumps(document, separators=(",", ":"),
                           ensure_ascii=True).encode("utf-8")
    if len(plaintext) > 4800:
        raise PermissionError("Private result payload exceeds limit")
    eph = X25519PrivateKey.generate()
    shared = eph.exchange(parse_recipient(record["recipient_public_key"]))
    salt, nonce = secrets.token_bytes(16), secrets.token_bytes(12)
    key = HKDF(algorithm=hashes.SHA256(), length=32,
               salt=salt, info=HKDF_INFO).derive(shared)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, AAD)
    eph_pub = eph.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw)
    return {
        "schema": "plenum-sealed-browser-result-v1",
        "encoding": "x25519-hkdf-sha256-aes256gcm",
        "ephemeral_public_key": _b64(eph_pub),
        "salt": _b64(salt),
        "nonce": _b64(nonce),
        "ciphertext": _b64(ciphertext),
        "plaintext_in_github": False,
    }

"""Owner-issued, action-bound, single-use approvals for future private browser writes.

SOURCE FOUNDATION ONLY: Not connected to ChatGPT, MCP, website sessions or live
Cloud Run. The approval issuer MUST be called only after a verified owner has
reviewed the exact origin and complete action plan in a trusted private UI.
The model, browser page and public GitHub events must never receive the key.

Only the exact plan digest, not its content, is embedded in the signed grant.
Production replay prevention requires an atomic persistent store, not RAM.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import ipaddress
import json
import re
import secrets
import time
from urllib.parse import urlsplit

MAX_TTL_SECONDS = 600
MAX_PLAN_BYTES = 16384
MAX_TOKEN_BYTES = 2048
_HOST = re.compile(r"^(?=.{4,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z][a-z0-9-]{1,62}$")
_ALLOWED_ACTIONS = frozenset({"fill", "select", "click", "submit", "upload", "download", "navigate", "delete"})


class ApprovalRejected(PermissionError):
    """Invalid, expired, mismatched or previously consumed owner approval."""


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode(value: str) -> bytes:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise ApprovalRejected("Invalid approval encoding")
    try:
        decoded=base64.b64decode(value + ("=" * (-len(value) % 4)), altchars=b"-_", validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ApprovalRejected("Invalid approval encoding") from exc
    # Noncanonical base64url strings can have distinct trailing characters
    # decoding to exactly the same HMAC bytes. Reject those textual mutations.
    if _b64(decoded)!=value:
        raise ApprovalRejected("Noncanonical approval encoding")
    return decoded


def _origin(value: str) -> str:
    if (not isinstance(value, str) or len(value) > 253
            or any(ord(ch) < 33 or ord(ch) == 127 for ch in value)):
        raise ApprovalRejected("Invalid website origin")
    try:
        p = urlsplit(value)
        host = p.hostname or ""
        port = p.port
    except ValueError as exc:
        raise ApprovalRejected("Invalid website origin") from exc
    if (p.scheme != "https" or not _HOST.fullmatch(host)
            or port not in (None, 443) or p.path not in ("", "/")
            or p.username or p.password or p.query or p.fragment):
        raise ApprovalRejected("Website origin must be exact approved HTTPS host")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ApprovalRejected("IP literals cannot be approved here")
    if host.endswith((".local", ".internal", ".localhost", ".test", ".invalid", ".onion")):
        raise ApprovalRejected("Local/private host cannot be approved")
    return "https://" + host


def _plan_bytes(plan: dict, origin: str) -> bytes:
    if not isinstance(plan, dict) or set(plan) != {"origin", "operations"}:
        raise ApprovalRejected("Unexpected action plan format")
    if _origin(plan["origin"]) != origin:
        raise ApprovalRejected("Plan origin mismatch")
    operations = plan["operations"]
    if not isinstance(operations, list) or not 1 <= len(operations) <= 16:
        raise ApprovalRejected("Action plan size invalid")
    if any(not isinstance(op, dict) or op.get("op") not in _ALLOWED_ACTIONS
           for op in operations):
        raise ApprovalRejected("Unrecognized action type")
    try:
        encoded = json.dumps(
            plan, sort_keys=True, ensure_ascii=True, allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ApprovalRejected("Unserializable action plan") from exc
    if len(encoded) > MAX_PLAN_BYTES:
        raise ApprovalRejected("Action plan too large")
    return encoded


class OwnerApprovalGate:
    """HMAC-signed grant bound to a single owner, HTTPS origin and exact plan.

    `issue` is owner-UI ONLY, never an accessible model or page tool.
    `consume` delegates replay exclusion to a trusted atomic persistent store.
    This module performs no browser actions and cannot grant access by itself.
    """

    def __init__(self, *, key: bytes, nonce_store):
        if not isinstance(key, bytes) or len(key) < 32:
            raise ValueError("Approval HMAC key must be at least 256 bits")
        if nonce_store is None or not callable(getattr(nonce_store, "claim", None)):
            raise ValueError("Atomic one-time approval store required")
        self._key = key
        self._nonce_store = nonce_store

    def _owner_hash(self, owner_id: str) -> str:
        if not isinstance(owner_id, str) or not 3 <= len(owner_id) <= 256:
            raise ApprovalRejected("Verified owner identity required")
        return _b64(hmac.digest(self._key, ("owner:" + owner_id).encode(), "sha256"))

    def issue(self, *, verified_owner_id: str, plan: dict,
              ttl_seconds: int = 120, now: int | None = None) -> str:
        """Only trusted private UI may issue after explicit exact-plan consent."""
        if (not isinstance(ttl_seconds, int) or isinstance(ttl_seconds, bool)
                or not 1 <= ttl_seconds <= MAX_TTL_SECONDS):
            raise ApprovalRejected("Invalid approval lifetime")
        timestamp = int(time.time()) if now is None else now
        if not isinstance(timestamp, int) or isinstance(timestamp, bool) or timestamp < 1:
            raise ApprovalRejected("Invalid issued time")
        origin = _origin(plan["origin"]) if isinstance(plan, dict) and "origin" in plan else ""
        digest = hashlib.sha256(_plan_bytes(plan, origin)).hexdigest()
        payload = {
            "v": 1, "owner": self._owner_hash(verified_owner_id),
            "origin": origin, "plan_sha256": digest,
            "iat": timestamp, "exp": timestamp + ttl_seconds,
            "nonce": secrets.token_hex(16),
        }
        body = _b64(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())
        signature = _b64(hmac.digest(self._key, ("plenum-owner-approval-v1:" + body).encode(), "sha256"))
        return "v1." + body + "." + signature

    def consume(self, *, token: str, verified_owner_id: str,
                plan: dict, now: int | None = None) -> bool:
        """Return True exactly once; reject every unauthorized/replayed attempt."""
        if not isinstance(token, str) or len(token) > MAX_TOKEN_BYTES:
            raise ApprovalRejected("Invalid owner approval")
        parts = token.split(".")
        if len(parts) != 3 or parts[0] != "v1":
            raise ApprovalRejected("Invalid owner approval")
        body, signature = parts[1], parts[2]
        expected = hmac.digest(
            self._key, ("plenum-owner-approval-v1:" + body).encode(), "sha256")
        if not hmac.compare_digest(_decode(signature), expected):
            raise ApprovalRejected("Invalid owner approval signature")
        try:
            payload = json.loads(_decode(body))
        except (UnicodeDecodeError, ValueError) as exc:
            raise ApprovalRejected("Invalid owner approval payload") from exc
        if not isinstance(payload, dict) or set(payload) != {
            "v", "owner", "origin", "plan_sha256", "iat", "exp", "nonce"
        } or payload.get("v") != 1:
            raise ApprovalRejected("Unrecognized owner approval payload")
        timestamp = int(time.time()) if now is None else now
        iat, exp = payload["iat"], payload["exp"]
        if (not isinstance(timestamp, int) or isinstance(timestamp, bool)
                or not isinstance(iat, int) or isinstance(iat, bool)
                or not isinstance(exp, int) or isinstance(exp, bool)
                or exp <= timestamp or iat > timestamp + 5
                or not 0 < exp - iat <= MAX_TTL_SECONDS):
            raise ApprovalRejected("Owner approval expired or invalid")
        origin = _origin(plan["origin"]) if isinstance(plan, dict) and "origin" in plan else ""
        plan_digest = hashlib.sha256(_plan_bytes(plan, origin)).hexdigest()
        if (payload["owner"] != self._owner_hash(verified_owner_id)
                or payload["origin"] != origin
                or payload["plan_sha256"] != plan_digest
                or not isinstance(payload["nonce"], str)
                or not re.fullmatch(r"[a-f0-9]{32}", payload["nonce"])):
            raise ApprovalRejected("Owner approval does not match action plan")
        # The store must perform an atomic CREATE-IF-ABSENT. A failed/ambiguous
        # claim is treated as a rejection; no browser action can proceed.
        if self._nonce_store.claim(
                owner_hash=payload["owner"], nonce=payload["nonce"], expiry=exp) is not True:
            raise ApprovalRejected("Owner approval already consumed or unavailable")
        return True


class GCSAtomicNonceStore:
    """One-time marker using GCS create-only precondition (future private runtime).

    Pass an already-authorized PRIVATE bucket object. Configure bucket lifecycle
    deletion separately; do not reuse public research storage or GitHub artifacts.
    """

    def __init__(self, private_bucket):
        if private_bucket is None:
            raise ValueError("Private approval bucket required")
        self._bucket = private_bucket

    def claim(self, *, owner_hash: str, nonce: str, expiry: int) -> bool:
        from google.api_core.exceptions import PreconditionFailed
        name = "browser-approvals/v1/" + hashlib.sha256(
            (owner_hash + ":" + nonce).encode("ascii")).hexdigest()
        blob = self._bucket.blob(name)
        try:
            blob.upload_from_string(
                str(expiry), content_type="text/plain",
                if_generation_match=0,
            )
        except PreconditionFailed:
            return False
        # All other storage failures propagate and prevent execution.
        return True

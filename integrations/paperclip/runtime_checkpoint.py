"""Optional scoped Cloudflare checkpoint metadata client for owner runtime only.

No owner-private memory credential. No public CI network access. A lost volume
with a completed remote digest is blocked: the digest is not the artifact.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
import re
import uuid
from urllib.error import HTTPError
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler

ENDPOINT = "https://plenum-public-wake.chadkhalil21.workers.dev"
DIGEST = re.compile(r"[0-9a-f]{64}")
MAX_RESPONSE = 4096


def response_json(stream):
    raw = stream.read(MAX_RESPONSE + 1)
    if len(raw) > MAX_RESPONSE:
        raise ValueError("Checkpoint response exceeds bound")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate checkpoint response key")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("Nonfinite checkpoint response number")
    return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class CheckpointRejected(RuntimeError):
    def __init__(self,status,code=None):
        self.status=status
        self.code=code
        super().__init__("Checkpoint HTTP rejected: "+str(status))


class RuntimeCheckpoint:
    def __init__(self, company, mission, role, issue, *, sender=None, secret=None, scope=None):
        if os.getenv("GITHUB_ACTIONS") == "true":
            raise PermissionError("Public CI cannot access runtime checkpoint capability")
        self.secret = os.getenv("PLENUM_PAPERCLIP_CHECKPOINT_HMAC_SECRET", "") if secret is None else secret
        scope = os.getenv("PLENUM_PAPERCLIP_CHECKPOINT_SCOPE", "") if scope is None else scope
        for value in (company, mission, issue):
            if str(uuid.UUID(value)) != value:
                raise ValueError("Invalid native task identity")
        if scope != company + "/" + mission or len(self.secret) < 32:
            raise PermissionError("Missing exact runtime checkpoint grant")
        if role not in ("intelligence", "research", "engineering", "commercial", "verification"):
            raise PermissionError("Unknown checkpoint role")
        self.path = "/paperclip-checkpoints/" + scope + "/" + role
        self.issue = issue
        self.sender = sender or build_opener(ProxyHandler({}), NoRedirect).open

    def request(self, method, body=None):
        if (method == "GET" and body is not None) or (method == "POST" and not isinstance(body, dict)) or method not in ("GET", "POST"):
            raise ValueError("Invalid checkpoint request")
        raw = "" if body is None else json.dumps(body, separators=(",", ":"), sort_keys=True)
        stamp = str(int(datetime.now(timezone.utc).timestamp() * 1000))
        sig = hmac.new(self.secret.encode(), "\n".join((method, self.path, stamp, raw)).encode(),
                       hashlib.sha256).hexdigest()
        req = Request(ENDPOINT + self.path, method=method,
                      data=raw.encode() if body is not None else None,
                      headers={"x-plenum-memory-time": stamp, "x-plenum-memory-signature": "sha256="+sig,
                               "Content-Type": "application/json"})
        try:
            with self.sender(req, timeout=8) as response:
                if response.status != 200:
                    raise ValueError("Unexpected checkpoint HTTP status")
                data = response_json(response)
        except HTTPError as exc:
            if method == "GET" and exc.code == 404:
                # Only the actual scoped storage endpoint returns not_found.
                # A generic old Worker route 404 cannot authorize activation.
                try: missing=response_json(exc)
                except (ValueError, OSError): missing=None
                if missing=={"error":"not_found"}:return None
                raise RuntimeError("Checkpoint route not verified") from None
            try:
                error=response_json(exc)
                code=error.get("error") if isinstance(error,dict) else None
            except (ValueError,OSError):code=None
            raise CheckpointRejected(exc.code,code) from None
        except Exception as exc:
            raise RuntimeError("Checkpoint transport unverified: " + type(exc).__name__) from None
        if (not isinstance(data, dict) or set(data) != {"issue", "state", "attempt", "revision", "sha256"}
                or data["issue"] != self.issue or data["state"] not in ("reserved", "completed")
                or type(data["attempt"]) is not int or data["attempt"] not in (1, 2)
                or type(data["revision"]) is not int):
            raise ValueError("Unexpected runtime checkpoint response")
        completed = data["state"] == "completed"
        if (data["revision"] != data["attempt"] + int(completed)
                or (completed and (not isinstance(data["sha256"], str) or not DIGEST.fullmatch(data["sha256"])))
                or (not completed and data["sha256"] is not None)):
            raise ValueError("Invalid checkpoint state, revision or digest")
        if method == "POST":
            expected = {"issue": self.issue, "state": body["state"], "attempt": body["attempt"],
                        "sha256": body["sha256"], "revision": body["expected_revision"] + 1}
            if data != expected:
                raise ValueError("Checkpoint write acknowledgment disagrees with requested transition")
        return data

    def reserve(self, number):
        if type(number) is not int or number not in (1, 2):
            raise ValueError("Invalid checkpoint attempt")
        prior = self.request("GET")
        if number == 1 and prior is None:
            revision = 0
        elif number == 2 and prior and prior["state"] == "reserved" and prior["attempt"] == 1:
            revision = prior["revision"]
        else:
            raise RuntimeError("Remote checkpoint conflicts with local evidence; do not replay")
        self.request("POST", {"issue": self.issue, "state": "reserved", "attempt": number,
                             "sha256": None, "expected_revision": revision})

    def complete(self, digest):
        if not isinstance(digest, str) or not DIGEST.fullmatch(digest):
            raise ValueError("Invalid completion digest")
        prior = self.request("GET")
        if not prior:
            raise RuntimeError("Missing remote reservation")
        if prior["state"] == "completed":
            if prior["sha256"] != digest:
                raise ValueError("Remote completed digest disagrees")
            return
        self.request("POST", {"issue": self.issue, "state": "completed", "attempt": prior["attempt"],
                             "sha256": digest, "expected_revision": prior["revision"]})


def configured(company, mission, role, issue):
    if not (os.getenv("PLENUM_PAPERCLIP_CHECKPOINT_SCOPE") or os.getenv("PLENUM_PAPERCLIP_CHECKPOINT_HMAC_SECRET")):
        return None
    return RuntimeCheckpoint(company, mission, role, issue)

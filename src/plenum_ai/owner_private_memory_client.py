"""Minimal private owner client for existing Cloudflare Durable Object memory.

No third-party API or LLM. Never run with founder data on public GitHub CI.
The canonical Google Drive ledger still requires separate authenticated readback.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from hmac import new
import json
import os
import re
from urllib.request import Request, urlopen

ENDPOINT = "https://plenum-public-wake.chadkhalil21.workers.dev"
KEY = re.compile(r"^[a-z0-9][a-z0-9:_-]{0,79}$")
LEVELS = {"VERIFIED", "FOUNDER_REPORTED", "PENDING", "OPEN", "BLOCKED"}


class PrivateMemoryUnavailable(RuntimeError):
    """No live owner-authorized memory capability; never claim stored."""


class PrivateMemoryClient:
    """Use only with an owner-controlled secret kept outside ChatGPT and GitHub."""

    def __init__(self, secret: str | None = None, *, sender=urlopen):
        if os.environ.get("GITHUB_ACTIONS") == "true":
            raise PrivateMemoryUnavailable("Public GitHub Actions cannot access founder memory")
        self.secret = secret if secret is not None else os.getenv("PLENUM_PRIVATE_MEMORY_HMAC_SECRET", "")
        if len(self.secret) < 32:
            raise PrivateMemoryUnavailable("Owner-private memory secret unavailable")
        self.sender = sender

    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        if not (path == "/memory" or
                (path.startswith("/memory/") and KEY.fullmatch(path[8:]))):
            raise ValueError("Invalid memory path")
        raw = "" if body is None else json.dumps(body, separators=(",", ":"), sort_keys=True)
        if len(raw.encode("utf-8")) > 2900:
            raise ValueError("Memory record too large")
        stamp = str(int(datetime.now(timezone.utc).timestamp() * 1000))
        signed = "\n".join([method, path, stamp, raw]).encode("utf-8")
        signature = new(self.secret.encode("utf-8"), signed, sha256).hexdigest()
        request = Request(
            ENDPOINT + path,
            data=raw.encode("utf-8") if method == "POST" else None,
            headers={
                "x-plenum-memory-time": stamp,
                "x-plenum-memory-signature": "sha256=" + signature,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method=method,
        )
        try:
            with self.sender(request, timeout=8) as response:
                return json.loads(response.read(4096))
        except Exception as exc:
            # Never include a failed signed URL, token or personal content in logs.
            raise PrivateMemoryUnavailable(
                f"Private continuity read/write unverified: {type(exc).__name__}"
            ) from None

    def get(self, key: str) -> dict:
        if not KEY.fullmatch(key):
            raise ValueError("Invalid memory key")
        return self._request("GET", "/memory/" + key)

    def put(self, *, key: str, summary: str, source: str, observed_at: str,
            level: str, expected_revision: int) -> dict:
        if not KEY.fullmatch(key) or level not in LEVELS or not isinstance(expected_revision,int):
            raise ValueError("Invalid memory record")
        record = {
            "key":key,"summary":summary,"source":source,
            "observed_at":observed_at,"level":level,
            "expected_revision":expected_revision,
        }
        return self._request("POST", "/memory",record)

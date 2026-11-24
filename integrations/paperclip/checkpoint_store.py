"""Task-bound, atomic local-volume checkpoint; two attempts, no blind replay."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
from urllib.error import URLError, HTTPError

MAX_BYTES = 2_000_000


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def exclusive(path, value):
    """Atomically publish complete bytes without overwriting previous evidence."""
    data = encoded(value)
    if len(data) > MAX_BYTES:
        raise ValueError("Checkpoint too large")
    fd, name = tempfile.mkstemp(prefix=".checkpoint-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(name, path)
        dfd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    finally:
        os.unlink(name)


def checked(path, expected):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError("Invalid checkpoint file")
    value = json.loads(path.read_bytes())
    if any(value.get(k) != v for k, v in expected.items()):
        raise ValueError("Checkpoint identity mismatch")
    return value


def transient(exc):
    if isinstance(exc, HTTPError):
        return exc.code in (500, 502, 503, 504)
    return isinstance(exc, (TimeoutError, ConnectionError, URLError))


def execute_once(directory, company, role, issue, produce, *, remote=None):
    """Called only after Paperclip's exclusive checkout; never retry a 409.
    
    A crashed attempt consumes its reservation. A second failure is terminal.
    An ambiguous/non-transient failure is terminal even on the first attempt.
    """
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("Unsafe checkpoint directory")
    identity = {"company": company, "role": role, "issue": issue}
    target = directory / (role + ".json")
    if target.exists() or target.is_symlink():
        receipt = checked(target, identity)
        if receipt["sha256"] != hashlib.sha256(encoded(receipt["result"])).hexdigest():
            raise ValueError("Receipt digest mismatch")
        return receipt
    for number in (1, 2):
        marker = directory / (role + ".attempt-" + str(number))
        failure = directory / (role + ".failure-" + str(number))
        expected = dict(identity, attempt=number)
        if marker.exists() or marker.is_symlink():
            checked(marker, expected)
            if failure.exists() or failure.is_symlink():
                status = checked(failure, expected)
                if status.get("retryable") is not True:
                    raise RuntimeError("Terminal specialist failure")
            continue
        if remote is not None:
            remote.reserve(number)
        exclusive(marker, expected)
        try:
            result = produce()
            receipt = dict(identity, result=result, sha256=hashlib.sha256(encoded(result)).hexdigest())
            exclusive(target, receipt)
            return receipt
        except Exception as exc:
            allowed = transient(exc) and number == 1
            exclusive(failure, dict(expected, retryable=allowed, error_type=type(exc).__name__))
            if not allowed:
                raise RuntimeError("Terminal specialist failure") from exc
    raise RuntimeError("Bounded specialist attempt budget exhausted")

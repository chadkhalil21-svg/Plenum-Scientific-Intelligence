"""Produce bounded IAP service-account JWT claims for an owner-approved HEALTH probe.

This module contains no signing keys, IAM credentials or network operations.
The trusted GitHub Actions runner signs claims with Google IAMCredentials.
The audience is *only* /healthz; it cannot authorize browser work or writes.
"""
import argparse
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urlsplit

SERVICE = "plenum-computer-browser"
SA_RE = re.compile(r"^[a-z][a-z0-9-]{1,60}@[a-z][a-z0-9-]{2,60}\\.iam\\.gserviceaccount\\.com$")


def health_url(cloud_run_url):
    if not isinstance(cloud_run_url, str) or len(cloud_run_url) > 250:
        raise ValueError("Invalid service URL")
    try:
        parts = urlsplit(cloud_run_url)
        port = parts.port
    except ValueError as exc:
        raise ValueError("Invalid service URL") from exc
    host = parts.hostname or ""
    if (parts.scheme != "https" or port not in (None, 443)
            or not host.startswith(SERVICE + "-")
            or not host.endswith(".run.app")
            or not re.fullmatch(r"[a-z0-9.-]+", host)
            or parts.username or parts.password or parts.path not in ("", "/")
            or parts.query or parts.fragment):
        raise ValueError("Only this private Cloud Run service is permitted")
    return "https://" + host + "/healthz"


def claims(service_account, cloud_run_url, *, now=None):
    """Five-minute URL-scoped service JWT claim; no wildcard audience."""
    if not isinstance(service_account, str) or not SA_RE.fullmatch(service_account):
        raise ValueError("Invalid signer service account")
    stamp = int(time.time() if now is None else now)
    if stamp < 0:
        raise ValueError("Invalid timestamp")
    return {
        "iss": service_account,
        "sub": service_account,
        "aud": health_url(cloud_run_url),
        "iat": stamp,
        "exp": stamp + 300,
    }


def verify_health_response(value):
    """Reject a login redirect, HTML, a mock failure or unexpected response."""
    if not isinstance(value, dict):
        return False
    return (value.get("service") == SERVICE
            and value.get("ready") is True
            and value.get("remote_mutations_enabled") is False)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--cloud-run-url")
    parser.add_argument("--service-account")
    parser.add_argument("--claims-file")
    parser.add_argument("--health-response")
    args = parser.parse_args(argv)
    if args.health_response:
        data = json.loads(Path(args.health_response).read_text(encoding="utf-8"))
        if not verify_health_response(data):
            raise SystemExit("BLOCKED: Cloud Run private health response was invalid")
        print("PASS: IAP-protected private Cloud Run health response verified.")
        return
    if not args.cloud_run_url or not args.service_account or not args.claims_file:
        raise SystemExit("Cloud Run URL, service account and scratch output are required")
    output = Path(args.claims_file)
    if not output.is_absolute() or output.exists():
        raise SystemExit("Use an unused absolute temporary claims path")
    payload = json.dumps(claims(args.service_account, args.cloud_run_url), separators=(",", ":"))
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(payload)
    print("Prepared bounded five-minute IAP health claim, without credentials.")


if __name__ == "__main__":
    main()

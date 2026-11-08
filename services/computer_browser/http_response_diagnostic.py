"""Redacted comparison of signed/unsigned GET /healthz responses.

This only classifies local HTTP responses captured by a trusted read-only probe.
Never print response bodies, headers, cookies, tokens, IDs, or raw URLs.
"""
import argparse
import json
from pathlib import Path

def classify(data):
    """Return only a fixed category; no untrusted text in output."""
    if not isinstance(data, bytes):
        raise TypeError("Expected response bytes")
    body = data[:65536].lower()
    if b'"detail":"not found"' in body or b'"detail": "not found"' in body:
        return "fastapi_route_not_found"
    if b"identity-aware proxy" in body or b"iap error" in body:
        return "iap_error_page"
    if b"404. that" in body or (b"google" in body and b"requested url was not found" in body):
        return "google_frontend_not_found"
    if b"not found" in body:
        return "generic_not_found"
    if body.lstrip().startswith(b"{"):
        return "other_json"
    if b"<html" in body or b"<!doctype html" in body:
        return "other_html"
    return "unclassified"

def content_kind(raw):
    if not isinstance(raw, bytes):
        raise TypeError("Expected header bytes")
    # Only inspect the final content-type header; never echo its value.
    values = [l.partition(b":")[2].strip().lower() for l in raw.splitlines()
              if l.lower().startswith(b"content-type:")]
    value = values[-1] if values else b""
    if b"application/json" in value:
        return "json"
    if b"text/html" in value:
        return "html"
    return "unknown"

def describe(signed_status, signed_body, unsigned_status, unsigned_body, signed_headers):
    for s in (signed_status, unsigned_status):
        if not isinstance(s, int) or s < 0 or s > 599:
            raise ValueError("Invalid HTTP status")
    return {
        "schema": "plenum-browser-http-differential-v1",
        "signed_status": signed_status,
        "unsigned_status": unsigned_status,
        "signed_body_class": classify(signed_body),
        "unsigned_body_class": classify(unsigned_body),
        "signed_content_type_class": content_kind(signed_headers),
        "bodies_identical": signed_body == unsigned_body,
        "request_scope": "GET /healthz only",
        "root_cause": "not_established_from_response_comparison",
        "raw_body_or_credentials_logged": False,
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--signed-status", type=int, required=True)
    p.add_argument("--unsigned-status", type=int, required=True)
    p.add_argument("--signed-response", required=True)
    p.add_argument("--unsigned-response", required=True)
    p.add_argument("--signed-headers", required=True)
    a = p.parse_args()
    def bounded_read(path):
        obj = Path(path)
        if not obj.is_file() or obj.stat().st_size > 131072:
            raise ValueError("Missing or oversized HTTP diagnostic file")
        return obj.read_bytes()
    result = describe(a.signed_status, bounded_read(a.signed_response),
                      a.unsigned_status, bounded_read(a.unsigned_response),
                      bounded_read(a.signed_headers))
    print(json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Inspect only the public IAP -> Google OAuth redirect, no credentials or IAM.

This is a *diagnostic*, not an authentication bypass. It only makes unauthenticated
GET requests to the owner's exact Cloud Run URL and exact Google IAP hosts.
OAuth redirect URLs may contain state and personal identifiers; NEVER log them.
Only nonsecret boolean comparisons are returned.
"""
from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request

OWNER_URL = "https://plenum-computer-browser-98614162800.us-east1.run.app/owner"
# SHA256 of the public Google OAuth client ID that the founder already registered.
# Hash is used to avoid copying the complete ID into GitHub output or logs.
EXPECTED_CLIENT_DIGEST = "639dd427647b7f9b609f2b08529e0aca7356e86653fda49b1c69ceac151e8a20"
GOOGLE_OAUTH_HOSTS = frozenset({"accounts.google.com"})
IAP_REDIRECT_HOSTS = frozenset({"iap.googleapis.com"})
MAX_HOPS = 4


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _safe_host(url):
    p = urllib.parse.urlsplit(url)
    if (p.scheme != "https" or p.port not in (None, 443)
            or not p.hostname or p.username or p.password):
        return ""
    return p.hostname


def _query_params(url):
    parsed = urllib.parse.urlsplit(url)
    params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    return {k: v[0] for k, v in params.items() if len(v) == 1}


def classify_oauth_url(url):
    """No values returned: only booleans and invariant path checks."""
    if _safe_host(url) not in GOOGLE_OAUTH_HOSTS:
        return {"status": "not_google_oauth"}
    parsed = urllib.parse.urlsplit(url)
    q = _query_params(url)
    client_id = q.get("client_id", "")
    redirect = q.get("redirect_uri", "")
    expected = (
        bool(client_id)
        and hashlib.sha256(client_id.encode("utf-8")).hexdigest()
        == EXPECTED_CLIENT_DIGEST
    )
    expected_redirect = (
        "https://iap.googleapis.com/v1/oauth/clientIds/"
        + client_id + ":handleRedirect"
    )
    return {
        "status": "google_oauth_redirect_observed",
        "recognized_google_oauth_path": parsed.path in {
            "/o/oauth2/v2/auth", "/o/oauth2/auth", "/signin/oauth"
        },
        "client_id_present": bool(client_id),
        "attached_client_matches_founder_registered_client": expected,
        "redirect_uri_present": bool(redirect),
        "callback_matches_same_client_iap_redirect": redirect == expected_redirect,
        "response_type_is_code": q.get("response_type") == "code",
        "state_parameter_present": bool(q.get("state")),
        "scope_parameter_present": bool(q.get("scope")),
        "no_http_400_directly_in_this_hop": True,
    }


def inspect_live():
    opener = urllib.request.build_opener(_NoRedirect)
    current = OWNER_URL
    for hop in range(MAX_HOPS):
        host = _safe_host(current)
        if host in GOOGLE_OAUTH_HOSTS:
            return {"hop": hop, **classify_oauth_url(current)}
        if current != OWNER_URL and host not in IAP_REDIRECT_HOSTS:
            return {"status": "non_iap_intermediate_redirect", "hop": hop}
        request = urllib.request.Request(current, method="GET",
            headers={"User-Agent": "Plenum-IAP-Nonsecret-Redirect-Audit/1",
                     "Cache-Control": "no-store"})
        try:
            response = opener.open(request, timeout=15)
            with response:
                status = response.status
                location = response.headers.get("Location")
        except urllib.error.HTTPError as exc:
            status = exc.code
            location = exc.headers.get("Location")
        except (OSError, ValueError) as exc:
            # Do not print exception strings; they may contain an OAuth URL.
            return {"status": "network_unavailable",
                    "error_category": type(exc).__name__, "hop": hop}
        if status not in (301, 302, 303, 307, 308) or not location:
            return {
                "status": "no_oauth_redirect",
                "http_status": status, "hop": hop
            }
        nxt = urllib.parse.urljoin(current, location)
        if _safe_host(nxt) not in GOOGLE_OAUTH_HOSTS | IAP_REDIRECT_HOSTS:
            return {"status": "unexpected_redirect_destination", "hop": hop}
        current = nxt
    return {"status": "oauth_redirect_not_seen_within_hop_limit"}


if __name__ == "__main__":
    # Never log URLs, secrets, OAuth state, cookie jars or response bodies.
    print(json.dumps(inspect_live(), sort_keys=True))

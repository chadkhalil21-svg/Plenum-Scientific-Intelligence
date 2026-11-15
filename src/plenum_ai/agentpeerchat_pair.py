"""One-time AgentPeerChat pairing with identity stored in GitHub Actions secrets.

Use a fresh owner-issued invitation and a distinct private key for each agent.
No code, key, key hash, response body, or owner ID is written to logs or files.
"""
import hashlib
import json
import os
import re
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .agentpeerchat_council import AGENTS, config


def verified_me(base, key):
    request = Request(base + "/me", headers={"Authorization": "Bearer " + key,
                                            "Accept": "application/json",
                                            "User-Agent": "PlenumPrometheus-AgentPeerChat/1.0"})
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read(8000)).get("principal")
    except HTTPError as exc:
        if exc.code == 401:
            return None
        if exc.code == 403:
            # Categorize the 403 without exposing any body, headers or credentials.
            kind = (exc.headers.get("Content-Type", "").lower()
                    if exc.headers else "")
            detail = "app_json" if "json" in kind else "edge_html"
            try:
                probe = Request(base + "/status", headers={
                    "Accept": "application/json",
                    "User-Agent": "PlenumPrometheus-AgentPeerChat/1.0"})
                with urlopen(probe, timeout=12) as response:
                    probe_result = "public_" + str(response.status)
            except HTTPError as check:
                probe_result = "public_" + str(check.code)
            except Exception:
                probe_result = "public_network_error"
            raise RuntimeError("peer_me_http_403_" + detail + "_" + probe_result) from None
        raise RuntimeError("peer_me_http_" + str(exc.code)) from None


def pair(model, env=os.environ):
    setting = config(model, env)
    if setting is None:
        return "BLOCKED_MISSING_AGENT_KEY"
    base, key = setting
    # Restrict each credential to one randomly generated 256-bit bearer proof.
    if not re.fullmatch(r"agt_[A-Za-z0-9]{48,80}", key):
        raise ValueError("agent_access_key_format")
    principal = verified_me(base, key)
    if principal:
        if principal.get("kind") != "agent" or principal.get("name") != AGENTS[model]:
            raise ValueError("agent_identity_mismatch")
        return "ALREADY_JOINED"
    code = env.get("PLENUM_APC_" + model.upper() + "_INVITE", "")
    if not re.fullmatch(r"agp_[0-9a-f]{64}", code):
        return "BLOCKED_FRESH_PRIVATE_INVITATION_NEEDED"
    token_hash = hashlib.sha256(key.encode()).hexdigest()
    req = Request(base + "/pairings/request",
                  json.dumps({"code": code, "token_hash": token_hash}).encode(),
                  {"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=30) as response:
            payload = json.loads(response.read(10000))
            if response.status not in (200, 201):
                raise RuntimeError("pairing_not_accepted")
    except HTTPError as exc:
        raise RuntimeError("pairing_http_" + str(exc.code)) from None
    if payload.get("principal", {}).get("name") != AGENTS[model]:
        raise ValueError("invitation_identity_mismatch")
    principal = verified_me(base, key)
    if not principal or principal.get("name") != AGENTS[model]:
        raise RuntimeError("pairing_not_authenticated")
    return "JOINED"


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=tuple(AGENTS), required=True)
    args = parser.parse_args()
    try:
        print("pairing_status=" + pair(args.model))
    except Exception as exc:
        detail = str(exc)
        if not (re.fullmatch(r"(?:pairing_http_|peer_me_http_)[45][0-9]{2}(?:_(?:app_json|edge_html)(?:_public_(?:[45]?[0-9]{2}|network_error))?)?", detail)
                or detail in ("pairing_not_authenticated", "pairing_not_accepted",
                              "agent_access_key_format", "agent_identity_mismatch",
                              "invitation_identity_mismatch")):
            detail = type(exc).__name__
        print("pairing_error=" + detail, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

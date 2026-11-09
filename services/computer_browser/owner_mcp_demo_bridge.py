"""Strict owner-identity adapter for a FUTURE authenticated MCP read-only tool.

Source-only until a separately verified OAuth 2.1 ChatGPT connector exists.
No public endpoint, no GitHub issue task execution, and no account mutations.
The exact public demonstration origin is the only supported site.
"""
import asyncio
import hashlib
import os
import re

DEMO_ORIGIN="https://the-internet.herokuapp.com"
OWNER_SERVICE="plenum-browser-owner-auth0"
FEATURE_FLAG="PLENUM_MCP_PRIVATE_DEMO_READ_ENABLED"


def derive_vault_owner_id(config):
    """Bind a verified OAuth sub to the same opaque ID as the Auth0 owner portal.

    This function MUST only be reached after OwnerJWTVerifier verified a
    signature, issuer, audience, scope, client, owner-sub and short expiry.
    """
    from .owner_auth0 import ISSUER
    config.validate()
    if (config.issuer != ISSUER
            or not isinstance(config.owner_sub,str)
            or not 8 <= len(config.owner_sub) <= 240):
        raise PermissionError("MCP identity cannot be mapped to owner vault")
    return hashlib.sha256((config.issuer+config.owner_sub).encode()).hexdigest()


def _check_provisioned(config):
    if (os.environ.get("K_SERVICE")!=OWNER_SERVICE
            or os.environ.get(FEATURE_FLAG)!="true"
            or os.environ.get("BROWSER_ALLOWED_ORIGINS","").split(",").count(DEMO_ORIGIN)!=1
            or not os.environ.get("BROWSER_PROFILE_BUCKET")
            or not os.environ.get("BROWSER_SESSION_KEY")
            or len(os.environ.get("COMPUTER_BROWSER_TOKEN",""))<32
            or os.environ.get("AUTH0_OWNER_PUBLIC_ORIGIN")
               != "https://plenum-browser-owner-auth0-2lak3vl73q-ue.a.run.app"):
        raise PermissionError("Owner-bound MCP saved-session bridge is disabled")
    return derive_vault_owner_id(config)


async def verified_saved_demo_status(config):
    """Return only protected demo success/failure, never confidential page data.

    The caller MUST have already checked an authenticated short-lived bearer
    token with the browser:read scope. No model-supplied URL/owner ID.
    """
    owner_id=_check_provisioned(config)
    from .owner_saved_session import read_saved_site
    try:
        result=await asyncio.wait_for(
            read_saved_site(site=DEMO_ORIGIN,owner=owner_id),
            timeout=38,
        )
    except Exception:
        # Never send GCS paths, HTTP response bodies or identity metadata.
        return {
            "schema":"plenum-owner-saved-demo-check-v1",
            "demo_origin":DEMO_ORIGIN,
            "result":"unavailable",
            "authenticated_profile_restored":False,
            "website_writes_executed":False,
            "private_page_content_disclosed":False,
        }
    ok=(isinstance(result,dict)
        and result.get("site")==DEMO_ORIGIN
        and result.get("demo_authenticated_restored") is True
        and result.get("http_status")==200)
    return {
        "schema":"plenum-owner-saved-demo-check-v1",
        "demo_origin":DEMO_ORIGIN,
        "result":"verified" if ok else "not_verified",
        "authenticated_profile_restored":bool(ok),
        "website_writes_executed":False,
        "private_page_content_disclosed":False,
    }

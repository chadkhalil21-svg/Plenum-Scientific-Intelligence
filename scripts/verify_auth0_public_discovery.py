"""Read-only public Auth0 discovery check for the owner's EXISTING tenant.

No API tokens, Management API, browser login, user enumeration, role changes,
third-party requests beyond Auth0 public discovery, or billable Google calls.
"""
import json
import re
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

DOMAIN = "dev-8sylxsg44yh5kkhh.us.auth0.com"
ISSUER = f"https://{DOMAIN}/"
OIDC_URL = ISSUER + ".well-known/openid-configuration"
JWKS_URL = ISSUER + ".well-known/jwks.json"


def same_origin_url(url):
    if not isinstance(url,str) or len(url)>500:
        return False
    try:
        p=urlsplit(url)
        return (p.scheme=="https" and p.hostname==DOMAIN
                and p.port in (None,443) and p.username is None
                and p.password is None and not p.query and not p.fragment)
    except ValueError:
        return False


def fetch_public_json(url):
    if not same_origin_url(url):
        raise ValueError("Refusing any URL outside owner Auth0 issuer")
    with urlopen(Request(url,headers={"Accept":"application/json","User-Agent":"Plenum-OAuth-Public-Metadata-Check/1.0"}),timeout=15) as reply:
        if reply.geturl()!=url or reply.status!=200:
            raise ValueError("Unexpected issuer redirect or non-200 response")
        raw=reply.read(64*1024+1)
    if len(raw)>64*1024:
        raise ValueError("Issuer public discovery is unexpectedly large")
    result=json.loads(raw)
    if not isinstance(result,dict):
        raise ValueError("Issuer response must be an object")
    return result


def validate_oidc(metadata):
    if metadata.get("issuer")!=ISSUER:
        raise ValueError("Issuer mismatch; cannot proceed")
    for key in ("authorization_endpoint","token_endpoint","jwks_uri"):
        if not same_origin_url(metadata.get(key)):
            raise ValueError(f"Untrusted Auth0 {key}")
    if metadata["jwks_uri"]!=JWKS_URL:
        raise ValueError("Unexpected tenant JWKS endpoint")
    if "code" not in metadata.get("response_types_supported",[]):
        raise ValueError("Authorization-code flow not advertised")
    if "S256" not in metadata.get("code_challenge_methods_supported",[]):
        raise ValueError("OAuth PKCE S256 is not advertised")
    return {
        "issuer_exact":True,
        "authorization_code_supported":True,
        "pkce_s256_supported":True,
        "cimd_advertised":metadata.get("client_id_metadata_document_supported") is True,
        "dcr_advertised":same_origin_url(metadata.get("registration_endpoint")),
        "stable_redirect_issuer_response_supported":metadata.get("authorization_response_iss_parameter_supported") is True,
        "provider_token_endpoint_public_client_method_advertised":"none" in metadata.get("token_endpoint_auth_methods_supported",[]),
        "issuer_jwks_configured":True
    }


def validate_jwks(jwks):
    keys=jwks.get("keys")
    if not isinstance(keys,list) or not any(
        isinstance(k,dict) and k.get("kty")=="RSA"
        and isinstance(k.get("kid"),str) and k.get("kid")
        and isinstance(k.get("n"),str) and isinstance(k.get("e"),str)
        for k in keys):
        raise ValueError("No usable public RSA signing key from issuer")
    return True


def main():
    oidc=fetch_public_json(OIDC_URL)
    result=validate_oidc(oidc)
    validate_jwks(fetch_public_json(JWKS_URL))
    # Only nonsecret booleans; no user data or token values in output.
    result["rsa_jwks_available"]=True
    print("PASS: Public Auth0 issuer and RSA keys verified.")
    for key,value in result.items():
        print(f"{key}={str(value).lower()}")
    if not result["cimd_advertised"] and not result["dcr_advertised"]:
        print("NEXT_GATE: Enable carefully scoped CIMD or DCR, or pre-register the ChatGPT OAuth client.")
    print("NO_CHANGE: No Auth0 settings, Google IAM, billing or deployed browser changed.")


if __name__=="__main__":
    main()

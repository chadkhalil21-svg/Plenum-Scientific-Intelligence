"""Pre-deployment OAuth resource boundary for a future PRIVATE browser MCP facade.

This module is not imported by the existing Cloud Run browser application.
It issues no OAuth tokens, accepts no cookies, and performs no website writes.
An established OAuth 2.1 authorization server must provide login and consent.
The facade must remain undeployed until the real owner OAuth flow and protected
private transport are independently verified.
"""
from dataclasses import dataclass
import ipaddress
import os
import re
import time
from urllib.parse import urlsplit

READ_SCOPE = "browser:read"
MACHINE_PATH = "/machine/v1/public-read"
FIXTURE_URL = "https://example.com/"
MAX_TOKEN_SECONDS = 600
MACHINE_URL_RE = re.compile(
    r"^https://plenum-computer-browser-machine-[a-z0-9.-]+[.]run[.]app$"
)


def _https_url(value, *, permit_path):
    if not isinstance(value, str) or not (12 <= len(value) <= 420):
        return False
    if any(ord(ch) < 33 or ord(ch) == 127 for ch in value):
        return False
    try:
        p = urlsplit(value)
        host = p.hostname or ""
        port = p.port
        ipaddress.ip_address(host)
        return False
    except ValueError:
        pass
    try:
        p = urlsplit(value)
        port = p.port
    except ValueError:
        return False
    return (p.scheme == "https" and port in (None, 443)
            and bool(p.hostname) and "." in p.hostname
            and not p.username and not p.password
            and not p.query and not p.fragment
            and (permit_path or p.path in ("", "/"))
            and not p.hostname.endswith((".local", ".internal", ".localhost", ".test")))


@dataclass(frozen=True)
class ResourceConfig:
    issuer: str
    resource: str
    jwks_url: str
    owner_sub: str
    machine_url: str

    @classmethod
    def from_environment(cls):
        return cls(
            issuer=os.environ.get("PLENUM_MCP_OAUTH_ISSUER", ""),
            resource=os.environ.get("PLENUM_MCP_RESOURCE_URL", ""),
            jwks_url=os.environ.get("PLENUM_MCP_OAUTH_JWKS_URL", ""),
            owner_sub=os.environ.get("PLENUM_MCP_OWNER_SUB", ""),
            machine_url=os.environ.get("PLENUM_MCP_MACHINE_URL", ""),
        ).validate()

    def validate(self):
        if not (_https_url(self.issuer, permit_path=True)
                and _https_url(self.resource, permit_path=True)
                and _https_url(self.jwks_url, permit_path=True)):
            raise ValueError("Trusted OAuth issuer, HTTPS MCP resource and signing keys are required")
        issuer = urlsplit(self.issuer)
        keys = urlsplit(self.jwks_url)
        if ((issuer.scheme, issuer.hostname, issuer.port)
                != (keys.scheme, keys.hostname, keys.port)):
            raise ValueError("OAuth signing keys must share the configured issuer origin")
        if not keys.path or keys.path == "/":
            raise ValueError("Dedicated issuer JWKS path required")
        if not isinstance(self.owner_sub, str) or not 3 <= len(self.owner_sub) <= 250:
            raise ValueError("Expected immutable authorized owner subject required")
        if not MACHINE_URL_RE.fullmatch(self.machine_url):
            raise ValueError("Expected exact private IAM machine Cloud Run URL required")
        if self.resource.rstrip("/") == self.machine_url.rstrip("/"):
            raise ValueError("Public MCP facade must be separate from IAM-private browser worker")
        return self


def enforce_verified_claims(claims, config, *, now=None):
    """Validate ALREADY signature-verified issuer claims, never untrusted JWT text."""
    config.validate()
    if not isinstance(claims, dict):
        raise PermissionError("Unverified OAuth principal")
    timestamp = int(time.time()) if now is None else now
    issued, expires = claims.get("iat"), claims.get("exp")
    if (not isinstance(issued, int) or isinstance(issued, bool)
            or not isinstance(expires, int) or isinstance(expires, bool)
            or not (0 < expires - issued <= MAX_TOKEN_SECONDS)
            or issued > timestamp + 15 or expires <= timestamp
            or claims.get("iss") != config.issuer
            or claims.get("sub") != config.owner_sub):
        raise PermissionError("OAuth owner identity or token lifetime rejected")
    audience = claims.get("aud")
    if audience != config.resource and audience != [config.resource]:
        raise PermissionError("OAuth token not minted exclusively for browser MCP")
    scope = claims.get("scope")
    if not isinstance(scope, str) or READ_SCOPE not in scope.split():
        raise PermissionError("Required browser read scope unavailable")
    return {
        "subject_verified": True,
        "scopes": [READ_SCOPE],
        "expires_at": expires,
    }


class OwnerJWTVerifier:
    """Verify RS256 provider JWT using issuer-hosted signing keys, no homegrown AS."""

    def __init__(self, config):
        self.config = config.validate()
        # Lazily constructed so offline checks never request remote provider keys.
        self._key_client = None

    def verify(self, access_token):
        import jwt
        if not isinstance(access_token, str) or not 80 <= len(access_token) <= 10000:
            raise PermissionError("Missing OAuth access token")
        try:
            header = jwt.get_unverified_header(access_token)
            if header.get("alg") != "RS256" or not isinstance(header.get("kid"), str):
                raise PermissionError("OAuth signing algorithm or key ID not allowed")
            if self._key_client is None:
                self._key_client = jwt.PyJWKClient(
                    self.config.jwks_url, cache_jwk_set=True, lifespan=300, timeout=5
                )
            key = self._key_client.get_signing_key_from_jwt(access_token).key
            claims = jwt.decode(
                access_token, key, algorithms=["RS256"],
                issuer=self.config.issuer, audience=self.config.resource,
                leeway=15,
                options={"require": ["iss", "aud", "sub", "iat", "exp"]},
            )
            return enforce_verified_claims(claims, self.config)
        except (jwt.PyJWTError, OSError, ValueError, TypeError) as exc:
            raise PermissionError("OAuth access token rejected") from exc


def validate_public_machine_result(body):
    """Return a bounded untrusted excerpt, never raw headers, cookies or arbitrary JSON."""
    if not isinstance(body, dict):
        raise PermissionError("Browser worker result rejected")
    if (body.get("schema") != "plenum-private-browser-read-v1"
            or body.get("status") != 200
            or body.get("final_url") not in (FIXTURE_URL, FIXTURE_URL[:-1])
            or body.get("external_site_changed") is not False
            or body.get("authenticated_site_used") is not False
            or body.get("AGI_demonstrated") is not False):
        raise PermissionError("Browser worker read-only proof rejected")
    title = body.get("title_untrusted")
    excerpt = body.get("body_excerpt_untrusted")
    if (not isinstance(title, str) or not isinstance(excerpt, str)
            or len(title) > 900 or len(excerpt) > 900):
        raise PermissionError("Unexpected browser worker response size")
    return {
        "schema": "plenum-owner-mcp-public-fixture-v1",
        "visited": FIXTURE_URL,
        "title_untrusted": title,
        "excerpt_untrusted": excerpt,
        "authenticated_website_used": False,
        "external_website_modified": False,
        "private_session_access": False,
    }


async def read_fixed_public_fixture(config):
    """Future facade -> IAM-private machine using workload identity, no key files.

    There is deliberately NO generic task URL, account login, or write action.
    The facade service identity needs an explicit machine-specific Invoker grant
    after OAuth, egress and owner-bound tool tests. No such grant is made here.
    """
    config.validate()
    from google.auth.transport.requests import Request
    from google.oauth2 import id_token
    import asyncio
    import httpx

    # A Google-signed audience token from the facade's own runtime identity.
    # Do not accept a service-account file, token parameter, or public GitHub job.
    identity = await asyncio.to_thread(id_token.fetch_id_token, Request(), config.machine_url)
    if not isinstance(identity, str) or not identity:
        raise PermissionError("Private worker identity unavailable")
    async with httpx.AsyncClient(
        timeout=25.0, follow_redirects=False, trust_env=False
    ) as client:
        response = await client.post(
            config.machine_url + MACHINE_PATH,
            json={"url": FIXTURE_URL},
            headers={"Authorization": "Bearer " + identity},
        )
    if response.status_code != 200 or len(response.content) > 8192:
        raise PermissionError("Private browser worker unavailable")
    try:
        body = response.json()
    except ValueError as exc:
        raise PermissionError("Invalid private browser response") from exc
    return validate_public_machine_result(body)

"""Owner-only MCP OAuth resource server using the OFFICIAL MCP Python SDK v2.

Not deployed or connected to ChatGPT. Requires an established OAuth 2.1
provider, trusted CIMD client identity, and an explicitly authorized separate
Google IAM facade service account. It does not implement authorization-code
issuance and MUST NOT serve stdio for production (stdio bypasses bearer auth).
"""
import time
from .oauth_resource_boundary import (
    READ_SCOPE, OwnerJWTVerifier, ResourceConfig, read_fixed_public_fixture,
)


def create_private_browser_mcp():
    from pydantic import AnyHttpUrl
    from mcp.server import MCPServer
    from mcp.server.auth.provider import AccessToken
    from mcp.server.auth.settings import AuthSettings
    from mcp.server.auth.middleware.auth_context import get_access_token

    config = ResourceConfig.from_environment()
    verifier = OwnerJWTVerifier(config)

    class SDKTokenVerifier:
        async def verify_token(self, token: str) -> AccessToken | None:
            try:
                claims = verifier.verify(token)
            except PermissionError:
                return None
            return AccessToken(
                token=token,
                client_id=config.client_id,
                subject=config.owner_sub,
                scopes=claims["scopes"],
                resource=config.resource,
                expires_at=claims["expires_at"],
            )

    server = MCPServer(
        "Plenum Computer Browser (Private OAuth Read-Only)",
        token_verifier=SDKTokenVerifier(),
        auth=AuthSettings(
            issuer_url=AnyHttpUrl(config.issuer),
            resource_server_url=AnyHttpUrl(config.resource),
            required_scopes=[READ_SCOPE],
            validate_token_resource=True,
        ),
    )

    def require_owner():
        bearer = get_access_token()
        if (bearer is None
                or bearer.subject != config.owner_sub
                or bearer.client_id != config.client_id
                or bearer.resource != config.resource
                or READ_SCOPE not in bearer.scopes
                or bearer.expires_at is None
                or bearer.expires_at <= int(time.time())):
            raise PermissionError("Owner-authenticated browser scope required")

    @server.tool()
    async def browser_capabilities() -> dict:
        """Report verified read-only capabilities; no private account or writes."""
        require_owner()
        return {
            "schema": "plenum-mcp-browser-capabilities-v1",
            "owner_authenticated": True,
            "read_only_fixture_available": True,
            "fixture": "https://example.com/",
            "logged_in_websites_available": False,
            "remote_clicks_forms_and_uploads_available": False,
            "account_changes_available": False,
        }

    @server.tool()
    async def browser_read_public_fixture() -> dict:
        """Use Google IAM to privately read only the public Example Domain fixture."""
        require_owner()
        return await read_fixed_public_fixture(config)

    return server


def main():
    # Never fall back to an unauthenticated stdio MCP server.
    server = create_private_browser_mcp()
    server.run(transport="streamable-http")


if __name__ == "__main__":
    main()

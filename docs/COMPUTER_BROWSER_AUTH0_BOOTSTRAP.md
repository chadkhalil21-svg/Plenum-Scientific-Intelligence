# Plenum Computer Browser: one-time managed OAuth activation

## Status

The `services/computer_browser/oauth_resource_boundary.py`, `mcp_resource_server.py`, `oauth_asgi.py` and `facade.Dockerfile` implement an **isolated, not-yet-deployed** MCP resource server. Nothing here changes the existing IAP owner browser, private Cloud Run Playwright machine, or GitHub bridge. Public machine read is verified; **private account automation is not**.

## The one step that cannot be completed in source code

The owner must authorize a managed OAuth tenant, because ChatGPT's user-bound OAuth needs genuine sign-in and consent. Use official Auth0 Free (currently advertised at $0 with no credit card needed to sign up): https://auth0.com/signup

1. Create or sign into an Auth0 tenant using an existing Google sign-in if desired. Choose a tenant label such as `plenum-computer-browser` if available. Do not enable paid features or custom domains.
2. Return only the tenant's **Domain**, available in Auth0 application settings, for example `tenant-name.us.auth0.com`. This is a nonsecret identifier. Never send passwords, JWTs, MFA codes, client secrets, Google service-account keys, cookies, or a browser profile through GitHub issues or ChatGPT.
3. If asked to approve paid features or a new bill, decline; this initial step requires only managed sign-in and resource server authorization.

## Next activation steps after that domain exists

1. Verify issuer metadata, signing keys, S256 PKCE and CIMD/DCR support using the provider's published endpoints.
2. Deploy the **separate** small OAuth MCP facade on Cloud Run with dedicated keyless runtime identity and no session vault. Its public URL becomes the resource identifier ending in `/mcp`. Never expose the private Playwright machine to anonymous access.
3. In Auth0, register an API whose identifier is the exact facade resource URL and permission `browser:read`. Set an access-token lifetime of 600 seconds. If ChatGPT uses the RFC 8707 `resource` parameter, enable Auth0's **Resource Parameter Compatibility Profile** under Tenant Settings > Advanced. Source: https://support.auth0.com/center/s/article/mcp-audience-error-with-auth0 .
4. Use CIMD where Auth0 supports it, otherwise DCR or an explicitly registered public client. Get the exact ChatGPT callback and client ID from the connection UI instead of guessing. Bind the owner's exact immutable subject `sub` from a verified login, not email text.
5. Verify protected-resource metadata, unauthenticated 401, denied wrong owner/client/resource/scope/expired JWT, valid owner OAuth login, and a real ChatGPT tool call restricted to the public fixture.
6. Only afterward add independently reviewed owner session storage, private egress restrictions and explicit approvals before private websites, forms, messages, purchases or account changes.

Auth0's OpenID scope can add issuer-owned `/userinfo` as a second token audience. Our verifier allows only that issuer-owned endpoint in addition to the exact MCP resource, never an arbitrary second API audience.

## Costs and boundaries

Auth0's free plan has usage limits and may change. Google Cloud Run/Build and GitHub Actions have separate billing. No unlimited-free promise and no need to revisit Google's earlier IAP error 9 for the machine connection.

This PR builds and verifies a facade container but **does not deploy** it, create third-party accounts, publish private data, grant IAM roles or authorize site writes. Verified public browser proofs: [issue #139](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/139) and [issue #141](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/141).

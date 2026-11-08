## Verified live private MCP endpoint (November 8, 2026)

- **Endpoint:** `https://plenum-computer-browser-mcp-2lak3vl73q-ue.a.run.app/mcp` (this is the exact Auth0 API audience to register, not a guess).
- **Project:** `plenum-computer-browser`; region `us-east1`; separate Cloud Run service `plenum-computer-browser-mcp`.
- **Verification:** [owner issue #160](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/160) confirms GitHub short-lived identity-token **signed /health HTTP 200**, anonymous Cloud Run denied, and an IAM-authenticated but OAuth-unsigned `/mcp` request returned **401**. The Auth0 issuer `https://dev-8sylxsg44yh5kkhh.us.auth0.com/` and JWKS origin were verified by live discovery before deployment.
- **Safe staging only:** Auth0 owner subject and OAuth client values are intentionally locked placeholders, no browser accounts or writes enabled. This private service temporarily shares the existing zero-project-role keyless **machine-runtime service account**. A dedicated MCP facade service identity and actual owner OAuth must be configured **before** opening this service for ChatGPT OAuth bearer traffic.
- **No original browser changes:** independent IAP browser and IAM Playwright machine remain untouched. Cloud Build's first portable-Dockerfile attempt failed before any deployment ([#148](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/148)); the corrected portable build passed CI and live deployment ([#160](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/160)).

### Next one-time Auth0 API registration

In your authenticated Auth0 dashboard: **Applications → APIs → Create API**. Use:
- **Name:** `Plenum Computer Browser MCP`
- **Identifier (Audience):** `https://plenum-computer-browser-mcp-2lak3vl73q-ue.a.run.app/mcp`
- **Signing algorithm:** `RS256`

Then open the API's **Permissions** tab, add `browser:read` (description: `Read authorized public browser pages`), and in **Settings**, set Access Token Expiration and Browser Flow Expiration to `600` seconds, where supported. Do **not** select a paid plan. Auth0's tenant-level Resource Parameter Compatibility Profile has already been confirmed enabled; leave DCR and CIMD unchanged until ChatGPT's client registration method is verified.

**Do not yet make Cloud Run public or send client secrets, access tokens or cookies to ChatGPT or GitHub.** Once the API exists, the following steps remain: dedicated facade runtime identity, Auth0 OAuth client registration and actual founder user `sub`, server environment update with immutable allowlisted OAuth client, Cloud Run public OAuth-only route verification, ChatGPT connection sign-in and tool smoke, then separate private session and per-action approval work.

# Plenum Computer Browser: one-time managed OAuth activation

## Status

The separate `plenum-computer-browser-mcp` Cloud Run service has now been **deployed privately** and verified. Its OAuth resource code comes from `services/computer_browser/oauth_resource_boundary.py`, `mcp_resource_server.py`, `oauth_asgi.py` and `facade.Dockerfile`. Nothing here changes the existing IAP owner browser, private Cloud Run Playwright machine, or GitHub bridge. Public machine read is verified; **private account automation is not**.

## Tenant created: next required owner action is Auth0 API registration

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

## November 8: Private Cloud Run address bootstrap

Your Auth0 tenant already exists at `dev-8sylxsg44yh5kkhh.us.auth0.com` (copied from the user-provided Auth0 application Settings screenshot). You confirmed the **Resource Parameter Compatibility Profile is enabled**. Leave CIMD and DCR unchanged until we know the ChatGPT connection registration method.

The repo now contains an **owner-gated, narrowly scoped** private Cloud Run address bootstrap:
- `.github/workflows/computer-browser-auth0-private-facade-bootstrap.yml` triggers only for the founder's exact owner issue (never for a push or arbitrary issue) and requires the existing protected production environment.
- It FIRST requests public OIDC discovery and validates the **exact issuer and JWKS origin**. A typo or inaccessible tenant stops the workflow **before** Cloud Build spends credits.
- It builds only `services/computer_browser/facade.Dockerfile` via the existing dedicated Cloud Build identity. The immutable image goes to a separate Artifact Registry name.
- It creates only `plenum-computer-browser-mcp` in `us-east1`, with **Cloud Run authentication required**, IAM-private access and zero minimum instances. It uses the existing zero-project-role machine runtime account **only for bootstrap**, because creating a new user-managed service account still needs Cloud IAM owner rights. **Do not make this service public while it shares the machine runtime identity.**
- Its registered OAuth owner and OAuth client are deliberately nonfunctional placeholders. Only after deployment does it resolve the real Cloud Run URL and update the MCP resource identifier to `<new-service-url>/mcp`. This final address can then be registered as an Auth0 API audience.
- It grants only the existing GitHub deployer `roles/run.invoker` on **this new facade service**, strictly to test signed `GET /health` 200 and **OAuth-unsigned `POST /mcp` 401**; Cloud Run anonymous invocation must fail. No Google IAP settings, Playwright image, owner cookies or browser actions are modified.
- This is **address reservation and secure smoke only**, not a working ChatGPT plugin. A dedicated facade service account, exact real owner `sub`, OAuth client identity, Auth0 API scopes, endpoint OAuth verification and ChatGPT sign-in/consent must precede any transition to an internet-callable OAuth MCP server.

After the bootstrap passes, create the Auth0 API with Identifier **exactly equal to the output `https://plenum-computer-browser-mcp-...run.app/mcp`** and scope `browser:read`. Use 600-second access tokens if the free tenant permits. No client secret should be copied into the repository, chat, or public GitHub issues.


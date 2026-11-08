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

## The next required owner action

The Auth0 tenant is already created and its resource-parameter compatibility setting is enabled. The verified Cloud Run MCP service is already deployed privately. Register the **exact URL above** as an Auth0 custom API, add the `browser:read` permission, preserve RS256, and set the token expiration to 600 seconds. The signing algorithm and new owner OAuth sign-in must be verified before exposing this interface to ChatGPT.

## Costs and boundaries

Auth0's free plan has usage limits and may change. Google Cloud Run/Build and GitHub Actions have separate billing. No unlimited-free promise and no need to revisit Google's earlier IAP error 9 for the machine connection.

The facade **is now deployed privately**, with a narrowly scoped Invoker grant only to the existing GitHub deployer for testing. It still does not accept real owner OAuth credentials, authenticate private website accounts, or authorize site writes. Verified public browser proofs: [issue #139](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/139) and [issue #141](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/141).

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


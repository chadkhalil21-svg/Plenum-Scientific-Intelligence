# Computer Browser: private ChatGPT-to-Cloud Run connector contract

## Verified base (2026-11-08)

1. The dedicated Cloud Run service `plenum-computer-browser-machine` is **private** and has an exact Invoker principal: `plenum-browser-deploy@plenum-computer-browser.iam.gserviceaccount.com`. Google-signed ID-token `GET /health` returned HTTP 200; anonymous requests were denied. See founder issue #130.
2. Existing owner `plenum-computer-browser` remains behind Google IAP; no authentication or IAM changes are required for the private machine transport.
3. The Computer Browser personal ChatGPT plugin presently binds **GitHub**, and its verified actions are **public** Playwright reading and bounded navigation. It has no custom private MCP server connection or authenticated private-action tool. Do not confuse a plugin skill with private browser controls.

## Verified live smoke (owner-gated; 2026-11-08)

`POST /machine/v1/public-read` starts **disabled**. If `MACHINE_IAM_PUBLIC_READ=true` is explicitly enabled on the independent machine service, it accepts **only** `{"url":"https://example.com/"}` or the same URL without the trailing slash. It invokes existing `read_public` Playwright, which creates a fresh cookie-free Chromium context, blocks non-GET traffic and non-approved origins, and returns a bounded text excerpt. Cloud Run IAM authorizes the one deployer caller and rejects anonymous requests **before** FastAPI sees them. The endpoint cannot read private sites, save cookies or modify external accounts.

The exact production tests must verify: immutable image digest and dedicated runtime identity; solely the existing Invoker principal; no app secrets or session vault; signed request returns HTTP 200 with expected *Example Domain* from real Chromium and no site writes; unsigned identical request returns non-2xx. No raw page output is posted to public GitHub, only non-sensitive PASS/FAIL.

This is a **public fixture read across a private transport**, not access to a user's private website.

## Required private MCP facade before personal browsing

A custom OAuth 2.1-authenticated MCP facade must sit **in front of** the IAM-only worker. It is a separate service, not the Cloud Run machine service publicly exposed. Use the official plugin authorization specification: publish OAuth protected-resource metadata and per-tool `securitySchemes`; authenticate the actual owner; use short-lived, audience-scoped access tokens. ChatGPT cannot use arbitrary customer-supplied service-account keys as a substitute for OAuth.

Architecture:

```
ChatGPT personal plugin -> OAuth2.1 private owner MCP facade
                     -> scoped owner approval + task policy
                     -> Google-signed short-lived ID token (dedicated facade identity)
                     -> IAM-private Cloud Run Playwright worker
                     -> private response over authenticated channel
```

Grant any eventual facade identity `roles/run.invoker` **on this machine service only**, after testing. Keep the currently deployed Invoker account unchanged unless owner approves a reviewed migration. Do not route sensitive requests through GitHub public issues, comments, artifacts or logs. Do not place Google credentials in repository files or the plugin manifest.

Proposed MCP read tools, when real auth exists:
- `browser.read_public(url)`: approved HTTPS public origins, no cookies, no write methods, bounded responses.
- `browser.prepare_private_session(site)`: returns a short-lived owner sign-in link; browser credentials typed only in an owner-authenticated private UI.
- `browser.observe_private(session_id)`: read-only, owner-scoped output with prompt-injection labeling and no credential leakage.
- `browser.plan_change(session_id,actions)`: dry-run description only, origin-limited and expiring.
- `browser.execute_approved(plan_id,approval_id)`: only after explicit owner approval **per consequential action**. Payments, account deletion, publishing, messaging and submissions need specific consent; never default to automatic permission.

Implement distinct task IDs, expirations, purpose scoping, idempotency keys, rate limits, private result retention, redaction, audit logs and encrypted session storage. Allow owner revoke/kill switch. Website network traffic must be isolated from cloud metadata, local/private IP ranges, DNS rebinding and unapproved redirects **before** private sessions are enabled. Current DNS precheck alone is not sufficient.

**Verification gates:** end-to-end owner OAuth authentication and denied wrong-user access; private task/result secrecy; browser session stored and restored without exposing cookies; per-action approval with replay prevention; denied cross-origin network; one successful real logged-in task with owner approval; and plugin tool invocation from ChatGPT. Until all pass, mark private account automation **unavailable** and do not claim a Work-equivalent general browser.

Sources:
- https://developers.openai.com/plugins/build/auth
- https://docs.cloud.google.com/run/docs/authenticating/service-to-service
- https://developers.openai.com/api/docs/mcp

## Completed proof, 2026-11-08
The fixed fixture feature and complete public-chat transport are now independently **live verified**:
- [PR #133](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/pull/133) and [owner issue #134](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/134): machine-only image and `MACHINE_IAM_PUBLIC_READ=true` passed real Playwright HTTPS `example.com` read, HTTP 200, anonymous IAM denial, strict no-cookie/no-write checks.
- [PR #135](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/pull/135) and [chat-created issue #137](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/137): **PASS** for an actual normal-chat owner request traversing connected GitHub → short-lived Google IAM token → private Cloud Run → real Playwright → sanitized public issue response.
- No third-party website account session was used and no arbitrary remote browser action was enabled. Do not infer private MCP/Work parity from this proof.

## OAuth MCP resource foundation (2026-11-08, offline only)

The new `services/computer_browser/oauth_resource_boundary.py` and `mcp_resource_server.py` reuse official **MCP Python SDK 2.3.0** for the protected resource, tool metadata and HTTP bearer middleware; **there is no homegrown login system**. The offline tests in `tests/test_browser_oauth_resource_boundary.py` sign synthetic RS256 JWTs and reject wrong issuer, audience, owner, client, scope, token expiry, signing algorithm, and cryptographic signature. They also demand HTTP 401 for anonymous `/mcp` calls and verify protected-resource discovery metadata. No real owner account or Google credentials are read in CI.

**Never deploy these files into the current IAP owner service or the IAM-only machine itself.** The eventual OAuth facade must be a **different hostname** and dedicated runtime identity. It must not store browser cookies; the only implemented worker method is the existing fixed public `example.com` fixture over short-lived Google IAM identity, after the dedicated facade identity receives exact-machine `roles/run.invoker` permission.

A future deployment requires an **existing OAuth 2.1 provider**, configured with secure owner login and consent, **S256 PKCE**, supported CIMD or DCR client identification, a `resource` indicator reflected in access-token `aud`, and a provider JWKS. OpenAI's plugin guide: https://developers.openai.com/plugins/build/auth . Prepare only these **nonsecret configuration identifiers** after the provider is selected:

| Setting | Purpose |
|---|---|
| `PLENUM_MCP_OAUTH_ISSUER` | Exact signed token issuer, HTTPS |
| `PLENUM_MCP_RESOURCE_URL` | Full public HTTPS MCP endpoint on a separate hostname, ending in `/mcp` |
| `PLENUM_MCP_OAUTH_JWKS_URL` | Provider's HTTPS JWKS endpoint on the same host as issuer |
| `PLENUM_MCP_OWNER_SUB` | Exact immutable OAuth owner subject, not guessed from email |
| `PLENUM_MCP_ALLOWED_CLIENT_ID` | Provider-recognized client metadata identifier for ChatGPT's OAuth client |
| `PLENUM_MCP_MACHINE_URL` | Exact existing private `plenum-computer-browser-machine` Cloud Run URL |

The source checks all six before creating an MCP server. Access tokens must be RS256, provider-signed, aud-bound **only** to this resource, issued to the configured subject and exact client ID, carry `browser:read`, and last at most **600 seconds**. Both MCP tools advertise OAuth2 `browser:read` with no write scope. The separate machine invoker identity is obtained from Cloud Run workload credentials, **never** from a JSON key.

**Unfinished verification gates:** obtain the actual provider and founder OAuth authorization, connect the new facade privately to Google IAM with least privilege, deploy and test on an independent hostname, prove unauthorized/wrong-user and revoked-token rejection, verify provider redirects/consent and an actual tool invocation from ChatGPT. Then separately harden private session vault, DNS-rebinding/egress controls and per-action approvals for private accounts and writes. This source-only foundation is **not yet a usable private plugin or Work-like browser**.

## IAM-private Auth0 gateway staging verified (2026-11-08)

[Owner-gated issue #160](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/160) returned **PASS** for the independent `plenum-computer-browser-mcp` Cloud Run staging service at `https://plenum-computer-browser-mcp-2lak3vl73q-ue.a.run.app/mcp`: Google-signed `/health` was HTTP 200; anonymous Cloud Run invocation was denied; a Google-IAM-signed but OAuth-unsigned `/mcp` request returned HTTP 401. The service remains **IAM-private** and its OAuth owner/client settings are intentionally nonfunctional bootstrap placeholders. No private browser session, public MCP endpoint, third-party login, or website write was activated. The former owner-IAP service and the IAM-private Playwright machine were not modified by this gateway staging.

**Next authorized setup, not completed:** owner authenticates to Auth0 administrator console and registers the exact MCP resource as the API identifier/audience, defines `browser:read`, sets a trusted ChatGPT OAuth client identification method (prefer CIMD or a manually registered client, not unrestricted DCR), records the real immutable owner subject privately, and uses the callback URL shown by ChatGPT for this specific connection. After provider configuration, give the facade a **dedicated** keyless runtime identity, grant invocation on the one private machine service only, complete OAuth denial/refresh/revocation tests, and only then consider exposing the MCP facade via an OAuth-enforced external endpoint. This staging verification is NOT a connected ChatGPT browser and does not authorize private account actions.

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

## Founder Auth0 API authorization progress (2026-11-08)

**Confirmed by owner-shared Auth0 dashboard screenshots:** The Auth0 custom API **Plenum Computer Browser** was created with the *exact* identifier `https://plenum-computer-browser-mcp-2lak3vl73q-ue.a.run.app/mcp`, JWT algorithm **RS256**, and `browser:read` permission (description: approved website reading). The API uses **per-app authorization**. **New founder screenshots at 02:49 on 2026-11-08 prove the official `ChatGPT` third-party CIMD app was imported from `https://chatgpt.com/oauth/client.json` with the expected connector redirect, and now has `2/2` user-delegated permissions granted for `browser:read` and `browser:write` on the Plenum Computer Browser API.** Client and anonymous access were not requested. The `browser:write` *Auth0 scope* does not implement or authorize arbitrary browser writes in the Cloud Run worker; software support and per-action approvals remain separate security gates. The founder explicitly confirmed that **Resource Parameter Compatibility Profile was enabled previously**. Do **not** ask the founder to recreate this API, re-add `browser:read`, or re-enable that compatibility setting. No unrestricted DCR was authorized.

**Remaining engineering and authentication gates (Auth0 API/client setup completed):**
1. **Completed Auth0 administration:** ChatGPT CIMD client was manually imported using official `https://chatgpt.com/oauth/client.json`, expected redirect was visible in the mapping, and the owner granted `browser:read` and `browser:write` (`2/2`) on the API under user-delegated access. Do not repeat this registration or these grants. DCR remains restricted; `browser:write` in Auth0 is a reserved authorization scope, **not** an implemented executable MCP browser write tool.
2. **Private owner identity:** obtain the immutable Auth0 user `sub` through an authenticated **private** channel, and verify Auth0 actually issues resource-audience-bound RS256 access tokens with `browser:read`, the expected `azp`/client and short lifetime. Never publish access tokens, passwords, cookie material or owner subject in public repository issues.
3. **Cloud bridge:** replace disabled bootstrap owner/client placeholders, create a dedicated least-privilege keyless facade runtime, grant machine-specific invoker, verify invalid/other-owner/revoked tokens are denied, and only then make the **facade** OAuth-accessible to ChatGPT. Keep the browser **worker** IAM-private. Validate one genuine ChatGPT tool call before advertising private account support.

**Important session boundary:** Founder successfully logged into Auth0 from the local iPad Edge/Safari browser. That login is **not shared with TinyFish's remote browser profile**; remote human verification repeatedly looped. Do not automatically retry TinyFish sign-in or ask the founder to repeat an already completed Auth0 setting. No direct Auth0 Management API administrative connector/token is currently established. This staging verification is **not** a connected ChatGPT browser and does not authorize private website actions.

Official reference: https://developers.openai.com/plugins/build/auth ; manual Auth0 CIMD registration documented by Auth0 team: https://community.auth0.com/t/auth0-cimd-registration-appears-incompatible-with-the-current-chatgpt-client-id-metadata-document/203817/6 .


## Dedicated MCP runtime identity staging: verified Cloud IAM blocker (2026-11-08)

**Done:** [PR #169](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/pull/169) added and passed a founder-gated, no-grants workflow. [Founder issue #170](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/170) then verified **both existing Cloud Run services and their private IAM configuration** before trying to provision the dedicated keyless facade runtime.

**Exactly blocked:** Google returned \`iam.serviceAccounts.create\` **PERMISSION_DENIED** for the existing GitHub WIF/deployer identity. This identity therefore cannot create \`plenum-browser-mcp-runtime@plenum-computer-browser.iam.gserviceaccount.com\`. No existing Cloud Run revision, service account, IAM binding, project role or external website was altered. Do not repeatedly retry the owner issue until the missing service account exists or an authorized Google Cloud administrator has made a narrow decision.

**Smallest owner action without widening the GitHub deployer role:** From the owner's signed-in Google Cloud Console, open [Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts?project=plenum-computer-browser) in the **plenum-computer-browser** project and create exactly \`plenum-browser-mcp-runtime\`. Give it **no project roles, no user-managed keys, no delegated users**. Then rerun the existing issue #170 **prepare** job (do not recreate a different service or trigger Cloud Build). The workflow checks the exact service account and preserves the existing worker IAM. A later independent, reviewed step can grant that one identity service-specific Invoker on \`plenum-computer-browser-machine\` and bind it to the facade, but **not before owner OAuth and public MCP security tests**.

**Additional remaining private identity:** The owner's immutable Auth0 \`sub\` was not provided in the conversation. It must be obtained from the existing Auth0 **User Management → Users** owner profile through a private, authenticated channel (do not guess from email or add to public GitHub), and the actual signed bearer token must be tested to identify whether the Auth0 local \`tpc_\` client ID or CIMD URL appears in the verified token client claim. ChatGPT OAuth and browser writes remain unavailable until these gates and subsequent live tests pass.

**Do not redo:** Auth0 API registration, Resource Parameter Compatibility Profile, CIMD ChatGPT import or its 2/2 delegated \`browser:read\` + \`browser:write\` permissions. Neither Auth0 scope alone supplies an executable write tool, nor does the existing IAM-only machine proof imply private website control.

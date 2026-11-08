# Computer Browser: private ChatGPT-to-Cloud Run connector contract

## Verified base (2026-11-08)

1. The dedicated Cloud Run service `plenum-computer-browser-machine` is **private** and has an exact Invoker principal: `plenum-browser-deploy@plenum-computer-browser.iam.gserviceaccount.com`. Google-signed ID-token `GET /health` returned HTTP 200; anonymous requests were denied. See founder issue #130.
2. Existing owner `plenum-computer-browser` remains behind Google IAP; no authentication or IAM changes are required for the private machine transport.
3. The Computer Browser personal ChatGPT plugin presently binds **GitHub**, and its verified actions are **public** Playwright reading and bounded navigation. It has no custom private MCP server connection or authenticated private-action tool. Do not confuse a plugin skill with private browser controls.

## Next live smoke (owner-gated; separate release)

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

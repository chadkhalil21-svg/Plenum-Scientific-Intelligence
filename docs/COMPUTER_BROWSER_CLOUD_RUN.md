# Computer + Prometheus: one shared Cloud Run browser (staged)

**Goal:** enable Computer in ordinary chats and independent Prometheus to
navigate sites, log in with user consent, fill forms, upload documents,
review, submit and conduct longer workflows through one reusable Playwright
browser platform. Build only the missing secure connectivity. This service is
**NOT** a working logged-in general browser yet.

## What this release actually provides

- Uses existing `plenum_ai.browser_worker` and official Playwright/Chromium
  already verified through PRs #60, #62, #63 and #65.
- New separate deployable `services/computer_browser` FastAPI gateway:
  `GET /healthz` (no secrets), `POST /v1/plan` (stages site actions
  without executing writes), `POST /v1/read` (an approved public page),
  and `POST /v1/local-smoke` (real click and text entry against an
  *offline local fixture*, never an external account).
- All non-health endpoints require a 32+ character secret in
  `COMPUTER_BROWSER_TOKEN`. Production Google Cloud Run is configured
  **IAM-private too**; both are required.
- Per-deployment approved HTTPS origins in `BROWSER_ALLOWED_ORIGINS`,
  defaulting to public `https://example.com`. No private IP, localhost,
  cloud metadata host, arbitrary external writes, login/cookie storage or
  downloads. A best-effort DNS preflight is **not** DNS-rebinding-proof;
  production sensitive use still needs egress proxy/firewall and auditing.
- Non-root official Playwright Python 1.64.1 container, 2 CPU/2 GiB
  anticipated on-demand environment, one instance, one concurrent request.
- Dedicated GitHub CI verifies HTTP authentication, policy, real local
  Chromium input and click, public navigation, and Docker production image.

## Why not a new repository?

An isolated **service directory and container in the same
`Plenum-Scientific-Intelligence` repository** keep versions, reviewed
changes, underlying Python browser logic, CI evidence and the research ledger
together. It does *not* mean mixing the Computer browser's private cookies,
credentials or screenshots into public GitHub. No repo secret or site login
is in source control.

## Preferred production topology

```
Computer ChatGPT plugin (future OAuth2/MCP link)  ──┐
                                                     ├─ Authenticated browser coordinator
Plenum Prometheus LangGraph planner ────────────────┘  ├─ scopes / approvals
                                                        ├─ site-specific encrypted profile vault
                                                        └─ private on-demand Cloud Run Chromium worker
```

One browser engine is reused. Give Computer and Prometheus **separate
identities/scopes**; never share indiscriminate credentials. The public
ChatGPT GitHub/Playwright bridge remains an alternative for **public only**
pages without a persistent web service.

## Deployment, no unapproved cloud spend

Google's Cloud Run request-based pricing currently has a monthly free tier
of 2 million requests, 180k vCPU-seconds and 360k GiB-seconds (based on
us-central1, shared across projects of a billing account). Hosting still
requires a billing-enabled Google Cloud project and may incur Artifact
Registry, builds, network egress or overage charges. A 2 vCPU, 2 GiB,
60-second browser task consumes ~120 vCPU-seconds and 120 GiB-seconds,
**before cold-start and other usage**. Free tier is not a guarantee of $0.

Suggested settings: region `us-east1` (check applicable regional rates),
`min-instances=0`, `max-instances=1`, `concurrency=1`,
`timeout=300`, `cpu=2`, `memory=2Gi`, no GPU and
`--no-allow-unauthenticated`. Use a dedicated service account, Secret
Manager for the private service token, least-privileged workload identity
and billing budget alerts. No production deployment is enabled from this
repo until project/credentials and owner approval exist.

To build locally:
```
docker build -f services/computer_browser/Dockerfile -t plenum-computer-browser .
```

The project's container must not have Kaggle, GitHub, payment, Gmail or
other unrelated credentials. No credentials appear in logs. Use Cloud Run
IAM and explicit application authentication; anonymous public listeners
and forwarding generic Cloud Run credentials to a browser are not approved.

## What remains before it operates **any authorized account** from chats

1. **Private persistent sessions:** human-operated browser sign-in flow,
   scoped by domain and owner identity, encrypted per-session storage with
   Cloud Storage + KMS (or comparable secure vault), rotation, logout and
   TTL. Playwright storage state includes sensitive impersonation tokens,
   so never return it to ChatGPT or commit it to GitHub.
2. **Actual remote interactions:** site-scoped click, type, form, file,
   select and multi-step operations, isolated sessions, full navigation
   checks, screenshot/DOM evidence, retries and a user-visible confirmation
   page for site writes. Default-deny purchases, payments, deletions,
   sending messages or security changes until per-action approval.
3. **Secure MCP gateway in ChatGPT:** deployed HTTPS MCP service with
   OAuth 2.1 and per-tool scopes, owner authorization and ChatGPT plugin
   connection. Cloud Run IAM by itself is **not** a ChatGPT OAuth login.
   Custom full write-capable MCP connections can depend on account/workspace
   plan and web UI availability. This guide does not claim it is connected.
4. **Robust isolation:** network egress ACL/proxy (SSRF, DNS rebinding,
   metadata endpoint), source-page prompt-injection handling, DOM/screenshot
   privacy, encryption in transit, audit log and budgets. No unrestricted
   model-generated shell/JavaScript execution inside the browser.
5. **Independent testing:** authenticated staging account, approval and
   rollback drills, phishing tests, account boundary and exfiltration tests.
   Only then promote browser operations to real sites.

## Why this architecture

Google documents headless and full-desktop browser automation for Cloud Run:
https://docs.cloud.google.com/run/docs/browser-automation

Microsoft Playwright supports isolated contexts and storage state, but
warns that saved state can impersonate the user:
https://playwright.dev/docs/auth

OpenAI's remote MCP plugins require authentication and owner authorization:
https://developers.openai.com/plugins/build/auth

Render free apps spin down and lose local state; Cloudflare Browser Run
free offers just ten browser minutes daily. Cloud Run is the more flexible
existing-Google-cloud path for bounded on-demand tasks, provided billing
and correct auth are configured. It is not indefinitely free.

## Encrypted session preservation proof

The separate `services/computer_browser/session_crypto.py` component now
uses official Python `cryptography==50.0.2` Fernet envelopes around
Playwright's `storage_state`, with owner and site-origin binding and
expiry. Real isolated Chromium must create a **synthetic test cookie**,
encrypt its state, restore it into a new browser context, and verify the
cookie survives. No real person signs in during this test.

**This is not persistent private account access.** The encryption key in
the offline test is ephemeral; production will need a KMS/Secret Manager
protected key, a private Cloud Storage vault with versioning and TTL,
human-operated sign-in UI, approved OAuth integration and ownership checks.
Never return storage-state ciphertext, private cookies or passkeys to
ChatGPT, model tools, public GitHub, browser logs or screenshots.

## November 7: parallel IAM-only machine connection (staged)

The existing `plenum-computer-browser` Cloud Run deployment **remains IAP-protected**. The live signed IAP health probes returned HTTP 404 even after granting the existing deployment account access to that one IAP resource. We do **not** disable IAP on the owner service.

A separate, purpose-built **health-only** Cloud Run machine endpoint is staged by `.github/workflows/computer-browser-iam-machine-health.yml`. The workflow is gated by owner-created GitHub issue with exact title `Computer Browser: deploy IAM machine health` and body `IAM_MACHINE_HEALTH_APPROVED:2026-11-07`, or manual dispatch with `IAM_MACHINE_HEALTH_APPROVED`.

- New service: `plenum-computer-browser-machine` in `us-east1`. It reuses the **immutable, deployed and verified existing** Playwright image digest without rebuilding it.
- New isolated runtime: `plenum-browser-machine-runtime@plenum-computer-browser.iam.gserviceaccount.com`. It must be explicitly created with **no project roles or keys**; the current GitHub deployer gets **Service Account User on this one account only**. The workflow fails without the prerequisite. It never creates or edits project-wide IAM policies.
- Invoker: only the already-connected GitHub deployer service account gets `roles/run.invoker` **on the new machine service alone**.
- Security: `--no-iap --invoker-iam-check --no-allow-unauthenticated`, on-demand min instances 0/max 1, no Cloud Run secrets, no login vault, no `COMPUTER_BROWSER_TOKEN` app secret. All existing browser endpoints requiring the app bearer fail closed; only `GET /healthz` may succeed for the IAM-authorized identity. The IAP owner console remains unavailable on the machine service without an IAP-signed owner assertion.
- First live test obtains a short-lived **OIDC ID token** whose audience is exactly the new service's Cloud Run URL; it checks signed `GET /healthz` returns expected JSON and anonymous `GET /healthz` does **not** return 2xx. Tokens never appear in public GitHub issues or log output.
- Fails closed if a service already exists, if any public invoker binding is present, if the runtime/image differs or if unexpected secret configuration appears. No existing Cloud Run service is modified.

This **does not create a working remote browser tool in ordinary ChatGPT chats**. It tests the secure machine-to-machine transport, after which private read-only browser actions can be added with an independently authenticated app-layer gateway, approved origins, and a private task/result transport. Full authenticated browsing requires further profile isolation and explicit action approvals.

Zero min instances reduces idle compute charges but does not guarantee zero total Google Cloud spending. No usage projections or user credits can be relied upon without current billing data. If this health-only service is not needed, it can be deleted separately without touching the IAP owner browser.

Google documentation:
- https://docs.cloud.google.com/run/docs/authenticating/service-to-service
- https://docs.cloud.google.com/run/docs/securing/managing-access

## November 7 live IAM machine-health preflight

- [PR #119](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/pull/119) merged successfully after both scientific and private-browser CI completed with success. The new feature is **not a production private browser**, only the IAM-only health connection scaffold.
- Owner-created [issue #120](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/120) triggered the guarded workflow. It returned **BLOCKED at preflight**, specifically: `Dedicated runtime identity unavailable or machine service already exists. No deployment attempted.`
- No new Cloud Run service has been confirmed deployed. The workflow's sanitized status does **not distinguish** missing service account, insufficient permissions to read it, or an existing service. Confirm that narrow prerequisite rather than changing the existing IAP service.
- TinyFish's saved Google Cloud browser session subsequently required a fresh user sign-in; no automated access to Cloud Console is available until the owner signs in through TinyFish's secure profile setup. After sign-in, inspect and create only the dedicated zero-role runtime account if missing, and grant the existing deployer `roles/iam.serviceAccountUser` **on this single account**, not project-wide. Then rerun the same owner-gated workflow.
- Service creation may incur usage charges despite min instances 0. Preserve owner Cloud Run IAP and all existing project IAM settings throughout.

## November 7 at 23:24 ET: IAM-only runtime bootstrap live result

- [PR #122](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/pull/122) passed both CI workflows and merged. It allows an **owner-gated GitHub-to-Google** workflow to inspect or create the exact dedicated machine runtime account with no project role grants or keys, then grant deployer Service Account User **on that one account only**.
- [Issue #123](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/123) triggered the workflow and returned **BLOCKED: GitHub deployer cannot create the dedicated service account with current permissions. No new project roles were granted.** Therefore no machine service was deployed or tested.
- The TinyFish Google profile was saved by the founder but the later automated browser run redirected to password entry; no Google Cloud changes were made by that run. Avoid more paid TinyFish login retries for this dependency.
- Next prerequisite: the founder (already authenticated in their own Google Cloud console) creates just `plenum-browser-machine-runtime@plenum-computer-browser.iam.gserviceaccount.com` with **zero project roles and no keys**, then, on that service account resource only, grants `plenum-browser-deploy@plenum-computer-browser.iam.gserviceaccount.com` `roles/iam.serviceAccountUser`. Once this account is verified, owner-gated issue trigger for the isolated IAM-only service can be rerun. Do not widen deployer project permissions merely to bypass bootstrap.

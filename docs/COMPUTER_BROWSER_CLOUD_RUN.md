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

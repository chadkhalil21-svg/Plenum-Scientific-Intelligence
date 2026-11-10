# Plenum Business Workforce | Operational Gate Register
2026-11-10 UTC. Keep this document factual. Do not overstate deployed capabilities.

## Live infrastructure reused
- Existing LangGraph research coordination, nine n8n/Qwen draft agents and an OpenHands/Qwen review-only syntax-valid candidate already demonstrated.
- American Rider already runs its own scheduled read-only Google Cloud production audit in the American-Rider-Commercial repository; it remains untouched.
- Native connected Render returned LIVE website/platform deployments at source SHA 247bb0f5781929d3233f8aca0006fe6e9b785135. Independent authenticated GitHub lookup of the American Rider release/current branch returned that exact SHA. This verifies release metadata alignment, not actual customer transactions.
- Native connected Resend returned two verified sending domains: americanrider.tech and americanrider.app. No email was sent. A ChatGPT connection does not automatically create credentials inside n8n.

## Scheduled zero-new-host-cost layer
- Free standard GitHub Actions runners in the existing public Plenum repository run the new public-business-readback workflow four times daily and via manual dispatch. These are **ephemeral scheduled jobs, not permanent n8n hosting**.
- Public readbacks check exact corporate, platform and server /health HTTPS URLs from the existing Render inventory. Require TWO separate successful GET responses per service; up to THREE bounded attempts per readback, with backoff. Do not follow redirects or accept unverified content types. Never publish private response content.
- Unit tests separately verify transient recovery, final failure, no redirect, double-read outcome and no claims of commerce. Actual live website results must pass CI before real availability is declared verified.
- Original American Rider production audit already covers backend Cloud Run; this new work covers a different surface: Render-hosted public web assets.
- GitHub Actions scheduled jobs may be delayed and public repo workflows can be disabled after 60 days without activity. Standard GitHub-hosted public repository runners are free under current GitHub terms.
- Render free web services are unsuitable for secure persistent n8n: 15-minute idle spin-down, filesystem loss on restart/redeploy, and free Postgres expiry after 30 days. Existing owner-private GitHub Codespaces n8n+Ollama remains an **on-demand** development option, not always-on.

## Secure business apps: actual access versus future work
- Connected native ChatGPT GitHub/Render/Resend tools were used in a live read-only business task; Gmail and Drive are also listed as available native tools. None of their ChatGPT secrets may be copied into public GitHub or assumed usable by n8n.
- Business data in n8n requires a private persistently encrypted credential store and least-privilege OAuth/provider tokens, narrow scopes, audit logs, revocation, encryption and explicit owner approval.
- Email sends, campaign publication, account deletion, security changes, financial transactions, production deployment and customer-facing support messages must have separate task-specific owner review and independent outcome verification.
- Public GitHub jobs must never receive live customer records, account passwords, session cookies, payment tokens, private patent data or cross-provider OAuth credentials.

## Upstream options from the founder's images
**Agency Agents** is MIT-licensed *Markdown persona/rubric content*, not 280 already-running AI workers. We adapted only minimal process rubrics into our original nine n8n roles, drawn conceptually from:
- Reality Checker: https://github.com/msitarzewski/agency-agents/blob/main/testing/testing-reality-checker.md
- Chief of Staff: https://github.com/msitarzewski/agency-agents/blob/main/specialized/specialized-chief-of-staff.md
- Support Responder: https://github.com/msitarzewski/agency-agents/blob/main/support/support-support-responder.md
- Growth Hacker: https://github.com/msitarzewski/agency-agents/blob/main/marketing/marketing-growth-hacker.md
- Original MIT license: https://github.com/msitarzewski/agency-agents/blob/main/LICENSE
The operational roles remain unable to send or change external systems without safe tools and owner authorization.

**Obscura** is an Apache-2.0 Rust headless browser with its own CDP/Playwright/MCP entrypoints. Its browser and saved-context parity are still evolving, and it does not solve owner OAuth, browser connector exposure, or app permissions. Do not replace existing Plenum Playwright absent one genuine owner-approved website comparison in a sandbox.
- Source: https://github.com/h4ckf0r0day/obscura
- Compatibility caveats: https://github.com/h4ckf0r0day/obscura/blob/main/docs/Use-with-Playwright.md

## Remaining before a complete autonomous workforce can be claimed
1. Durable private always-on n8n/model host; no reliable zero-cost permanent host has yet been independently verified.
2. Real n8n OAuth/provider read-write connectors with scoped permissions, revocation and no public credentials.
3. One genuine independently verified provider-app business action with its readback and human approval where consequential.
4. Persistent per-task checkpointing, bounded retries, idempotent operations, recovery, audit and cost ceilings beyond the narrow public GET monitor.

Sources on free quotas and hosting limitations:
- https://docs.github.com/en/actions/concepts/billing-and-usage
- https://docs.github.com/en/actions/reference/events-that-trigger-workflows#schedule
- https://render.com/docs/free
- https://docs.n8n.io/hosting/

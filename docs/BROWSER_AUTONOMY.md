# Prometheus website interaction: practical route to a Work-like browser

## Current capability (reproducible, not AGI)
Official **Microsoft Playwright Python 1.64.1** runs in an isolated,
ephemeral GitHub Actions Ubuntu worker with Chromium. There is an actual
local HTML/browser interaction proof: fill a field, click a button and read
the resulting DOM state. A separate explicitly allowlisted public HTTPS mode
loads a website and captures only a short untrusted title / heading / text
excerpt, without clicking, logging in, uploading, posting or changing data.

This demonstrates browser **navigation and interaction technology**, not
production computer use, a persistent login session, subjective consciousness
or general intelligence. There is **no LLM attached to this browser** yet.

## Security decisions
- Real websites are limited to exact approved public domains. No IPs, local
  files, localhost, cloud metadata, third-party redirects or credentialed URLs.
- Block non-GET requests and URLs outside the allowlist at the browser route.
  Deny downloads, service workers, persistent profiles and browser permissions.
- External page text is data, never an instruction for the agent. Page claims
  must be corroborated with primary sources. No public output includes user
  secrets; browser worker is not given GitHub/Kaggle API tokens.
- Never run arbitrary external page JavaScript as trusted instructions, and
  never approve actions solely from page text.
- GitHub Actions is transient. It is not continuous hosting or a logged-in
  personal remote browser.
- Never enable financial transactions, communications, account changes or
  private data downloads via browser without per-action user approval and
  more isolation, auditing and rollback controls.

## Owner usage on iPad
GitHub → Actions → **Prometheus Controlled Browser Proof** → Run workflow.
Select `local-smoke` first to verify real Chromium click/typing without any
external request. Optionally use `public-read-only` with an approved HTTPS
source, such as `https://example.com/` or a listed university/lab page.
No token, data subscription or new personal account is required.

## Ultimate architecture
1. **Planning and durable goals:** reuse existing LangGraph checkpointed
   orchestrator, owner objectives and canonical research-memory ledger.
2. **Knowledge:** use verified public APIs (arXiv, Crossref, Europe PMC,
   OpenAlex, CAS) first. Browse only when there is no suitable structured API.
3. **Browser perception and action:** use official Playwright; as autonomous
   model/tool orchestration becomes reliable, consider official
   [Playwright MCP](https://github.com/microsoft/playwright-mcp) for
   accessibility-aware, high-level interaction with an MCP-compatible agent.
   Alternatively evaluate [browser-use](https://github.com/browser-use/browser-use)
   as an agent framework, but do not install multiple overlapping controllers.
4. **Private sessions:** future separate hosted browser with isolated
   encrypted session storage; no GitHub Actions secret passed to web pages.
   Human logs in by an approved route. Screenshots and DOM can contain private
   information and must not be committed to public GitHub.
5. **Actions:** explicit task scope, allowed sites, cost controls, typed
   per-action approval for messaging, purchases, posting, account mutation,
   deployment and shared files. Implement screenshots, replay and audit
   without exposing private content.
6. **Durable execution:** only later deploy a small authenticated coordinator
   with job queues and ephemeral browser workers. GPU inference can remain
   separate. A persistent research service is distinct from Kaggle notebooks.

Tested browser automation is infrastructure, not AGI and not equivalent to
ChatGPT Work's native browser capabilities.

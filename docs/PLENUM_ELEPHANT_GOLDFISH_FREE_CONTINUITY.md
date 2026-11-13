# Plenum | Elephant–Goldfish continuity and free wakeable workforce

## 12 November 2026 — cross-chat memory gap and free upstream adoption

**Verified incorporation:** a PRIVATE ChatGPT skills plugin named **Plenum Continuity** v0.1.0 was created and read back in the owner's plugin account. Its procedure retrieves the pre-existing private `Plenum Industries | Master Control Ledger` (where connected), checks Conversation Register/Context Protocol, and cross-checks original provider results against older source before proposing actions. The existing Minister skill also now has a mandatory read-first continuity preflight. **This is actionable ChatGPT-side guidance, not a running background ingest, an installation across all chats, or proof of automatic plugin selection.** The founder must install/select the private plugin if needed; ChatGPT selects installed skills contextually, not on every request.

**No needless new dependencies:** Plenum already pins free MIT `langgraph==1.2.20` and `langgraph-checkpoint-sqlite==3.1.3` as optional orchestration dependencies. Reuse those existing thread checkpoint facilities for agent runs, plus the founder-controlled Google Drive master as the private cross-project durable index. A SQLite checkpoint alone is not a searchable shared transcript service; an ephemeral GitHub runner loses local disk unless a supported durable store is explicitly supplied.

**Free and open-source alternatives assessed, not silently installed:**

| Upstream | License / constraints | Decision |
|---|---|---|
| [LangGraph](https://github.com/langchain-ai/langgraph) | MIT; already pinned in Plenum | **REUSE** for existing agents; no duplicate framework |
| [MCP Knowledge Graph Memory Server](https://github.com/modelcontextprotocol/servers/blob/main/src/memory/README.md) | MIT, local JSONL on a persistent private volume, no required model fee | **OPTIONAL** for genuinely local owner-controlled MCP clients; not a ChatGPT-wide memory hook |
| [Mem0](https://github.com/mem0ai/mem0) | Apache-2.0 library; self-host model, embedding and DB requirements vary | **DEFER** until a measured retrieval gap merits extra complexity |
| [Graphiti](https://github.com/getzep/graphiti) | Apache-2.0 temporal graph; requires operated graph DB, embedder and model | **DEFER** unless large, conflicting temporal histories demand graph retrieval |
| [Letta](https://github.com/letta-ai/letta-code) | Stateful full agent platform, with its own runtime/host needs | **NO DUPLICATE ENGINE** alongside Plenum Chief/LangGraph |
| [OpenMemory](https://github.com/mem0ai/openmemory/blob/main/openmemory-archive/README.md) and [Zep Community Edition](https://www.getzep.com/blog/announcing-a-new-direction-for-zeps-open-source-strategy/) | Archived / no longer supported | **DO NOT ADOPT** as a fresh maintained host |

**Access boundary:** No open-source library, custom plugin, or project `AGENTS.md` can force native ChatGPT Memory to import all account conversations or automatically read every Google Drive item. ChatGPT's [own current Memory documentation](https://help.openai.com/en/articles/8590148-memory-in-chatgpt) states retrieval is selective. Keep the master ledger private and use authorized connectors on demand. Reconcile event evidence by `DONE (founder-reported)`, `VERIFIED`, `PENDING`, `OPEN` and `BLOCKED`; preserve superseded history. Do not send personal context to public repository, CI logs or unapproved third-party embeddings.

**Remaining real work:** establish and prove one authenticated read-first execution at the start of a new eligible Plenum conversation/task; do not mark universal future-chat auto-ingestion DONE. For owner-controlled external agents, a private Google Drive OAuth/MCP connection plus durable private storage would be needed before an always-on retriever could read private founder records. Do not buy hosting or promise reliability without direct runtime evidence.
Updated 11 November 2026 — original-source architecture, live project-task evidence separated from new code.

## Founder instruction reconciled
The **Elephant–Goldfish architecture** was previously defined in Plenum as two different jobs, NOT the name of a specific Google product:
- **Elephant**: persistent, dated, searchable memory of founder goals, approved decisions, completed results, sources, assumptions, mistakes, blockers, deadlines and responsible workers. Use original GitHub Issues/docs, appropriate LangGraph checkpoint persistence and approved private storage, not a huge repeated prompt.
- **Goldfish**: independent, fresh-context reviewer. Receives the artifact, claim, source links and acceptance checklist but NOT the original agent's whole reasoning/conversation or self-evaluation. It challenges false confidence, fact drift, repetition, cost and errors. Existing Qwen `agent_council.py` already implements a fresh-context model reviewer.
- **Minister**: original Chief does selection/scheduling; Business Advisor recommends what to do and why. Neither memory nor the reviewer creates an independent always-on worker.
- **Skills**: domain-specific portable procedures loaded only when pertinent, rather than stuffing every role with all skills or full Humanizer Markdown.

## Solution for Oracle A1 Always Free capacity
Oracle's own documentation suggests another availability domain in the same home region (where available), otherwise retry later. There is no promised free-capacity date. Do not upgrade to paid in contradiction of founder's $0 policy.

**Pragmatic first-choice now: the original GitHub issue and workflow event execution.** New work can run promptly as a public project job, then terminate with a record; it does NOT require an AI process sitting idle. Existing public founder issue worker, Chief, council, and weekly reports already prove this model on bounded tasks.

**Second layer:** Cloudflare Workers Free has a no-new-charge *always-reachable HTTPS endpoint* for short event handling (100,000 free requests/day, 10 ms CPU time per request as of October 2026). A Worker can verify a small signed PUBLIC issue ID and invoke GitHub's documented `repository_dispatch`; the existing original project worker wakes, reads the issue from GitHub and skips already recorded completed work. Code and an offline no-model acceptance are prepared in:
- `integrations/cloudflare/plenum-github-wake-worker.mjs`
- `integrations/cloudflare/wrangler.toml`
- `src/plenum_ai/public_issue_wake.py`
- `.github/workflows/plenum-free-public-wake.yml`
No private contents or WhatsApp messages ever cross the PUBLIC repo API; only a previously created public issue number.

**Third layer:** Only when the founder owns/authorizes a Cloudflare account and a narrowly scoped repository-dispatch credential may this be installed. Secrets `PLENUM_WEBHOOK_HMAC_SECRET` and `PLENUM_GITHUB_DISPATCH_TOKEN` stay in the Cloudflare secret store, never in the public repository, requests or ChatGPT. User must deploy within their Cloudflare account with strict Free plan safeguards; source code merged to GitHub is **not** an actual Cloudflare deployed service. The responder cannot run Paperclip, Hermes, a local Qwen model or full private WhatsApp gateway under a 10 ms CPU limit.

An alternative **Google Cloud Run** can scale to zero, offering request-triggered work within free quota (180,000 vCPU-seconds, 360,000 GiB-seconds, 2 million requests per month for request-based billing, subject to allocation/egress). This uses an actual authenticated Google Cloud project and billing guardrails; it is neither free unlimited runtime nor an existing private Plenum agent host. Plenum already has a protected browser service in Cloud Run, but that does not prove a dedicated persistent model host is allocated.

**Cloudflare Queues Free** also became available in February 2026 with 10,000 queue operations/day and 24-hour retention, potentially useful for durable event buffering if the owner actually establishes a Cloudflare account. Do not add a new queue or duplicate original GitHub Issues until message volume/latency justifies it. Cloudflare D1 Free is an optional privacy-scoped state store for future private workflows, not an automatically installed one.

## True constraints and facts
- GitHub standard-hosted runners are free in public repositories for eligible project CI/research, but have a six-hour per-job execution limit; Actions must not be abused as a generic commercial always-on host, CDN or serverless inference farm.
- Scheduled cron events can be delayed or dropped in busy windows. Do not promise instant 24/7 response from periodic GitHub jobs; original issue webhooks and owner-authenticated Cloudflare receive events instead.
- Every original Plenum public worker currently has narrower actual ability than generic AI engineering employees. An owner-authenticated, signed-in browser task remains gated #310, and a no-new-charge always-on VM or a genuinely working private agent host remains gated #384.
- Paperclip and Hermes can be installed on a real allocated owner-controlled machine; do not create a fake permanent host with a GitHub 6-hour sleep loop. Do not connect an unofficial WhatsApp personal number or any private patent, financial or customer record through the PUBLIC repo.
- User controls ChatGPT plugin installation and app access. Official OpenAI guidance says installed plugins are chosen automatically when relevant; explicit `@` mention is optional. A private Plenum Editorial Council plugin already exists; no agent or plugin can guarantee that every future chat follows the saved skill if it is unavailable in that context.

## Skill specialization and correct reuse
`integrations/hermes/roster.json` has 11 names and 13 Plenum role-specific skills plus editorial support. The new `src/plenum_ai/role_skill_router.py` chooses only relevant skills for a stated task (up to three) and cannot create tool permissions. Pinned full Humanizer is now *available on demand* only for Chief, Creative, Marketing, Support, and Founder Business Advisor. Other roles follow appropriate factual/technical standards, not a full large Humanizer prompt. They are not all identical agents.

The Goldfish verifier retains the original `plenum-independent-verification` skill rather than inheriting every skill from the creator. The Elephant stores a durable outcome and its sources, not the original agent's speculation. Each substantive output can be given to Goldfish for a fresh review, then be accepted into Elephant after independent evidence.

## Source references and operational next steps
Official documentation:
- GitHub Actions limits (job six hours): https://docs.github.com/en/actions/reference/limits
- GitHub Actions terms and allowed project use: https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features
- GitHub repository_dispatch API: https://docs.github.com/en/rest/repos/repos
- Cloudflare Worker free limits: https://developers.cloudflare.com/workers/platform/limits/
- Cloudflare HMAC verification: https://developers.cloudflare.com/workers/examples/signing-requests/
- Cloudflare Queue free: https://developers.cloudflare.com/changelog/post/2026-02-04-queues-free-plan/
- Google Cloud Run free pricing: https://cloud.google.com/run/pricing
- Oracle Always Free: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- OpenAI automatic plugin selection: https://help.openai.com/en/articles/20001256-plugins-in-chatgpt
- Anthropic progressive skill disclosure: https://www.anthropic.com/research/equipping-agents-for-the-real-world-with-agent-skills

[ ] Independently verify exact-head CI for event ingress, existing original issue replay guard and role-specific skills before merge.
[ ] Owner creates/selects a genuine Cloudflare Workers **Free** account; check current account quota, and configure only public-task HMAC/dispatch credentials. Do not create paid Workers services or extra storage until needed.
[ ] Actually deploy and prove one signed PUBLIC issue event -> Cloudflare 202 -> GitHub 204 dispatch -> original worker accepted result -> independently checked issue comment; then test duplicate/expired request. Only then mark **FREE EVENT ENTRANCE LIVE**.
[ ] Activate only additional user-authorized Paperclip/Hermes/WhatsApp components for functions which cannot be served by the project-bound GitHub + Cloudflare system.
[ ] Keep all 5 logical workforces and Chief/Business Advisor roles; report accepted outcomes and appropriate costs, not number of catalogued agent prompts.

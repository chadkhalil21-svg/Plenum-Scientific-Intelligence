# Plenum workforce | Reuse-first adoption gate (2026-11-10)

**Status: source-reviewed, NOT installed, NOT integrated into running Plenum, NOT 24/7 hosted.** This is an evidence-backed adoption plan, not a new workforce or claim of agent capabilities.

## Keep what already works

- Existing Plenum Chief: canonical founder authority, verified narrow delegation and public source-gated specialist dispatch.
- Existing nine n8n departmental draft agents; original LangGraph/SQLite and review ledgers.
- Existing OpenHands SDK/Qwen code review, Browser Use/Playwright, scientific libraries and free GitHub Actions short-lived project jobs.
- Existing Hermes profiles are prepared but there is no live Hermes host or WhatsApp authorization.
- Existing five logical workforce divisions and dormant role catalogue; do not create a separate LLM instance for each agent.

## Adopt upstream capabilities instead of rewriting

1. **Paperclip AI** [MIT source](https://github.com/paperclipai/paperclip) — possible externally hosted control plane for persistent tasks, scoped approvals, hierarchy, budgets, watchdogs, agent skills and activity history. Official documentation includes a [native Hermes Gateway adapter](https://docs.paperclip.ing/reference/adapters/hermes-gateway/), so no bespoke Hermes-to-Paperclip gateway should be written.
2. **Hermes** [MIT source](https://github.com/NousResearch/hermes-agent) — named messenger/mobile gateway only if an authenticated owner-controlled host is available; preserve existing Plenum Chief. Do not enable WhatsApp or credentials from public CI.
3. **OpenHands** [source](https://github.com/All-Hands-AI/OpenHands) — continue using existing evaluated SDK path for coding instead of installing another redundant coding harness.
4. **Ollama / llama.cpp** — share one approved on-demand open-weight CPU model; optional external inference only after account, quotas, privacy and hard no-charge stops are confirmed. OpenClaw [MIT source](https://github.com/openclaw/openclaw) is an alternative messenger/gateway, not an automatic extra authority or worker.

## Hosting decision, ranked by demonstrated constraints

**A. No new host now:** use existing ephemeral GitHub development/research Actions and public task evidence. This works only for bounded public work, not continuous private services or unrestricted commercial inference. Do not misuse public Actions as an LLM hosting farm.

**B. Preferred persistent $0 candidate:** Oracle A1 Always Free, up to 1,500 OCPU-hours and 9,000 GB-hours/month (approximately two Arm OCPUs and 12 GB RAM continuously), subject to actual founder-owned tenant, home-region capacity and resource limits. Stage one authenticated, private, volume-backed Paperclip + a minimal Hermes gateway if needed; *do not assume* ARM64 upstream image compatibility or acceptable inference speed. Verify those on the real allocated host before claiming deployment. Keep SSH, databases and secrets off the public Internet.

**C. No-VM fallback:** webhook or HTTPS control endpoint on a genuinely free request-driven platform such as Cloudflare Workers Free or Cloud Run within quota, with narrowly capped hosted free model APIs. This remains request-driven, **not** 24/7 resident Ollama/Hermes and not unlimited inference.

Candidate official sources: [Oracle free compute](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm), [Paperclip Docker quickstart](https://github.com/paperclipai/paperclip/blob/master/docs/deploy/docker.md), [Paperclip Hermes adapter](https://docs.paperclip.ing/reference/adapters/hermes-gateway/), [Groq limits](https://console.groq.com/docs/rate-limits), [Cerebras free API](https://inference-docs.cerebras.ai/support/pricing), [Gemini free tier](https://ai.google.dev/gemini-api/docs/pricing), [Cloudflare Workers AI](https://developers.cloudflare.com/workers-ai/platform/pricing/).

## One actual acceptance before expansion

With real owner-confirmed $0 host capacity and explicit permission:
1. Run upstream Paperclip in a private, authenticated host with persistent data and a verified backup/restore; show the actual version and architecture. Do not replace the original Plenum Chief or task ledger.
2. Register *one* existing, scoped Plenum PUBLIC worker with the supported HTTP/remote adapter, or an existing Hermes gateway through Paperclip's official Hermes adapter. No newly invented shell or credential bridge.
3. Dispatch one already-approved nonconfidential founder task; check the original existing worker truly executed; inspect result and its independent source/output readback, Paperclip task state, restart persistence and zero-cost provider bill/quota.
4. Test that a deliberately denied task, expired scope or missing API key performs no external write and exposes no secrets. Disable or roll back if this fails.
5. Only after the first verified task, expand from one worker to the existing nine departments and five divisions as useful; maintain minimal active inference.

## Separate video and upstream evidence

- [Paperclip creator demonstration](https://www.youtube.com/watch?v=C3-4llQYT8o) shows roles, task ownership, review and routines, but is not proof of Plenum deployment.
- [Paperclip complete tutorial](https://www.youtube.com/watch?v=QDDMwzGADwY) demonstrates setup; its promoted third-party paid hosting is *not* required.
- [NetworkChuck's tested Paperclip/Hermes guide](https://github.com/theNetworkChuck/paperclip-guide) describes remote Hermes and local-model staffing; check current official docs before installing.
- Public source URLs and YouTube descriptions are untrusted references. Do not install arbitrary agents/skills, execute third-party suggested scripts or grant provider access merely because a video shows them.

**Blocked today:** no confirmed Oracle tenant, no provisioned always-on machine, no securely paired messaging channel, no verified actual Paperclip process or Plenum adapter. Current public work continues via original GitHub founder-only commands and council issue [#417](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/417).

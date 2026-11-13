# Plenum Public Wake — Cloudflare Workers Free

## Private continuity records on this SAME Worker — founder request Nov 12

**Existing founder-agent Python client:** \`src/plenum_ai/owner_private_memory_client.py\` signs each GET or POST with the same protocol and uses the already-original Workers URL. It does not introduce a new host. Only instantiate \`PrivateMemoryClient()\` from an owner-approved PRIVATE execution context with the secret injected via the environment (never a public GitHub Actions job or ChatGPT message). Use \`get("american-rider:app-review")\` to read an exact key; for an authorized correction, use \`put(key=..., summary=..., source=..., observed_at=..., level=..., expected_revision=...)\` and then independently read it back. Do not infer success from source creation, avoid duplicating the source-ledger row, and do not send private data to an unconnected agent.



Cloudflare Workers Free already supports **SQLite-backed Durable Objects** that persist between requests (without an always-running VM). To avoid duplicating hosting, this repository adds a SEPARATE *private* Durable Object class \`PrivateContinuityMemory\` to the EXISTING \`plenum-public-wake\` worker. Original \`/health\` and signed PUBLIC \`/wake\` semantics remain unchanged.

This is **optional explicit factual continuity**, not running Graphiti or Mem0, not a ChatGPT account-memory hook, and not automatic ingestion of conversations. Private \`/memory\` and \`/memory/:key\` routes **fail closed with 503** until a distinct \`PLENUM_PRIVATE_MEMORY_HMAC_SECRET\` (32+ random characters) is configured privately through Cloudflare. It must NEVER reuse \`PLENUM_WEBHOOK_HMAC_SECRET\`. The separate \`PLENUM_PRIVATE_MEMORY\` binding points to the new class, isolated from public replay records. Never enable untrusted public writes.

Owner clients authenticate by computing HMAC-SHA256 over \`METHOD + "\\n" + PATH + "\\n" + TIMESTAMP_MS + "\\n" + RAW_BODY\`, with headers \`x-plenum-memory-time\` (Unix milliseconds), \`x-plenum-memory-signature\` (\`sha256=<hex>\`), HTTPS, ±120-second freshness. A GET uses empty body. POST only accepts exactly the bounded object \`{key,summary,source,observed_at,level,expected_revision}\`, where level is one of \`VERIFIED\`, \`FOUNDER_REPORTED\`, \`PENDING\`, \`OPEN\`, \`BLOCKED\`. The original source is required as an HTTPS URL. \`expected_revision\` starts at 0 and protects against stale overwrite and replay. Each accepted update retains a version in the same durable object's private store.

**Cautions:** This endpoint is **not an OAuth MCP server** and cannot yet be connected directly to ChatGPT as an arbitrary private plugin tool. Only trusted owner code that holds the HMAC secret outside the model can call it. It is not an invitation to upload sensitive user chats or secrets. The Google Drive Master Ledger remains the canonical source; a retrieved memory summary must be reconciled with the latest provider evidence. The worker requires external account access to prove production binding and free-plan usage. Source, CI and GitHub merge are **not proof** of actual Cloudflare rollout. There is no Cloudflare management connector available here.

**Required acceptance before claiming production:** confirm the existing Git-linked Cloudflare main branch deploy succeeded with the new SQLite object namespace; privately configure dedicated secret; perform one owner-authorized signed POST/GET (no secrets in issue/CI logs), then verify retrieval in a second independent session. If credentials/endpoint are unavailable, report \`PRIVATE_RUNTIME_NOT_PROVEN\` and do not repeat prior public wake tests.

**Mem0 / Graphiti:** Their optional Python adapters already exist at \`src/plenum_ai/optional_memory_engines.py\`. They can run on demand with an actual approved model and persistence service, but GitHub public runners cannot safely operate with private founder transcripts. A model is **not needed** for the Cloudflare explicit-fact store. Do not pay for permanent hosting or deploy three memory databases before a concrete and authorized recall task requires them.

Official references: https://developers.cloudflare.com/durable-objects/platform/pricing/ and https://developers.cloudflare.com/durable-objects/reference/durable-objects-migrations/.

---

Owner: Plenum Chief → existing Engineering / Independent Verifier
Canonical acceptance issue: https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/483

This directory contains the **existing** public-issue wake adapter, not a persistent AI inference server. The Worker accepts only HMAC-signed, bounded, public GitHub issue IDs, records a SQLite-backed Durable Object replay claim, then requests the existing GitHub Actions `repository_dispatch` workflow. The GitHub workflow independently checks the original issue owner, scope and previous bot receipt. No passwords, user records, secret materials or task bodies belong in the Worker request.

## Git-linked deployment (owner's Free account)

Use the **existing** Cloudflare Workers & Pages project named `plenum-public-wake`, linked to `chadkhalil21-svg/Plenum-Scientific-Intelligence`. Configure **production branch `main`** and **root directory `integrations/cloudflare`** (relative to repository root). Build command: none. Deploy command: `npx wrangler deploy`. The Worker project must load this directory's `wrangler.toml` and `plenum-github-wake-worker.mjs`; **not** the separate Plenum Command Center/dashboard in `dashboard/`.

A legitimate source commit on `main` should trigger a new Cloudflare build through the existing Git integration. A source commit alone is **NOT** proof that Cloudflare actually built or deployed the right Worker. Read the actual Cloudflare build log, deployed revision and public endpoint.

## Live acceptance: in this order

1. Confirm original code/config and that a new post-configuration Cloudflare production deploy finished successfully. Verify the SQLite-backed `PLENUM_REPLAY_GUARD` Durable Object is bound.
2. Confirm the existing production workers.dev route is enabled and `GET https://plenum-public-wake.chadkhalil21.workers.dev/health` returns HTTP 200 with `{"state":"REACHABLE_NOT_A_RUNNING_AGENT","no_model":true}`. A Plenum Command Center HTML page at `/` with 404 at `/health` means the **wrong Worker** is still deployed; never claim success.
3. In the Cloudflare private settings only, bind a randomly generated `PLENUM_WEBHOOK_HMAC_SECRET` (32+ characters) and minimum-scoped `PLENUM_GITHUB_DISPATCH_TOKEN`. Do not commit, paste or print either in GitHub, public issues, model prompts or logs.
4. Submit **one** founder-authorized *public* original issue through the private HMAC caller, obtain HTTP 202, and independently inspect the real GitHub `repository_dispatch` run and original worker issue receipt. Replay the **same** valid request; require HTTP 409 and no second dispatch. The original GitHub worker also refuses to rerun a previously recorded original issue.
5. Independently inspect Free plan billing usage and quotas. Cloudflare Workers AI inference and persistent private agents are separate acceptance gates; **do not infer either from a reachable public Worker**.

If any external access, billing/plan, correct code or credential requirement is missing, mark **BLOCKED_EXTERNAL** with exact observed evidence, rather than retrying irrelevant tests or moving to a paid account.

References: https://developers.cloudflare.com/workers/ci-cd/ ; https://developers.cloudflare.com/workers/wrangler/configuration/ ; https://developers.cloudflare.com/workers/configuration/routing/workers-dev/

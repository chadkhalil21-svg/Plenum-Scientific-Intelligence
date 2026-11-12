# Plenum Public Wake — Cloudflare Workers Free

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

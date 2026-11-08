# Plenum Computer Browser: progress and acceptance ledger

Updated: 2026-11-08 18:18 UTC
Owner: Founder, Plenum Industries
Status: **PARTIAL / NOT WORK-OR-TINYFISH-EQUIVALENT**
Canonical browser-specific, append-only progress record; keep the broader scientific milestones in [LEDGER.md](LEDGER.md).

## Standing mandate

Build Plenum-owned, official Playwright-powered browser operations callable from **ordinary ChatGPT chats**, without dependence on ChatGPT Work or TinyFish: navigation; inspect, click, type; owner-authorized account login and persistent encrypted sessions; files upload/download; running multistep workflows; and approved consequential writes. Computer and Prometheus should share a secure execution engine but use distinct scopes and identity. TinyFish is allowed only as an explicitly temporary bootstrap aid, with cost awareness; it is not a required component in the target design. **Do not claim parity before independent end-to-end verification.**

The founder requires continuous progress awareness: **Before modifying a browser module or deployment, read this ledger and check current source, deployment, CI, and task evidence. After each meaningful change or failed experiment, update this ledger in the same PR or commit, stating exact objective, observed result, blockers, cost/permissions impact, and next action.** Do not mark a task complete because code exists or a mock test passed. Do not reset progress when starting a new chat. The repository, not conversational memory, is the source of truth.

## Current verified capabilities and limitations

| Gate | Current status | Evidence | Exact missing proof |
| --- | --- | --- | --- |
| B1. Actual independent Playwright engine | **Verified** | [Private Sovereign Gateway issue #4](https://github.com/chadkhalil21-svg/Sovereign-Gateway/issues/4), [public issue #188](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/188) | No additional bootstrap |
| B2. Ordinary-chat command transport | **Verified, limited public-site operations** | Private GitHub-owned issue -> Actions -> Chromium -> private issue result; supported navigate/inspect/extract/screenshot, bounded safe GET search, public fill and non-submit button | General direct private MCP transport and protected results |
| B3. Cloud Run IAM-private browser worker | **Verified for fixed public fixture** | [Owner issue #134](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/134), [chat issue #137](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/137) | Owner-specific arbitrary site tools and account sessions |
| B4. Auth0 API and ChatGPT CIMD permission registration | **Registered; not end-to-end operational** | Founder-verified Auth0 API, RS256 and 2/2 read/write delegated scopes, described in [private MCP bridge](COMPUTER_BROWSER_PRIVATE_MCP_BRIDGE.md) | Real owner-bound short-lived bearer and production ChatGPT MCP invocation |
| B5. Cloud Run MCP facade | **Deployed but intentionally IAM-private and disabled** | [Owner issue #160](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/160): signed health 200, no bearer 401 | Separate scoped facade identity, Google-to-worker invoker, Auth0 owner config, secure ChatGPT reachability |
| B6. General click/fill/select/upload action engine | **Source + offline synthetic tests only** | [actions guide](COMPUTER_BROWSER_ACTIONS.md) | Authenticated private production dispatch; real staging origin verification |
| B7. Encrypted owner session store and session UI | **Code merged, not real-login verified** | [PR #194](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/pull/194) | Live deployed owner sign-in, encrypted save/restore/revoke, ownership/expiry checks |
| B8. Secure production network/approvals | **Incomplete** | [private bridge plan](COMPUTER_BROWSER_PRIVATE_MCP_BRIDGE.md) | Egress ACL against SSRF/DNS rebinding, prompt-injection boundaries, signed short-lived approvals, audit and revoke |
| B9. One genuine signed-in site workflow initiated in ordinary chat | **Not verified** | No passing end-to-end account task | Prove authorized login, protected read, explicitly approved write, no leaked credentials |
| B10. Full Work/TinyFish operational parity | **NOT ACHIEVED** | B5-B9 unfinished | Independent scenario suite across multiple real authorized sites and files |

**Current supported ordinary-chat route:** the connected GitHub app calls the PRIVATE `chadkhalil21-svg/Sovereign-Gateway` browser issue workflow. This executes real Chromium, but its allowed traffic is **unauthenticated public HTTPS GET** with no cookies, POSTs, uploads, downloads or account mutations. Task/result visibility is limited to repository collaborators, but do **not** put credentials or confidential account data in GitHub issues. The private repository is not an encrypted browser-session vault.

**Current platform constraint:** A ChatGPT skill/plugin manifest alone is not a native MCP tool. Actual availability of custom write-capable remote MCP tools depends on ChatGPT product/account capabilities; this must be verified from this account, not assumed. Where native connection is unavailable, continue the guarded private GitHub bridge without exposing sensitive session material.

## Remaining completion gates, in dependency order

- [ ] **P1. Private identity path:** verify the already-created keyless `plenum-browser-mcp-runtime` service account *without retrying account creation or broadening project permissions*; bind only necessary resource-specific service invoker, and ensure private worker rejects unauthorized principals. Do not repeatedly redo the completed Auth0 API/CIMD registration.
- [ ] **P2. Owner OAuth evidence:** bind real immutable Auth0 owner `sub` and ChatGPT client ID via server-side secret configuration only; prove issuer/audience/client/scope/expiry and wrong-owner/token-revocation rejection. No passwords, tokens, cookies or identifying private claims in public issues.
- [ ] **P3. Chat-to-MCP transport:** expose only the OAuth-protected facade via approved authenticated HTTPS route; keep machine private; verify a live ChatGPT tool call **if this user's product supports it**. Otherwise keep private GitHub tasks strictly non-sensitive until an equivalent secure tool transport exists.
- [ ] **P4. Production browser actions:** reuse existing Playwright action engine, implement scoped private task/result delivery, browser session binding, timeouts, safe screenshot/DOM outputs, bounded uploads/downloads, idempotency and logging. Never simply turn on unrestricted website writes.
- [ ] **P5. Real owner logins:** live owner-operated sign-in into a non-sensitive staging account; restore encrypted session across a fresh worker and test revocation/logout, isolation, expiration and privacy.
- [ ] **P6. Security and authorization:** enforce network-level DNS/IP/private-address egress restrictions beyond DNS preflight; guard redirects; protect against prompt injection; explicit owner approval per consequential action; test replay/abuse cases.
- [ ] **P7. End-to-end release tests:** from normal chat request through real worker to an authorized staging site, read/update/upload/download with correct approvals and confidential task/results, plus failure, rollback, revoke and budget tests.
- [ ] **P8. Comparison:** run a measured scenario suite for browsing, authentication, files, site writes and unattended multistep operations; only then label the independent tool Work/TinyFish-comparable.

## Rules for every browser change

1. Read this ledger and the real code, deployment and workflow runs before making changes.
2. Record both what passed and what **did not** pass. Use **source only**, **offline verified**, **live verified**, or **blocked**, not vague checkmarks.
3. Add a dated entry with PR/issue/run URL, what changed, observed results, permissions, costs and the next single highest-value gate.
4. Update the appropriate gate row. If browser code or deployment workflows change, update this file in the same PR; CI enforces this.
5. Never expose accounts, secrets, session state or private data through PUBLIC GitHub issue tasks. Do not use broad IAM permissions to bypass a narrow blocker.
6. Keep existing approved OAuth/CIMD setup, the Cloud Run private worker and the working GitHub browser route; do not rebuild functional pieces.
7. After a failed experiment, log the exact failure and what is needed next; avoid repeating it without a changed prerequisite.
8. When ChatGPT returns to this project in another conversation, fetch this file again. Updating a repository cannot guarantee the model will read it unless the next run retrieves it, so this retrieval is part of the workflow.

## Change log

### 2026-11-08: Founder directive and baseline reconciliation

- **Objective:** maintain an always-current browser progress ledger and reach independent Work/TinyFish-class capability from ordinary conversations.
- **Verified from live repositories:** Plenum Scientific Intelligence main contains browser Cloud Run code and an IAM-locked Auth0 MCP facade; PRIVATE Sovereign Gateway contains independently tested chat-to-Playwright public browsing. Plugin metadata was last read as v0.4.6, which remains GitHub-connected rather than a private authenticated browser interface.
- **Source integration (not live verification):** [PR #194](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/pull/194) adds encrypted owner session readback/revocation code. Merging source does not prove a saved real account session.
- **Risk:** complete private authenticated browser and direct ChatGPT MCP tools are still unverified. The earlier five-system list overstates what must be built anew; these are integration, safety and release-validation gates.
- **Money and permissions:** no extra subscriptions or blanket IAM grants are required merely to maintain this ledger. Cloud Run, storage, GitHub private Actions or temporary TinyFish can incur usage charges.
- **Next:** validate the existing dedicated MCP runtime identity and least-privilege bridge, then Auth0 owner-token/transport verification; only after that integrate real session actions and approve a staging-site end-to-end test.

### 2026-11-08 18:12 UTC: owner cloud-account verification; IAM bootstrap **blocked**

- **Objective:** verify the already-created dedicated `plenum-browser-mcp-runtime` and minimally authorize the existing deployer and private worker transport, without changing IAP or exposing services publicly.
- **Live positive evidence:** temporary authenticated browser read-only session accessed Google Cloud Console. The dedicated `plenum-browser-mcp-runtime@plenum-computer-browser.iam.gserviceaccount.com` was visible and **enabled**. Cloud Run service `plenum-computer-browser-mcp` was visible, though its attached runtime and grants were not readable on the loaded page.
- **No verified permissions changed:** temporary Cloud Shell automation attempted exact resource-level IAM operations but returned no success message or policy readback; treat every requested IAM grant as **unverified**, not completed. Do not run repeated cloud permission grants merely because an automation timed out.
- **Independent post-attempt proof:** [Founder issue #200](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/200) triggered the existing [Google WIF preflight run 42508804597](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42508804597). **Live Cloud Run service/worker IAM baseline passed**, meaning no unexpected second invoker was observed; **keyless facade account verification failed**, since the GitHub deployer still cannot independently complete its service-account describe and key-list gate. No service/deployment/permissions were changed by that workflow.
- **Engineering fix in this change:** correct IAM workflow founder result selection so PASS requires all three stages `PREFLIGHT && IDENTITY && VERIFY`. Earlier logic could incorrectly report success if final verification succeeded after a failed identity check.
- **Status:** P1 remains **BLOCKED**, despite owner confirmation that account exists. P2-P8 remain incomplete. No broad IAM changes, additional cloud deployments, remote website account writes or private ChatGPT MCP tools were enabled.
- **Next:** from an authenticated owner environment, verify and grant only exactly scoped deployer `roles/iam.serviceAccountUser` on that one MCP runtime, ensure required service-account metadata/key visibility, and then owner-approved `roles/run.invoker` on the *machine service only* for the facade runtime. Independently verify the resulting policy before any facade runtime deployment. Replace P1 blocked only when real Google IAM output and protected workflow pass.

### 2026-11-08 18:16 UTC: repair preexisting browser tests blocking general CI

- **Actual CI evidence:** [PR #201 general scientific suite](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42509004044) failed for two independently identified browser-specific test defects despite passing targeted MCP identity and browser-ledger checks: optional FastAPI package was absent from the science-only runner, and the facade Docker test still required an obsolete `browser_mcp` filename.
- **Engineering change:** import browser session integration tests only if the separate browser-gateway dependencies exist; **do not skip** those tests when gateway CI actually installs FastAPI/HTTPX/JWT/multipart. Update Docker contract assertion to the actual `mcp_resource_server.py` being copied into the facade image; still prohibit browser/session code in facade.
- **Status:** CI fixes are **source proposed**, not verified until the next full workflow. These repair test configuration; they do **not** enable website logins or change Cloud IAM.

### 2026-11-08 18:18 UTC: continuity and CI repairs live merged

- **Verified release:** [PR #198](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/pull/198) merged the mandatory browser ledger and `AGENTS.md` with the actual [ledger guard CI passing](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42507350583).
- **Verified release:** [PR #201](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/pull/201), merged at `40d37373cd0bd45229769e94c1d41a884c8772da`, passed **five** workflow suites: [scientific foundation](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42509297410), [browser-gateway CI](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42509297463), [mandatory ledger check](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42509297423), [MCP IAM static policy](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42509297981), and [OAuth bootstrap static policy](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42509297413).
- **Private gateway continuity:** [Sovereign Gateway PR #16](https://github.com/chadkhalil21-svg/Sovereign-Gateway/pull/16) merged; the private Playwright source now requires engineers to retrieve and update this canonical ledger. Earlier stale overlapping [PR #197](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/pull/197) closed as superseded by #201, with explanation.
- **Scope of green checks:** source/regression/offline tests passed. **No production OAuth owner binding, IAM facade invoker change, real login restoration, external site write or direct work-like ChatGPT connection was deployed or verified.** Owner subject and issuer-bound live OAuth proof remain absent. P1-P8 must stay uncompleted.
- **Next dependency:** only after exact least-privilege Google service-account visibility and identity/invoker binding are verified should the owner-authenticated MCP facade be connected. Full write-capable ChatGPT MCP tools also depend on the current ChatGPT host/account capability; use working private GitHub public browser functions until that is confirmed.

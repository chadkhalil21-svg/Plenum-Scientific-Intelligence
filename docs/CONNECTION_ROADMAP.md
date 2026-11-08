# Prometheus integration strategy: do not clone everything

**Founder mandate:** reuse proven external engines, APIs and connectors, while
maximizing validated breadth and avoiding duplicated engineering, large bills
or unnecessary access grants.

## Actual status as of 2026-11-07
| Area | Already implemented or verified | Next worthwhile step | Permission/cost |
|---|---|---|---|
| GitHub engineering | Owner repository, Actions, reviewed PRs, public memory ledger | Extend independent benchmarks; protect sensitive environments | Existing access |
| Kaggle GPU | Official API authorization verified #42408852329; **private trial notebook uploaded without execution** via [#42413145594](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42413145594) | In Kaggle, inspect quotas, enable free T4×2 and internet, explicitly opt in to Qwen3.6-27B first inference | Owner API secret exists; GPU runtime is free but quota-limited |
| General web/browser | Ordinary-chat public Playwright [read #66](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/66), [navigation #100](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/100), IAM-only signed /health [#130](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/130), **real IAM-private Playwright fixture read [#134](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/134), and live ordinary-chat → GitHub → IAM Cloud Run → Playwright [#137](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/137)** verified. Computer Browser plugin still lacks private interactive account tools. | Build owner OAuth2.1 MCP facade and private request/response transport with separate invoker identity, approved site sessions, per-action owner review and egress isolation. Fixed new machine workflow only reads public example.com; never publish personal tasks to public GitHub. | Cloud Build/Run can incur charges, unlike a guaranteed free unlimited browser. Public CI subject to GitHub usage policy |
| Journals/science | OpenAlex, arXiv, Europe PMC, Semantic Scholar, Crossref, OSTI, CAS/China-affiliated works, selected lab feeds and research memory | Improve discovery quality, translation, full-text licenses and prospective verification | Public metadata only |
| Science engines | SciPy, RDKit, OpenMDAO, Aviary, Astropy, PyBaMM, OpenMM, PySCF, Lean, and selected evaluated papers | Connect actual method workflows into one end-to-end research question | Pinned isolated runners |
| Reasoning models | Small Qwen/SmolLM and Inspect AI, broader trials planned | Perform real Kaggle 27B quantified inference with matched independent tasks | Limited free GPU quota |
| Voice | LiveKit agent SDK integration has been trialed | Bind STT/TTS model and hosted realtime transport for a voluntary voice conversation | Runtime/audio provider and consent needed |
| Video/creativity | Public NASA YouTube metadata, Openverse, Met and MusicBrainz; original SVG/MusicXML | Add licensed captions/media processing and visual understanding; no blanket scraping | Rights and keys where required |
| Google Workspace | Connectors for Google Drive and Gmail are available in ChatGPT; not automatically installed inside Prometheus | Add OAuth-backed scopes and audit logs only if required for a concrete task | Separate owner authorization |
| Other provider apps | Render, Resend, Stripe and others are available in ChatGPT but NOT general Prometheus credentials | Install one narrow connector per owner-approved workflow, not entire accounts | No financial or communications permission by default |
| Colab / HF ZeroGPU | Evaluated as optional short-running alternatives | Use only if Kaggle quota/compatibility demands | Separate accounts and usage limits |
| Long-running autonomy | Daily scheduled CI research and research-memory ledger | Durable authenticated coordinator, queues, retries, permissions and test harness | Host selected after verified task |
| Computer control | Actual Playwright interaction tests, public navigation, isolated IAM machine `/health` live | Implement private MCP-compatible task gateway, egress restrictions and approved click/fill actions; then verify end-to-end authenticated account task | No silently permitted site mutations or shared cookies |

**Avoid immediately connecting every service:** much of the world is accessible
through public APIs. OAuth tokens, paid subscriptions, persistent cloud servers
and overlapping browsers increase attack surface, not intelligence. Add only
connections that have a tested use, rights to data, explicit operational scope,
and rollback.

The ledger remains the authoritative `research-memory/state/AGI_PROGRAM.json`;
this document is an integration map, not a capability certificate.

## Free-first strategy: avoid unnecessary subscriptions

**Selection rule:** prefer an existing verified public API or local open-source library. Only use a hosted/metered browser agent when the requested website cannot reasonably be handled by an allowed free route and the owner specifically approves consumption.

| Task | Free-first route | Important limit |
|---|---|---|
| Quick public web search in a ChatGPT conversation | ChatGPT native web search; TinyFish Search is currently $0 | Search is not arbitrary clicking, login or form submission |
| Read public webpages / scholarly publications | ChatGPT web, existing arXiv/OpenAlex/Europe PMC/CAS adapters, or TinyFish Fetch ($0) | Full texts and copyrighted research may be restricted |
| Interactive browser in a ChatGPT conversation | ChatGPT Work Cloud Browser *when eligible* | Separate Work mode; available with plan usage limits, not unlimited or necessarily available in standard chat |
| Cloud-browser operations inside Prometheus | Existing pinned Microsoft Playwright / Playwright MCP in public GitHub Actions | GitHub CI is short-lived; the present MCP gateway only reads a fixed public example; it is **not yet** model-directed arbitrary browsing |
| Scientific monitoring and research briefings | Existing scheduled GitHub workflow and owner daily research reminder | A public feed is not a verified scientific discovery; standard Actions free in public repositories subject to GitHub policy |
| Model benchmarking | Kaggle quota-limited T4×2 and existing Inspect AI evaluation | Official source model weights and 19.1 GB quantization still require free compute quota and actual inference |
| Voice / online account operations | Open-source libraries, selectively integrated | Audio hosting, persistent credentials and managed real-time providers may have costs |

**TinyFish wallet:** $8 was credited on account creation, not an $8 invoice. Current confirmed account rates (Nov 7, 2026): Search and Fetch $0; Agent $0.016/step; Browser $0.002/min; Monitor $0.005/check plus free search/fetch; Deep Research $2/run; Max Research $3/run. Auto-reload unconfigured, no pending top-up. This platform is **not needed** for the existing Plenum Playwright + GitHub CI research workflow.

**Prevent accidental costs:** do not enable TinyFish Agent/Browser/Research/Monitor for routine scientific scanning or conversational questions without a separate owner-approved task and a cost limit. Do not install duplicate browser controllers (browser-use, Stagehand, another MCP) until a measured reliability/capability gap justifies replacement.

**Provenance:** [Kaggle draft upload run](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42413145594); [Playwright MCP proof](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42412389018); [LangGraph + MCP proof](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42412589718).

### Next gates, not yet complete

1. Open private Kaggle trial notebook and manually set `APPROVE_FREE_GPU_RUN=True` after checking T4×2, reported scratch disk, quota and Internet. Run to produce `prometheus_free_cloud_report.json`. This smoke check is not AGI.
2. Preserve actual model revision, GGUF hash, runtime provenance, timing, memory and outputs, including negative or inconclusive results. Independently score held-out general tasks using the **existing** Inspect AI framework instead of writing another evaluator.
3. Only then connect an evaluated model to the **already verified** guarded LangGraph → Playwright MCP pipeline for read-only tasks. Add private sessions and account-changing actions after independent reliability evidence, per-action approval, and approved budget.
4. Stage continuous coordination and durable private memory separately from temporary Kaggle or CI runners. Do not describe scheduled GitHub Actions as full 24/7 AGI.

**AGI has not yet been demonstrated.** No completion percentage is scientifically supported by these subsystem tests.

### Verified Computer Browser machine connection (2026-11-08 UTC)

- **Done:** owner-scoped GitHub WIF → short-lived Google identity token → private Cloud Run IAM → FastAPI. Signed `GET /health` returns 200 and anonymous request is denied ([production owner issue #130](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/130)); [PR #129](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/pull/129) built and released the immutable image. Original IAP owner service untouched.
- **No longer required for this machine connection:** troubleshooting the human Google IAP OAuth error 9, reconfiguring Google OAuth clients, sharing service-account keys or starting paid TinyFish login sessions.
- **Still not done:** the personal ChatGPT plugin currently advertises public web read and bounded public navigation via GitHub; it does **not** provide interactive private Cloud Run tools in ordinary chats. The machine runtime does not have website cookies, persistent user sessions, or an app credential for private browser endpoints. Authenticating to Cloud Run is not the same as authorizing third-party website changes.
- **Efficient next gate:** reuse existing Playwright engine and `services/computer_browser` request schemas; design a private, owner-bound tool channel and only implement audited read-only first, then permit owner-approved high-impact actions and secure session storage. Never route personal task content through the public GitHub repository.

### Chat-to-IAM machine browser demonstration, 2026-11-08
[Owner issue #137](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/137) proves a chat-created owner event triggered GitHub's short-lived WIF credentials, privately authenticated to the machine service, executed Microsoft Playwright against the fixed **public** `example.com` fixture, and returned a sanitized PASS. It does not mean ChatGPT has direct private MCP tools, private browser sessions or permission to submit on unrelated websites. The [private OAuth MCP bridge contract](COMPUTER_BROWSER_PRIVATE_MCP_BRIDGE.md) defines those remaining requirements; the human Google IAP error 9 is no longer relevant to this machine-only path.

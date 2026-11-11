# Plenum five workforces | Platform integration map and commissioning checklist
Source-checked: 11 November 2026 | **DESIGN & ORIGINAL SOURCE INTEGRATION; no new cloud accounts or running third-party hosts**

## Founder-visible chain
Founder
  -> **AI Minister of Operations** (proposed user-facing name; preserve existing `chief` internal code)
  -> 1. Scientific Research (`research`, `simulation`)
  -> 2. Engineering & Manufacturing (`engineering/coding`, `creative`)
  -> 3. Commercial Operations (`operations`, `marketing`, `support`)
  -> 4. Global Intelligence (`research`, `browser`)
  -> 5. Verification & Advisory Council (`verification`)
  -> Cross-functional **Business Advisory Council** (operational and verification perspectives, NOT a sixth executable workforce).

**The same named profile may serve multiple logical departments.** Ten Hermes role definitions include Chief plus nine types; running agent count must be separately observed. Run `python -m plenum_ai.workforce_directory` to derive the display and `--json` for the source-backed machine-readable directory.

## Give each platform one distinct job — use ALL without duplicate authority

| Layer | Plenum component | Role | State and real acceptance |
|---|---|---|---|
| Founder task ledger & evidence | **Existing GitHub** | Single canonical public issue queue, source control, exact-head PR checks, dated outputs | **Live limited**. Public Issues only; private tasks elsewhere |
| Agent reasoning / hierarchy | **Existing LangGraph + Deep Agents** | One Chief delegates specialist tasks; checkpoint when tool/task really supports it | **Live bounded**. Reuse original `chief_team_mission.py`; no second Chief |
| Fixed business processes | **Existing n8n** | Scheduled reviews, deterministic data handling, approved workflow nodes, draft queue | **Source-configured**. Manual example is not evidence of always-on host |
| Organization dashboard | **Paperclip** | Assign tasks, goals, budgets, agent runtimes, approvals, run evidence | **Source-reviewed only**. Requires authenticated persistent host; use upstream adapter |
| Named agent personas + messaging | **Hermes Agent** | Named `chief`, `research`, `coding`, etc., with profile-scoped skills and eventual WhatsApp Chief | **Profiles prepared only**. No connected WhatsApp, no running gateway |
| Additional agent/channel executor | **OpenClaw** | Optional external agent under Paperclip with a separate business-specific tool/channel need; do not run another Chief or second WhatsApp login | **Candidate only**, no running service |
| Computation | Shared **Ollama / llama.cpp** | One local budgeted on-demand model, not one per role; optional approved rate-limited free hosted API | **Ephemeral bounded existing**, persistent model not confirmed |
| Browser | **Plenum Computer Browser / Playwright** | Approved site tasks, saved state in original encrypted owner-only vault, explicit task-specific write scopes | **Protected Cloud Run live bounded**; signed-in third-party acceptance missing |

## Adoption sequence, exact practical gates

### NOW — no new host or account
- [x] Reuse existing exact-title founder issue triggers. A public issue containing an attractive but mismatched title **does not dispatch any agent**. Supported examples: `[Plenum Workforce] public research` with `PLENUM_PUBLIC_WORKFORCE_V2` 3-line envelope; `[Plenum Chief] public mission` with `PLENUM_CHIEF_PUBLIC_MISSION_V1` 2-line envelope; `[Plenum Council] public agenda` with `PLENUM_COUNCIL_PUBLIC_V1` 2-line envelope.
- [x] Account for all five logical workforces and the original ten Hermes role definitions; distinguish shared roles from live runtime counts.
- [x] Reuse original public council and add four domain-specific **business advisory** reviewer perspectives without granting business-account access.
- [ ] Independently inspect real artifacts, actual accepted content, and a dated founder decision. A source count is NOT a full fact-check.
- [ ] Audit all outstanding non-triggering planning issues: #428–#432; link to actual runs, do not mark completed merely for creating an issue.

### FIRST HOST (requires owner-confirmed genuine no-new-charge persistent compute)
- [ ] Verify an allocated Always Free instance or another owner-approved persistent free host, architecture, storage persistence, recovery, access control and zero-billed statement. Existing OCI issue #384 remains owner tenancy/capacity gate.
- [ ] Pin current official upstream versions and inspect ARM64 builds before installing; do not pull arbitrary mutable images into production or assume an account exists.
- [ ] Deploy **one authenticated Paperclip** instance on founder-controlled host, with storage backup, one company and five logical reporting groups; do not migrate or duplicate GitHub's canonical public issue history until a verified integration exists.
- [ ] Connect ONE original public worker using the official Paperclip HTTP/agent adapter and do a real job: assigned -> execute original Plenum worker -> independent readback -> visible accepted output -> survives restart -> no overage. No private customer or patent records in trial.
- [ ] Install **one Hermes gateway** and enable only Chief plus one specialist, after owner approval; verify model and profile state, stop and restart. Prefer official Paperclip Hermes adapter; no custom bridging where unnecessary.
- [ ] If OpenClaw supplies a distinct tool/channel unavailable through existing Hermes/Plenum Browser, register it as a **specialist** through Paperclip's native OpenClaw adapter, with narrow permissions. Do not duplicate the WhatsApp channel or main Chief.
- [ ] Import approved n8n drafts into that owner's private instance; connect only authorized sources. Verify one end-to-end founder review with a genuine input and real output; keep private data private.
- [ ] Adopt useful LangGraph supervisor/tutorial patterns only where needed for checked multi-step tasks, rather than adding an unrelated second framework.

### WHATSAPP (separate first-party authorization)
- [ ] Select supported **WhatsApp Business Cloud API** DM for a stable official business deployment, with a dedicated approved number and verified webhook and provider quotas. Its DM limitations are honest.
- [ ] **Literal WhatsApp group** with a bot: current Hermes Baileys bridge is unofficial and risks account restrictions. Use only a separate expressly owner-approved account, never a personal account paired without specific consent; keep group and participant allowlists with @mention.
- [ ] If eligible Meta WhatsApp Agent Platform beta is actually visible, assess its third-party-agent DM route independently; do not claim group support or universal rollout.
- [ ] Do not connect *both* Hermes and OpenClaw to the same WhatsApp identity. An OpenClaw worker may instead be invoked behind Hermes's single outward messaging gate.
- [ ] Prove a real message, correct agent handoff, real task, reply, and independent event readback. Only then mark live.

### WEEKLY OPERATING STANDARD
Minister reports: goals; five workforces; real completed and independently accepted tasks; failed/incomplete; cost and use of quotas; blockers requiring founder; business advisory recommendations with validated citations; next accountable action. Do not mark pending implementation as RUNNING.
The outcome is the work, not the number of agent profile prompts.

## YouTube examples reviewed as *demonstrations*, not deployment proof
- [LangChain hierarchical multi-agent supervisor (12 February 2025)](https://www.youtube.com/watch?v=B_0TNuYi56w): supervisor/handoff patterns. Existing Plenum Chief already does bounded delegation.
- [AI Foundations n8n agent course (31 January 2025)](https://www.youtube.com/watch?v=ZbIVOy_GPyQ): triggers, tools, memory, specialist subagents. Map them onto current n8n roles.
- [Nate Herk multi-agent n8n swarm (25 July 2025)](https://www.youtube.com/watch?v=vpyllOeLhs4): parent agent and child agent tools; emphasizes when not to use multi-agent patterns.
- [Paperclip upstream creator demonstration](https://www.youtube.com/watch?v=C3-4llQYT8o): org/task/agent management, hosting/inference not included.
- **No video alone authorizes third-party installer execution, free billing assumptions or account permissions.**

## Official product/documentation references
- Paperclip source and truthful runtime limits: https://github.com/paperclipai/paperclip
- Paperclip bring-your-own worker adapters: https://github.com/paperclipai/paperclip-docs/blob/main/docs/how-to/bring-your-own-agent.md
- Hermes Bot Mode (named profiles and group chats): https://hermes-agent.nousresearch.com/docs/user-guide/bot-mode
- Hermes WhatsApp, official API comparison and Baileys account risk: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/whatsapp
- LangGraph multi-agent patterns: https://docs.langchain.com/oss/python/learn
- n8n open source: https://github.com/n8n-io/n8n
- U.S. SBA/SCORE advisory resources: https://www.sba.gov/counseling/local-assistance/resource-partners/
- Plenum original verified artifacts: issues #310 (browser), #381 (two-worker mission), #384 (host), #433 (fresh public research), #435 (fresh two-worker mission).

## No false-live milestone
Adding these source-based files is **not** installing Paperclip, OpenClaw, or Hermes, not starting a private always-on model, not registering a WhatsApp account, not creating licensed human advisors, and not completing business-account access. The actual free persistent host and signed-in third-party authorizations remain the execution gates.

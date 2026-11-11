# PLENUM AI ORGANIZATION — WORKFORCE & BUSINESS ADVISORY MASTER LEDGER
Version: 1.0 | Prepared: 2026-11-11 | Steward: Founder / existing Plenum Chief | Classification: PUBLIC-ONLY operating plan
Purpose: A single operational checklist for existing agents. This ledger does not grant credentials, authorize spending, install agents, or prove a task was executed. The canonical truth is source plus separately observed run/output, not a checkmark.

## Decision and definitions
- **Agent**: a configured worker with a role, model/inference access, instructions, allowed tools, scoped memory, task input/output, cost ceiling, and evidence of successful execution. A named prompt, indexed persona, source repository, or model is NOT by itself an active agent.
- **Workforce**: a logical department containing a lead/supervisor, one or more executable specialist roles, queue, tools, decision boundaries, accepted deliverables, and status reporting. A logical registry entry need not mean permanently running staff.
- **Chief**: existing central dispatcher; connects founder objectives to registered workforce roles. Use event-driven work and ephemeral execution where feasible, not 24/7 occupied inference.
- **Business Advisor**: proposed cross-functional advisory agent/council, coordinated by Chief, with planning, operations, finance, commercial, regulatory/IP-risk *review perspectives* and clear human decision authority. Simulated perspectives are not retained or licensed professional counsel.
- **Completion standard**: a real independently inspectable artifact and acceptance note, with limits disclosed; drafting, comments, source-only integration, and CI do not count as private business execution.

## Live baseline (source checked 2026-11-11)
Existing integrations/workforces/five-workforces.json identifies **five logical workforces**, not five persistent executable departments:
1. Scientific Research — research + simulation; bounded public research/scientific tooling; GitHub Actions ephemeral.
2. Engineering & Manufacturing — engineering + creative; two-worker public code/artifact mission verified in issue #381; GitHub Actions ephemeral.
3. Commercial Operations — operations + marketing + support; n8n draft workflows and public health audits; NOT an autonomous private business operator.
4. Global Intelligence — research + browser; public intelligence/radar; GitHub Actions ephemeral.
5. Verification & Advisory Council — verification; limited public/advisory output; NOT professional expert review.
Source catalogue: 35 reviewed references, 283 idle agency persona prompts, 1,106 media metadata records; these are **not working agents**.
Existing protected Computer Browser Cloud Run release: 00041-8q7 confirmed in docs/COMPUTER_BROWSER_PROGRESS.md and issue #310; owner controls, encrypted same-site state, bounded no-replay navigation. Signed-in third-party three-action acceptance, general model-directed recovery, live ChatGPT private browser control remain unverified.
Oracle Always Free host: candidate only, not provisioned; issue #384. Existing Render command center is static, not an always-on agent server.
Do not invent a team size, account access, running gateway, autonomous capabilities, or free model capacity.

## Recommended architecture (reuse before adding)
Founder -> existing Chief of Staff -> five existing workforces; add a **Business Advisory Council** as a capability spanning Commercial Operations and Verification, NOT a sixth persistent workforce until actual execution warrants it.
Chief uses one task queue (existing GitHub issues for public work; a separate permissioned/private store for sensitive business records), priority and due date, task ownership, deterministic workflow for fixed steps, agent reasoning only when ambiguous, and evidence-based readback.
Each workforce has: lead, agents by skill, executable task adapters, approved tools, memory/knowledge scope, task queue, review policy, budget, output standard, and daily/weekly scorecard.
Every worker/job card: mission; job owner; input provenance; permissible tools; permissions; budget/timeout; deliverable; proof/acceptance condition; next action or blocker.
Every task should have a single accountable lead; reviewers must not self-certify their own unverified drafts. Do not repeat completed smoke tests. Limit retries and stop when inputs/host permissions are missing.
Control plane: keep the original Chief/GitHub/n8n architecture. Assess Paperclip as an optional control dashboard AFTER an actual persistent host is available; Paperclip manages agents but is not an inference host. Assess Hermes Bot Mode or OpenClaw for named chat interfaces AFTER a connected, persistent gateway exists. Do not deploy all three overlapping managers.
Use shared local Ollama/llama.cpp inference if hardware permits, otherwise *explicitly opted-in* free-tier model providers within hard limits; free source code != free compute, hosting, or unlimited calls.
Founder remains approver for external sending, irreversible account changes, filings, material cost, contracts, investment decisions, public patent disclosures, and sensitive access. Public GitHub contains **no credentials, confidential research or correspondence**.

## BUSINESS ADVISORY COUNCIL — charter
**Mission:** Proactively convert verifiable business facts into concise founder decisions and delegate approved execution to suitable workforces.
**Council seats** (logical perspectives; can share one model/runtime):
- Chief Business Advisor / Operating Lead: integrates recommendation, prioritization and follow-through.
- Strategy & Commercialization: markets, competitive positioning, commercialization milestones, customer discovery, pricing.
- Finance & Capital: forecast, cash runway, unit economics, funding alternatives, budget variances; only when granted private financial data.
- Operations & Delivery: weekly priorities, process bottlenecks, product readiness, owner dependencies, KPI dashboards.
- Partnerships & Funding: public grants/sponsors, deadlines, eligibility, university collaboration tasks, outreach drafts.
- Legal / Regulatory / IP Risk Reviewer: flags questions for qualified counsel; never claims to be the user's attorney, accountant or regulated adviser.
- Independent Verification: validates citations, calculations, contradicting evidence, and accepted output; challenges proposed action.
**Input tiers:** Tier A: public institutional and company sources only (available now). Tier B: connected private Drive/email/business data in authorized private workspace (not public issue or logs). Tier C: financial, customer, contracts, patents only with separately scoped permissions. No tool or agent may treat a public issue as permission to retrieve Tier B/C.
**Required answer format (one-page founder brief):** Business objective; 3 material facts with citations and as-of dates; decision sought; recommended action; 1–2 alternatives; owner and due date; forecast cost/expected benefit with uncertainty; risks/questions for professional counsel; accepted evidence or explicit unverified status.
**Cadence:** daily short exception report; weekly priorities and KPI/finance review; monthly strategic review. These cadences are planned, not yet provisioned or active.
**Pilot:** public-only assessment of Plenum's agent labor model and the comparative usefulness of a central Chief; deliver one ranked practical recommendation without invented financial data. Next private pilot only after approved connection.

## MASTER ACTION CHECKLIST — ordered by dependency
| ID | Priority | Lead | Task | Acceptance / done evidence | Current state |
|---|---|---|---|---|---|
| A01 | P0 | Chief + Verification | Inventory executable agents vs source-only personas vs logical workforces | Dated machine-readable roster with last real outcome; no inflated agent counts | OPEN |
| A02 | P0 | Chief | Keep one canonical founder queue; label priority, owner, blocker, accepted output and source | At least one real multi-worker mission created, outputs linked and independently evaluated | PARTIAL (issue #381) |
| A03 | P0 | Engineering | Preserve and use existing GitHub Actions task adapters, n8n drafts and browser, no rebuild | Can route a new public task through original Chief using original runner | PARTIAL |
| A04 | P0 | Browser + Verification | One owner-approved real signed-in website task with 3 substantive actions, account-specific readback, safe recovery | Original issue #310 closed only after genuine independent proof | BLOCKED: needs real owner session/task |
| A05 | P0 | Engineering + Founder | Confirm real $0 persistent hosting option with explicit quota and idle/reclaim behavior | Host exists, runs original gateway, restarts, and produces private status, at $0 billed | BLOCKED: issue #384 owner account/capacity |
| A06 | P0 | Business Advisor + Council | Establish business advisory charter, public-only pilot recommendation, proof of review | Dated concise recommendation with sources, one actual next action owner, independent acceptance | PLANNED |
| A07 | P0 | Verification | Enforce outcomes across every task: evidence, decision, bounded retry, status | One failed/unrelated model draft correctly marked unaccepted; no false VERIFIED | PARTIAL |
| A08 | P1 | Chief + Commercial Operations | Build weekly founder operating brief from authorized sources | Decision queue, deadlines, cash/risks only when lawful input is available; no invented private values | PLANNED |
| A09 | P1 | Commercial Operations | Business scorecard: revenue, burn, cash runway, pipeline, conversion, product milestones, blockers | Data dictionary, source and as-of date for every metric; missing data labelled unavailable | PLANNED |
| A10 | P1 | Finance advisory | 13-week cash forecast and budget vs actual in private workspace | Founder-approved financial data; reconciled statement; no public financial figures | BLOCKED: source authorization |
| A11 | P1 | Strategy + Intelligence | Market/customer and competitor briefing with links and freshness | 1 ranked business opportunity / hypothesis and evidence | PLANNED |
| A12 | P1 | Partnerships/Research | Grant and partner opportunity monitor | New dated lead, eligibility and award route, next action; no automated submission | PARTIAL (issues #428/#429) |
| A13 | P1 | Chief + Communications | Named-agent conversational interface, ideally WhatsApp group by mention | One permitted end-to-end message -> role -> bounded task -> reply; separate group vs DM scope | BLOCKED: 24/7 gateway + WhatsApp setup |
| A14 | P1 | Engineering | Assess Paperclip vs existing Chief control plane, avoid duplication | Decision memo: which existing gap it solves, additional host/storage cost, migration/no migration | PLANNED |
| A15 | P1 | Verification | Agent quality metrics: jobs accepted/rejected, median time, cost/job, blockers, error types | Weekly source-linked scorecard; measurements not self-claims | PLANNED |
| A16 | P1 | Founder + Commercial Ops | Connect only authorized app accounts for approved business operations | Verified scoped read of a real private task via private endpoint; no secret in GitHub | BLOCKED: account consent |
| A17 | P2 | Engineering | Optional n8n schedules/sub-agents/Bot Mode, only if existing runtime can host them | Actual low-cost resumed task with checkpoint and correct end-state | PLANNED |
| A18 | P2 | Chief | Scale number of working roles from demonstrated demand, not prompt-library count | Incremental agent adds net positive accepted tasks per cost and supervision | DEFER |
| A19 | P2 | Council | Monthly strategy/policy/IP-advisory review with external professional referral as needed | Approved brief and action register; no false claim of regulated professional signoff | PLANNED |
| A20 | P2 | Founder + Chief | Promote from five logical workforces to genuinely staffed operating departments | Verified recurring tasks, accountable owner, report, cost, and permission per department | NOT YET |

## Immediate delegation, without repeating previous failed model experiments
1. Existing **Scientific Research / Global Intelligence**: produce a source-linked public study of 3–5 useful agent workforce patterns and their advantages for small-team industrial R&D and business operations. No account data.
2. Existing **Engineering**: prepare a *reuse-first*, implementation-gap inventory; prove any claimed improvement against original repository paths and real working adapters. No speculative installs, no old 7B coder retries.
3. Existing **Commercial Operations**: produce a private-ready business KPI dictionary and public-only operating brief template; do not request financial statements through public GitHub.
4. Existing **Verification Council**: review the public source evidence, contest optimistic ROI claims, distinguish accepted from simulated advice, reject unusable drafts.
5. **Chief**: consolidate independently accepted outputs into this ledger with a named next action, rather than generating more workers to look busy.
6. **Founder-only gates**: one authentic site/login (A04), one $0 host account/capacity confirmation (A05), scoped private app permissions (A10/A16), and WhatsApp account pairing (A13). Never bypass MFA, consent, published platform rules or export secrets into public repositories.

## Sourcing and comparative findings (retrieved 2026-11-11)
- Microsoft Agent Framework (official): use an agent for open-ended reasoning, a deterministic workflow for well-defined steps; if a normal function suffices, avoid an agent. https://learn.microsoft.com/en-us/agent-framework/overview/
- LangGraph (official) and LangChain video: supervisor/hierarchical patterns, state persistence, tool-based handoffs. https://www.langchain.com/langgraph ; https://www.youtube.com/watch?v=B_0TNuYi56w ; https://www.youtube.com/watch?v=4oC1ZKa9-Hs
- n8n (official): agents can have model, tools, memory, sub-agents and schedules; existing flows must be inspected before adding new ones. https://github.com/n8n-io/n8n-docs/blob/main/docs/build/build-and-manage-agents.md ; tutorial https://www.youtube.com/watch?v=geR9PeCuHK4
- Paperclip (official): organizational goals, org chart, heartbeat-scheduled agent work, task budgets, status; control plane NOT a compute entitlement. https://github.com/paperclipai/paperclip ; https://docs.paperclip.ing/guides/org/agents/
- Nous Hermes Agent (official): Bot Mode, named bots, group mentions and messaging gateway. https://hermes-agent.nousresearch.com/docs
- OpenClaw (official): WhatsApp group allowlists, mention-triggering, scoped sessions. Such a channel needs a separately installed gateway and account-linked access. https://docs.openclaw.ai/group-messages
- US SBA (official): operational management calls for bookkeeping, cash flow/financials, marketing, compliance and measurable plan reviews; AI should not replace qualified professional advice. https://www.sba.gov/counseling/manage-your-business/ ; https://legacy.sba.gov/business-guide/plan-your-business/write-your-business-plan
- YouTube demonstrations show architectures and examples, not evidence that Plenum has deployed them. Dates and product capabilities can change; confirm upstream before installation.

## Operating review / provenance
Update only after checking live source, run, and independently readable output. Status vocabulary: OPEN / PLANNED / PARTIAL / BLOCKED / DEFER / VERIFIED. A model-generated draft is DRAFT (never VERIFIED).
Always include evidence links and as-of dates. New source records should distinguish verified deployment, workflow check, public demo, or proposed design. Avoid repetitive tests already accepted in issues #310, #381 and #384.
Canonical prior evidence:
- https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/blob/main/integrations/workforces/five-workforces.json
- https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/blob/main/docs/COMPUTER_BROWSER_PROGRESS.md
- https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/310
- https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/381
- https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/384
- https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/428
- https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/429

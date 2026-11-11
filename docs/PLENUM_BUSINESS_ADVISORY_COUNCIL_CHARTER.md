# PLENUM INDUSTRIES | AI Business Advisory Council Charter
Status: Founder-facing operating design, public-only pilot | 11 November 2026

## Authority, nature and objective
This **AI Business Advisory Council** is an internal, *non-statutory* consultative and analytical function supporting the Founder/CEO. It is **not** Plenum Industries' legal Board of Directors, does not create corporate officers or fiduciary duties, does not pretend the four model-generated lenses are retained human professionals, and does not authorize transactions. Final business decisions and legally required corporate governance remain with duly authorized humans.

Design grounded in (a) MIT Orbit entrepreneurship guidance distinguishing formal board composition, conflicts and industry expertise; (b) Stanford GSB work on the responsibilities of actual company boards; (c) SBA/SCORE models of individual and multidisciplinary mentoring for small businesses; and (d) evidence-gated review common to research and financial management. The **AI** implementation is Plenum's adaptation, not an MIT/Stanford-accredited board.

## How the council is structured (minimum useful implementation)
**Founder** -> **AI Minister of Operations** (proposed public-facing alias; existing technical `chief` stays intact) -> two cooperating functions:
1. **Commercial Operations**: owner of operating facts and proposed business actions.
2. **Verification & Advisory Council**: fresh-context challenge, fact checking and competing hypotheses.

The existing public council `src/plenum_ai/agent_council.py` now chooses four focused deliberation lenses **when an owner-public agenda contains 'business advisory' or 'business operations'**:
- **Operating Lead / COO lens:** priorities, bottlenecks, responsible workers, execution dates, accepted outcome.
- **Finance & Capital / CFO lens:** cash flow, revenue assumptions, funding paths, cost and 13-week cash planning *only from authorized, reconciled private records in an appropriately private environment*.
- **Strategy & Markets lens:** customer problems, differentiation, markets, price and measured experiments.
- **Governance / Risk lens:** risk register, IP and contract questions for qualified counsel, conflict-of-interest and disclosure checks.

An independent fresh-context reviewer critiques all four outputs. The existing model does not automatically fetch university papers, banking or legal records, so the council's public model drafts **do not count as independently verified advice**. A separate research worker verifies any external facts and citations. One shared model may serve different seats sequentially; do not confuse four perspectives with four autonomous employees.

## Standard of business advice
Each report must be a concise decision memo:
1. **Decision required**, with founder objective and date.
2. **Evidence table:** fact, primary source URL, as-of date, confidence and limitations; private evidence cited only in authorized private workspace.
3. **Recommendation and two real alternatives**, including *do nothing* when appropriate.
4. **Financial consequence** with sources, assumptions, costs and sensitivity; if unavailable write **unknown**.
5. **Next 7 and 30 days:** owner, output, due date, acceptance method and dependencies.
6. **Independently reviewed risks:** legal, regulatory, customer, security, science, funding, execution.
7. **Approval gate and monitoring:** recommend/draft vs founder-approved execution vs accepted output.

## Scope of continuing operations
- **Daily, only when an actual schedule/host is active:** exception report on deadlines, failures and blockers, not generic brainstorming.
- **Weekly:** five-workforce progress, commercial opportunities, grant pipeline, finance from authorized records, forecast changes, top three choices.
- **Monthly:** strategy, pipeline economics, business model, customer validation, enterprise risk and research portfolio priorities.
- **On demand:** public-source proposal review, business correspondence drafts, funding diligence, partner due diligence and decision options.
- **Output state:** `DRAFT`, `SOURCE_VERIFIED`, `FOUNDER_APPROVED`, `EXECUTED`, `INDEPENDENTLY_ACCEPTED`; never jump from draft to executed.

## Specific existing Plenum applications
1. **American Rider:** if company permissions are separately granted, cash collection, pricing/unit economics, review or release blockers, customer/partner acquisition and compliance planning. Until then use only genuinely public facts.
2. **Plenum Terra:** public funder/program eligibility, original scientific milestone gates, institutional partner budget scoping; never publish unpublished IP or private correspondence.
3. **Plenum AION:** customer discovery among infrastructure owners, validation milestones, commercial procurement path; distinguish experimental claims from verified measurements.
4. **Workforce itself:** actual accepted jobs per inference cost, idle count vs operational worker count, failed attempts, delegated tasks, host cost, blockers and time saved.
None of these project use cases establishes new access to financial, customer or patent material.

## Institutional basis and source hierarchy
Primary references (consult current versions when acting):
- MIT Orbit — founder boards and their responsibilities: https://orbit-kb.mit.edu/hc/en-us/articles/211583446-What-should-founders-consider-in-developing-a-Board-Of-Directors/
- MIT Orbit — necessary board competencies and conflict awareness: https://orbit-kb.mit.edu/hc/en-us/articles/205240613-What-are-the-necessary-components-of-the-board/
- Stanford GSB — directors in entrepreneurial ventures (actual corporate board, *not* an AI council): https://www.gsb.stanford.edu/faculty-research/case-studies/note-boards-directors
- U.S. SBA — SBDC and SCORE resource partners, financial management and operational advising: https://www.sba.gov/counseling/local-assistance/resource-partners/
- SCORE — actual advisory board model, a multidisciplinary group of human mentors (specific program may charge): https://www.score.org/ny/new-york-city/score-advisory-board/
- SCORE — free one-to-one mentoring vs separate paid programs: https://www.score.org/score-faqs-business-mentoring-resources-support/
- Existing Plenum document editorial hierarchy: Google Drive 'Plenum Industries | Document Production Standards Ledger' (private, do not copy into public repo).

## Boundaries and sign-off
- An AI advisory perspective is **not** a licensed lawyer, CPA, investment adviser, physician or the human it references.
- Corporate board minutes, shareholder/board approvals, intellectual-property filings, grant submissions, taxes, contracts, and external correspondence need appropriate authorized human review and permissions.
- Public GitHub issues, model prompts, Qwen logs and WhatsApp groups must not contain customer data, banking records, access tokens, unpublished patents or confidential correspondence.
- A founder may authorize particular private tool reads in a private environment. That decision is not inferred from this public charter.
- Never imply '24/7 live advisor' until persistent host, model, schedule, state, and independently verified real delivery exist.

## First pilot
1. File exact two-line issue `[Plenum Council] public agenda` with marker `PLENUM_COUNCIL_PUBLIC_V1` and a short public business-advisory objective.
2. Original ephemeral council computes four business-specific perspectives plus independent critique, stores artifact and publishes its truthful status.
3. Research worker checks named public claims and official sources; Verification challenges any unsourced claims. Founder receives a one-page decision, not a list of proposed plugins.
4. Only after accepted public pilot, a founder-scoped private business-advice workflow may be activated on a real persistent host. The current public council is not a private CFO.

Prepared from original-source research and founder constraints; review periodically as products and official guidance change.

# Plenum Prometheus | Agent Catalogue and Founder Council
Updated: 2026-11-10

## What is real
The original Plenum Chief, nine existing n8n AI departments, Browser Use/Playwright tools and research platforms stay canonical. This integration **does not create 283 running models**.

The upstream `msitarzewski/agency-agents` catalogue was inspected at immutable source commit `8ae6164602c95ca78828b148b9052460ee426885`: **283 Markdown persona profiles across 18 divisions** after excluding integration/administrative files. It is licensed MIT, listed in `integrations/agent-catalog/agency-agents.index.json`. Each entry stays `catalogued_idle` and its individual upstream Git blob SHA is preserved. `src/plenum_ai/agent_library.py` can **select and fetch a named role only on demand**, checking the content's actual Git SHA before storing it as untrusted source, never directly executing it. This avoids cloning unreviewed scripts and needless always-on models.

Other public tools and directories are classified in `integrations/agent-catalog/upstream-sources.json`. **OpenMontage** advertises 700+ skills and production-knowledge files but uses AGPL-3.0. Do not assume its commercial distribution or hosted derivative obligations are identical to MIT. EGM is Apache-2.0; its fresh-context methodology is adopted into the council, without pretending its official plugin has been installed in the local worker. Qwen-AgentWorld is a specialized open model and benchmark; full-size variants do not fit our low-resource free runtime.

## Founder council — a real on-demand meeting, not five copies of a persona
A PUBLIC agenda uses an original founder-authored GitHub issue in this repository:
- Exact issue title: `[Plenum Council] public agenda`
- Exact body:
```
PLENUM_COUNCIL_PUBLIC_V1
objective: Evaluate free AI agent catalog governance
```

`.github/workflows/plenum-agent-council.yml` validates founder identity **before** starting an ephemeral local Qwen3:1.7b. It requests distinct, fresh model responses under four independent role instructions: Chief (problem framing), Engineer (reusability and feasibility), Economist (operating costs), Product (user experience). A fifth, fresh-context critic sees only those resulting drafts and identifies contradictions, missing evidence, risk and the cheapest reversible test. The output is an **advisory proposal** for founder decision. It does not launch jobs, deploy systems, access accounts or approve itself. Evidence is retained seven days in GitHub Actions and a bounded issue status is posted. A source-only passing unit test is not proof the actual model meeting executed; inspect the associated live run.

## Council and advisers remembered
**Henry Ford** — standardization, manufacturing efficiency and practical engineering.
**John D. Rockefeller** — capital allocation, integration and operating costs.
**Steve Jobs** — product clarity and frictionless user experience.
**Harvard, MIT, Stanford and Princeton** — public institutional guidance for business, engineering, innovation and fundamental scientific evidence; not live endorsements or commissioned professional counsel.
**Google EGM fresh-context reviewer** — independently challenges proposals rather than simply echoing the Chief's instructions.
These are intellectual lenses expressed through AI prompts and public standards, **not actual historical persons or retained advisers**. Final decisions remain with the founder, and scientific, commercial, legal and security claims require original evidence or a suitably qualified actual expert.

## Dashboard
`dashboard/index.html` already provides the original Plenum Command Center: GitHub run status, scheduled jobs, ten-role workforce, task composer and browser voice transcription/briefing. This change adds a **Council & Catalogue** tab, all 283 indexed specialist profiles, division/name search, and a **founder-reviewed public council issue composer**. It does not pretend to run a model in a static browser page or access private accounts.

## Selection architecture
1. Founder declares an outcome, constraints, deadline, and public/private sensitivity.
2. Chief checks current canonical ledger and verified existing tools.
3. Council chooses a small mission-specific selection (e.g. engineering + finance + verification), not hundreds of simultaneous agents.
4. Selected idle persona may be loaded by SHA-checked retrieval, reviewed, and mapped to **an existing permitted runtime** with per-task tools and budget.
5. Independent reviewer critiques the plan. Founder approves any consequential step; worker executes and returns verifiable evidence.
6. Status is recorded in the original GitHub issues, action logs and canonical ledger; inactive roles consume zero inference.

**Limits:** The PUBLIC Issue/Pages dashboard cannot accept private inventions, customer or email data, credentials or payment actions. Confidential council meetings require a separate secure authenticated path. The dashboard static file is not evidence of a deployed HTTPS dashboard. No paid hosting, app permissions or new account numbers were created by this change.

# PLENUM | AI Skill Curriculum & Tool Adoption Ledger
11 November 2026 | Founder-requested, public-only | Version 1.0

## Operating standard
A role names responsibility; a portable SKILL.md provides a repeatable procedure; a tool enables actions; an AI model supplies reasoning; a host supplies actual execution. Profile definitions, source catalogues and workflow drafts do not imply a running agent. Prefer official APIs over browser clicking. Train skills against real outcomes rather than stacking more agent managers.

Anthropic: https://www.anthropic.com/research/building-effective-agents
Google Cloud: https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system
Anthropic/AI Engineer video: https://www.youtube.com/watch?v=CEvIs9y1uog
Hermes skills (source standard): https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/

## All five workforces and mapped agents
The canonical role-to-skill mapping is stored in integrations/hermes/roster.json; 11 named profiles (1 Chief, 9 original specialists, 1 founder Business Advisor) now point to 13 professional skill files under skills/plenum-*/SKILL.md. The five divisions are not 5 perpetual independent AI programs.

| Division | Roles | Key expertise and practical result |
|---|---|---|
| Scientific Research | research, simulation | Source and prior-art analysis, falsifiable experiments, validated simulations |
| Engineering & Manufacturing | coding, creative | Original source inspection, narrow implementation, review, product & design deliverables |
| Commercial Operations | operations, marketing, support, business_advisor | Business decision recommendations, financial questions, growth hypothesis, delivery and support |
| Global Intelligence | research, browser | Current original source/video research, external intelligence and owner-approved navigation |
| Verification & Advisory Council | verification | Independent reality check, output acceptance, reviewed third-party skills |
| Cross-functional direction | chief (proposed display title AI Minister of Operations) | One founder queue, division coordination, decisions requiring approval, status and outcomes |

13 portable skills added:
plenum-business-advisor; plenum-minister-operations; plenum-research-youtube; plenum-science-evidence; plenum-coding-delivery; plenum-browser-operations; plenum-finance-operations; plenum-growth-sales; plenum-creative-quality; plenum-support-service; plenum-independent-verification; plenum-simulation-validity; plenum-skill-curation.

Use integrations/hermes/skills-external-dirs.example.yaml after installing official Hermes on a separately authorized host; merely adding skill IDs to a roster does not install them on that host. The original public Chief and Qwen council may now use the decision pattern, while private app access remains restricted.

## Actual Founder Business Advisor — advisory recommendation, not a simulated meeting
This new distinct named `business_advisor` profile belongs to Commercial Operations. The existing public council reviews independent Operations, Finance, Strategy and Governance perspectives; one **Business Advisor** should then synthesize a decision recommendation: **What should we do now? Why this option? Why not the alternatives? Which constraint governs? What is the next measurable action and which workforce owns it?** The founder chooses; the agent may propose and delegate only within real tool permissions.

A decision memo must include: Decision | Recommended action with rationale FIRST | Two alternatives including defer | Primary evidence/as-of date | Cost, benefit, time and reversibility with uncertainty | First action + deadline + completion signal | Founder approval required. Follow each accepted decision with a later actual-vs-plan review. Avoid fabricated balances, funding commitments, customer counts, proprietary patents, citations or professional licenses.

Source basis: Stanford GSB disciplined decision making (https://www.gsb.stanford.edu/exec-ed/programs/stanford-lead/curriculum/courses/decision-making); Harvard Business Review decision framing, alternatives and traps (https://hbr.org/2023/08/using-chatgpt-to-make-better-decisions and https://hbr.org/2006/01/the-hidden-traps-in-decision-making); SBA finance, cash flow, pricing, compliance and business plan updates (https://www.sba.gov/counseling/manage-your-business/). An AI advisor is distinct from Plenum's actual Board of Directors or retained human legal/financial professionals.

## Tool choices: what each does and what Plenum actually uses
Status: USED = observed limited real task; PREPARED = local source/config; OPTIONAL = independent use-case evaluation; LATER = defer until demand; EXCLUDE = no fit with strict no-new-charge operating baseline.

| Technology, skill or source | Use | Current decision |
|---|---|---|
| Deep Agents + LangGraph / Qwen | Original Chief routing, checkpointing and source-bound specialist tools | USED bounded; retain as the sole technical Chief |
| GitHub + Actions + source ledger | Public task inbox, source control, bounded runners and accepted evidence | USED; remain canonical public source |
| n8n | API workflows, fixed business triggers, schedules and review queues | PREPARED original nine-role drafts; private runtime not continuously confirmed |
| OpenHands | Coding tasks and program development | PARTIAL original SDK work; previous 7B draft errors, no general coding reliability claim |
| Plenum Playwright/Browser Use | Website interaction and owner-saved sessions | PARTIAL deployed original browser; signed-in 3-step acceptance incomplete #310 |
| Hermes Agent | Named role chats, memory, skills, scheduling, delegation and WhatsApp gateway | PREPARED 11 profiles/skills; no live Hermes process/WhatsApp credentials |
| Paperclip | Company board, goal/agent chart, budgets, task assignment and status | PREPARED official adapters; no installed live service |
| OpenClaw | Messaging/agent gateway and optional additional specialist execution | OPTIONAL only where Hermes lacks distinct function; avoid duplicate control/WhatsApp |
| Ollama / llama.cpp | Shared local inference without recurring per-model API bills | USED only on bounded ephemeral jobs; not a persistent free server |
| Oracle Cloud Always Free | Candidate persistent low-cost coordination host | BLOCKED real free capacity/tenancy #384; no billed fallback |
| Obscura | Agent browser alternative | OPTIONAL only if original Plenum Browser cannot perform required task |
| Agency Agents | Specialist prompts, checklists and skills inspiration | PREPARED catalogued 283, not 283 running agents |
| Ordain | Soul/profile and portable skill generator | LATER, native roster + SKILL.md now cover practical need |
| Grok Bot Marketplace | Ready-made specialist templates | OPTIONAL inspiration; not assured $0 operating runtime |
| FreeBuff | Supplemental coding or browser inference | OPTIONAL public-only, finite/ad-supported and privacy-dependent |
| Base44 Superagents | Rapid hosted app / agent prototypes | OPTIONAL finite free trial/tier; not unlimited inference or business host |
| Abacus AI Bot | Desktop assistant, app tools, messaging, code | OPTIONAL alternate workstation, not second Chief |
| Mistral Agents / Le Chat | Alternate public specialist chat and model | OPTIONAL, distinguish chat access from billable API |
| ChatGPT Dots | Proactive personal agent orchestration | OPTIONAL only if eligible; not Plenum-owned execution |
| Airbyte | Consolidate disparate API data into analytics | LATER only when many authorized sources need ETL |
| ClickHouse | High-volume event warehouse and analytics | LATER after measured scale requires it |
| Kai AI / fal / SeedDance / Tesseract | Creative assets, avatar/video/transcription | OPTIONAL for approved marketing, check costs and rights |
| OpenRouter | Model provider abstraction and free-limited inference | OPTIONAL capped fallback, no unlimited $0 inference |
| Hostinger | Paid always-on server | EXCLUDE from strict $0 core |
| Telegram | Alternative messaging group/channel | LATER, WhatsApp preferred |
| WhatsApp | Founder chat, messages to Chief and specialist delegation | BLOCKED separate authorized pairing/API and host; official business DM differs from unofficial group bridge |
| Credential vault / 1Password | Keep third-party passwords out of GitHub and agent prompts | PARTIAL original encrypted GCS site vault and GitHub secrets; third-party vault optional |
| Last 30 Days | Recent YouTube, Reddit and forum scouting | Portable source-checking practice in plenum-research-youtube; marketplace skill not installed |
| Remotion / HyperFrames | Programmatic motion graphics, maps and animation | OPTIONAL creative skill, license / rights check first |
| Humanizer | Writing tone and mechanical-style cleanup | OPTIONAL; Plenum document production standard governs first |
| Claude-video | Analyze actual video content | OPTIONAL when accessible transcript/official docs insufficient |
| Superpowers / Gstack | Coding, review and release methodology | Superpowers procedures partially USED; evaluate Gstack only for missing workflow |
| Impeccable | Visual/UI audit and polish | OPTIONAL creative design evaluation |
| NVIDIA SkillSpector | Source/agent-skill security scan prior to import | Skill curation gate ADOPTED as procedure; scanner package not yet installed on owner host |

## YouTube & official research priorities
Research issues #439 (video and agent workflows), #440 (university decisions), #441 (source-grade skills) were submitted using the original exact GitHub worker issue trigger. The existing World Horizon researcher retrieves public leads and metadata, not guaranteed full video transcripts. Do not treat YouTube demos as Plenum's production acceptance.
- Anthropic/AI Engineer, portable skills lecture: https://www.youtube.com/watch?v=CEvIs9y1uog
- LangChain hierarchical agents: https://www.youtube.com/watch?v=B_0TNuYi56w
- Paperclip creator demo: https://www.youtube.com/watch?v=C3-4llQYT8o
- Official Hermes skills: https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/
- Official Paperclip adapters: https://github.com/paperclipai/paperclip/blob/master/docs/adapters/overview.md
- Official NVIDIA SkillSpector: https://github.com/NVIDIA/skillspector
- Original Agency Agents: https://github.com/msitarzewski/agency-agents

## Minimum needed to make imported managers genuinely useful
- [x] Define all five divisions; named Business Advisor; professional skill files; explicit role-to-skill mapping.
- [ ] Merge and verify the changed council business adviser synthesis and profile skill mapping with focused checks.
- [ ] Run the new real public council assignment AFTER merge, inspect the actual recommendation and independent evidence needed.
- [ ] Reuse existing Github/Deep Agents and n8n; do not buy or configure a second Chief.
- [ ] Founder-controlled persistent free host #384 becomes available; install official pinned Paperclip and Hermes, attach ORIGINAL scoped worker via built-in adapter and prove real task survived restart.
- [ ] OpenClaw installed **only if** it performs a distinct real approved task that Hermes/Plenum cannot do; avoid two WhatsApp gateways for same identity.
- [ ] One legitimately authorized private account session for Plenum Browser issue #310.
- [ ] One authorized WhatsApp account/channel with genuine incoming message, specialist handoff and reply; do not infer consent to pair a personal number.
- [ ] Add actual authorized company financial/CRM/operations sources to a private, not public, advisor environment.
- [ ] Make every report decision-focused and performance-focused, not a recital of installed products.

**Do not count completed source files as installed runtime processes or accepted private business work.**

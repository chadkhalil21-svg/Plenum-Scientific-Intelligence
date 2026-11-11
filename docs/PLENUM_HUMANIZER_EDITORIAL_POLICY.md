# Plenum Industries — natural-language, Humanizer and presentation quality policy
As of November 11, 2026. Source and approved-skills implementation; not automatically account-wide ChatGPT behavior.

## Decision
**Adopt one unified evidence-first editorial quality standard across the 11 defined Plenum AI roles and every client-facing medium.** Vendor the unchanged Humanizer v4.0.0 MIT skill at its pinned source, and use Plenum's reader/genre-specific editorial guide as its controlling wrapper.

### The existing assets we ought to reuse
1. The founder's private Google Doc **Plenum Industries | Document Production Standards Ledger** defines the actual recipient/source/editing hierarchy for company artifacts, and already references Humanizer.
2. A private ChatGPT **Plenum Editorial Council** plugin with a Humanizer guidance skill was already created November 10, 2026 according to that ledger. This GitHub implementation neither replaces that plugin nor proves automatic invocation in every chat.
3. The existing Plenum source skill and reusable Hermes profile roster are now extended to the pinned original MIT Humanizer and the explicit company style policy, with a separate full MIT license.
4. The n8n public draft workflow and Qwen council prompt must employ a concise editorial standard; style quality is **not evidence of factual correctness**.
5. GitHub Actions executes short-lived public work and can run source/contract reviews without Oracle, but it cannot retain persistent Paperclip/Hermes/WhatsApp sessions simply by including their files in a repository.

### Five-stage method for every artifact
**1. Identify genre and reader.** Email vs scientific paper vs law memo vs slide, visual media, speech or chat. Recipient, journal, sponsor and current legal/form constraints govern. Preserve the founder's requested tone in founder-directed chat, but do not copy theatrical flourishes into grant proposals or letters to agencies unless specifically desired.

**2. Establish claim integrity.** Read actual documents and source claims. Distinguish hypotheses from observations, source-reported effects from Plenum results, funding proposals from awarded sums, code merges from actual deployments, and draft emails from sent messages. Check critical figures, exact names, punctuation, quotations, references and patent status.

**3. Draft for use.** Answer first; active voice; plain language; one claim per paragraph/slide when useful; concrete next actions; natural rhythm; clear data visualization and accessible layouts. No decorative faux authority or robotic padded introductions.

**4. Humanizer editorial pass.** Review the pinned upstream `skills/humanizer/SKILL.md` for repeated AI syntax: staged false contrasts, dramatic closers, automatic triads, relentless em dashes, generic sales praise, fake familiarity, heavy bold labels and conclusions that repeat what was just said. Humanization means reducing formulaic patterns while retaining the author's authentic style and all evidence. This is not an AI-origin detection/evasion guarantee.

**5. Independent final audit when material.** Compare transformed text to original source: factual claims, quotes, citations, quantitative values, units, equations, dates, document structure, recipient instructions, accessibility and legal/financial meaning. For PowerPoint and PDF, inspect **rendered pages**, not just slide source. Keep changed-prose-only scopes where appropriate and do not add false certainty.

## Medium-specific rubric

| Medium | Quality standard | Must not change |
|---|---|---|
| Principal-to-principal email | Short, realistic, context-aware request, appropriate warmth, precise next step. Natural salutation and closing. | Facts about recipient, correspondence state, grant terms, commitments; emails require founder approval before sending |
| Chat and spoken interaction | Immediate clear answer; language accessible to principal with law background; no filler theatre, repeated praise or unjustified certainty; personal style when requested. | Status of actual tasks, sources, technical constraints and costs |
| Investor/strategic business advice | One clear recommended action with WHY, alternatives, cash/effort and uncertainty, delegate and next measure. | Financial actuals, partnership status, legal authority |
| Scientific paper/grant/technical report | Correct scholarly voice, recipient's actual templates, hypotheses/measurements and citation system; logical narrative and evidence. | Precise definitions, chemistry, formulas, statistical numbers, prior work and uncertainty |
| Legal/regulatory document | Precise definitions, clauses, statutory references, exact quotations and recipient demands; restrained formal tone. | Operative language, legal rights, deadlines and scope |
| PowerPoint, investor deck, data graphic | Clear message, meaningful hierarchy, uncluttered slides, sourced figures, legible typography, accessibility, consistent design; render review. | Data, claim strength, units, charts, attribution and identity |
| Public website/product UI | Apple HIG situational voice, actionable labels, plain accessible copy, helpful errors and reader purpose. | Customer terms, actual product behavior, legal disclosures |
| Creative content/marketing | Natural brand voice, audience-appropriate specificity, originality and commercial rights; thoughtful pacing. | Verified product capabilities, brand facts, licensing |
| Developer docs/code comments | Google technical writing: concise active language, precise code and APIs, complete examples. | Code identifiers, executable commands, architecture and version restrictions |

## Institutional primary source consensus
- **OpenAI, Model Spec October 29, 2026:** faithfulness, truth and transparency, support user agency, adaptable language for specific reader; https://openai.com/index/updated-model-spec/
- **OpenAI, prompting best practices:** clear reader, task and requested tone; https://help.openai.com/en/articles/10032626-prompt-engineering-best-practices-for-chatgpt
- **Google, Developer Documentation Voice and Tone:** conversational, precise, jargon-limited, not overly cute or formal; https://developers.google.com/style/tone
- **Google, Developer Style Guide priority:** project-specific instructions before generic guidance; https://developers.google.com/style
- **Apple, Human Interface Guidelines / Writing:** choose vocabulary and situational tone, clear action, inclusivity and accessibility; https://developer.apple.com/design/human-interface-guidelines/writing
- **Anthropic, effective context engineering:** minimal complete instructions, not bloated prompts; https://www.anthropic.com/research/effective-context-engineering-for-ai-agents
- **Anthropic, Agent Skills:** concise discoverable skill with real examples; https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- **Humanizer, v4.0.0:** verbatim pinned `blader/humanizer` from `b48c832f0f809c1b5658edbb838c2521b72f2413`; https://github.com/blader/humanizer
- University/sponsor-specific standards for a Plenum grant, paper, legal document or presentation remain above generic stylistic preferences where they apply. A vendor's writing style does not imply a university endorsed Plenum's implementation.

## YouTube and community skill research
The founder supplied multiple video summaries of AI skill packs, Humanizer, Last 30 Days, Claude-video, Remotion, Superpowers, Gstack and Impeccable. These are useful *leads* but do not automatically prove upstream licenses, factual correctness, applicability, model cost, or installation. Start with directly verified original vendors' skills and institutional guidance. Research assignments in GitHub #444–#447 use the EXISTING permitted public-source worker and must be described as source metadata lead retrieval, not proof that a full video was watched.

## Actual incorporation checklist
- [x] Original MIT Humanizer skill & license vendored into repository at pinned commit.
- [x] Plenum audience/evidence/editorial skill created with cross-media rubric.
- [x] Both assigned to all 11 named Hermes profile definitions, with original role skill mapping.
- [ ] Existing source-only n8n draft system prompt and public Qwen council prompt updated for lean, factual, natural language and code checked.
- [ ] First real task uses the source-connected skill on a running model and is independently compared with original claims. A config test alone is NOT an end-to-end editorial execution.
- [ ] Private Hermes agent host loads external skill directory via actual installed process. No always-on host or personal WhatsApp connection has yet been confirmed.
- [ ] Founder-approved private mail/docs/browser access for substantive business output; no secret in GitHub issues.
- [ ] Human review on high-stakes legal, scientific and financial deliverables; don't apply a generic automated style rewrite to legal operative clauses or empirical data.

## All earlier software options remain recorded
See `docs/PLENUM_AGENT_SKILLS_AND_TOOL_LEDGER.md`, which enumerates Deep Agents, LangGraph, Qwen, GitHub, n8n, OpenHands, Plenum Browser, Playwright, Obscura, Agency Agents, Ordain, Paperclip, Hermes, OpenClaw, Ollama, Oracle, Grok Bot Marketplace, FreeBuff, Base44, Abacus AI Bot, Mistral, OpenRouter, Dots, Airbyte, ClickHouse, Kai AI, fal, SeedDance, Tesseract, Hostinger, Telegram, WhatsApp, credential vault, Last 30 Days, Remotion, HyperFrames, Humanizer, Claude-video, Superpowers, Gstack, Impeccable and SkillSpector. These are not all installed; choose each by a documented missing capability, price/rights, and a real acceptance. No duplicate general-purpose agent bosses.

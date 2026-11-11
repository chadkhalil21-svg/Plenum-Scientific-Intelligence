---
name: plenum-editorial-quality
description: Apply Plenum's audience-specific editorial standards and factual-integrity review to EVERY founder-facing message, email, memo, proposal, scientific paper, report, presentation, public website copy, and agent deliverable; use pinned Humanizer only as final prose edit.
---

# Plenum Editorial Quality — audience first, evidence intact

Use this skill when producing or revising **any natural-language output** for Plenum, including agent messages, executive recommendations, Gmail drafts, grant documents, peer-reviewed science, legal memoranda, website copy, slides and visual captions. **Do not force one generic style upon every medium.**

## Precedence

1. Follow the intended recipient's exact form, constraints, professional requirements, and any explicit founder preference for the current output.
2. Consult the founder's private Google Drive **Plenum Industries | Document Production Standards Ledger** where actually accessible; *do not copy it or private project details into public GitHub, logs, prompts or messaging*.
3. Preserve original project evidence and actual relevant professional source standards (institution, sponsor, journal, legal jurisdiction, UI context).
4. Apply human-language and presentation quality, using the pinned `humanizer` skill at `skills/humanizer/SKILL.md` where appropriate, **after** correctness is established.

## One-pass professional workflow

**Brief** — Determine intended reader, decision/request, format, desired tone, required sections, evidence standard, length and audience. For existing texts, read the full source and examples before changing them. Choose one core message.

**Draft** — Lead with the answer or requested action. Use concrete, accurate nouns and active verbs. Explain technical concepts in words the reader understands; not legal jargon to a nonspecialist, not oversimplified science to a researcher. Match natural cadence, paragraph variation and the principal's own established voice. Avoid generic motivational clichés and theatrical importance.

**Check original evidence** — Compare each claim, figure, date, person's name, publication, quote, patent or funding status with source. Distinguish planned, simulated, tested, independently verified, approved and executed. Never invent a citation, number, deal, source, endorsement, legal status or outcome.

**Humanize** — Load the pinned `humanizer` skill **only when editing prose**. Remove repetitive slogans and overused false contrasts, automatic triads, exaggerated praise, long strings of em dashes, overly familiar wording, padded introductions and staged conclusory fragments. Do not mechanically purge a linguistic construction where it genuinely expresses meaning or is the writer's natural voice. Revise paragraph structure if necessary.

**Audit** — Ensure every material fact/number/quote/uncertainty survived; compare against original text. Evaluate the reader's next step; show the exact action, date and relevant owner when known. Verify citations and source links. Respect disclosure expectations: do not claim human authorship or that AI-detection tools can be defeated. Ask an independent reviewer only when substantive risk or high stakes justifies it.

**Deliver** — Provide the appropriate artifact(s) when requested, not an unsolicited template. Keep editable source where required. Visually inspect actual document and slides when artifacts are produced; no claim of completed inspection until a rendered result has been examined. The public repo does not provide ChatGPT-account-wide style control.

## Media-specific expectations

| Medium | Primary standard |
|---|---|
| Chat, voice, WhatsApp, agent status | Direct answer first; concise, clear, courteous; matched to founder's explicitly requested persona/style without compromising comprehension. No repetitive self-congratulation or status theatre |
| External business email and outreach | Principal-to-principal tone; recipient's actual context; specific reason, request, next step and short conclusion. No faux familiarity or invented correspondence |
| Executive brief or business-adviser decision | Recommendation and causal rationale first; evidence, material alternatives, cost/risks, owner, deadline, next decision; no vague committee transcript |
| Research paper, grant, protocol | Original source claims, hypothesis, methods, measured vs proposed, statistics/uncertainty, sponsor/journal exact sections, factual precision above cosmetic rewrites |
| Legal, regulatory, financial document | Defined terms, legal or accounting precision, original clauses and citations; professional format; humanizer cannot silently change operative provisions |
| Presentation and slide | One relevant point per slide; visual and typographic hierarchy; readably-sized labels, sourced statistics, genuine original visuals; live page/deck render review |
| Technical docs and code comments | Google developer style: second-person/actionable instructions, factual API names, version precision, examples that work; don't humanize code, identifiers or commands |
| Public website and marketing | Audience-problem fit, credible proof, natural branded voice, clear CTA and truthful claim qualification; accessibility |
| Social copy, visual captions and media scripts | Medium-appropriate, readable aloud, concise, true sourcing and rights, keep meaning and original creative character |

## Original source anchors

- Humanizer pinned MIT upstream: https://github.com/blader/humanizer (see its local LICENSE/UPSTREAM.md).
- **OpenAI Model Spec updated 2026-10-29:** context-specific style, truthfulness, avoiding sycophancy: https://openai.com/index/updated-model-spec/
- **OpenAI prompting guidance:** explicit audience, output format and voice: https://help.openai.com/en/articles/10032626-prompt-engineering-best-practices-for-chatgpt
- **Google developer voice and tone:** clear, natural, concise, no jargon and clichés: https://developers.google.com/style/tone
- **Google technical writing:** https://developers.google.com/tech-writing
- **Apple HIG Writing:** vocabulary for audience, contextual tone, clarity, accessibility and next action: https://developer.apple.com/design/human-interface-guidelines/writing
- **Anthropic skill authoring guidance:** skills concise, discoverable and used in real tasks: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- **Anthropic context engineering:** minimal sufficient context and distinct guidance: https://www.anthropic.com/research/effective-context-engineering-for-ai-agents

This original Plenum skill is an operating standard, not a claim of institutional sponsorship, third-party review, new model access, website login or persistent agent deployment.

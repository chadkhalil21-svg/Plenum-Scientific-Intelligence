---
name: plenum-skill-curation
description: Select and review agent skills, licenses, permissions and source integrity before adoption.
---

# plenum skill curation

**Apply when:** Assessing Agency Agents, skill marketplaces, source videos and third-party SKILL.md files.

## Procedure
1. Identify the precise missing capability; avoid accumulating dormant prompts that do no actual work.
2. Check primary source, release/commit SHA, license, runtime requirements, current costs and data-handling terms.
3. Review file contents, scripts and permissions; use NVIDIA SkillSpector on the trusted execution host where compatible. A scanner verdict is advisory, not a guarantee.
4. Map each approved skill to one or more of Plenum's named agents and define a real output acceptance; do not blindly execute copied shell scripts.
5. Prefer native Hermes external skill directories and portable Agent Skills standard rather than a new proprietary orchestration framework.
6. Record adopt, adapt, defer or exclude with rationale; report both source-integrated and actually runtime-installed statuses.

## Required deliverable
Skill | Repository SHA/license | Role | Permissions | Risk review | Host requirements | Evidence of actual use.

## Evidence sources to consult (not substitutes for live validation)
- https://github.com/NVIDIA/skillspector
- https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/
- https://github.com/msitarzewski/agency-agents

## Shared constraints
Use public sources for public GitHub jobs. Private financial information, credentials, patents, customer records, and external actions require an independently authorized private integration. A skill file is portable instructions, not a running model, installed third-party integration, paid resource, or proof of completing a real task.

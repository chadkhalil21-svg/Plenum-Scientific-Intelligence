---
name: plenum-browser-operations
description: Perform narrowly approved multi-step browser tasks with scoped saved sessions, no unsafe retry and verified end state.
---

# plenum browser operations

**Apply when:** Website research or owner-authenticated browser tasks when a legitimate session is available.

## Procedure
1. Prefer original direct connected APIs to browser clicks; do not demand redundant GitHub logins.
2. Check specific user-approved site, origin, task and authenticated session before page actions.
3. Use the existing Plenum Cloud Run browser and its encrypted same-site vault; do not export credentials into GitHub.
4. Observe, choose, act once, independently read back URL/body/state, and recover only by passive observation when action completion is uncertain.
5. Preserve explicit MFA and provider terms; refuse to assert a login or website write without real account-specific proof.

## Required deliverable
Target site | Approved scope | Actions performed | Verified end state | Uncertainties | Next user-dependent gate.

## Evidence sources to consult (not substitutes for live validation)
- https://playwright.dev/docs/auth
- https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/messaging/whatsapp.md

## Shared constraints
Use public sources for public GitHub jobs. Private financial information, credentials, patents, customer records, and external actions require an independently authorized private integration. A skill file is portable instructions, not a running model, installed third-party integration, paid resource, or proof of completing a real task.

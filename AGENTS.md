# Project working instructions

**Repository continuity requirement.** For every task involving Plenum Computer Browser, Prometheus browser automation, browser-backed plugin tools, browser Cloud Run services, session storage, authorization or the associated GitHub workflows:

1. Read `docs/COMPUTER_BROWSER_PROGRESS.md` and `docs/LEDGER.md` before proposing further engineering.
2. Examine actual source, last commits, PRs and workflow/deployment evidence. Reuse verified components instead of rebuilding.
3. In the **same change** as any meaningful browser feature, fix, deployment or acceptance test, update `docs/COMPUTER_BROWSER_PROGRESS.md`: status gate, date, objective, evidence, actual result, costs/permissions, blockers and next action. Update `docs/LEDGER.md` for material program milestones.
4. Write `verified` only for actual live tests, `offline` for isolated tests and `source only` for untested code. Never treat OAuth scopes, a passing mock test, a successful deployment or plugin instructions as proof of full ChatGPT Work parity.
5. Use private task transport for nonpublic information. Never write credentials, tokens, cookies, owner OAuth identifiers or account contents into PUBLIC GitHub issues or source control. Do not grant broad IAM roles merely to bypass missing narrowly scoped permissions.
6. Honor the objective: Plenum-owned Playwright accessible directly from ordinary chats; TinyFish is an optional temporary bootstrap tool, not a permanent dependency.
7. Treat the progress ledger as a source-of-truth **retrieval step**, not as model memory that updates automatically in every chat. If work did not execute, record the blocker rather than a completion claim.

CI enforces contemporaneous updates to the browser-specific ledger on PRs changing browser source or browser deployment workflows.

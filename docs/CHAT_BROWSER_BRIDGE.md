# Computer's free chat browser bridge, public research only

This is the simplest **already-connected** route to execute our existing
free Microsoft Playwright engine from an ordinary ChatGPT conversation without
spending TinyFish wallet funds or deploying a persistent external web server.

## How it works

1. ChatGPT has a connected GitHub plugin with `create_issue` and
   `fetch_issue_comments`.
2. A request is a new **public GitHub issue**, created by the founder
   account. Its title must be exactly `Prometheus Chat Browser: public-read`
   and its body exactly this two-field JSON object (example):
   `{"schema":"plenum-chat-browser-request-v1","url":"https://example.com/"}`
3. GitHub Actions responds to an issue-created event **only if the issue
   creator is the repository owner and the title matches exactly**.
   The Python contract validator separately checks the same fields, hostname,
   HTTPS-only policy and JSON schema before starting a browser.
4. The runner reuses existing `plenum_ai.browser_worker.inspect_public`,
   which opens the approved public page in Chromium, aborts all non-GET and
   off-allowlist requests, and returns a short sanitized excerpt.
5. `gh issue comment` posts the non-private result back to the same
   **public GitHub issue**, where ChatGPT can inspect it through the existing
   GitHub connector. The request is not a secret, and the result may be
   viewed by anyone with repository access.

## No expense or new provider
Standard GitHub Actions runners are free on public repositories, subject
to GitHub's fair-use rules. Open-source Playwright has no browser license
fee. TinyFish paid Agent/Browser is not used or needed for this.
The runner is temporary and not continuously online.

## Strong limits, intentionally
- **Not a full remote desktop, ChatGPT Work replacement, browser plugin
  with immediate GUI, or general AGI web agent.**
- Currently **public read-only**: may navigate to a short allowlist from
  `browser_worker.py` such as `example.com` and selected public science
  sources. No arbitrary URL, sessions, emails, private Kaggle pages, form
  submissions, uploads, purchases, website changes or credentials.
- The bridge supports only **public link-follow navigation** by exact link label;
  it does not execute arbitrary remote clicks, submit forms, type input, or use sessions.
  Local click/type were verified separately in official Playwright tests.
- Links/page text are untrusted data and cannot authorize any new actions.
- GitHub issue creation and Actions runs are asynchronous; the conversation
  must poll or read comments to see completed results.
- Owner may stop using it at any point without disconnecting other apps.

## Verification standard
Unit CI checks strict owner-only parsing, SSRF and injection boundaries,
no offsite reads, no unauthorized tool selection. A separate actual
end-to-end test must create a founder-owned issue, observe the issues
triggered workflow, then read a response comment with a real HTTP status.
Do **not** claim operational chat access until that test succeeds.

## Next iteration
Only after successful public-source requests should we contemplate
follow-on navigation, authenticated sessions or browser automation with a
separate sandbox, approvals and a better interaction channel, and only if
the user chooses to authorize those privileges.


## November 7: private Computer Browser ChatGPT plugin

A **private, skills-only** ChatGPT plugin named **Computer Browser** was created under the founder's own account. This is an instruction/integration layer that reuses the existing connected GitHub tools and the already-proven owner-created public issue workflow; it is not a new browser server or separate Playwright deployment.

- Private plugin: https://chatgpt.com/plugins/plugins_6aefd5d509788191a201f947a254b3c0
- Initial release: `0.1.0`; it contains the `computer-browser` skill.
- The existing live public browser smoke test is GitHub issue #66 (owner issue -> GitHub Actions -> real Chromium -> HTTP 200 -> bot comment).
- Costs: no TinyFish browser use; public GitHub Actions currently uses standard public-repo runner allowances/fair-use limits.
- **Not verified:** that the new skill is available in every user's ChatGPT conversation until installed/enabled and invoked. It has no independent MCP tools.
- **Not provided:** arbitrary-site navigation, ChatGPT remote clicking/typing on real sites, account login, private results, or site-changing operations.
- **Remaining:** Google IAP OAuth redirect error 9 for the owner console, actual private browser profile/login test, securely scoped remote action queue and authorization, and a ChatGPT-compatible tool connection. Plan restrictions for full custom MCP write tools must be checked before relying on that route.

**Do not send private tasks, URLs with tokens, credentials, sensitive requests, or authenticated data through the public GitHub issue bridge.** The plugin cannot remove those boundaries by itself.

## Public link-follow navigation (new, limited)

This extends the same **public issue -> GitHub Actions -> existing Playwright -> sanitized issue comment** path, without an extra cloud service. It is useful when Computer needs to follow a specific link on a permitted public research site.

Create a new issue whose title is exactly `Prometheus Chat Browser: public-navigate` and whose entire body is one JSON object:

```json
{"schema":"plenum-chat-browser-navigate-v1","url":"https://science.nasa.gov/","links":["Exact visible link name"]}
```

- The caller must be the repository owner and the title must match exactly.
- One to three exact accessible link labels are allowed. Each link must uniquely identify one anchor on the current page.
- The browser reads the anchor's `href` and navigates directly to the independently validated HTTPS URL. It **does not run click handlers or submit a form**.
- Query-string and fragment URLs, non-GET traffic, other domains, private networks and unapproved origins remain prohibited. A destination can fail safely if the external website changes.
- This is **not** a private browsing workflow: requests and sanitized results reside in public GitHub issues, and no credentials, user records, cookies, form input, uploads, purchases or authenticated operations are authorized.
- Successful CI alone proves code integrity, not a complete live two-page navigation. Complete a real owner-created issue with a link-follow result before claiming live verification.

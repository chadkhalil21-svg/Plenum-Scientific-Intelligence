# Computer's reusable multistep browser actions

The shared Cloud Run browser now has a bounded Playwright action engine.
It supports typed locator operations for typing into fields, clicking,
selecting dropdowns, checking boxes, pressing keys, uploading previously
approved small files and inspecting page titles.

**Independently verified offline:** official Chromium fills a form, selects
a dropdown, checks a box, uploads a tiny synthetic text file, and clicks a
preview button, with zero external network requests. The worker returns
only completion statuses, not secret input values or cookies.

**This does not authorize acting on real sites.** Before the browser can
use this engine on Kaggle, government sites, banking, research portals or
business services, an actual owner-authenticated workflow must supply
scope, separately approved origins, a private authorized browser profile,
private upload source and explicit user review when consequences warrant it.
Production traffic must also pass real egress/DNS-rebinding protection,
phishing and prompt-injection handling. No endpoint exposes these steps
to arbitrary website content or the public internet today.

The next work is the owner sign-in interface, durable private workflow
queue and human approval gate, followed by a real authorized staging
account. Cloud Run deployment and ChatGPT plugin connectivity remain separate
conditions. No TinyFish metered use or cloud resources are spent for tests.

## Real chat-driven public form work, independently verified 2026-11-08

`src/plenum_ai/public_form_browser.py` now includes **public-form-inspect** and **public-form-search**. They run actual Chromium on GitHub Actions from regular ChatGPT-connected GitHub issue creation, without TinyFish. Search form selection is explicit; public GET search may carry up to four user-specified harmless parameters (e.g. `searchtype=all`), and never imports arbitrary HTML hidden field values. All requests remain GET-only and the search destination must stay on the same approved public host.

[Issue #185](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/185) returned a sanitized arXiv form inventory. [Issue #188](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/188) confirmed genuine search results: `Showing 1–50 of 47,582 results for all: dark energy`, HTTP 200. The worker never requested TinyFish. Consult `docs/CONNECTION_ROADMAP.md` for exact job titles and schemas.

This is **not** our final full private browser. It must not accept private user inputs in PUBLIC GitHub issues, and it cannot act in logged-in accounts or write to websites. Existing bounded locator action engine and encrypted profile vault are source/test foundations awaiting a private owner-authenticated production pathway.

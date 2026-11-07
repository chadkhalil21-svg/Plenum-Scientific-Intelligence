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

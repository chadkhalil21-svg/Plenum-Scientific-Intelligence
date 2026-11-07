# One-time private website sign-in screen

This release adds an owner-operated browser view to the same Computer and
Prometheus Cloud Run service. It is **not yet deployed or connected to
ordinary ChatGPT website-modifying tools**.

Once Google Cloud Run and IAP owner authorization are configured, the owner
can open `/owner/sign-in` in a browser, sign into an approved website
through streamed Chromium screenshots and clicks/keyboard, and explicitly
save the website's session into encrypted private Cloud Storage. No password
is typed into ChatGPT or the public GitHub repository.

This is a **human-operated sign-in ceremony** rather than a general
autonomous website agent. The previously verified Playwright action executor
remains available for future individually approved browser tasks.

The websocket requires signed Google IAP identity, explicit owner email,
the exact HTTPS origin of the service, and an allowlisted target website.
Its browser blocks unauthorized external origins, downloads, arbitrary
keyboard code and JavaScript evaluation. This is not yet a complete network
firewall; a production egress proxy and independent testing are required
before arbitrary owner-chosen websites become safe.

The optional `demo=1` fixture runs only when the CI-only environment
flag `COMPUTER_BROWSER_CI_ONLY=true` is manually set; the manual
deployment workflow does not set that flag. The CI test uses actual
Chromium over the signed-user WebSocket interface to click and type into
a local fixture without external requests, private data or GPU use.

**Remaining:** signed-in Google Cloud project/billing, WIF/secret setup,
Google Cloud Run service deploy, IAP external-user policy, allowed origin
configuration, real staging website sign-in, private GCS/KMS checks and
ChatGPT action integration. Do not claim full account control from this
source test.

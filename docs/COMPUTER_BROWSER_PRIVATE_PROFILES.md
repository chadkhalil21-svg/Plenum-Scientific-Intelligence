# Computer browser secure profile storage

This implements application-side encrypted website-session storage for the
existing shared Computer/Prometheus browser. It does **not** capture, save or
restore any real user login yet; the only tests use synthetic cookies.

## Production requirements

Create a **dedicated private Google Cloud Storage bucket** for browser
profiles, separate from any public research files or customer data. Enable
uniform bucket-level access and public access prevention, with a lifecycle
rule that removes expired session objects. Restrict a dedicated Cloud Run
runtime identity to read/write objects inside this one bucket; do not grant
project-wide storage administration.

Put a fresh 32-byte Fernet key (URL-safe base64 format) in Google Cloud
Secret Manager as `computer-browser-session-key`. NEVER commit it, paste it
into ChatGPT or expose it to GitHub logs. Restrict secret version access to
the browser runtime service account. Mount it as an environment variable,
`BROWSER_SESSION_KEY`; set `BROWSER_PROFILE_BUCKET` to the private bucket
name. The key never appears in the hosted browser pages, logs or model
tool results.

The `BrowserProfileStore` reads/writes only sealed profiles and requires
a server-authenticated owner ID and exact public HTTPS origin. It supports
create-only, conditional replacement and explicit revocation. It stores only
hashed owner/domain object paths, and uses the verified Fernet envelope with
site, owner and expiry binding. The runtime may restore decrypted state
**internally** into Playwright, never into an API response.

## Remaining critical work

- Signed-in person must control browser login and explicitly agree to save
  an account session; browser profiles are extremely sensitive.
- Proper OAuth user identity and session-specific permissions, private
  browser control UI, domain-scoped access, anti-CSRF, short-lived approvals,
  deletion/revocation, monitoring, and HTTPS/browser network isolation.
- Before adding arbitrary external site writes, establish production egress
  controls preventing DNS rebinding, metadata/localhost access, browser-side
  prompt injection, redirects to unauthorized domains, and downloaded files
  escaping the private sandbox.
- Cloud Run's filesystem is transient. **Never** store saved sessions there.
- No external website can be accessed with this module until owner login
  interface and a per-action authorization flow are independently verified.

Costs: Cloud Storage and Secret Manager have small free usage allowances in
eligible US regions but can bill beyond the allowance; budgets and alerts are
necessary. No deployment or billing activation is performed by this change.

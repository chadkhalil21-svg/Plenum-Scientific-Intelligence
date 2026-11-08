# Alternative Auth0 Owner Entrance: one-time setup and protected activation

**Purpose:** bypass a broken Google IAP *owner sign-in* without changing or weakening the original IAP-protected `plenum-computer-browser` Cloud Run service. Reuse our real Playwright, private GCS encrypted profiles and owner browser WebSocket, and Authlib's managed OIDC/PKCE. No new password database or browser engine.

## Status and boundaries

- New, **separate** Cloud Run service: `plenum-browser-owner-auth0` in project `plenum-computer-browser`, region `us-east1`.
- Bootstrap source: `services/computer_browser/owner_auth0.py` with Authlib OpenID Connect, authorization code + PKCE S256, state and nonce checks, signed 30-minute HTTPS/SameSite/HttpOnly owner session and verified exact owner email (and optional pinned Auth0 `sub`). The same source module is inactive in original Google IAP service by checking `K_SERVICE`.
- Reuse exact prebuilt Playwright image `b078968113f0c688873306258c30f1f7aa662457`; Cloud Build adds only Authlib dependencies and current owner routes. No Chromium rebuild.
- On initial bootstrap the separate public HTTPS service exposes **only a welcome/login-link page and health**. No configured OAuth client, so `/auth0/login` returns 503. `/owner` and `/owner/sign-in` return 401, even with forged IAP headers. Private profile bucket and session encryption key are **not attached yet**.
- Public HTTPS reachability is needed for Auth0 authorization redirects; account data and browser controls still require a short-lived **authenticated application session**. Do not interpret public invoker permission on this *separate* portal as permission to access protected routes. Do not apply any of this to the original IAP service.
- Hosted service may accrue bounded Cloud Run and Cloud Build costs; min instances 0, max 1. Auth0 free plan may impose authentication limits.

## Founder-only bootstrap (one command from this chat, no user secrets)

The PR's dedicated owner-only GitHub issue workflow is triggered only by:

- Title: `Computer Browser: bootstrap Auth0 owner portal`
- Body: `OWNER_AUTH0_LOCKED_BOOTSTRAP:2026-11-08`

It builds thin layer using existing image, deploys locked portal and posts its exact new public HTTPS `URL` and expected Auth0 callback URL `URL/auth0/callback` to the private founder issue.

## ONE required human authorization at Auth0

In the founder's *existing* Auth0 tenant (`dev-8sylxsg44yh5kkhh.us.auth0.com`), register or inspect one **first-party Single Page Application (public PKCE client)** for `Plenum Computer Browser Owner`. It is **not** the ChatGPT CIMD OAuth client and does **not** require a client secret.

- Application type: **Single Page Application**, Authorization Code flow with PKCE enabled; token endpoint authentication method `None`.
- Allowed Callback URLs: **exactly** `<portal URL>/auth0/callback` from the bootstrap issue. Allowed Logout URLs and Allowed Web Origins: `<portal URL>`. Enable the required database/passwordless connection for the founder's own account; avoid a Google social connection if Google login is malfunctioning.
- Save the **public client ID** privately as the GitHub repository Actions variable `AUTH0_OWNER_CLIENT_ID` in `chadkhalil21-svg/Plenum-Scientific-Intelligence`. This is not a password or client secret, but still do not paste it in public issues.
- Ensure the founder's Auth0 account email is verified and equals the existing `COMPUTER_OWNER_EMAIL` cloud setting. Optionally pin its exact immutable Auth0 `sub` to `AUTH0_OWNER_SUB` server-side in a subsequent protected release (not necessary for the first email-verified owner login).

No client secret, password, MFA, OAuth authorization code, JWT or website cookie needs to enter ChatGPT or GitHub issue bodies. If an owner-connected TinyFish profile is available, it can automate these **UI configuration** steps with explicit authorization, but it currently has no Auth0 sign-in.

## Owner-only activation (no new build)

After the client is registered and its public ID is saved, create a founder issue:

- Title: `Computer Browser: activate Auth0 owner portal`
- Body: `ACTIVATE_AUTH0_OWNER_CLIENT:2026-11-08`

The activation workflow checks the existing private GCS bucket and session secret, updates **only** the separate Auth0 portal with `AUTH0_OWNER_CLIENT_ID` and encrypted session-vault configuration, and proves:
- Anonymous `/owner` and `/owner/sign-in` return 401.
- `/auth0/login` redirects to Auth0 (302).
- No passwords, OAuth tokens or profile data are written to GitHub.

Then the founder can open `<portal URL>/`, sign into Auth0, and use the already-existing `/owner/sign-in` browser view on a **non-sensitive demonstration website**. Signing in and saving a real demo website session remains UNVERIFIED until actual owner use and readback prove it.

## Still required for full Work/TinyFish parity

A real owner-authenticated chat-to-website PRIVATE task transport is not implemented by a manual owner web UI. The existing GitHub issue bus remains limited to *public* tasks and must never carry cookies, credentials or confidential account data. It must be bridged to an authenticated private worker with DNS/IP egress controls and existing one-use plan approval before general account modifications. A successful Auth0 login alone is not proof of those remaining capabilities.

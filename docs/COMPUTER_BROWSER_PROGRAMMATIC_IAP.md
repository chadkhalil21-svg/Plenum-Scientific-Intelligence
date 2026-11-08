# Chat-to-private Cloud Run: programmatic IAP health probe

**Why:** Founder Google IAP sign-in still returns OAuth redirect error 9. That blocks the owner's *web console*, but does not necessarily block short-lived **service-account JWT** access by a trusted GitHub Actions job. This verifies the connection to the existing Cloud Run service without disabling IAP, creating a public endpoint, deploying software, or using browser credentials.

Google's [programmatic IAP authentication](https://docs.cloud.google.com/iap/docs/authentication-howto) describes service-account JWTs signed with Google IAMCredentials. The JWT audience in this probe is exactly the current service's `/healthz` URL, valid for five minutes, with no wildcard scope.

## What was implemented

- `services/computer_browser/programmatic_iap_probe.py` constructs a bounded claim without keys and validates a non-sensitive private health response.
- `.github/workflows/computer-browser-iap-health-probe.yml` uses the existing GitHub WIF connection, owner-only trigger and `computer-browser-production` environment. It obtains Cloud Run's service URL, signs a JWT with Google's IAMCredentials API, sends it using `Proxy-Authorization`, and reads **only** `GET /healthz`.
- `tests/test_programmatic_iap_probe.py` checks target URL scoping, claim lifetime, identity validity and workflow anti-deployment safeguards.

No signed tokens are printed, uploaded as artifacts or placed in issues. No real login, website navigation, browser commands, file submission or session-state access occurs. The probe does not give ChatGPT a private browser tool by itself.

## How to run

An owner-created public repository issue must have **exact** title `Computer Browser: verify programmatic IAP health` and **exact** body `VERIFY_IAP_HEALTH_ONLY:2026-11-07`. The public issue is merely a non-secret trigger. Alternatively, the owner may use the GitHub workflow's manual dispatch.

The job will print PASS only on a signed private HTTP 200 response matching `plenum-computer-browser` with remote mutations disabled.

## Possible permission blocker

The existing GitHub deploy service account might lack `iam.serviceAccounts.signJwt` on its **own** service-account resource or `roles/iap.httpsResourceAccessor` on the **one Cloud Run IAP resource**. If blocked, the job fails safely with no role changes, and the owner must review the narrowly scoped grants. Do not grant `roles/iam.serviceAccountTokenCreator` at the whole project level; Google warns that this could allow impersonating every project service account.

If the health probe works, the GitHub service-to-service route can bypass the failed *interactive owner OAuth sign-in* for authorized machine-readable requests. It **cannot** bypass identity authorization, access the signed-in owner's other websites, provide a private cookie vault to ChatGPT, or authorize unrestricted site writes. Actual private browser use still needs a secure owner login/consent pathway, a private task transport, an audited approval queue, separate Computer/Prometheus identities and reliable egress restrictions.

Cost: No build or deployment. One Cloud Run health request and ordinary GitHub Actions usage can still incur provider charges outside eligible allowances.

**Verification status:** source/CI and a live invocation must be checked separately. Do not claim programmatic IAP access until an owner-triggered job genuinely returns PASS.

## Real owner-triggered results (2026-11-07)

- [Issue #105](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/105) ran the first probe but did not provide a result comment.
- [Issue #107](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/107) returned `NOT VERIFIED` using the new sanitized callback.
- [Issue #109](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/109) identifies the precise failed **step**: `gcloud iam service-accounts sign-jwt`. Earlier GitHub WIF authentication and service metadata/claim preparation succeeded. No signed request reached Cloud Run.

Next owner-controlled prerequisite: verify that the existing GitHub browser deployment service account is allowed to call `iam.serviceAccounts.signJwt` **on itself only** (e.g., target-resource-scoped `roles/iam.serviceAccountTokenCreator`), and that IAM Service Account Credentials API is enabled. Never grant Token Creator at the whole project level. Inspect the failed Actions step if the reason is uncertain; a failed signing step does not prove which IAM/API subcondition failed. After narrow permission verification, rerun the same owner-only health probe and check any subsequent IAP resource access grant separately.

**Google browser IAP OAuth redirect error 9 remains unresolved for human login, but is not required for the machine-to-machine experiment.** This health probe is not a private logged-in browser or full ChatGPT Work replacement.

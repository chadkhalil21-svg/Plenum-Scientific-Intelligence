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

## November 7 at 10:08 PM ET: signed request returned HTTP 404

The founder granted the deployer service account **Service Account Token Creator on itself**. GitHub's manually dispatched *Verify Computer Browser Programmatic IAP Health* run #4 now passed the identity federation, service metadata, and JWT-signing stages. The signed `GET /healthz` returned **HTTP 404**. This proves signing succeeded, **not** that IAP authorization was granted or that the request reached the container.

Google's Cloud Run troubleshooting guidance says 404 can arise from a wrong URL, an application route, **restricted ingress** or a **disabled default `run.app` endpoint**. Do not infer missing IAP Web App User access from HTTP 404 alone, and do not grant additional IAM roles yet.

A read-only, redacted route metadata check has been added to the health probe. It reports only service readiness, ingress mode, whether the default URL is disabled, and a possible cause. It does not alter ingress, IAP, service identities, or deployments. Run the owner-only workflow again after the updated code is merged. If route metadata is normal, inspect provider request logs and the IAP authorization grant before proposing any changes.

Evidence: GitHub Actions `Verify Computer Browser Programmatic IAP Health (No Deployment)` run #4, screenshot provided in chat. Google reference: https://docs.cloud.google.com/run/docs/troubleshooting

## 2026-11-07: additional read-only findings and exact resource audit

A TinyFish session using the founder-saved Google profile confirmed the active Cloud Run revision is `plenum-computer-browser-00002-8xf`, 100% of traffic, deployed at 19:02:47 EST. Ingress is `ALL`, the default run.app URL is enabled, and IAP plus Cloud Run IAM are both active.

A targeted Logs Explorer search around 22:08–22:16 EST did not show matching Cloud Run revision request logs for the 404; IAMCredentials `GenerateAccessToken` and `SignJwt` entries were observed. No request log **suggests**, but does not prove, a rejection before the container.

TinyFish's project IAM view did not list the deployer's IAP Web App User role or the IAP service agent's Cloud Run Invoker role. **Project-level IAM is not sufficient to conclude these grants are absent**, because they can be applied directly to the IAP Cloud Run resource and Cloud Run service. The IAP resource-policy principals were not fully expanded.

Consequently, the existing no-deployment health probe now executes two extra **read-only** calls: `gcloud iap web get-iam-policy --resource-type=cloud-run --service=plenum-computer-browser --region=us-east1` and `gcloud run services get-iam-policy plenum-computer-browser --region=us-east1`. It prints only sanitized, exact resource-level grant statuses for the deployer and IAP agent; policy files and unrelated principal names are never printed. `unavailable` and `no_explicit_binding` are **not** interpreted as no effective access.

Official Google documentation: https://docs.cloud.google.com/run/docs/securing/identity-aware-proxy-cloud-run and https://docs.cloud.google.com/iap/docs/authentication-howto.

**No permissions or deployment configuration have been changed by this audit.** After CI passes and the code is merged, inspect this audit's results before making any IAM changes.

## November 7 22:59–23:00 ET: exact IAP grant, unchanged HTTP 404

- GitHub [run #6](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42444165574) showed the IAP service agent already had `roles/run.invoker` explicitly on the Cloud Run service. The read-only IAP policy query was *unavailable*, not evidence of a missing grant.
- The founder's saved Google Cloud browser session viewed the actual service-level IAP policy: only the founder was listed. TinyFish then added **only** `serviceAccount:plenum-browser-deploy@plenum-computer-browser.iam.gserviceaccount.com` to `roles/iap.httpsResourceAccessor` on this one Cloud Run IAP resource, preserved the founder's existing access, saved, and reopened the policy to verify both identities. No project IAM changes were made.
- Owner-triggered [issues #113](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/113) and [#114](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/114) still returned HTTP 404 after the access grant.
- Read-only [issue #116](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/116) compared one signed and one unsigned `GET /healthz`. Both returned **identical HTTP 404 HTML pages**, classified as generic not found. This makes a shared front-end/routing response plausible but does **not** prove the origin. Application repository source does include `@app.get("/healthz")`; deployed revision remains `plenum-computer-browser-00002-8xf`.
- Next low-risk diagnostic: sign a new five-minute JWT for the Google Cloud Console-verified canonical Cloud Run domain `https://plenum-computer-browser-98614162800.us-east1.run.app/healthz`, rather than relying solely on `status.url` (which can have an alternate `.a.run.app` form). The owner-only workflow compares the canonical signed response without altering any IAM, IAP, ingress, service, or deployment configuration. The separate JWT can access **only this exact health URL**.

**Do not claim private browser connectivity or fix the 404 until an actual signed health result validates.** 

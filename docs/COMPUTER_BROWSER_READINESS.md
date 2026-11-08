# Computer's cloud browser: zero-cost readiness check

You can ask Computer to test whether the **existing GitHub repository**
is configured to deploy our privately hosted browser. This check never
contacts Google Cloud, deploys anything, opens private accounts or uses
TinyFish. It only reports whether six required settings are present.

Computer can create an issue with the exact title:

`Computer Browser: check cloud readiness`

The existing GitHub Actions infrastructure runs
`Computer Browser Cloud Setup Readiness (No Deployment)` only if the
issue was created by the founder's GitHub account. Computer can then
inspect the job logs and summarize exactly what is missing.

Items checked: Google Cloud project identifier, browser runtime service
account, private login-state bucket, approved Google account, GitHub-to-GCP
identity link, and deployment service identity. The values of secrets
and identities are **never printed**. Missing settings cannot be
created automatically from GitHub, since only Google Cloud's account
owner can grant access. Present values do not prove permissions, billing,
private bucket protections or readiness to deploy.

To complete production setup with minimal typing, the founder can
open the Google Cloud Console, select an existing project, and
authorize the required setup. GCP still needs an actual permission
grant or an owner-launched Cloud Shell process: a GitHub connector alone
cannot administer a Google Cloud account. The private browser remains
undeployed until those steps have been approved.

## Verified live cloud identity checkpoint — November 7, 2026

- Founder configured the private Google Cloud project `plenum-computer-browser`, eligible billing, Cloud Run/Cloud Build/Artifact Registry/Secret Manager/IAP and storage services, two initial service accounts, a dedicated least-privilege build account, private browser-profile and build-source buckets, and secret resources. These were created using founder-run Cloud Shell commands. Cloud Resource Manager API was initially unavailable, then the founder enabled it.
- GitHub environment `computer-browser-production` now contains all six required metadata/identity settings. The presence-only check passed: [GitHub run 42425963324](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42425963324). This alone did **not** test cloud access.
- The first owner-triggered actual federated-identity check authenticated Google successfully but failed because the Cloud Resource Manager API was disabled: [GitHub run 42426234022](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42426234022).
- After API enablement, the **live read-only identity/resource-metadata check passed**: [GitHub run 42426496904](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42426496904), launched through [founder GitHub issue #79](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/79). It verified short-lived workload identity federation, project metadata, browser Artifact Registry, both secrets' metadata without reading their values, the profile bucket and the separate build-source bucket. No deployment, software build, private website session or chargeable browser runtime was initiated.
- Least-privilege dedicated Cloud Build identity and isolated source bucket changes were tested and merged in [PR #76](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/pull/76); the separate read-only cloud identity verification workflow was tested and merged in [PR #77](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/pull/77).

**Historical status before November 7 live deployment:** actual production Cloud Build and Cloud Run deployment; verification of Cloud Run first-time IAP OAuth/Google owner access (a personal Google project may require Cloud Console interaction); independent staging-site login and encrypted session restoration; browser egress safety; approval-gated real website actions; and a deployed OAuth/MCP ChatGPT integration. Do not claim that ordinary ChatGPT chats can yet directly operate logged-in websites with this browser. The manual workflow `computer-browser-cloud-run-deploy.yml` explicitly requires owner-supplied `DEPLOY_APPROVED` and can incur Cloud Build, Artifact Registry, Cloud Run, storage, IAP or network costs despite some free allowances.

## Verified Google Cloud Run deployment — November 7, 2026 (7:02 PM Eastern)

- Founder approved actual Cloud Run deployment from ChatGPT. Computer implemented a founder-only, exact-title/body GitHub issue deployment trigger, retaining independent manual approval, IAM-private `--iap`, 2 vCPU / 2 GiB, minimum instances zero, maximum instances one and concurrency one. [PR #81](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/pull/81) merged.
- Initial [deployment #42427413142](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42427413142) **stopped before the build** because the Cloud Storage safety check used native JSON API IAM field names with normalized gcloud metadata. PR #83 added the documented `--raw` flag without weakening public-access-prevention or uniform bucket-level access requirements.
- The real [Cloud Run deployment #42427584118](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42427584118), launched by founder-authorized [issue #85](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/85), **completed successfully**. Actual Cloud Build succeeded and Google deployed `plenum-computer-browser`, initial revision `00001-2zt`, followed by `00002-8xf` when setting `BROWSER_PUBLIC_ORIGIN`; second revision serves 100% of Cloud Run traffic.
- Private service URL (Google IAP authentication required): `https://plenum-computer-browser-98614162800.us-east1.run.app`. User sign-in path: `/owner`, then `/owner/sign-in`. This is **not a publicly accessible service**. Container availability is established by Google Cloud's successful deployment logs, not by an authenticated owner browser session.
- `gcloud run deploy --iap` warned that this personal, non-organization project might need **one-time Cloud Console IAP OAuth setup**, and the logs do **not** demonstrate that the owner already has IAP access. Official docs: https://docs.cloud.google.com/run/docs/securing/identity-aware-proxy-cloud-run. Owner must verify or configure IAP custom OAuth consent and IAP-Secured Web App User access through the Cloud Run Security tab. No passwords or tokens belong in ChatGPT or GitHub.
- **Still pending before the goal of ordinary ChatGPT control of third-party websites:** confirmed owner access to `/owner`; independently authorized real website sign-in/session restoration; production network egress isolation and action approvals; and a private OAuth2/MCP ChatGPT plugin connection. A successful Cloud Run deployment does **not** give the ChatGPT conversation arbitrary site click/type/upload capability.
- Cloud Build, Artifact Registry, Cloud Run, Secret Manager, IAP and egress can bill even when request-based free allowances apply. Do not claim zero cost; preserve scale-to-zero and single-instance limits.

## Verified live private Cloud Run deployment — November 7, 2026

- Founder approved one private, potentially billable deployment in ChatGPT. Source-controlled PR #81 implemented the exact owner-initiated GitHub issue gate; it was merged after automated tests.
- First authorized deployment failed closed at private bucket metadata parsing without building. PR #83 corrected the check using raw Cloud Storage API field structure and independently passed tests.
- **Second authorized deployment succeeded**: [GitHub Actions run 42427584118](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42427584118). Artifact Registry image successfully built via Google Cloud Build; Cloud Run service `plenum-computer-browser` deployed in `us-east1`, final revision `plenum-computer-browser-00002-8xf` serving all traffic. Private URL: `https://plenum-computer-browser-98614162800.us-east1.run.app`. The deployment command included `--no-allow-unauthenticated --iap`, `--min-instances=0`, `--max-instances=1`, 2 CPU/2 GiB and concurrency 1. No public browser access was granted.
- Google Cloud emitted an **IAP first-time configuration warning** for a project without an organization. Deployment succeeded, but owner browser sign-in and IAP OAuth consent/user entitlement are **not independently verified**. Google says first-time OAuth client configuration may require a Cloud Console step.
- **Still unverified and not claimed working:** live owner IAP access; arbitrary website sign-in/action (initial allowed origin is just `https://example.com`); persistent encrypted real-user session; scoped approval for consequential site mutations; and a real OAuth 2.1 MCP/plugin binding callable from ordinary ChatGPT conversation. The present FastAPI private API is not an MCP tool connection by itself. The Cloud Run service is live as *software infrastructure*, not yet a TinyFish-equivalent private browser accessible from this chat.
- Cloud Build, Artifact Registry, network, storage and running browser invocations may incur charges even with scale-to-zero/free allowances. No cost amount was independently confirmed.

## Live deployed service access control verified — November 7, 2026

- Live security check [run 42428761339](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42428761339) **passed** using Google Workload Identity Federation, authenticated project resource checks, actual Cloud Run service discovery, and Cloud Run IAM policy inspection.
- The service reports `Iap Enabled: true`; its IAM policy contains no public invocation binding for `allUsers` or `allAuthenticatedUsers`. This verifies Google IAP is configured and access is not public, not that a human has successfully signed in.
- [PR #91](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/pull/91) corrected an overly rigid Cloud Run URL format comparison responsible for the first failed read-only audit.
- First owner acceptance test, without terminal commands: sign in through [the owner console](https://plenum-computer-browser-98614162800.us-east1.run.app/owner). If Google reports no access or no OAuth client, owner must configure Cloud Run > plenum-computer-browser > Security > Identity-Aware Proxy and grant owner the IAP-Secured Web App User role. Google documents a manual first-time OAuth setup for projects without an organization. **Do not disable IAP or allow unauthenticated access just to make the page work.**
- To use this independently hosted browser as an ordinary ChatGPT tool, implement a **separate OAuth 2.1-protected streamable HTTP MCP service** and register a private ChatGPT plugin. A Cloud Run IAP-protected FastAPI URL by itself is not MCP and cannot be called through the current GitHub plugin. Do not advertise a plugin until its actual endpoint and authentication work.
- Current initial permitted origin remains `https://example.com`; this is **not** a general-purpose unrestricted browser. Privileged remote website writes must remain user-authorized and auditable. Only after identity and MCP access are independently verified, test synthetic browse/read then account interactions in stages.

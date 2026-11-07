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

**Still not completed:** actual production Cloud Build and Cloud Run deployment; verification of Cloud Run first-time IAP OAuth/Google owner access (a personal Google project may require Cloud Console interaction); independent staging-site login and encrypted session restoration; browser egress safety; approval-gated real website actions; and a deployed OAuth/MCP ChatGPT integration. Do not claim that ordinary ChatGPT chats can yet directly operate logged-in websites with this browser. The manual workflow `computer-browser-cloud-run-deploy.yml` explicitly requires owner-supplied `DEPLOY_APPROVED` and can incur Cloud Build, Artifact Registry, Cloud Run, storage, IAP or network costs despite some free allowances.

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

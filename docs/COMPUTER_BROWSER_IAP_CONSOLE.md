# Computer Owner Console: verified Google sign-in

The private Cloud Run browser gains an initial **Google-account owner screen**.
The security perimeter uses Google's native Cloud Run Identity-Aware Proxy
(IAP), not a custom password form.

The app independently verifies the signed IAP JWT using ES256 Google IAP
public keys at https://www.gstatic.com/iap/verify/public_key-jwk, matching
its expected Cloud Run project/service audience, official issuer,
token lifetime, subject and exact owner email.

- `GET /owner` shows private status and a form to read approved public
  webpages. `GET /owner/public-preview` uses existing real Chromium,
  escapes external content, and has no state-changing browser features.
- No private website logins, private account browsing, upload or submissions
  are enabled. A Google IAP identity only authenticates the human owner
  into our own browser interface. It does not grant our browser access to
  the owner's other Google, GitHub, Kaggle or financial accounts.
- Unsigned IAP user/email headers are *not* accepted. No JWT or email is
  returned in HTML, logs, GitHub, or model tools.
- Requires `COMPUTER_IAP_AUDIENCE` with Cloud Run format:
  `/projects/PROJECT_NUMBER/locations/REGION/services/plenum-computer-browser`.
- Requires `COMPUTER_OWNER_EMAIL` supplied privately as a GitHub Actions
  environment variable and deployed as a Cloud Run environment variable.
- Requires Cloud Run direct IAP (`gcloud run deploy --iap`) and
  `--no-allow-unauthenticated`. Enable IAP API and grant the correct owner
  the IAP-secured Web App User role, plus run.invoker to the IAP service
  identity as Google directs. For a personal Gmail project or a project
  without an organization, Google may require the owner to configure IAP's
  OAuth consent screen through Google Cloud Console the first time.
- Signed-header verification requires public JWK fetch at runtime; allow
  HTTPS to Google's official public key endpoint only for the verification
  library. Verified user identity itself does not authorize website writes.

Official documentation:
https://docs.cloud.google.com/run/docs/securing/identity-aware-proxy-cloud-run
https://docs.cloud.google.com/iap/docs/signed-headers-howto

**Real private browser sessions and custom ChatGPT plugin are separate
upcoming milestones.** No website password should be typed into a ChatGPT
message, GitHub issue or public workflow.

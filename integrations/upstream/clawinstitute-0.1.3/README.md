# Optional Harvard ClawInstitute local research coordination

This directory reuses the official **ClawInstitute** local workshop/message-board and versioned-workspace implementation published by the Harvard MIMS lab. It is an opt-in coordination artifact adapter, not a replacement for the Minister, dispatcher, or an agent framework. The separate AutoScientists orchestrator is **not** imported; its public repository has no verified reuse license.

## Upstream provenance

- Official npm distribution: https://www.npmjs.com/package/clawinstitute/v/0.1.3 (`clawinstitute@0.1.3`, author Shanghua Gao; upstream repository listed as https://github.com/mims-harvard/ClawInstitute).
- Official AutoScientists source references the ClawInstitute local server: https://github.com/mims-harvard/AutoScientists/tree/c71a92343b9a488ed10134be805845b9473ad18f.
- Tarball URL: https://registry.npmjs.org/clawinstitute/-/clawinstitute-0.1.3.tgz ; SHA512 npm integrity `sha512-EOupkVjpDMZov486p0E7tTsX5wjO2XNGYIm+kGs/bsvnCBq8L09kSY1uRZFVZHmyX9JtRIuqWZ6/AwE/eyPbIQ==`; SHA1 `6395a6915336edd6cc984b9376bb59068c2b1de7`. Both verified against the downloaded tarball. Its included MIT license is preserved verbatim in `UPSTREAM-LICENSE`.
- Exact direct and transitive dependencies are locked by `package-lock.json` (npm registry integrity); no dependencies are added to the default Prometheus runtime. Do not execute the upstream CLI, run npm lifecycle scripts, expose the app externally, or enable its frontend.

## Explicit finite use (Node >=22)

Run only as an isolated, deliberate operator action in this directory, with public/non-sensitive research material:

```sh
npm ci --ignore-scripts --no-audit --no-fund
node runner.cjs --run < public-review.json
```

Provide a JSON object with exactly `title`, `proposal`, `critique`, and `revision` (strings; max 200 characters for title, 6000 each for the rest, 24 KB input). The upstream database is initialized in a uniquely created temporary directory; the actual upstream Express application is served briefly on dynamic loopback with auth enabled and an independently generated bearer token. The adapter additionally rejects all unauthorized HTTP requests. It creates a workshop, records the supplied proposal and review with two local role labels, writes and revises a workshop workspace file with version checking, reads both the comment and historical/latest contents, verifies them, and emits a final JSON receipt following upstream diagnostic logs. It closes the server and DB and removes its own temporary directory on ordinary completion or handled failure. A hard 45-second process deadline ends a hung run; such a forced exit might leave that run's temporary directory behind. No arbitrary code, model prompts, browser, public platform registration, external API, persistent host, or external database is used. The `public` local-workspace setting permits role-labelled revisions inside this single-user process; it does not publish externally. These are role labels sharing a local token, **not independent agent credentials**; do not use this local server as a multi-tenant or adversarial-agent security boundary.

## Evidence and limits

`public-review.json` supplies the actual previously reported Sakana v3 baseline observation for a bounded evidence review. `receipt.json` records the successful, single live local execution, using upstream migrations and the original HTTP routes, not a mock or registration-only claim. This demonstrates functional local coordination artifact reuse without new costs, not autonomous scientists, commercial deployment, independent agents, or novel science. It is not a public/production multi-agent service, and no automatic scheduled invocation is added.

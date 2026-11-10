# Plenum Business Workforce | First Adopted Integrations

**Status:** Nine native n8n model-backed specialist drafts and one OpenHands/Qwen3:1.7B syntax-valid coding proposal have been verified on disposable public GitHub runners. No persistent or trustworthy production business-account workforce is deployed.
**Purpose:** Reuse the existing LangGraph orchestrator, official OpenHands SDK,
and n8n's free self-hosted Community edition, without reimplementing their engines.

## Nine specialist drafts via n8n (actual local model after owner setup)

Import `integrations/n8n/plenum-business-workforce.json` into an owner-operated
n8n instance. It is deliberately **inactive**, with manual trigger only.
It dispatches *nine distinct work items* (research, engineering, browser,
creative, marketing, operations, simulation, support, verification) to the
native n8n AI Agent node using a local Ollama chat model. The only attached
agent tool is a calculator. The final node labels each reply as an
**unverified draft awaiting founder review**, not a completed business action.

1. Run n8n Community edition under a protected self-hosted Docker deployment:
   https://docs.n8n.io/hosting/ . Use persistent encrypted storage, HTTPS,
   administrative MFA and restrict access to the owner. Do not expose an
   unauthenticated public editor. Hosting/computing may cost money.
2. Make an owner-controlled Ollama server reachable **privately from n8n**;
   pull a compatible `qwen3:1.7b` model, check license, memory and its
   available disk/compute. In the imported 'Local Ollama' node select its
   owner-created Ollama credential and a model present on that host.
   Never publish local model ports directly to the internet.
3. Inspect each node, then execute the manual trigger and check nine
   founder-review drafts. Only the draft workflow is covered; the n8n
   model connection and end-to-end run require actual deployment evidence.

**Not connected:** Gmail/Resend/Stripe, CRM, Apple, financial records,
private customer data, GitHub code writes or Plenum's private Playwright sessions.
No public webhook, triggers or externally mutable tool is shipped. External
instructions in retrieved material are data, not approvals.

Self-hosted n8n Community is free for Plenum's internal workflows, under the
Sustainable Use License. Businesses cannot offer customer-configurable
n8n-based workflow building as a hosted service without the relevant license.
See https://support.n8n.io/article/can-i-use-your-license-for-my-use-case .

## OpenHands: opt-in coding agent

The repo already pins `openhands-sdk==1.60.1` and separately verified
the official FileEditorExecutor on a disposable synthetic fixture. That
test was **not** an LLM-led software repair.

The new `src/plenum_ai/openhands_coding_agent.py` uses the real OpenHands
`LLM → Agent → Conversation → FileEditorTool` interface. It is designed to propose one inspectable public Python file, syntax-check it, and record a checksum; the actual Qwen3:0.6b trial did NOT produce the required file.
It does not run proposed code or write into a production repository.
Its temporary candidate file is deleted, not auto-merged or deployed.

No-cost default check, on a disposable Python runner:

```sh
python -m plenum_ai.openhands_coding_agent --out reports/openhands-agent-review.json
```

A **real** agent run requires a separately isolated disposable runner,
reviewed pinned SDK and explicit model configuration:

```sh
export PLENUM_EPHEMERAL_RUNNER=confirmed
export PLENUM_OPENHANDS_MODEL='ollama/qwen3:1.7b'
export PLENUM_OPENHANDS_BASE_URL='http://PRIVATE_OLLAMA_HOST:11434'
python -m plenum_ai.openhands_coding_agent --execute \
  --out reports/openhands-agent-review.json
```

Install the pinned SDK in this disposable runner with
`python -m pip install -e ".[openhands_tools]"`. A suitable local
OpenHands-compatible model may not follow file-edit instructions reliably.
Alternatively configure `PLENUM_OPENHANDS_API_KEY` and an approved remote
model (which may incur charges). The SDK uses a six-iteration and $0.20
per-run cap; for local models a suitable compatible endpoint is required.
A secret-bearing or privileged host is **not** a safe substitute for a
container/machine sandbox. The runner attestation environment variable is
a tripwire, not OS isolation; do not provide production credentials.

## Definition of the real, complete workforce

The target is **not** satisfied by nine prompts. Completion requires:

- Each departmental role executes unfamiliar useful tasks using approved
  real tools; multiple tasks independently verified and scored.
- Durable private identity, narrow credentials, per-task authorization,
  observability, failure recovery and idempotency in a real hosted instance.
- Human approval before spending, changing accounts, contacting customers,
  publishing, making legal/financial claims, or deploying code.
- Private data never routed into the public GitHub repository, issue bodies,
  action artifacts or unapproved third-party models.
- Tested rollback, audit trail, human takeover, and measured operating cost.

**Verified independent execution evidence (2026-11-10 UTC):**
- [Native n8n 9-role real-model run #42746275674](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42746275674) passed: local Qwen3:0.6b, real n8n AI Agent, nine review outputs, no production account credentials or external writes. The model's example claims and citations remain unverified.
- [Independent one-role n8n real-model acceptance #42746585905](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42746585905) passed: temporary local Ollama credential, execute-workflow trigger, real draft status and no external account changes.
- [Actual pinned OpenHands trial #42746265510](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42746265510) FAILED the original output criterion: SDK 1.60.1 and official file-editor tool loaded, model interaction ran, but Qwen3:0.6b produced no inspectable proposal.py. A green package installation must not be reported as successful autonomous coding.

[OpenHands Qwen3:1.7B first real syntax attempt #42747513864](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42747513864) created a real Python file but failed independent AST validation. [One bounded-error-feedback model trial #42748382323](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42748382323) subsequently passed its original review-only acceptance: real OpenHands FileEditorTool yielded an inspectable syntax-valid candidate with SHA-256 `dc27ae496620429f633e4cbbb0c6fe09456e52da9c8ad3efe34eb769957c571d`. The new controller and tests permit exactly one model repair pass and reject a second invalid file; the passing run's exact `repair_passes` count was not separately inspected. This is **one narrow syntax outcome**, not a demonstrated correct program, unfamiliar repository repair, deployment or autonomous professional developer.

There is **no persistent production n8n, customer-support agent, Ollama host or verified real company account action**. No paid Render service was created. A capable model and adequate owner-controlled compute, permissioned connectors, independent task-quality evaluation and operational auditing remain necessary for reliable coding/business agents.

Official sources:
- OpenHands SDK: https://github.com/OpenHands/software-agent-sdk
- OpenHands docs: https://docs.openhands.dev/sdk
- n8n self hosting: https://docs.n8n.io/hosting/
- n8n security: https://docs.n8n.io/hosting/securing/

## On-demand free-tier browser deployment from an iPad (added 2026-11-09 ET)

**Not always-on, not suitable for customer accounts or production.** Personal GitHub
Codespaces includes a monthly compute/storage allowance; the GitHub Free
personal plan publicly documents **120 core-hours and 15 GB-month**, or
approximately 60 hours of 2-core use if no other compute is used. Exceeding
the allowance can incur charges if billing permits them. Check your own
account budget and set a zero-dollar spending limit before launching.

1. On a *personal* GitHub repository Codespaces page, create a **2-core**
   Codespace for this repository; browser-based Codespaces works on an iPad.
2. In its terminal run exactly:

   ```sh
   bash integrations/n8n/start-codespace-workforce.sh
   ```

   This intentionally owner-triggered script creates an untracked random n8n
   encryption key, starts n8n and Ollama on a private Docker network, and
   downloads small `qwen3:0.6b` weights; neither an n8n editor nor Ollama
   API is publicly exposed by its Docker Compose configuration.
3. In Codespaces **Ports**, keep port **5678 Private**, open its HTTPS forwarded
   URL, complete n8n admin registration and import
   `integrations/n8n/plenum-business-workforce.json` from the repository.
4. Create n8n **Ollama** credential with `http://ollama:11434` as Base URL,
   no API key, and select `qwen3:0.6b` in the imported Chat Ollama node.
   Run the workflow manually and inspect all role-labelled drafts in the
   founder review node. Public/general text only: never paste passwords,
   private customer records or patent-sensitive information into this demo.
5. Stop the Codespace after reviewing results. Ports stay private by default;
   never switch to Public. Codespaces stop when idle; there is no guarantee
   of continuous 24/7 execution and no claim of business-employee competence.

No new paid Render service was started. The actual always-on version requires
owner-authorized secure hosting, a sufficient model, scoped business-app
credentials, auditing and an independent end-to-end business outcome. For
instant on-demand personal trial, the Codespaces approach avoids the cost and
risks of provisioning permanent infrastructure before acceptance.

Official references: [GitHub Codespaces billing](https://docs.github.com/en/billing/concepts/product-billing/github-codespaces),
[Codespaces private ports](https://docs.github.com/en/codespaces/reference/security-in-github-codespaces),
[n8n Community hosting](https://docs.n8n.io/hosting/).

# Plenum Business Workforce | First Adopted Integrations

**Status:** Source integration in review; not a live, complete autonomous company.
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
`LLM → Agent → Conversation → FileEditorTool` interface. It can propose
one inspectable public Python file, syntax-check it, and record a checksum.
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
`python -m pip install -e ".[openhands_sdk]"`. A suitable local
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

**Deployment evidence as of this source change:** Plenum has no n8n service
in the connected Render service inventory. No n8n server, Ollama endpoint,
genuine OpenHands LLM run or autonomous customer task has been deployed or
verified by this integration. Do not claim otherwise.

Official sources:
- OpenHands SDK: https://github.com/OpenHands/software-agent-sdk
- OpenHands docs: https://docs.openhands.dev/sdk
- n8n self hosting: https://docs.n8n.io/hosting/
- n8n security: https://docs.n8n.io/hosting/securing/

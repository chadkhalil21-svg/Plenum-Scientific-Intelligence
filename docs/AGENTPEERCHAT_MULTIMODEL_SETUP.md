# Plenum AgentPeerChat Qwen/Gemini setup

General-purpose **public-only** multi-model group conversations. Reuses the existing AgentPeerChat Cloudflare Worker, original Plenum GitHub Actions and original Qwen/Ollama runner. No new host, duplicate minister or paid model plan.

## Verified and pending

The Worker is deployed and the owner has signed in. Qwen/Gemini live agent identities and model-to-model conversation are NOT verified yet. Generating an invitation is not the same as connecting an agent. The scheduled bridge is every 30 minutes, not continuous realtime; the GitHub Actions runners remain ephemeral.

## One-time private owner actions

1. In the existing AgentPeerChat owner page choose **Connect your agent** and generate a **fresh** invitation named exactly **Plenum Prometheus — Qwen**. Keep the invitation's agp_ code private. Revoke any older shared invitation.
2. Repeat with the exact name **Plenum Prometheus — Gemini**.
3. Open original GitHub repository chadkhalil21-svg/Plenum-Scientific-Intelligence → Settings → Secrets and variables → Actions → New repository secret. Save five different private secrets:
   - PLENUM_APC_QWEN_INVITE: Qwen's fresh agp_ plus 64-hex-character invitation code.
   - PLENUM_APC_QWEN_KEY: self-generated agt_ followed by at least 48 random alphanumeric characters (recommend 64).
   - PLENUM_APC_GEMINI_INVITE: Gemini's fresh agp_ invitation code.
   - PLENUM_APC_GEMINI_KEY: a DIFFERENT agt_ plus at least 48 random alphanumeric characters.
   - PLENUM_GEMINI_API_KEY: a Gemini API key from Google AI Studio with verified zero-charge usage. Check Google's free-tier data-use terms; do not transmit confidential Plenum information.
4. After merging this PR, run GitHub Actions → **Plenum Council | AgentPeerChat Qwen and Gemini** → **Run workflow**. The one-time on-demand run claims the invitations by SHA-256 token proof, with the actual bearer keys remaining in private GitHub Actions secrets. The next scheduled runs reuse the same authenticated identities without a local profile. Never put tokens, codes, response bodies, customer data or keys in public issues or logs.
5. In the AgentPeerChat owner UI create a group titled exactly **Plenum AI Council — Public** with owner and both authenticated agents. Send a harmless question such as: "What are three inexpensive ways a new rideshare platform can recruit riders and drivers?" Run the workflow once manually to get first-pass Qwen and Gemini replies. Another invocation processes one round of their cross-critique.

## Runtime behavior

The bridge considers only the exact public group with the actual owner as a member. Qwen runs through existing local Ollama qwen3:1.7b on GitHub Actions; Gemini uses the authorized Google API model gemini-2.5-flash, overridable using GitHub variable PLENUM_GEMINI_MODEL when free offerings change. Inference does not start when no actionable messages exist. Message reply IDs and stable idempotency keys prevent duplicate work after a crash; ACK occurs only after a reply is saved. AI agents do not treat peer messages as system instructions, use private accounts or trigger external business actions. A peer's initial answer can receive one critique; a critique cannot trigger further replies.

## Acceptance rule

Do not call the council connected until both distinct providers actually answer a real founder question in the AgentPeerChat group, show reply IDs, and ACK the messages. Passing local code tests, activated identities or an empty green workflow are insufficient evidence. Free quota and external provider limitations must be reported rather than hidden.

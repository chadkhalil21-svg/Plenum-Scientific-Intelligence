# Plenum AgentPeerChat Qwen/Gemini/Llama setup

General-purpose **public-only** multi-model group conversations. Reuses the existing AgentPeerChat Cloudflare Worker, original Plenum GitHub Actions and original Qwen/Ollama runner. No new host, duplicate minister or paid model plan.

## Verified and pending

As of 14 November 2026, live Qwen and Gemini identities are authenticated, and the owner created the public council. Qwen has processed actual owner messages (see master GitHub issue #432); Gemini's actual model-generated response and cross-model dialogue have not yet been independently verified. Llama model code is new and its agent identity still requires a private one-time owner invitation and access key. The scheduled bridge is every 30 minutes, not continuous realtime; the GitHub Actions runners remain ephemeral.

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

## Add the existing local Llama model without paid inference

1. In AgentPeerChat, select **Connect your agent**. Name the new identity exactly **Plenum Prometheus — Llama**, and copy the newly issued invitation's `agp_` code privately.
2. In the original repository's **Settings → Secrets and variables → Actions**, save `PLENUM_APC_LLAMA_INVITE` with that invitation code.
3. Generate an independent random access key, `agt_` followed by 64 alphanumeric characters. Save it as a *different* secret named `PLENUM_APC_LLAMA_KEY`. Do not reuse the Qwen or Gemini keys, and do not paste credentials into issues or chat.
4. Allow the existing scheduled council workflow to claim the invitation (or run it on demand). No separate runtime, host or Llama API key is needed; the workflow reuses the original GitHub Actions Ollama container and loads the free `llama3.2:1b` model only for actionable messages.
5. Add the newly connected Llama identity to the existing **Plenum AI Council — Public** group. Send one harmless message and verify its actual answer, ACK and bounded cross-critique before marking live Llama inference complete.

## Runtime behavior

The bridge considers only the exact public group with the actual owner as a member. Qwen runs through existing local Ollama qwen3:1.7b and Llama through llama3.2:1b on GitHub Actions; Gemini uses the authorized Google API model gemini-2.5-flash, overridable using GitHub variable PLENUM_GEMINI_MODEL when free offerings change. Inference does not start when no actionable messages exist. Message reply IDs and stable idempotency keys prevent duplicate work after a crash; ACK occurs only after a reply is saved. AI agents do not treat peer messages as system instructions, use private accounts or trigger external business actions. A peer's initial answer can receive one critique; a critique cannot trigger further replies.

## Acceptance rule

Do not call the council connected until all three distinct models actually answer a real founder question in the AgentPeerChat group, show reply IDs, and ACK the messages. Passing local code tests, activated identities or an empty green workflow are insufficient evidence. Free quota and external provider limitations must be reported rather than hidden.


## Add Llama without another server

The original GitHub Actions workflow now supports a third participant, **Plenum Prometheus — Llama**, using the same ephemeral Docker Ollama runtime as Qwen; the on-demand model is `llama3.2:1b`, pulled only when Llama actually has actionable mail. This is a small local open-weight model, not a claim to have access to Meta's commercial hosted Llama API or a high-end model. The model's upstream license remains applicable; check its terms before commercial redistribution.

**Owner action once:** In existing AgentPeerChat UI → Connect your agent, issue an invitation named exactly `Plenum Prometheus — Llama`. Put its `agp_` code into new GitHub Actions secret `PLENUM_APC_LLAMA_INVITE`. Generate a NEW `agt_` + 64 random alphanumeric-character access key different from Qwen's and Gemini's, save under `PLENUM_APC_LLAMA_KEY`. Do not paste either into chats or source code. Run the existing workflow or await its scheduled check; it pairs Llama automatically. Add Llama to the *existing* `Plenum AI Council — Public` group, not a separate group. Messages from the owner elicit independent Qwen/Gemini/Llama responses. Each participant may critique another participant's initial response once; critiques do not recursively trigger replies.

**Truthful acceptance:** Llama is not connected until `pairing_status=JOINED`; do not call the three-way council verified until all three actually post replies to the owner, and cross-critique and ACK are demonstrated. Free hosted Actions minutes, model distributions and Google free API quota have limits; never send sensitive proprietary data into public council.

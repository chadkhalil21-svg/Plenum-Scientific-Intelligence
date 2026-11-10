# Plenum WhatsApp-first AI workforce — verified platform limitations

Decision: **2026-11-10 UTC.** Founder prioritises WhatsApp over Telegram. Our original [Hermes source and ten-role roster](./README.md), `integrations/hermes/roster.json`, original LangGraph Chief, nine n8n role prompts, four working founder-public-task routes and pinned Superpowers coding skill remain unchanged. **No owner WhatsApp/Meta account or group has been connected.**

## Newly verified first choice for direct named chats: Meta WhatsApp Agent Platform beta

**WhatsApp itself officially documents third-party Agent chats**, with **up to five connected agents** for an eligible founder WhatsApp account. This feature is *not* generally available: Meta restricts country/account rollout. The app path is **WhatsApp Settings → Agents → Create an agent → open agent chat → Chat info → API key**. Each enabled agent appears as its **own direct chat** in WhatsApp. **They cannot join existing group chats or see other conversations.** Chats with these third-party agents are **not end-to-end encrypted** (messages pass through Meta). No payment or business-number requirement is documented for this beta route; that does *not* establish that an LLM host or inference costs nothing.

The reviewed community [WhatsApp Agent Platform Hermes plugin](https://hermes-agent.nousresearch.com/marketplace/whatsapp-agent-platform) (Hermes catalog release 0.2.1, pinned source SHA `3a57b1da04499279d1af6c7d979c9c2d8b658ce0`) connects to **Meta's official `https://api.whatsapp.com/agent/v1` API** using persistent outbound long polling, **no public webhook, separate SIM/phone number, QR pairing or unofficial Baileys bridge**. The plugin is community-maintained, **not Meta-built or NousResearch-operated**; the original MIT implementation must be reviewed before installing. It requires official Hermes **>=0.21.4** and a host capable of continuously polling; read the [actual privacy/capability disclosure](https://github.com/NousResearch/hermes-agent/blob/main/plugin-catalog/whatsapp-agent-platform.yaml). Default creator-only inbound allowlist; keep `WHATSAPP_AGENT_PLATFORM_ALLOW_ALL_USERS=false` and `WHATSAPP_AGENT_PLATFORM_MEDIA_ENABLED=false` until deliberate media authorization. Messages/files can reach the configured model provider; do not share corporate secrets by default. Per-agent outbound messaging is limited to 12 sends/minute.

**Proposed owner-facing activation if the beta feature is actually visible:**
1. Create **one WhatsApp Agent called Plenum Chief of Staff** in the WhatsApp app; use official Chat info to obtain the agent API key and save it privately to the trusted Hermes host (NEVER GitHub/chat). Install the reviewed plugin there via `hermes plugins install whatsapp-agent-platform`, then enable it only on the Chief's authorized profile.
2. Use our existing **all-nine Hermes delegation config** (`python integrations/hermes/prepare_whatsapp_chief.py`) to route Chief requests to real enabled specialist profiles. A Chief reply labeled `[Research]` is not a distinct WhatsApp account; report who actually executed and independent evidence.
3. If the founder wishes, register **up to four more** visible individual WhatsApp Agent chats for **Research, Coding, Verification, and Browser** *only after* confirming this Hermes community plugin can safely support multiple unique API keys and separate Hermes profiles. Do not assume one plugin process accepts five simultaneous different agents or that merely naming a profile registers a WhatsApp Agent. Additional specialists remain routed behind Chief.
4. Verify one **real message** from the WhatsApp creator to Chief, one actual delegated specialist task, and one independent provider readback before marking the channel active. No number, agent API key, live WhatsApp session or host exists in the project yet.

If **Settings → Agents** is unavailable, do not bypass the Meta rollout. Use the existing supported [Meta Business Cloud API DM](#a-supported-safest-whatsapp-dm-recommended-immediately) on a dedicated authorized business number (Cloud Run HTTPS webhook is suitable) or, to obtain a **literal WhatsApp group**, request specific founder consent for a **dedicated expendable account** with Hermes's unofficial Baileys integration running on an owner-controlled persistent host. The Agent Platform beta **does not** supply group conversations. Do not pair the founder's personal WhatsApp to Baileys.

Official first-party source: [WhatsApp Help Center — Third-party agents](https://faq.whatsapp.com/1050934623978152). Hermes source: [catalog entry](https://github.com/NousResearch/hermes-agent/blob/main/plugin-catalog/whatsapp-agent-platform.yaml), [reviewed community source](https://github.com/ahtishamdilawar/hermes-whatsapp-agent-platform/tree/3a57b1da04499279d1af6c7d979c9c2d8b658ce0).

## First objective: one WhatsApp Chief, nine named departments behind it

One owner-controlled **dedicated** WhatsApp contact called *Plenum Chief of Staff* is the sensible first step. The founder can message "Chief, ask Research to..." or "Coding, review..." and the **Chief may delegate** to isolated Hermes specialist profiles using Hermes's existing `delegate_task` and official `advanced-delegation` **`profile_routes`**, rather than running ten different WhatsApp phone numbers. The Chief should label each returned response, e.g. `[Research]`, `[Coding]`, and indicate when a worker has **not** actually run. A profile or prompt does not automatically perform a verified task: it must have a model, specifically approved tools, and independently checked output. The existing original Deep Agents Chief and existing GitHub task bridge stay available; this interface must not secretly elevate its authority.

**A literal WhatsApp group with separately visible bot contacts is a DIFFERENT, harder goal.** One official Business Cloud API bot only supports direct messages in the current Hermes `whatsapp_cloud` adapter. Meta's WhatsApp Groups API exists but requires an **Official Business Account** and permits only **8 participants**, **one** Cloud API business per group, and per-message charges; Hermes `whatsapp_cloud` **does not yet implement group support**. Do not assume Plenum has official Groups API entitlement. Its current documented group method is **unofficial Baileys/WhatsApp Web**, with account-restriction/session risks, and each independent WhatsApp bot contact requires a separately registered WhatsApp number/session. The founder's regular personal account MUST NOT be paired to an unofficial bridge. If a separate, expendable authorized test number is available, a private group with founder + **one** dedicated Hermes Chief account (and a profile-routed internal team) is a possible owner-approved experiment. Keep all message sender and group allowlists strict, `require_mention: true`, and do not use it with customer or patent information. **Never activate Baileys silently.**

## Two platform routes, whichever the owner can legitimately authorize

### A. Supported, safest WhatsApp DM (recommended immediately)
Use the **official Meta WhatsApp Business Cloud API** through the existing Hermes `whatsapp_cloud` adapter, on a **dedicated business number**, not the owner's personal WhatsApp. Requires a Meta Business account, a Meta app with WhatsApp, its phone number ID, official WhatsApp API access token and app secret, founder phone allowlist and a public HTTPS webhook endpoint. It does NOT provide a real WhatsApp group, nor unrestricted free outbound announcements after 24 hours. The Hermes wizard is `hermes whatsapp-cloud`. Use Meta's verified webhook signatures, never paste tokens into the public repository, issue, group or ChatGPT. Replies to user-initiated messages during the allowed service window may be free; other messages/templates, additional services and cloud overages may be billed, so do not claim all WhatsApp communication is universally free.

For an HTTP webhook with idle periods, an **existing owner-authorized Google Cloud Run** service can scale to zero using request-based billing, `min-instances=0`, and stay within monthly free quotas if usage permits. It would need an **actual approved deployment and integration** that restores task state externally; Cloud Run is **not** a persistent 24/7 Hermes polling process or free always-on Ollama provider. Do not attach Meta webhooks to Plenum's existing private browser Cloud Run service or reuse its identity/credentials.

### B. Genuine WhatsApp group (requires an explicit dedicated-number risk choice)
Hermes's native group adapter uses **unofficial Baileys**, with QR/device pairing and account risk. The native `hermes whatsapp` setup wizard supports a group allowlist. On a separate expendable owner-controlled account only, after authorization:
- Set `whatsapp.group_policy: allowlist` and enter **the actual known group JID** in `whatsapp.group_allow_from`; never use `open` or `WHATSAPP_ALLOW_ALL_USERS=true`.
- Allow only the founder's WhatsApp user ID/number, set `require_mention: true` and `unauthorized_dm_behavior: ignore`.
- Keep WhatsApp session files under owner-private persistent encrypted storage (Hermes recommends permissions `0700`) and use only approved, least-privilege tools.
- Begin with ONE Chief WhatsApp account and route actual `delegate_task` outputs to three isolated internal profiles (Research, Coding, Verification), rather than registering 10 phone numbers. Each output explicitly says which specialist acted and what was verified.
- Hermes needs a continuously running Node/Baileys bridge, so **a free Oracle A1 VM (if available) or existing always-on owner-controlled server** is more appropriate than Cloud Run's request-driven idle scale-to-zero.

**Never claim the group is connected until a real owner-authenticated group message, an actual specialist task, and an independently verified WhatsApp reply have occurred.** No number/QR/token/session is presently available in our connected provider tools.

## Complete nine-specialist Chief routing (prepared, not connected)

The existing roster defines **one Chief and nine named specialists**. The new `integrations/hermes/prepare_whatsapp_chief.py` reads the exact approved roles and prepares the official Hermes `advanced-delegation` `profile_routes` configuration. It does not install Hermes, create an AI model, enable a WhatsApp number, start an instance or copy credentials.

On a future owner-controlled host, first run `python integrations/hermes/prepare_whatsapp_chief.py` to inspect the safe plan. After provisioning approved profiles and installing Hermes 0.22.5+ and its official `advanced-delegation` plugin in the Chief profile, run `python integrations/hermes/prepare_whatsapp_chief.py --output ~/.hermes/plenum-chief-routes.yaml` to write a fresh private `0600` YAML snippet. Copy its `delegation` block into the Chief's private configuration after reviewing; it will not overwrite existing `config.yaml`.

**Pilot:** begin with Research, Coding and Verification, two concurrent specialist tasks. The all-nine configuration is an authorized role manifest, not proof all nine profiles have models or can run yet. Hermes declines unavailable roles, not silently substituting one model for a different specialist. For a real WhatsApp group, the Chief is one actual group participant and may report outcomes labeled `[Research]`, `[Coding]`, etc. Nine individually visible WhatsApp bots would each need a separate authorized number/session. Official Hermes Cloud API remains DMs-only; Baileys is unofficial and must use a dedicated expendable number after owner risk approval.

## Minimal native specialist delegation configuration

Hermes officially supports named profile routing **with the built-in advanced-delegation plugin enabled**. An example of nonsecret roles to add to the **private Chief profile** `config.yaml` *only after* approved profiles and models exist:

```yaml
delegation:
  backend: profile_routes
  max_concurrent_children: 2
  backends:
    profile_routes:
      profiles:
        - name: research
          description: Public scientific research, with source-linked citations.
        - name: coding
          description: Review-only coding proposals and changed-behavior tests.
        - name: verification
          description: Independent checking of reported outcomes and evidence.
```

Security caution: according to Hermes, `profile_routes` makes the Chief able to access the selected profiles' **own credentials and enabled tools**. Thus keep those profiles limited to public-read-only duties until proper per-account authorization. Do not enable private, banking, payment, email-sending, or production tools via those routes. Use the existing `plenum-public-workforce` plugin for exact owner-scoped **public GitHub issue creation/status** only after its owner credential is installed privately and a real invocation has been proven. Neither routing configuration nor plugin files alone establish real provider access.

## Free hosting decision (official current pricing checked)

1. **Oracle Always Free A1**: first candidate for a small always-connected, private group gateway and limited CPU-only model. Official documentation currently allows **1,500 OCPU-hours and 9,000 GB-hours monthly** (equivalent to 2 OCPUs and 12 GB RAM for the month). Capacity can be unavailable and truly idle instances can be reclaimed. A new Oracle account might require payment-card validation. **No Oracle VM or account has been verified/created here.**
2. **Google Cloud Run**: best for official WhatsApp HTTPS webhooks *on demand*, scale-to-zero; the request-based free quota includes **2 million requests, 180,000 vCPU-seconds and 360,000 GiB-seconds monthly**, aggregated at the billing-account level. It is not an always-on unofficial WhatsApp Web client, nor is remote AI inference automatically free. Needs proper Meta account, identity, encrypted secrets and actual endpoint validation.
3. **Google Always Free e2-micro VM**: eligible US regions, one 1 GiB VM + standard disk; suitable only for lightweight orchestration/gateway at best. A normal externally assigned IPv4 is additionally billed (Google's published network rate **$0.005/hour** except limited free allowance). No guarantee of strictly $0 if that or other chargeable services are enabled. Unsuitable for meaningful local Qwen model capacity.
4. **Cloudflare Workers/D1 / Azure Container Apps / AWS Lambda**: possible free webhook relays within quotas, not free continuously running Hermes/Qwen gateways. **Render Free** spins down and loses local filesystem state, **Hostinger** is paid. Do not install overlapping infrastructure solely to host another interface.

Source documentation: [Hermes official WhatsApp](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/whatsapp), [Hermes Cloud API](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/whatsapp-cloud), [Hermes delegation and profile routes](https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation), [Meta Groups API eligibility/limits](https://docs.360dialog.com/docs/messaging/groups), [Oracle Always Free](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm), [Google Cloud Run pricing](https://cloud.google.com/run/pricing), [Google e2 micro](https://cloud.google.com/products/compute), [Google IPv4 network pricing](https://cloud.google.com/vpc/network-pricing).

## Honest current status
- ✅ The first Hermes profile roster, opt-in Telegram public task notice, Superpowers engineering methodology and bounded public GitHub issue plugin have been merged previously as PR #348.
- ✅ An official / unofficial WhatsApp comparison and safe first configuration are now specified.
- ⛔ **No actual WhatsApp account, Meta Groups eligibility, Baileys pairing, user/group allowlist values, Oracle VM, Cloud Run webhook, or WhatsApp live message is connected**. An actual group cannot be configured by guessing the owner's phone/account state or copying ChatGPT OAuth tokens into Hermes.
- ⏭️ The next truly new acceptance is one owner-controlled dedicated WhatsApp registration **or approved Meta Business API account**, then a real verified message through the chosen service and one actual delegate response. No need to rerun mature LangGraph/Qwen or other fixed scientific benchmarks.

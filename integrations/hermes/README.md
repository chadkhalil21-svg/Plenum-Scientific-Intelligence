# Plenum: Hermes named-agent group chat — prepared, not yet activated

**Prepared on 2026-11-10.** Official [Hermes Agent](https://github.com/NousResearch/hermes-agent) MIT source reviewed at immutable commit `825322b16656905a4607be2fd6ce3d3db7d6b4a7`. [Superpowers](https://github.com/obra/superpowers) MIT source reviewed at `22f0b463e7a5e579904dd6211a520321035526f7`. Plenum's original Deep Agents Chief of Staff, nine n8n profiles, four public issue routes, browser, coding tool, and durable ledgers are preserved. **Hermes would be the messenger, not a replacement Chief or new science backend.**

## What is ready
- `roster.json`: ten named role profiles — Chief + nine existing specialist functions. Zero new AI model instances or customer-account permissions.
- `provision_profiles.py`: default **safe plan only**; on a trusted owner-controlled machine with official Hermes installed, `--apply` creates only selected isolated profiles and original Plenum SOUL.md rules. It never starts a server, contacts Telegram, clones secrets, overwrites a profile, or purchases compute.
- `skills/plenum-coding-superpowers/SKILL.md`: portable original Plenum engineering guidance adapted from the licensed Superpowers workflow.
- Existing GitHub Issue command inbox now has an **optional outgoing Telegram status notice** after each approved public task; group notices include role, issue link and status only, never an objective, prompts, code, personal records or passwords. Works *once* Telegram credentials exist in the GitHub repository's encrypted secret, with no permanent bot server needed for outgoing messages.

## Recommended communication experience
**Telegram group FIRST**: Create a private group for founder + Chief + Research + Coding. Hermes officially supports `@botusername` routing, allowlisted founder Telegram ID, `require_mention` and `exclusive_bot_mentions`; each separately named Telegram bot needs its **own BotFather token and own Hermes gateway profile**. A single generic bot can relay a roster menu, but individual Telegram names require distinct identities. Roll out 3 gateways first, then add other approved roles as useful; do not run ten model loops all day.

On an approved free VM with an owner-supplied authenticated account (not in public GitHub):
1. Install official Hermes on that VM after reviewing source at the pinned commit above. Use the official installer docs, but do **not** pipe an unpinned remote shell script blindly.
2. Run `python integrations/hermes/provision_profiles.py` (shows plan without changing anything). Then `python integrations/hermes/provision_profiles.py --apply --roles chief research coding` in a trusted checkout. Existing profiles are left untouched.
3. Create **three distinct Telegram bots** through [@BotFather](https://t.me/BotFather); put their private tokens into **separate secured Hermes profile credential stores**, never into issues, .env.example, GitHub files or chat text. Obtain the founder's Telegram numeric user ID through the official Telegram app and set `TELEGRAM_ALLOWED_USERS` to **that one ID**, not `*`. Add each bot to the founder-owned private group.
4. Apply the official Telegram safety settings in each separate profile's private `config.yaml`:
   ```yaml
   telegram:
     require_mention: true
     exclusive_bot_mentions: true
     bots_require_mention: true
   ```
   Keep group sender allowlist narrow. Each role gets its own bot token. Do **not** set `TELEGRAM_ALLOW_BOTS=all` without explicit per-bot mention enforcement (loop risk). Use `hermes -p <role> gateway install` only after tokens, model, least-privilege toolsets and secure persistent host are configured and approved.
5. Add **the one status-reporting Telegram bot token** to the **private GitHub Actions secret** `PLENUM_TELEGRAM_BOT_TOKEN`, and private Telegram group ID to repository variable `PLENUM_TELEGRAM_CHAT_ID`. This opt-in receives verified-status summaries from currently supported public issue tasks; it does not allow members of Telegram to create private GitHub tasks. No secret or connection has been configured automatically.
6. Coding role only, after plugin/security review: set `SUPERPOWERS_DISABLE_TELEMETRY=1` in its private runtime environment, then `hermes -p coding plugins install obra/superpowers --ref 22f0b463e7a5e579904dd6211a520321035526f7 --enable`. This is the upstream officially supported pinned plugin method. It should not enable file writes, shell, deployments or customer-account tools without separate granular approval.
7. Talk to `@chief_bot`, `@research_bot`, or `@coding_bot` in a **private Telegram group**. Separate Hermes profiles have separate memories by design. The original Plenum Deep Agents Chief and actual original workers are **not automatically linked just because Hermes profiles were created**. For public work, we already have the working GitHub Issue bridge accessible here; a private Telegram-to-issue command adapter still requires approved least-privileged GitHub credentials and authorized sender verification.

**WhatsApp**: Hermes can connect to WhatsApp group chats through the **unofficial Baileys bridge**, but the developer documents a risk of account restrictions and session credential exposure. Official Meta WhatsApp Cloud API currently supports only direct-message conversations in Hermes v1, and real groups are capability-gated. **Do not connect the founder's personal WhatsApp account to an unofficial always-on bridge.** Prefer Telegram group now and consider official WhatsApp Business direct messaging later if a dedicated business number and Meta permissions are authorized.

## Free hosting decision
See [HOSTING_FREE_AGENT_GATEWAYS.md](HOSTING_FREE_AGENT_GATEWAYS.md). **Recommended $0 candidate:** Oracle Always Free A1 VM (subject to account approval, home-region capacity and idle reclaim); **Google Compute e2-micro** may host a tiny messenger but its 1 GB RAM is not a Qwen/n8n engine, and public IPv4 can cost money. **Google Cloud Run** is a request-driven webhook route with `min-instances=0`, not a guaranteed 24/7 Hermes polling gateway.

## Independent launch criteria — NOT YET PASSED
- Owner-created Telegram bot tokens (never disclose in chat) and a founder-owned private Telegram group.
- Owner-approved private runtime and persistence, measured below $0 cap; no general paid cloud deployment.
- At least ONE real group message from the verified founder to a named Hermes specialist, one provider-authenticated reply and one independent audit trail.
- For actual GitHub issues from Telegram: one founder-authenticated delegated task with exact allowed public objective and limited provider identity, evidence-bound end-state comment. No private customer, patent, email, payment or release action authorized.

**What is NOT live:** Hermes host, Telegram bots, WhatsApp bridge, private credentials, Superpowers executable plugin or named AI employees in a real messaging chat. The code and original reusable method are prepared; the human-controlled Telegram/hosting account step remains genuinely necessary.

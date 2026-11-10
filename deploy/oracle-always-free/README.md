# Plenum Prometheus | Oracle Always Free staging

**State 2026-11-10:** prepared configuration; **NO Oracle tenancy, virtual machine, domain, payment method, persistent agent, or business OAuth has been provisioned or verified from ChatGPT.** This is a zero-new-cost *candidate*, not a deployed service. Do not infer that a public GitHub repository can authenticate to Oracle.

## Founder decision: Oracle FIRST, existing Plenum first (November 10, 2026)

This guidance reflects the current Oracle official Always Free limits and independently searched 2025–2026 YouTube tutorials. **No tenancy, VM, credential, service or model was created by this document.** The original [owner activation issue #384](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/384) remains the sole infrastructure gate.

**Why not Cloudflare first?** Cloudflare Workers Free allows only 10 ms CPU per HTTP request, excellent for tiny webhook or DNS functions but not a resident n8n, Hermes or local Qwen server. OCI A1 offers a genuine ARM64 Linux machine with 2 OCPU / 12 GB equivalent if an Always Free resource is available in the founder's home region. Cloudflare is optional, not a prerequisite.

**Use OCI's other included primitives before adding more providers:** up to 200 GB combined boot/block volume with five included volume backups; 20 GB total Object Storage for independent encrypted backup copies (50,000 Object Storage API requests/month); 150 Always Free Vault secrets with version limits; free OCI Bastion; included Monitoring and Notifications. A standalone external Neon/Qdrant/Cloudflare database or paid secrets manager is unnecessary until an independently established requirement exists. Verify each quota in the actual tenancy and keep backup encryption keys under founder control. Refer to [Oracle's official full free resource table](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm).

**Minimal deployment order, not another platform rebuild:**
1. Owner authenticates in OCI at [cloud.oracle.com](https://cloud.oracle.com/), checks home region and quotas under Governance & Administration > Limits, Quotas and Usage, and confirms an **Always Free eligible** A1.Flex shape. If absent, check another availability domain in the *same* home region; do not upgrade to Pay As You Go to chase capacity or create multiple free accounts.
2. Provision **one** 2-OCPU/12-GB Ubuntu ARM64 A1 VM only after verified always-free capacity, eligible boot/volumes, zero-amount cost review and founder consent. SSH keys and the n8n editor remain private. Prefer OCI Bastion or narrowly scoped SSH for administration; never open ports 5678/11434 to the Internet.
3. Reuse the *already checked-in* n8n+Ollama Compose and the existing nine roles; validate one original founder task and restart/checkpoint recovery. Keep **one shared on-demand CPU model** rather than one per department. This free machine is **not** a powerful GPU inference farm; do not add Paperclip, Coolify, Hermes and duplicate orchestration concurrently before a measured memory/CPU requirement.
4. Once the original worker is reliably serving tasks, consider upstream Paperclip's native Hermes adapter **only if** task management or messaging provides incremental value; preserve the original Chief and verification ledger. For a genuinely needed messaging gateway, use a single scoped Hermes profile (not ten resident bots).
5. Configure disk/credential backups, a basic heartbeat and independent task result readback, with stop-on-exceeded quotas. Do not generate synthetic busywork to avoid reclamation: Oracle may reclaim A1 machines idle under its seven-day CPU/network/memory criteria. Keep the current GitHub public task path as an intermittent fallback.

**Leading published operating guidance:** [Microsoft durable agent workflows](https://learn.microsoft.com/en-us/azure/durable-task/sdks/durable-agents-patterns) recommends checkpoints around non-deterministic calls; [AWS efficient agent orchestration](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentperf05-bp01.html) recommends bounded depth/fan-out and cycle detection. Plenum already has deterministic routing and SQLite science checkpoints; reuse these before installing another task engine. Always independently verify *outcomes*, not only a successful installation or generated draft.

**Video findings (not deployment evidence):** [Sanchit Tanwar, October 25 2026](https://www.youtube.com/watch?v=W2sFAqT0COY) demonstrates Oracle ARM64 + Hermes/Docker/Telegram but includes a suggested PAYG upgrade and separate model provider—*not* an acceptable strict-$0 default; [Anaam Rasool, November 1 2025](https://www.youtube.com/watch?v=mfTBWSa0XBI) demonstrates Oracle + n8n but advertises an old 4-OCPU/24-GB tier, superseded by current official 2/12 limits; [Abhay Kulkarni, May 26 2025](https://www.youtube.com/watch?v=CndSt8d5utY) shows Docker/reverse-proxy/Let's Encrypt pattern, but Plenum should retain private SSH/bastion editor access rather than expose n8n. Follow the official up-to-date OCI quotas and security instructions, never a video's billing advice.

**Existing agent work:** [Research #420](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/420) already completed a broad 93-link public metadata scan; it did *not* verify the above vendor quotas. [Engineering #421](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/421) generated only an unverified draft, which is not infrastructure execution. [Verification role #425](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/425) was explicitly asked for an additional scoped critique; that too requires independent source checks. No further duplicated agent-framework trials are authorized by this guidance.

## Official limits and risks

Oracle Always Free Ampere A1 is currently up to **2 OCPUs / 12 GiB total** on Always Free tenancies (1,500 OCPU-hours and 9,000 GB-hours monthly), subject to home-region quota and physical capacity. OCI requires owner registration and typically phone/card verification, with no charges unless upgrading; OCI can reclaim idle machines. Choose the home region carefully. See:
- https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm
- https://docs.oracle.com/en-us/iaas/Content/GSG/Tasks/signingup_topic-Sign_Up_for_Free_Oracle_Cloud_Promotion.htm

**Owner-only activation gate:** (1) confirm an existing OCI tenancy or register under the owner account; (2) provision one **Always Free-eligible** VM.Standard.A1.Flex (ARM64) VM with **2 OCPU, 12 GiB RAM** and an Always Free-eligible boot volume in the home region; (3) leave account on Free Tier, confirm free shape/volume/network allocations; (4) use SSH public keys, restrict inbound TCP/22 to owner's trusted IP, do not open ports 5678 or 11434; (5) verify host ARM64 and disk/free quotas before installing containers. A resource that is merely available during the $300 trial is **not** necessarily Always Free.

## Shared-host, five-workforce arrangement

Use the existing `integrations/workforces/five-workforces.json` to separate scientific, engineering, commercial, intelligence and verification scopes. This VM hosts **one n8n Community coordinator and one private Ollama runtime**, not five competing agent coordinators or hundreds of resident models. Reuse the existing nine-role n8n workflow and founder's public GitHub Actions queue. The 283 MIT prompt profiles remain indexed/on-demand; 1,106 AGPL documents remain indexed, not executed. Confidential business tools stay disabled until secured OAuth, logging, backups, and founder approvals are demonstrated.

For an owner-controlled Ubuntu ARM64 VM with Docker Engine and Docker Compose installed securely, copy only this directory from the public reviewed repo:

```sh
cd deploy/oracle-always-free
cp .env.example .env
chmod 600 .env
# Replace N8N_ENCRYPTION_KEY with a securely generated random secret on the VM.
# Pin reviewed ARM64 image digests before starting.
docker compose --env-file .env config
docker compose --env-file .env up -d
docker compose --env-file .env ps
docker compose --env-file .env exec ollama ollama pull qwen3:1.7b
```

The n8n editor listens only on VM loopback. From an owner-controlled trusted computer, use `ssh -N -L 5678:127.0.0.1:5678 ubuntu@VM_IP` and open `http://127.0.0.1:5678` locally. The secure cookie is deliberately disabled **only** for this localhost-over-SSH arrangement; do not publish the editor over ordinary HTTP. Set up the owner account in n8n. Do not expose Ollama's port or load browser sessions onto this host.

Import the existing reviewed `integrations/n8n/plenum-business-workforce.json` *only after* setting owner-only access; configure private Ollama at `http://ollama:11434`. Run one no-secret sample and inspect original nine review drafts. No provider credentials or external writes are automatically granted.

**Acceptance before claiming 24/7:** real OCI VM identity and Always Free tenancy quotas; `docker compose ps` running on the VM; SSH-tunnel-only n8n access; model CPU/memory responsiveness; one real scheduled n8n→existing specialist draft→status receipt; data restore exercise; restart recovery; no paid resources; and seven-day persistence observation. Provision secure off-machine encrypted backups and restoration before moving any private business data to n8n.

**Fallbacks without a VM:** keep GitHub Actions public-workflow runners (free for standard public repos), existing Render static dashboard, and on-demand Codespaces. Cloud Run can accept authorized webhooks but is not an always-running VM. None is a substitute for owner-approved private access.

**No unsupported claim:** there is currently no OCI connector or tenancy credential available through this ChatGPT workflow; owner must establish the account/VM before a genuine cloud deployment can be performed. Never ask for a card number, private key, password or token in a public GitHub issue or chat.

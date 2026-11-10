# Plenum Prometheus | Oracle Always Free staging

**State 2026-11-10:** prepared configuration; **NO Oracle tenancy, virtual machine, domain, payment method, persistent agent, or business OAuth has been provisioned or verified from ChatGPT.** This is a zero-new-cost *candidate*, not a deployed service. Do not infer that a public GitHub repository can authenticate to Oracle.

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

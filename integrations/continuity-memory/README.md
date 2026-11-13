# Plenum memory engines: installed separately, optional and private

This integration ADDS three established free open-source components to the **existing** Plenum Minister/agent system. It does not change native ChatGPT Memory. **The private Plenum Master Control Ledger in Google Drive remains canonical**; a memory search hit is not evidence that a source fact remains current.

| Component | Upstream | Function | Installation |
|---|---|---|---|
| MCP Memory Server | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers/tree/main/src/memory), MIT | Simple explicit graph observations across owner-controlled MCP client sessions | npm package pinned **2.1.1**, Node >=24 |
| Mem0 | [mem0ai/mem0](https://github.com/mem0ai/mem0), Apache-2.0 | Relevant memory extraction, embedding and retrieval | Python **mem0ai==2.2.1** |
| Graphiti | [getzep/graphiti](https://github.com/getzep/graphiti), Apache-2.0 | Temporal graph facts with source episodes | Python **graphiti-core[falkordb]==0.31.2** |

## Install NOW on a private machine with persistent disk

```bash
# From ORIGINAL Plenum-Scientific-Intelligence repository root:
# Requires Python 3.12+, Node 24+, npm and internet.
export PLENUM_PRIVATE_MEMORY_DIR="$HOME/.plenum/private-memory"
mkdir -p "$PLENUM_PRIVATE_MEMORY_DIR"
chmod 700 "$PLENUM_PRIVATE_MEMORY_DIR"
python3 -m venv "$PLENUM_PRIVATE_MEMORY_DIR/venv"
"$PLENUM_PRIVATE_MEMORY_DIR/venv/bin/python" -m pip install -e '.[memory_all]'
npm install --prefix integrations/continuity-memory --ignore-scripts
"$PLENUM_PRIVATE_MEMORY_DIR/venv/bin/python" -m plenum_ai.optional_memory_engines
```

This installs all three dependencies into the existing original Plenum project/private host environment. Source inclusion or a successful disposable GitHub CI install is NOT durable founder deployment.

## Run only on an approved private resident machine

MCP Memory: point an owner-controlled MCP client at Node 24's `npx -y @modelcontextprotocol/server-memory@2.1.1` with `MEMORY_FILE_PATH` set to an absolute **private persistent** JSONL file; `python -m plenum_ai.optional_memory_engines` prints install readiness. `mcp_memory_client_entry()` creates safe config only after `PLENUM_PRIVATE_MEMORY_DIR` is set.

Mem0: start private Ollama (with a suitable structured-output model and `nomic-embed-text`) and use `create_mem0_local(user_id=...)`. This explicitly uses local Qdrant persistence at `$PLENUM_PRIVATE_MEMORY_DIR/mem0-qdrant`, avoiding Mem0's default paid OpenAI configuration. Mem0's engine is not called automatically; only explicit owner-authorized data may be added.

Graphiti: a private, resident FalkorDB and local Ollama are needed. `docker compose -f integrations/continuity-memory/compose.yml up -d` starts **only FalkorDB** on loopback. `create_graphiti_local()` constructs the Graphiti client with local Ollama LLM/embeddings; the graph remains uninitialized until a private owner worker explicitly builds indices and adds approved episodes. Small models may fail Graphiti JSON extraction; this is not proof of operational reliability. Restrict Graphiti and the MCP stdio transport to the authorized owner process. Do not expose upstream reference HTTP MCP server on the internet: it does not implement production authentication.

## What is operational versus merely installed (current accepted evidence)

- **Operational now:** The existing Cloudflare Free Worker private Durable Object is a separate explicit-fact memory backend. Founder proved HMAC-signed write/read and a second-session read of the same source-linked revision 1 on Nov 12, 2026. No reinstallation, new secret, new host or more acceptance tests are needed. [Original evidence #483](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/483).
- **Source integrated, CI-installed only:** This directory's MCP Memory Server, Mem0 and Graphiti packages. A disposable GitHub job proves a package import, not a persistent private inference+database runtime. For iPad/Cloudflare-only founder operations, they do **not** automatically run under Cloudflare Durable Objects. Operating all of them independently would duplicate storage; prefer one purpose per backend.
- **MCP Memory:** use for an approved PRIVATE owner-machine knowledge graph persisted to an absolute JSONL path, never ephemeral node_modules or GitHub Actions artifacts. It is NOT already a remote OAuth ChatGPT plugin.
- **Mem0:** semantic recall requires an approved Ollama LLM+embedder and a persistent Qdrant-compatible private store, not a free remote ChatGPT Memory API.
- **Graphiti:** temporal supersession requires an approved structured-output model and FalkorDB/Neo4j. Do not expose the upstream reference MCP/REST server without auth; no such live private graph service is verified.
- **ChatGPT connection blocker:** Plenum Continuity v0.1.5 is a private skills-only plugin that can direct authorized Google Drive reads. ChatGPT full custom MCP connections need an OAuth 2.1 authenticated remote MCP endpoint plus supported workspace plan; the existing private HMAC endpoint is NOT that endpoint. Current [OpenAI documentation](https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt) lists Business and Enterprise/Edu full custom MCP creation on web, Pro read-only, not Plus. Never claim installed libraries change native ChatGPT Memory, or bypass availability by publishing private HMAC.
## Original Plenum integration rule

- The **Minister** reads the original private Master Control Ledger through an authorized connector, and verifies current original provider evidence before acting.
- Persistent LangGraph/SQLite checkpoints already in Plenum remain the agent's task state. MCP Memory handles explicit stable observations; Mem0 handles relevance-ranked memory; Graphiti handles temporal contradictions. **They are complementary but overlap**; enable only the minimum needed per task and never triple-write raw private chat history.
- Each adapter is lazy: adding dependencies does not read private chats, cause paid LLM usage, overwrite ledgers, or grant a new agent Google/Apple/Gmail permissions. **No automatic chat-wide Memory modification is possible from this repository.**
- Explicit user consent, existing authenticated connectors and a private persistent runtime are required before writing proprietary founder information. Never populate from GitHub public issues, artifacts, logs, or screenshots containing secrets.

## Truthful progress ledger

1. Source dependency registry, adapters and CLI: SOURCE INTEGRATED.
2. Independent CI installation: only VERIFIED after the exact GitHub workflow succeeds (ephemeral runner).
3. Resident private service and inter-chat retrieval: NOT YET CONFIRMED without an authorized always-on host and origin-specific connector.
4. Native ChatGPT account Memory replaced/updated: NO; this is an external agent memory stack.

Upstream docs: [MCP](https://github.com/modelcontextprotocol/servers/blob/main/src/memory/README.md), [Mem0 Ollama](https://github.com/mem0ai/mem0/blob/main/docs/cookbooks/companions/local-companion-ollama.mdx), [Graphiti local LLM](https://github.com/getzep/graphiti/blob/main/README.md).

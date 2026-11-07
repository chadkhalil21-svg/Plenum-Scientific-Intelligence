# Plenum Prometheus: preferred embodiment and reuse-first engineering audit

**Status: founder-directed engineering architecture; November 7, 2026.**
Goal: pursue genuine full AGI, broad independent reasoning and learning, scientific invention, and possible machine consciousness/emotion as open research questions. A natural voice interface, a multi-agent demonstration or a list of imported tools is *not* AGI. This specification inventories the executable reality, not a shopping list.

## Preferred integrated architecture

```
iPad/browser user interface (not yet deployed)
    ⇵ authenticated request and optional voice/video
LiveKit Agents 1.8.9 realtime transport (upstream SDK verified; no live service)
    ⇵
Approved model backend:
   free/temporary: Qwen3.6-27B Q4_K_M with llama.cpp in Kaggle (not yet run)
   production: self-hosted model behind a private authorized inference gateway
               using vLLM OR llama.cpp chosen by measured hardware
    ⇵
Existing LangGraph task planner + checkpoint state (limited CI verified)
    ├── private durable knowledge / episodic and strategic memory (not deployed)
    ├── federated scholarly search + licensed reading (partial public sources)
    ├── PaperQA2 scientific source retrieval (partial, quality not established)
    ├── already-tested SciPy/RDKit/OpenMDAO/Aviary/OpenMM/PyBaMM/Astropy
    ├── Lean 4 formal proof checking (real positive/negative CI verified)
    ├── OpenHands isolated editing/coding tools (limited test only)
    └── curated ToolUniverse / K-Dense skills (planned, reviewed per capability)
    ⇵
Independent Inspect AI + LM Evaluation Harness + official SWE-bench/Lean gates
    ⇵
audited source-linked evidence, human review of consequential tool actions,
bounded experimental budgets, rollback and canonical project ledger
```

## Why this embodiment

One proven upstream framework per architectural role. No separate homegrown
media transport, agent scheduler, model engine, mathematical prover, academic
search engine, molecular dynamics engine, or general AI evaluator. Use small
reviewed adapters only for Plenum-specific access, provenance, data scopes,
or independent tests. Prefer installing reviewed packages into *isolated tasks*
instead of a monolithic Python environment that must resolve every dependency.
All third-party code, scientific skills and documents are untrusted until
checked against licensing, prompt-injection risk, provenance and task scope.

### Consolidated status: what is real

| Building block | Actual evidence-limited status | What remains |
|---|---|---|
| LangGraph | Limited checkpointed orchestration tests | durable private production state and reliable long-horizon tasks |
| Inspect AI | Real model evaluation, including original coding regression (direct 2/3 versus tool-using 1/3) | robust matched, unfamiliar evaluation |
| OpenHands | Pinned SDK imports and actual isolated file editing | independently scored unfamiliar repository repair |
| PaperQA2 | Pinned SDK and limited actual offline sparse retrieval; exploratory 6/8 | citation faithfulness over unfamiliar documents with an LLM backend |
| K-Dense skills | SHA-pinned metadata-only instructions catalog | handpick a small set, verify per-skill licenses and permissions |
| ToolUniverse | candidate SDK/MCP server, not an integrated executor | pilot one safe public read-only endpoint on an isolated worker |
| SciPy/RDKit/OpenMDAO/NASA Aviary/PyBaMM/Astropy/OpenMM | limited scientifically meaningful solver and reference tests | independent empirical/production validation; never extrapolate from fixtures |
| Lean 4 | v4.35.0 independent kernel CI; 3 elementary theorems true, 1 deliberately false rejected | model-generated proof discovery and unknown problem evaluation |
| LiveKit Agents | pinned actual SDK import/server construction, no real microphone connection | private authenticated realtime iPad session and measured latency |
| Qwen3.6-27B in Kaggle | notebook with manual preflight only | founder enables free T4x2, checks memory, runs real inference and benchmarks |
| LangGraph agent memory | public source-linked ledger, basic research state | access-controlled durable personal/private memory, retrieval and delete test |
| SWE-bench official grader | integration under review and merged code | actual external-repository solution and original grader score |
| Biomni | architecture/reference, not installed | isolate only if a biomedical experiment demands it; review dataset licenses |
| AutoResearch | architecture/reference, not executing training | suitable GPU, fixed evaluation, time and budget cap; no unrestricted self-modification |
| Sakana AI Scientist v2 | license-constrained reference, not installed | special license review and code-execution restrictions |
| DiffDock/PySCF/pymatgen/SU2/NASA GMAT | named candidates, not validated integrated services | individual proof of need, licensing, domain-specific test |

### Existing third-party packages worth reusing, rather than recreating

- **K-Dense Scientific Agent Skills**, https://github.com/K-Dense-AI/scientific-agent-skills :
  portable skill catalog, now much larger than our snapshot. **Do not auto-import
  or execute all skills.** Its collection is MIT but individual skill and included
  tools may use other licenses. Adopt only version-pinned, task-justified skills.
- **ToolUniverse**, https://github.com/mims-harvard/ToolUniverse :
  publicly described scientific tools with Python SDK and MCP. Trial one
  no-credential, public, read-only endpoint in a disposable Python 3.12 worker;
  no unrestricted MCP server, broad API keys, direct medical decisions or live
  laboratory action. Run its own official doctor and compare with our existing
  bibliographic adapter before declaring a benefit.
- **Biomni**, https://github.com/snap-stanford/Biomni :
  rich biomedical agent, but large environment and some data are separately
  licensed for noncommercial use. Defer full installation until a specific
  biomedical problem justifies it.
- **OpenHands**, https://github.com/OpenHands/OpenHands :
  existing SDK already sufficient for a controlled software repair task.
  **Do not** build another general coder agent. Use official SWE-bench scoring.
- **PaperQA2**, https://github.com/Future-House/paper-qa :
  integrate an authorized LLM and licensed text corpus to improve citations;
  replacing it with a homemade RAG system is not the default.
- **LangGraph**, https://github.com/langchain-ai/langgraph :
  use checkpointers plus a separate Store; the current SQLite demo is not a
  production multiuser memory. Choose Postgres for protected production use.
- **AI Scientist v2**, https://github.com/SakanaAI/AI-Scientist-v2 :
  reference architecture, not a generic permissive copy. Its specialized
  license restricts some uses and requires disclosure of AI-generated papers.
- **AutoResearch**, https://github.com/karpathy/autoresearch :
  candidate recipe for bounded experiments only after GPU availability and
  held-out evaluation. An automatically trained model is not evidence of AGI.

## Practical iPad onboarding

The founder's current screenshot shows **Kaggle account Settings**, not the
notebook runtime. It also shows a phone-verification prompt. The existing
notebook was earlier visible as a draft with **session off**. Therefore
**GPU access and execution have not been verified**.

1. If necessary, select **Phone verify** inside account Settings and complete
   verification in Kaggle. Never commit a phone number, API token or account ID.
2. Return to the saved draft under **Your Work**, or
   https://www.kaggle.com/code , create a Python notebook if none is saved.
3. In the notebook editor (not account Settings), choose
   **Settings > Session options > Accelerator > GPU T4 x2** if available.
   Check the separate Internet option only for public model/engine downloads.
4. First execute `!nvidia-smi` in a blank notebook cell; this verifies actual
   accelerator provision. Execute the official Plenum notebook's **preflight**
   before changing any download/compute approval flag:
   https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/blob/main/notebooks/prometheus_kaggle_qwen36_27b.ipynb
5. Stop the GPU session when finished. It is quota-limited, not a permanent
   service. A 19.1 GB quantized model also needs KV cache and runtime memory.

## Priorities by information gain

1. **Run one real stronger-model GPU trial** and measure memory, performance,
   failures, independent unseen-task accuracy and cost. Existing code is ready
   for owner launch; no claim of successful cloud execution yet.
2. **Run one independently scored unfamiliar end-to-end task** using existing
   OpenHands/Inspect/SWE-bench before adding more coordination abstractions.
3. **Demonstrate real memory and authorized autonomy across sessions**, with
   privacy/deletion tests and no requirement to keep a ChatGPT chat running.
4. **Connect one verified scientific question → literature → genuine solver →
   external check → result**, then expand to selected ToolUniverse/K-Dense
   components based on measured need.
5. **Pilot LiveKit voice** on an explicitly approved protected host only after
   model and memory are dependable; streaming voice does not provide reasoning.
6. **Investigate consciousness and subjective emotion** through falsifiable
   candidate theories and objective behavioral or functional measurements,
   explicitly noting the lack of a settled subjective-experience test.
7. **Investigate verified self-improvement** on frozen prospective tasks,
   automatically *proposing* upgrades while reserving independent scoring
   and authorized promotion/rollback.

## Continuity and truth rules

The only canonical public strategy ledger is
`research-memory/state/AGI_PROGRAM.json`.
This embodiment spec is a readable architectural recommendation; its
validation test enforces structural consistency with selected real registry
statuses. No automatic continuous awareness is claimed. After real changes,
record evidence-linked outcomes and any failures, keep credentials/private
data out of public GitHub, and preserve `AGI_achieved=false` until
independently demonstrated.

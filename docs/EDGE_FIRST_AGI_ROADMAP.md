# Plenum Prometheus: edge-first AGI development checkpoint

**Objective:** a local-capable, general-purpose scientific intelligence system, measured by independent tests, not by component count. "Edge AI" is the deployment location. "AGI" is a disputed and substantially harder capability target. A local GGUF model is not automatically AGI.

## Reuse-first component audit (2026-11-07)

| Reusable component | Real status | Next test |
|---|---|---|
| Inspect AI / Inspect Evals | Integrated; genuine independent model scoring and Python tool use tested. Three original HumanEval coding tasks: direct 2/3, tool-using ReAct 1/3. | Unfamiliar repository repair with original official scorer. |
| LangGraph and existing scientific solvers | Some existing workflows and numerical reference tests used; not comprehensive general science. | Cross-domain prospective validations. |
| OpenHands SDK | Real isolated file-editor behavior verified on a synthetic fixture. Not yet an LLM-driven external repository repair. | Use original upstream agent on unfamiliar issue in isolated workspace. |
| PaperQA2 | Genuine offline sparse source retrieval tested (initial 1/2; exploratory 6/8 at 4096 hashed dimensions). Not reliable citation-faithful research yet. | Independent unseen document-retrieval and citation test. |
| ToolUniverse | Evaluated as an upstream candidate, not yet installed as an authorized/scoped scientific service. | Test one justified public read-only scientific endpoint; avoid installing hundreds of tools. |
| Karpathy AutoResearch | Valuable reference for bounded self-improvement experiments; not installed or running. Requires suitable GPU and frozen data/evaluator. | Owner-approved, limited baseline/held-out GPU pilot, never indefinite unsupervised spending. |
| Qwen3.6-27B | Real Apache-2.0 open-weight multimodal model published by Qwen; no Plenum benchmark or local device deployment yet. | Pin exact upstream revision, model format, tokenizer, device memory and permitted quantization; independently compare matched tasks. |
| SWE-bench | Official evaluator gate merged; no real repository bug-solving grade yet. | Issue #45, dedicated Docker host and independently scored agent work. |
| llama.cpp local edge runtime | New SHA256-pinned *offline-by-default* invocation bridge proposed; no model weights or local runtime binary shipped. | Review CI; then owner-supplied device/binary/model and one real measured run. |
| Persistent memory | Public research-memory branch and data-index modules exist; full private episodic/strategic memory and online learning absent. | Secure private store; retrieval quality and forgetting/privacy tests. |

The source screenshots' older statuses ("OpenHands pilot planned", "PaperQA2 pilot planned", "Inspect imports not installed") refer to earlier checkpoints, before the later limited functional tests. Do not downgrade completed evidence or mistake those tests for validated independent science.

## Proposed system

```
Scientific question / software objective / multimodal observation
   -> locally hosted reviewed model (fallback to approved remote only if authorized)
   -> existing LangGraph state and planning
   -> typed public/private knowledge and project memory
   -> allowlisted existing tools (Inspect, OpenHands, PaperQA2, numerical solvers)
   -> original independent evaluator / external data / safety checks
   -> signed, append-only evidence with negative outcomes
   -> human-reviewed candidate capability change
```

Do NOT create a new agent framework, AI model architecture or general-purpose evaluator without a measured gap. Do NOT promote a good result on contaminated public tests to a general-intelligence claim.

## Edge runtime: what is actually implemented

The optional `plenum_ai.edge_runtime` adapter executes an **already installed, local, hash-pinned** llama.cpp `llama-cli` executable against an **already present, hash-pinned GGUF** model. It contains no downloader, model weights, network API, private inputs or training code. Default command emits a plan only:

```sh
python -m plenum_ai.edge_runtime --out reports/edge/plan.json
```

For a separately reviewed device, place an existing compatible local model at `edge_assets/models/plenum.gguf` and the matching reviewed executable at `edge_assets/bin/llama-cli`. Record their externally reviewed SHA256 hashes. With local device network disabled and suitable RAM, deliberately execute one bounded public arithmetic smoke test:

```sh
python -m plenum_ai.edge_runtime \
  --model-sha256 <64-lowercase-hex-digest> \
  --engine-sha256 <64-lowercase-hex-digest> \
  --execute --out reports/edge/manual-run-001.json
```

**Important:** The two placeholders above are not genuine hashes; calculate them on the actual signed/reviewed files. Never insert any private research or patent into this public smoke prompt. The run sets CPU-only inference, 2 threads, 1024 context tokens, maximum 64 generated tokens and 180 seconds, with shell-free invocation and a restricted process environment. It records only hash/length of generated output, duration and process status. It **does not claim a correct answer or AGI**, and a successful CLI call does not certify offline isolation, model trust or scientific reliability. Device owner must establish physical/OS-level network isolation independently.

SHA256 alone does **not** validate model license, absence of malware, benchmark contamination, vendor claims, image/audio modalities or tokenizer compatibility. Running a large 27B parameter model on an iPad or a small laptop is NOT assumed feasible; the actual hardware, compatible GGUF implementation and quantization must be verified separately. The official Qwen3.6-27B release is primarily described as Transformers weights; do not assume a particular community GGUF is official or compatible.

## AGI science gates that remain

1. **General reasoning:** prospective unfamiliar coding, mathematics, science and multimodal tests; matched baselines and confidence intervals. Prior 1.7B coding tools made performance worse on 3 historical samples.
2. **Reliable agency:** successful independent external-repository bug repair and scientific research tasks, with action traces and test-based verification.
3. **Persistent learning:** secure, retrievable, provenance-aware project memory and demonstrated improvement on genuinely new tasks. Retrieval alone is not learning.
4. **Scientific discovery:** prospective predictions or inventions independently replicated with source-linked experiments; do not mistake speculative model output for discovery.
5. **Robustness and safety:** reliability over long horizons, unexpected failure handling, prompt-injection defense, controlled tool permissions, cost/memory/power limits and reversibility.

Suggested order: **verify edge model on real hardware → run matched independent baseline evaluations → enable one controlled scientific tool or repo repair agent → measure benefits and regressions → extend verified memory and long-horizon tasks → only then trial bounded training with an independently frozen holdout.**

Unbounded AutoResearch loops, automatic public deployment, secret-bearing tool integration and automatic model promotion are not prerequisites to safe research and are not authorized.

## Source links and accountability

- llama.cpp original CLI: https://github.com/ggml-org/llama.cpp/blob/master/tools/cli/README.md
- Qwen3.6-27B official model card: https://huggingface.co/Qwen/Qwen3.6-27B
- ToolUniverse: https://github.com/mims-harvard/ToolUniverse
- AutoResearch: https://github.com/karpathy/autoresearch
- Existing official coding issue: https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/45
- Audited three-case ReAct failure: https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/blob/research-memory/evidence/inspect-react-three/run-42350599820.json

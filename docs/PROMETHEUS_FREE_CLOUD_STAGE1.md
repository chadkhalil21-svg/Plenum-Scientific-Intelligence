# Plenum Prometheus: iPad-first, free-cloud Stage One

**Checkpoint:** 2026-11-07. This is a founder-requested research plan, not evidence that AGI or an always-on assistant has been deployed. This public document contains no confidential Plenum memoranda, user video, credentials, unpublished patents, or personal data.

## Objective

Develop a voice-first, multimodal, persistent and scientifically useful assistant as an interface layer for a longer-running **AGI research program**, without confusing fluent conversation with general intelligence. The founder's animated reference depicts a hypothetical transition from chatbots to very large populations of AI researchers, able to assist with software, engineering, scientific literature, laboratories and discovery. These images are a goal illustration, **not verified discoveries, a working million-agent system or proof of AGI**.

**First user experience (Samantha-like, inspired by the fictional OS in `Her`, not a copy):**
- Conversational voice with interruption handling and transparently disclosed AI identity.
- Consent-based multimodal observation and user-controlled tools: research, coding, calendars and project oversight.
- Private persistent project/task/episodic and strategic memory with provenance, correction and deletion controls; do not put this store in the public repository.
- Bounded agents that complete approved tasks, report uncertainty and independently test their work.
- iPad or browser client, with inference hosted on a separately permitted machine; model runtime is not assumed to fit on iPad.

**Beyond Stage One:** prospective replicated research, physical laboratory integrations, verifiable gains on unfamiliar problems, reliable long-horizon planning, persistent learning, robustness and trustworthy self-improvement. Fictional sentience or feelings are **not** an engineering milestone that can presently be guaranteed.

## Free-cloud route, discovered 2026-11-07

1. **Kaggle Notebooks (preferred experiment):** free, quota-limited `GPU T4 x2`, two 16 GB GPUs, approximately 29 GB host RAM in its public documentation. Kaggle retired P100 on 2026-09-15. Limited temporary storage and session quota; **not continuous production hosting**. The founder needs to enable the free accelerator in their Kaggle account and run the notebook.
2. **Google Colab free (fallback):** GPU availability and quota fluctuate; typically lower-memory configurations and no guaranteed persistent service. It may require a smaller model or CPU offload.
3. **Hugging Face ZeroGPU (alternative demo):** shared 48/96 GB Blackwell resources in Gradio-only Spaces, with free daily usage and eligibility restrictions. This is not equivalent to dedicated 24/7 GPU service.

Authoritative provider sources:
- https://www.kaggle.com/product-announcements/735239
- https://www.kaggle.com/docs/notebooks
- https://www.kaggle.com/docs/efficient-gpu-usage
- https://research.google.com/colaboratory/faq.html
- https://huggingface.co/docs/hub/spaces-zerogpu

## Candidate open model and measured feasibility gate

- **Upstream model:** https://huggingface.co/Qwen/Qwen3.6-27B (Apache 2.0)
- **Reviewed-community conversion source:** https://huggingface.co/ggml-org/Qwen3.6-27B-GGUF
- Q4_K_M GGUF listed at **19.1 GB** versus BF16 GGUF at **53.8 GB**. These are file sizes, not a complete runtime memory budget. Context/KV cache, model layers and kernel overhead require additional RAM and VRAM.
- **Open engine:** https://github.com/ggml-org/llama.cpp , manual Kaggle pilot targets the published `b12143` release/tag and records exact Git commit; repository tag is not a binary authenticity guarantee.
- **Pilot artifact:** [`notebooks/prometheus_kaggle_qwen36_27b.ipynb`](../notebooks/prometheus_kaggle_qwen36_27b.ipynb). Contains GPU/storage preflight, an explicit opt-in flag for model downloads and compilation, a single public arithmetic smoke query, and a local output/hash/latency record. Never supplies passwords, secrets or private research. Does not expose a public server or turn on payment.
- **Success criterion A:** notebook records GPU allocation, model and engine revisions, model file SHA256, inference exit code and exact response quality on public test; failure is preserved, not ignored. As of this checkpoint **no actual Kaggle run is claimed**.
- **Success criterion B (separate):** run prior official Inspect benchmarks or original evaluator on locked unfamiliar tasks with matched baselines, paired failure cases, resource usage, and documented regression rate. A single smoke result is insufficient.
- **Stage-One product gate:** after verifying usable compute, design independently measured ASR → model → TTS latency, opt-in private memory, permissioned tools and iPad UI; benchmark interruption, hallucination, prompt injection, privacy and continuity.
- **Cost gate:** free quota only unless founder separately approves paid compute. Stop free session at end. Never assume perpetual free GPUs or a stable runtime.

## Why not run on GitHub Actions directly?

GitHub is our source-of-truth and CI controller. Standard hosted runners are not the intended large GPU service; larger GPU runners have billing and account constraints. Use GitHub to preserve **public** code and measured results, not founder-sensitive information. Do not store cloud credentials or remote notebook access tokens in this public repository.

## Continuity rules

The canonical public status is `research-memory/state/AGI_PROGRAM.json`. This document is the public Stage-One design; it is **not** the AGI achievement record. The first live cloud experiment must add source-linked real evidence, preserve failures, and report specifically that AGI is not demonstrated.

**Next human action:** On an iPad, sign into Kaggle, create/import the notebook, enable **GPU T4 x2** and **Internet** as the platform permits, execute the free preflight, and deliberately change `APPROVE_FREE_GPU_RUN` from `False` to `True` only after reviewing storage, quota and data-sensitivity warnings. This requires the user's account action; it cannot be launched from GitHub alone.

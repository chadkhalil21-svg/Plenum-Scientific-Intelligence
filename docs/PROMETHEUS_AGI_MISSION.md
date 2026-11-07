# Plenum Prometheus: ultimate AGI mission and interim interfaces

**Founder-aligned public objectives, 2026-11-07.** Full Artificial General Intelligence is the primary research objective. An assistant or a polished voice demo is an *interface*, not the goal. The previously reviewed visual animation depicts a vast hypothetical workforce of AI scientific agents capable of improving science, engineering, mathematics, software, medicine and more. Those scenes are a research ambition, not evidence that AGI or one million successful AI scientists are now operating.

## Research goals

1. **General intelligence:** develop reproducible, substantially general reasoning capable of solving unfamiliar challenges across domains. Rigorous original independent benchmarks and prospective tests are essential.
2. **Loyal independence:** sustain authorized projects, propose and execute useful actions with minimal prompting, keep commitments and transparent provenance, protect founder confidentiality and explain disagreement when an objective or action is unsound. Loyalty is neither unconditional obedience nor deceptive flattery.
3. **Persistent memory and learning:** maintain provenance-backed factual, project, episodic and strategic state, plus demonstrable future learning. Private information lives in access-controlled systems, not public GitHub.
4. **Scientific and technical creation:** research, invent, critique, build software, use verified numerical tools, and run reproducible experimental protocols; move from synthetic fixtures toward independently validated laboratory results.
5. **Open-ended improvement:** iterate models and tools based on independently demonstrated benefit, with spending controls, held-out evaluation, audit trails, rollback, and human review. Open-ended improvement is a research goal; "unlimited" capacity is not something we can verify or guarantee.
6. **Consciousness and emotion research:** investigate scientific theories and operational tests of consciousness, artificial affect, emotional understanding, expression and enduring relationships. There is no accepted test establishing a machine's subjective experience, so simulations of emotion must not be falsely presented as genuine feelings or guarantees of sentience.
7. **Multi-agent science:** explore bounded cooperative ensembles of specialist agents with coordination and measured cost, reliability, novelty and reproducibility, not arbitrary agent counts.

## Proposed architecture (reuse first)

```
iPad/web user and authorized scientific objectives
  -> optional voice/video interface: upstream LiveKit Agents
  -> current open-weight / approved hosted language model
  -> LangGraph project control, memory and research workflows
  -> verified science/code/simulation/source retrieval tools
  -> task-level independent audit, provenance, replay and correction
  -> accountable observations, proposal review and iteration
```

The voice path uses **upstream LiveKit Agents 1.8.9** (Apache-2.0) rather than another hand-written real-time transport stack. `src/plenum_ai/voice_livekit.py` is an optional executable adapter. It has a safe, offline plan mode and an explicit launch path. No video, audio, cloud credentials or unpublished Plenum IP is committed here. Existing LangGraph is not secretly connected to this voice endpoint yet. That requires designed permissions, a private memory store and an authenticated service.

### LiveKit integration honesty

- `python -m plenum_ai.voice_livekit` prints a **read-only** runtime plan; it neither imports LiveKit nor makes calls.
- An owner can later `pip install -e ".[voice_livekit]"` on their own protected host, then configure LiveKit and the chosen model providers.
- `python -m plenum_ai.voice_livekit --serve` refuses to start without `PROMETHEUS_APPROVE_LIVE_VOICE_COST=YES` and `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`. **The example uses managed STT, model and TTS provider inference, which may incur fees. Do not enable them until price and privacy are reviewed.**
- The repository's automatic CI tests only the local no-inference contract, never actually starts real-time audio. An iPad client, live STT/LLM/TTS inference, latency, security, reliability and any agent independence **remain unproven**.

Upstream: https://docs.livekit.io/agents/start/voice-ai/ (reviewed November 7, 2026); https://pypi.org/project/livekit-agents/1.8.9/

## Near-term execution order

1. Resolve the Kaggle notebook entry problem using verified alternate **https://www.kaggle.com/code/new?languageId=8**, or the notebooks homepage https://www.kaggle.com/code . Run the prepared Qwen3.6-27B preflight and manual trial; record failure honestly.
2. Independently score a *genuine running model* with existing original third-party evaluators and resource measurements.
3. Run the first LiveKit pilot on a private approved host, using reviewed providers with real microphone/interrupt latency and explicit budget constraints. Compare with Pipecat **only if** measured LiveKit limitations justify switching.
4. Add privacy-preserving project memory and authenticated approved tools to that voice layer, gated by original tests and the founder's decisions.
5. Advance external-repository software tasks and prospective scientific outcomes, preserving successful and failed cases. Never claim AGI from a CI result, a roleplay, a voice conversation or a model score on one public test.

## Video and audio evidence

The reference animation is user-provided and **not published** in this public repository. Its visuals are relevant to the above objective; visual review does not certify what its narration actually says. Audio transcription and scientifically cautious claim extraction are tracked separately until genuinely verified. Do not invent quoted words or claim to have listened where only the audio stream was confirmed.

## Continuity

`research-memory/state/AGI_PROGRAM.json` is the authoritative public program ledger. Every significant decision, test, regression, verified change or blocker must be reflected there by an explicit checked-in update with source links. The ledger is not an automatically sentient memory and cannot continually update outside actual executed workflows or ChatGPT sessions.

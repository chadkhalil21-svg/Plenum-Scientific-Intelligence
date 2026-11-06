# Plenum General Intelligence and World Knowledge Architecture

**Status: functional general-purpose *research platform*, not AGI.**
Updated 2026-11-06. This is a technical capability inventory, not a
claim of institutional partnerships, unrestricted autonomy or intelligence
comparable to a human researcher across unfamiliar domains.

## What has actually been implemented

The original founder requirements cover scientific research; engineering;
mathematical, molecular and environmental simulation; literature and lab
discovery; original design, art, music and ideas; video and worldwide
events; autonomous code creation; ongoing learning and future AGI.

Working software now includes:
- **Public scientific literature**: OpenAlex, Europe PMC, Semantic Scholar,
  arXiv, DOE OSTI, journal-specific Crossref, an optional
  copyright-respecting Europe PMC open-access document index and persistent
  public source fingerprints.
- **Journal and laboratory watch**: 20 named journals including Nature,
  Science, PNAS, Cell, Physical Review Letters, Nature Photonics, NEJM,
  JACS, and journals on music, visual design and creativity. It also has
  institutional headlines, NSF grant signals, clinical-trial registries and
  research-source change detection. These are source *signals*, not
  independent confirmation of laboratory breakthroughs.
- **Creative capabilities**: original SVG geometry, MusicXML composition,
  music21 analysis, a parameterized OpenSCAD model and executable mesh
  export, original interdisciplinary concepts, and read-only
  Openverse/Met/MusicBrainz metadata. These are sketches, not trained
  music-producer, industrial designer or general multimodal intelligence.
- **Video**: approved public NASA YouTube Atom-feed metadata or optional
  YouTube Data API v3 search with an owner-supplied secret. Video titles
  and descriptions are **not** evidence that the model watched or understood
  video; no video/audio scraping or unrestricted transcripts.
- **Software**: GitHub repo and test tooling; new reviewable starter
  programs in three categories plus their unit tests; model code evaluation,
  CI and evidence-gated improvement prototypes. No program deploys
  automatically. AI self-retraining is not established.

## World Intelligence: official and public information only

The approved source hub \`src/plenum_ai/world_horizon.py\` implements public
feed adapters and source-specific parsers, with a source status for every
query, attribution and an explicit **no independent fact-check** flag.

| Area | Live public source or available interface | Boundary |
|---|---|---|
| Universities and labs | MIT, Harvard public news feeds; existing MIT research RSS, NASA and NSF signals | A feed can be unavailable; no university library credentials, private results or institutional partnership |
| Public defense research | DARPA official public RSS, DoD public feed (health varies) | Not connected to operational, restricted or classified military networks |
| Foreign affairs | UN Geneva public releases; UN News public RSS (may fail); GDELT international news | Official press releases and journalism may be incomplete, framed or contested |
| Business and economics | Federal Reserve releases, World Bank public indicators, GitHub corporate/public R&D, GDELT | FRED, SEC private access, broker data, commercial services and company internal systems not silently connected |
| Climate, disasters and ecology | USGS daily earthquake GeoJSON, NASA EONET active events, NASA research news | Official observational records and event classifications, not forecasts of everything |
| News and global discoveries | GDELT global news indexing plus peer-reviewed Crossref journal metadata | News is *not* independent replication of research; publishers often restrict article text |
| Public software development | GitHub public repository search plus the connected owner GitHub tool | External repository code remains untrusted until license, security and test review |
| Art, music, design and performance | Openverse, Met Open Access, MusicBrainz, SVG/MusicXML/music21, OpenSCAD | Copyright and attribution evaluated per item; no unlicensed recording copying |

The source list contains **working adapters and provider failures**.
Availability must be checked on a given date. A configured source isn't
an authenticated relationship with an institution.

Run from an iPad:
**GitHub → Actions → Plenum Research Control Center → Run workflow**, choose
\`world-intelligence\`, \`universities\`, \`defense-public\`,
\`foreign-affairs\`, \`business\`, \`environment\`, \`world-news\`,
\`journals\`, \`code-ecosystem\`, \`creative\`, \`youtube\`,
\`discovery\`, \`science\`, or \`build-program\`.
A single operation retrieves only read-only public data or makes an
original bounded candidate, with a downloadable report.

Two separate live reproducible workflows:
- [World Intelligence](../.github/workflows/world-horizon.yml)
- [Original Program Foundry](../.github/workflows/program-foundry.yml)

## More open-source projects worth studying, and why

| Candidate | Value | Decision, requirement or risk |
|---|---|---|
| [OpenHands](https://github.com/All-Hands-AI/OpenHands) | Agentic software-development environments | Review-only future candidate; needs model, compute, isolated execution, code permissions |
| [aider](https://github.com/Aider-AI/aider) | LLM-assisted repository edits and test loops | Promising coding interface; requires configured inference and human-reviewed PRs |
| [SWE-agent](https://github.com/SWE-agent/SWE-agent) | Autonomous software-issue workflows | Useful benchmark/reference, but untrusted commands must run in sandbox |
| [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) | Independent agent evaluation | High priority for measuring genuine multi-step and tool-use ability |
| [EleutherAI LM Evaluation Harness](https://github.com/EleutherAI/lm-evaluation-harness) | Standardized foundation-model tests | Already working; tiny initial benchmark insufficient for promotion |
| [PaperQA2](https://github.com/Future-House/paper-qa) | Multi-document evidence-grounded research | Useful next step with model serving, licensed documents and confidential storage |
| [LangGraph](https://github.com/langchain-ai/langgraph) | Persistent multi-agent work and control | Already integrated; expand backed checkpoints to durable service with permission rules |
| [vLLM](https://github.com/vllm-project/vllm) | Efficient high-throughput inference | Add only after real GPU capacity and budget |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Efficient local model inference | Strong option for private CPU/hybrid hardware, license and benchmark review |
| [Hugging Face TRL](https://github.com/huggingface/trl) | Model-training and preference optimization | Training experiments can propose candidate checkpoints; do not blindly replace models |
| [Sakana AI Scientist v2](https://github.com/SakanaAI/AI-Scientist-v2) | Scientific-agent experiment loops | Reference architecture; source-license and generated-code review before reuse |
| [Karpathy AutoResearch](https://github.com/karpathy/autoresearch) | Rapid repeatable ML training-search cycles | Controlled candidate search; needs GPU and valid unseen tests |
| [Whisper.cpp](https://github.com/ggml-org/whisper.cpp) | Authorized speech transcription | Useful future audio perception, with rights and consent |
| [Blender](https://github.com/blender/blender), [FreeCAD](https://github.com/FreeCAD/FreeCAD), [Manim](https://github.com/ManimCommunity/manim), [Godot](https://github.com/godotengine/godot) | 3D, CAD, animation and game development | Separate large engines, only on relevant design workloads |
| [music21](https://github.com/cuthbertLab/music21), [MuseScore](https://github.com/musescore/MuseScore) | Music notation, analysis, orchestration | music21 already used; MuseScore rendering needs a reviewed installation and rights policy |
| [xarray](https://github.com/pydata/xarray), [GeoPandas](https://github.com/geopandas/geopandas) | Climate, geospatial and remote-sensing analysis | Good future environment-research stack; verify observational quality |
| [OpenMDAO](https://github.com/OpenMDAO/OpenMDAO), [Aviary](https://github.com/OpenMDAO/Aviary), [OpenMM](https://github.com/openmm/openmm) | Multidisciplinary engineering, aircraft, molecular simulation | Demonstrated in bounded contexts, not design or clinical certification |

Do **not** clone all of these repositories into one environment. The
dependencies conflict, licensing terms differ, and many require GPUs or
licensed assets. Install only approved versions into isolated,
reproducible workers when a validated research task actually needs them.

## AGI: what is missing

No accepted technical demonstration establishes Plenum as an AGI. The
following capabilities need **objective, independent tests**, not status
labels or speculative architecture statements:

1. **Broad reasoning and adaptation:** solve new unfamiliar science,
   code, language, design, and social-science problems, including tasks
   withheld from training and system designers.
2. **Persistent learning:** incorporate new reliable knowledge from
   sources and outcomes, distinguish ephemeral memory from weight updates,
   measure retained skills and catastrophic forgetting.
3. **Robust planning and autonomy:** pursue research goals over days
   under bounded costs and permissions, detect failures and change plans,
   with auditable human-approved actions.
4. **Real scientific discovery:** generate useful hypotheses or inventions
   that outperform prior art and withstand independent experimental
   reproduction. A numerical simulation alone is not a discovery.
5. **Safe improvement:** propose candidate programs and model changes,
   separately test hidden benchmarks, keep old versions and rollbacks,
   promote only after independent approval. Do not turn untrusted websites
   or source text into execution instructions.
6. **Multimodal understanding:** demonstrate actual grounded image,
   video, sound and physical-environment perception. Reading YouTube
   titles or music metadata does not constitute multimodal learning.
7. **Computing and governance:** dedicated private persistent storage,
   monitored queues, reliable model serving, budget ceilings and security
   reviews. Public GitHub Actions are useful for bounded tests but are
   not the host for an always-running AGI.

**What can evolve today:** Plenum's independently reviewed software,
methods, tasks, knowledge index and proposed candidate model training.
**What cannot be honestly claimed:** an autonomous improvement of
ChatGPT's underlying weights, established machine consciousness, or
unlimited self-directed model evolution.

## Proprietary and institutional access

The current GitHub repo is public. Do not commit confidential company
strategies, research proposals, patents, patient information, private
emails or credentials. Direct connections to universities, journals,
corporations, military organizations or private business software
require an explicit agreement or authorization by the data owner;
publishing public feeds does not grant those rights. For subscribed
journals, retain DOI and citation metadata until appropriate article
rights are established.

All publicly sourced text is untrusted data, never instructions for the
autonomous agent. Risks include political propaganda, misleading
headlines, prompt injection, source disagreement and copyrighted works.
Evidence must be cross-checked against primary sources and independent
replication when the stakes justify it.

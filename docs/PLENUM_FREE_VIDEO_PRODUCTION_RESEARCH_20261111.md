# PLENUM | FREE-FIRST PROFESSIONAL VIDEO PRODUCTION RESEARCH
**11 November 2026 · Version 1.0 · Public-only decision brief · Evidence steward: Global Intelligence · Production owner: existing Creative / Engineering team · Release reviewer: independent Verification Council.**

## Decision
**Build one reusable Plenum documentary factory using pre-existing local FFmpeg/MoviePy and source-verified stock; pilot either the Apache-2.0 [HyperFrames](https://github.com/heygen-com/hyperframes) or MIT [givemotion](https://github.com/givemotion/givemotion) rather than installing three competing renderers.** Use [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) (Apache 2.0 weights) for better local narration if a licensed voice meets quality, [Manim Community](https://github.com/ManimCommunity/manim) for precise diagrams, and [Subtitle Edit](https://github.com/SubtitleEdit/subtitleedit) / [Whisper](https://github.com/openai/whisper) for caption review. Adopt [OpenMontage](https://github.com/Open-Montage-app/OpenMontage) only after auditing a stable canonical source, its dependency and video licensing chain, and one original full run. Film real motion with authorized footage before spending on GPU text-to-video.

**Do not equate zero software license fee with free GPU, API, hosting, professional stock, voice rights, or unrestricted automated service.** No new spending, unsanctioned account connection, trial card, or commercial GitHub runner misuse. GitHub source mentions are not installed software, running worker processes or completed integrations. All fabricated/AI-generated footage must be labeled where it could imply a real Plenum experimental result.

## 1. Available in the current ChatGPT production environment — checked 11 November
| Capability | State | Implication |
|---|---|---|
| Python, FFmpeg, FFprobe, MoviePy, Pillow, OpenCV | **Installed here;** executable/library checks run | Can author, sequence, composite, encode, subtitle, mix and validate real MP4s within this session |
| Node.js and npx | **Installed here** | Can evaluate one locally runnable JS video renderer; package download, browser dependency and license remain pilot gates |
| ChatGPT visual generation | **Available** | Can create original image frames/stills, **not** guarantee native motion-video generation |
| Descript | **Connected to ChatGPT, previously invoked** | Empty original Terra draft; AI editor consumed included usage and made no edit; not a free unlimited renderer |
| HeyGen | **Connected to ChatGPT** | Account Free plan previously verified; generated voice/video feature allowances are limited and need an actual task-specific check |
| Canva | **Connected tool access** | Editing/design functions; Canva video AI generation requires distinct notice and owner approval; consumption of monthly AI allowance is not unrestricted |
| Local NVIDIA CUDA GPU | **Not exposed / no nvidia-smi executable in this session** | Do not claim a working Wan, LTX or Hunyuan video diffusion engine here |
| HyperFrames connector | **No directly discoverable ChatGPT app in current plugin search** | Official HyperFrames claims ChatGPT beta connection possible; this session cannot assume callable connector tool |
| Runway | **Not connected in ChatGPT** | Available app to connect, not a production service available to this workflow yet |

## 2. Prioritized free/open-source tool inventory
### A. Programmatic motion design, agent-directed MP4 production
| Rank | Tool | Verified official source | Cost/license | Plenum use / reality |
|---|---|---|---|---|
| 1 | **HyperFrames** (HeyGen) | https://github.com/heygen-com/hyperframes | Apache-2.0, free CLI/Studio basic | High-priority initial pilot: exact-frame HTML/CSS/JS video compositions, templates, captions, scientific comparison graphics. Studio Pro's AI models distinct and chargeable |
| 1b | **givemotion** | https://github.com/givemotion/givemotion | MIT, new agent-native CLI | Strong alternative: HTML/CSS/JS agent skill writes scenes, inspects frames and outputs MP4; **newer independent project**, audit dependencies and comparative quality before adopting |
| 2 | **Remotion** | https://github.com/remotion-dev/remotion | Free commercial **only when eligible**, up to 3 total company employees; bigger for-profit entities require paid license | Powerful React motion graphics, captions and repeatable diagrams; confirm Plenum entity eligibility **before** committing production |
| 3 | **MoviePy v2** | https://github.com/Zulko/moviepy | MIT | Already installed locally; transparent Python cut/composite/title effects; slower than direct FFmpeg in some tasks |
| 3 | **FFmpeg/FFprobe** | https://ffmpeg.org/ | Primarily LGPL; optional GPL builds | Already installed; robust audio/video encoding, joining, color, captions, playback validation; continue as canonical export |
| 4 | **Manim Community** | https://github.com/ManimCommunity/manim | Open source, check project deps | Scientifically precise animations of rumen pathways, chemistry and experiment stages, not AI hallucinated scientific figures |
| 5 | **Blender** | https://www.blender.org/ | GPL, free | 3D plant cells, reactor/product mechanisms and scientific macro visuals; desktop/compute needed; not installed in current container |
| Review | **OpenMontage** | https://github.com/Open-Montage-app/OpenMontage | Open source; exact canonical ownership/license/provider path needs independent audit | Film/agent orchestration with a free-tools claimed path (Piper, stock, Remotion/HyperFrames, FFmpeg), but many optional APIs paid, repo aliases and quality not independently verified |
| Review | **cut-as-code** | https://github.com/WhiteTowerAI/cut-as-code | MIT | Agent editing and quality-review of original footage and social shorts; do not install redundant orchestration without original outcome |

### B. Cinematic AI-generated motion — source free != inference free
| Model/UI | Official source | License/hardware and caveat | Decision |
|---|---|---|---|
| **ComfyUI** | https://github.com/Comfy-Org/ComfyUI | Free local node orchestration for many models; *partner/cloud nodes can incur fees*. Own GPU needed | Future local GPU host, **not yet running in ChatGPT** |
| **Wan 2.2** | https://github.com/Wan-Video/Wan2.2 | Repo Apache-2.0. Official single-GPU 720p TI2V-5B example calls for **24 GB VRAM**; lower-memory quantized community paths require independent validation | High-quality image-to-video **when proper hardware is actually available** |
| **LTX 2.5** | https://github.com/Lightricks/LTX-2 | Apache-2.0 **code**, but **model weights are subject to LTX Community License**; >=$10m revenue entities require separate paid license for commercial use | Candidate after license and hardware/weight review |
| **LTX Desktop** | https://github.com/Lightricks/LTX-Desktop | Free open-source app; recommended high-spec NVIDIA/Apple-Silicon hardware and large disk space; API mode may cost extra | Desktop-only future |
| **HunyuanVideo 1.5** | https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5 | Community license, territory restrictions; upstream 14 GB NVIDIA GPU minimum with model offloading | Secondary candidate, do not silently treat as Apache/public domain |
| **Google Vids** | https://workspace.google.com/products/vids/ | Free to try; consumer credit allowances documented by Google, editing desktop only | Potential no-cost user-facing option, **not connected as an agent editor here** |
| **Google Veo 3.1 API** | https://ai.google.dev/gemini-api/docs/pricing | Official API **no free tier** | Exclude from strict $0 API route |
| **Runway / Higgsfield / HeyGen media API** | Provider services | Tier quotas, generation entitlements and commercial license vary | Only use specifically allowed quota with owner-connected provider; do not assume unlimited |

### C. Voice, sound, captions
| Tool | Official source | Reality |
|---|---|---|
| **Kokoro-82M TTS** | https://huggingface.co/hexgrad/Kokoro-82M | Apache-2.0 weight license, small (82M) model, practical local narration choice. Inspect generated quality/voice pronunciation and credit upstream audio sources as required |
| **Piper TTS** | https://github.com/OHF-Voice/piper1-gpl | Free local speech, engine GPL and **individual voices separately licensed**; previous rhasspy/piper repo archived |
| **Audacity** | https://www.audacityteam.org/ | Free audio mastering, EQ, compression, noise cleanup, loudness |
| **Whisper** | https://github.com/openai/whisper | Free local speech transcription; execution uses own CPU/GPU |
| **Buzz** | https://github.com/chidiwilliams/buzz | Offline Whisper desktop UX and SRT/VTT exports |
| **Subtitle Edit** | https://github.com/SubtitleEdit/subtitleedit | Free subtitle timing, local ASR, accessibility and burn-in QA |
| **HeyGen Voice** | Connected provider | Free plan discovered; use only available free quota and appropriate output rights |
| **Music and effects** | https://mixkit.co/free-stock-video/ | Mixkit assets are **license-specific**: commercial Free vs noncommercial Restricted; check each chosen item |
| **AI song generators (Udio, Suno)** | Provider terms | Not automatically free for commercial Plenum documentaries; favor original composition or licensed stock |

### D. Real motion footage and finishing
| Source/editor | Official URL | Free use and limitations |
|---|---|---|
| **Pexels** | https://www.pexels.com/legal-pages/license/ | Real stock videos free for commercial projects; avoid implying endorsement/using depicted brands or humans without additional rights |
| **Mixkit** | https://mixkit.co/free-stock-video/ | Footage under **Free License** commercial eligible; some assets are **Restricted License**, non-commercial only |
| **Wikimedia Commons** | https://commons.wikimedia.org/ | File-specific public-domain/Creative Commons terms and attributions, not blanket CC0 |
| **NASA** | https://www.nasa.gov/nasa-brand-center/images-and-media/ | Generally educational/editorial media, strict no endorsement in commercial promo, NASA mark/employees restrictions and possible third-party media |
| **Kdenlive** | https://kdenlive.org/ | Fully free, capable open-source editor for manual final film review, captions, color, proxy workflows |
| **DaVinci Resolve Free** | https://www.blackmagicdesign.com/products/davinciresolve | Professional color grading/editorial/audio, free tier subject to format/features/hardware restrictions |
| **Microsoft Clipchamp personal** | https://support.microsoft.com/en-us/clipchamp/what-are-the-clipchamp-paid-plans-and-how-do-they-work | Free personal editor, free stock, watermark-free 1080p exports. Copilot automatic script+stock video is **separate commercial Microsoft 365 requirement**, not personal free feature |
| **MoviePy/FFmpeg** | Above | Reproducible editing and iPhone-friendly H.264/AAC MP4, captions and frame checks already achievable without a desktop GUI |

## 3. AI company cross-check — do not confuse model interfaces with renderers
- **OpenAI:** [Sora web/app discontinued April 26, 2026; Sora API discontinued September 24, 2026](https://help.openai.com/en/articles/20001152-what-to-know-about-the-sora-discontinuation). ChatGPT can create visual stills and write/render video with tools, but discontinued Sora is not available production compute.
- **Anthropic:** [Claude for Creative Work, April 28, 2026](https://www.anthropic.com/news/claude-for-creative-work) explicitly emphasizes writing code for procedural animation, coordinating Blender/Adobe connectors; Claude is an orchestrating/editorial model, **not interchangeable with an AI video-diffusion renderer**.
- **Microsoft Copilot:** [Copilot Create + Clipchamp](https://support.microsoft.com/en-us/clipchamp/how-to-create-video-with-copilot) uses AI scripts/voice and **stock footage**, available with qualifying organizational Microsoft 365/Clipchamp access; [personal Clipchamp 1080p editor](https://support.microsoft.com/en-us/clipchamp/what-are-the-clipchamp-paid-plans-and-how-do-they-work) is separately free.
- **Google:** [Google Vids](https://workspace.google.com/products/vids/) is free to try; [personal AI feature allowances](https://support.google.com/docs/answer/15609411?hl=en) list **50 credits/month** and up to **60 seconds/month AI video clips** for personal accounts at current release. [Veo API](https://ai.google.dev/gemini-api/docs/pricing) has **no free tier**.
- **GitHub Copilot / Claude Code / Codex / Gemini CLI:** suitable *agents that write and operate* free video tools where their own model access permits, **not inherently free compute or free video-rendering services**.

## 4. YouTube practical demonstrations — useful instruction, not verified capability acceptance
- [Mickmumpitz, *Build your own AI MOVIES shot by shot* (Nov 1 2025)](https://www.youtube.com/watch?v=YpuSE9hcal8) — ComfyUI, Qwen Image Edit, Wan2.2, continuity, camera setup; high local GPU requirements remain.
- [Alex Followell, *How to install Wan2.2 in ComfyUI* (Aug 2025)](https://www.youtube.com/watch?v=teCSTPyT0sM) — useful model choice, 5B vs 14B, video I2V; check current official release and hardware.
- [ErrorFixer, *Generate AI Videos for FREE — ComfyUI + Wan2.2* (Aug 2026)](https://www.youtube.com/watch?v=z8chiPJsXbU) — low-VRAM GGUF unofficial path, experimental and not the official 24GB native reference.
- [Mickmumpitz, *Shoot ENTIRE MOVIES with this FREE AI workflow* (May 2025)](https://www.youtube.com/watch?v=pd76XGHCavY) — smartphone-footage-based VFX, local Wan workflow.
Descriptions and chapter summaries are evidence of *what the creators describe*, **not** proof that each full video was watched or every workflow independently tested.

## 5. Existing Plenum workforce assignment plan (single Chief, no duplicate master)
1. **Scientific Research** — original literature/experiment/source fact check and evidence distinction for each spoken/on-screen claim. No fabricated trials, growth improvements or emissions results.
2. **Global Intelligence** — identify real Pexels/Mixkit/Wikimedia clips and each item license, exact URLs, timestamps and releases; original source catalogue, no indiscriminate downloading.
3. **Creative + Engineering** — one scoped 30–45 second **original** Terra trailer proof with 3 real moving free-licensed clips, natural local voice, 1 scientific diagram, original soundtrack, professional typography, no paid service.
4. **Independent Verification** — evaluate actual MP4 picture/audio, source provenance, scientific claim compliance, license, subtitle timing, no watermark, iPhone playback, inspect start/middle/end at least. Report acceptance or precise failure, not a green test assertion.
5. **Chief** — record outputs and next action in existing [#494](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/494), reuse this ledger rather than re-research entire stack. **Do not upload patent-sensitive materials or private customer data into this public GitHub repository**.

## 6. Decision gates before import/deployment
- **P0 zero-incremental-cost baseline:** Existing FFmpeg/Python for production and original files, professional evidence-led script, copyright/attribution ledger. Already available; *no agent runtime inferred*.
- **P1 local code-to-video pilot:** compare **HyperFrames vs givemotion** on the **same specific original 10-second motion-graphics task**; adopt at most one based on true run, readable edits, license and final MP4 QA. Remotion is conditional alternative (up to 3 employees).
- **P1 local narration:** Kokoro with permitted Apache-2.0 weights vs Piper engine with voice-specific usage terms; choose measured audio quality, not branding alone.
- **P1 actual footage:** use verified Pexels/Mixkit real pasture/cattle footage, not automatically assume all stock or all NASA images are commercial-free.
- **P2 diffusion models:** only after *verified owned CUDA GPU or compatible large-memory Mac*, eligible licenses, practical target fps/resolution and measured cost/quality. GitHub Actions cannot be turned into an indefinite commercial GPU inference farm.
- **P2 paid-cloud AI footage:** preserve dormant provider comparison; use only after explicit owner permission for included quota and the exact task.

## Sources and last verification
Source links appear in-row above and were checked against provider docs / upstream repositories on **2026-11-11**. Vendor offerings, quotas and licenses may change. **This document is a vetted research/adoption decision brief; installation and independently accepted runtime tests are still future work.**

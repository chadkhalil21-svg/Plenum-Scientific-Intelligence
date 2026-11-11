---
name: plenum-research-youtube
description: Research YouTube and original technical or institutional sources without treating demonstrations or transcripts as independently validated facts.
---

# plenum research youtube

**Apply when:** Investigating new AI agent skills, tools, science, vendor claims and research recommendations.

## Procedure
1. Form a question and search official upstream documentation and dated YouTube presentations that address that question.
2. For each video log title, creator, publication date, URL, claim, timestamp if available, and whether original transcript/content was directly accessible. Never invent a transcript.
3. Check material specifications, prices, licenses, privacy terms and limitations against the vendor's current official source or original repository; mark a video-only demonstration as unverified.
4. Separate installed, source-integrated, executable, and simply referenced technology; video demonstrations cannot prove Plenum deployment.
5. Summarize only the three to five highest-value discoveries, why useful for a named workforce, integration needed, expected cost, potential risk, and a concrete evaluation test.
6. Record dates and enough citations to reproduce the claim; fail cleanly when a link/video is inaccessible.

## Required deliverable
Verified public source table: capability | source and date | claimed benefit | verified limitation | workforce | adopt/hold/exclude and why.

## Evidence sources to consult (not substitutes for live validation)
- https://www.anthropic.com/research/writing-tools-for-agents
- https://www.youtube.com/watch?v=CEvIs9y1uog

## Shared constraints
Use public sources for public GitHub jobs. Private financial information, credentials, patents, customer records, and external actions require an independently authorized private integration. A skill file is portable instructions, not a running model, installed third-party integration, paid resource, or proof of completing a real task.

## Uploader-description completeness before inference
For public videos with numbered software lists, prefer the creator's complete published description over platform tags alone, and independently cross-check a timestamped chapter-by-chapter summary or real published subtitles. Record each research input as Uploader Description, Timestamp Summary, Full Caption, or Full Playback; NEVER claim the latter two occurred when only the first two were obtained. An agent returning 100 generic URLs has not completed a video-specific tool list. Cross-reference the October 6 Fyv5CHAzq_A correction in docs/PLENUM_VIDEO_FYV5CHAZQ_A_REVIEW.md.

## 2026-11-11: Actual no-key public caption worker
On an original founder-issued PUBLIC research issue use `src/plenum_ai/youtube_public_caption_worker.py` and the existing GitHub Actions `.github/workflows/plenum-public-youtube-captions.yml`. This integrates upstream MIT `youtube-transcript-api==1.2.5`, requests the actual six reviewed video IDs, returns existing catalogue name matches with timestamp offsets, and never stores or reproduces the full copyrighted transcripts. Failing on a cloud YouTube IP is a legitimate `CAPTION_UNAVAILABLE` outcome, not evidence that the video has no captions. For tasks needing a comprehensive creator list, first use original uploader description/chapters and then accessible subtitles. Do not present generic 100 web source leads as fulfilled video research. See `docs/PLENUM_SIX_VIDEO_REVIEW_20261111.md` for actual source labels.

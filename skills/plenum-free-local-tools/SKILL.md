---
name: plenum-free-local-tools
description: Reuse current Ollama inference and optional approved local whisper.cpp and ffmpeg without a new subscription, account, or redundant model runtime.
---
# Free local software is useful only on real compute
Original Plenum already runs Qwen using Ollama on selected free project-bound GitHub actions. That is actual limited local inference, not a permanent private AI host. No new generic Ollama server is needed.
Run `python -m plenum_ai.free_local_tool_adapter --probe` on the intended legitimate owner-controlled computer to see if `whisper-cli`, `ffmpeg`, `ollama` and `llama-cli` exist. The tool reports availability; it does not fetch software, model weights, request paid tokens or install a host.
When owner-provided WAV + `whisper.cpp` model weights are present, `transcribe_local` can use the pinned local executable to create a plain text transcript without cloud APIs. Media data and model weights must be legally sourced, kept out of PUBLIC GitHub, and stored on approved private runtime. The implementation refuses automatic public GitHub transcription, arbitrary URL downloads, symlinks, unsupported inputs or non-existent models.
If no host is available, label these tools as `SOURCE_READY_NOT_RUNNING` rather than pretending they are active. LM Studio and AnythingLLM are optional GUI alternatives; importing all of them repeats the same local model capability. Privacy, copyright and free-license conditions still apply.

"""Bounded, zero-vendor-fee Kokoro speech auditions for Plenum's film studio.

No paid API, voice cloning, secret, owner private data or publication. The local
model weights and voice packs must be supplied from upstream, SHA-256 checked
by the independent workflow. Audio passing structural checks is NOT proof that
it sounds natural or that a particular voice is suitable for commercial use.
"""
from __future__ import annotations

import argparse
from array import array
from hashlib import sha256
import json
from pathlib import Path
import sys
import wave

VOICES = ("am_michael", "af_sarah")
MODEL_SHA256 = "ae315a79b623f244700e4afb9246c46a26066782e049ba174bf3ba433970ee9c"
VOICES_SHA256 = "bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d"
UPSTREAM = "https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.1"


def audit_wav(path: Path) -> dict:
    """Actual independent 16-bit PCM readback, not a WAV filename assertion."""
    with wave.open(str(path), "rb") as stream:
        rate = stream.getframerate()
        channels = stream.getnchannels()
        frames = stream.getnframes()
        width = stream.getsampwidth()
        audio = stream.readframes(frames)
    if channels != 1 or width != 2 or not 16000 <= rate <= 48000:
        raise RuntimeError("Unexpected or invalid mono 16-bit PCM speech")
    if frames < rate * 2 or frames > rate * 35:
        raise RuntimeError("Audition length outside 2–35 seconds")
    samples = array("h")
    samples.frombytes(audio)
    if sys.byteorder != "little":
        samples.byteswap()
    peak = max(abs(n) for n in samples) if samples else 0
    if peak < 256:
        raise RuntimeError("Silence/inaudible speech sample")
    return {
        "duration_seconds": round(frames / rate, 3),
        "sample_rate": rate, "channels": channels,
        "peak_amplitude": round(peak / 32768, 5),
        "file_sha256": sha256(path.read_bytes()).hexdigest(),
    }


def render_auditions(text_file: Path, model_file: Path, voices_file: Path, output_dir: Path) -> dict:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError("No overwriting original audition media")
    text = text_file.read_text(encoding="utf-8").strip()
    if not 35 <= len(text) <= 250 or "\n" in text:
        raise ValueError("Public approved audition text must be 35–250 characters and one line")
    if sha256(model_file.read_bytes()).hexdigest() != MODEL_SHA256:
        raise ValueError("Unexpected model bytes; upstream SHA-256 mismatch")
    if sha256(voices_file.read_bytes()).hexdigest() != VOICES_SHA256:
        raise ValueError("Unexpected voice-pack bytes; upstream SHA-256 mismatch")
    try:
        from kokoro_onnx import Kokoro
        import soundfile as sf
    except ImportError as exc:
        raise RuntimeError("Local free kokoro-onnx and soundfile must be installed") from exc
    output_dir.mkdir(parents=True, exist_ok=True)
    model = Kokoro(str(model_file), str(voices_file))
    tracks = []
    for voice in VOICES:
        samples, sample_rate = model.create(text, voice=voice, speed=0.94, lang="en-us")
        path = output_dir / (voice + ".wav")
        sf.write(str(path), samples, sample_rate, subtype="PCM_16")
        tracks.append({"voice": voice, "path": path.name, **audit_wav(path)})
    manifest = {
        "schema": "plenum-local-voice-audition-v1",
        "status": "REAL_SPEECH_TRACKS_RENDERED_NOT_ARTISTICALLY_ACCEPTED",
        "tracks": tracks,
        "text": text,
        "local_inference_only": True,
        "paid_inference_used": False,
        "owner_voice_cloned": False,
        "source_release": UPSTREAM,
        "model_sha256": MODEL_SHA256,
        "voices_sha256": VOICES_SHA256,
        "library_license": "MIT (verify upstream notices)",
        "model_license": "Apache-2.0 (verify individual voice attribution/rights)",
        "naturalness_independently_verified": False,
        "commercial_voice_rights_independently_verified": False,
        "founder_approval_for_film_release": False,
    }
    (output_dir / "audition_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text-file", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--voices", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(render_auditions(args.text_file, args.model, args.voices, args.out_dir), indent=2))


if __name__ == "__main__":
    main()

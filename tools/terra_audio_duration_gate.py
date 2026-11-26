#!/usr/bin/env python3
"""Fail closed on measured WAV scene timing for the unreleased Terra 5-minute film.

Usage: python tools/terra_audio_duration_gate.py EDITORIAL.json WAV_DIRECTORY
Inputs must contain scene_01.wav ... scene_10.wav (PCM WAV). No synthesis, upload,
external network, or automatic approval. WAV duration is a measurement of the
provided file, NOT evidence of naturalness, scientific review or caption sync.
"""
import json
import sys
import wave
from pathlib import Path


def audit(editorial_path: Path, wav_dir: Path) -> list[dict]:
    source = json.loads(editorial_path.read_text(encoding="utf-8"))
    scenes = source["scenes"]
    if len(scenes) != 10 or source["total_target_seconds"] != 300:
        raise ValueError("Expected exactly ten scenes in a 300-second picture timeline")
    results = []
    previous_end = 0.0
    for expected, scene in enumerate(scenes, start=1):
        if scene["scene"] != expected:
            raise ValueError(f"Scene order mismatch at {expected}")
        start = float(scene["picture_start_seconds"])
        end = float(scene["picture_end_seconds"])
        if abs(start - previous_end) > 0.001 or end <= start:
            raise ValueError(f"Discontinuous picture timeline at scene {expected}")
        path = wav_dir / f"scene_{expected:02d}.wav"
        with wave.open(str(path), "rb") as wav:
            if wav.getnchannels() not in (1, 2) or wav.getframerate() <= 0:
                raise ValueError(f"Invalid WAV format: {path}")
            duration = wav.getnframes() / wav.getframerate()
        available = end - start
        if duration > available + 0.001:
            raise ValueError(
                f"Scene {expected:02d} narration {duration:.3f}s exceeds "
                f"picture window {available:.3f}s"
            )
        results.append({
            "scene": expected,
            "wav": path.name,
            "measured_wav_seconds": round(duration, 3),
            "picture_window_seconds": round(available, 3),
            "remaining_seconds": round(available - duration, 3),
        })
        previous_end = end
    if abs(previous_end - 300.0) > 0.001:
        raise ValueError("Picture timeline must end at 300 seconds")
    return results


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: terra_audio_duration_gate.py EDITORIAL.json WAV_DIRECTORY")
    try:
        results = audit(Path(sys.argv[1]), Path(sys.argv[2]))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        sys.exit(f"NOT ACCEPTED: {exc}")
    print(json.dumps({
        "status": "MEASURED_WAV_FITS_PICTURE_WINDOWS_ONLY",
        "scenes": results,
        "caption_sync_verified": False,
        "narrator_artistic_approval": False,
        "scientific_approval": False,
        "film_release_approved": False,
    }, indent=2))

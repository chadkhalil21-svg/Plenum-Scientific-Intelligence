"""Free, reproducible Plenum short-film assembly using system FFmpeg only.

This tool creates actual playable MP4s from original color scenes and authorized
local stills/footage. It never downloads assets, calls metered APIs, generates
or impersonates voices, or declares third-party copyrights cleared. A missing
natural narration track is an explicit release blocker, not a synthetic voice.

Usage: python -m plenum_ai.film_factory --storyboard file.json --out-dir out
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import struct
import subprocess
import tempfile
import wave
from pathlib import Path

FPS = 24
SIZE = (1280, 720)
MAX_SCENES = 30
MAX_DURATION_SECONDS = 300
VALID_SOURCES = {"original", "owned", "cc0", "cc-by", "pexels", "mixkit-free", "reviewed-license"}
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def _local_file(path: str, root: Path) -> Path:
    """No URLs, traversal or symlinks: only explicit founder-provided local files."""
    if not isinstance(path, str) or not path or "://" in path:
        raise ValueError("Media must be a named local file, not an URL")
    candidate = Path(path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError("Media path must be relative and under storyboard folder")
    actual = root / candidate
    if not actual.is_file() or actual.is_symlink() or not actual.resolve().is_relative_to(root.resolve()):
        raise ValueError("Media missing, symlinked, or outside storyboard folder")
    return actual


def _validate_provenance(item: dict, *, original: bool) -> None:
    license_ = item.get("license")
    if original:
        if license_ != "original":
            raise ValueError("Procedural original scenes must use license=original")
        return
    if license_ not in VALID_SOURCES - {"original"}:
        raise ValueError("Explicit permissible source license category is required")
    if not item.get("creator") or not item.get("source_url"):
        raise ValueError("Media requires creator/source URL and manually checked rights")
    if not str(item["source_url"]).startswith("https://"):
        raise ValueError("Media source link must be HTTPS")
    if item.get("rights_reviewed") is not True:
        raise ValueError("A human must first confirm the precise asset license and context")



def _validate_audio_provenance(item: dict, kind: str) -> None:
    """Permit rights-reviewed original tracks while requiring explicit voice rights.

    A track marked original must be genuinely authored/recorded by its creator.
    Textual declarations are still claims, not independent copyright clearance.
    """
    if item.get("license") == "original":
        if (item.get("rights_reviewed") is not True
                or not isinstance(item.get("creator"), str)
                or not item["creator"].strip()
                or item.get("origin") not in {"self-recorded", "self-composed", "original-procedural"}
                or item.get("source_url")):
            raise ValueError("Original audio needs creator, origin and explicit rights review")
    else:
        _validate_provenance(item, original=False)
    if kind == "narration" and item.get("voice_usage_rights_reviewed") is not True:
        raise ValueError("Narration must have voice identity and commercial-usage rights reviewed")


def validate(storyboard: dict, root: Path) -> list[dict]:
    if storyboard.get("schema") != "plenum-film-storyboard-v1":
        raise ValueError("Unsupported film storyboard schema")
    scenes = storyboard.get("scenes")
    if not isinstance(scenes, list) or not 1 <= len(scenes) <= MAX_SCENES:
        raise ValueError("Expected 1–30 scenes")
    total = 0.0
    for scene in scenes:
        if not isinstance(scene, dict) or scene.get("type") not in {"color", "image", "video"}:
            raise ValueError("Scene must be color, image or video")
        seconds = scene.get("seconds")
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds <= 0 or seconds > 60:
            raise ValueError("Scene length must be 0–60 seconds")
        frames = round(seconds * FPS)
        if frames < 1:
            raise ValueError("Scene too short for one frame")
        scene["_frames"] = frames
        total += frames / FPS
        for key in ("title", "caption"):
            value = scene.get(key, "")
            if not isinstance(value, str) or len(value) > 220 or any(ord(c) < 32 and c != "\n" for c in value):
                raise ValueError("Unsupported title/caption")
        if scene["type"] == "color":
            if not HEX_COLOR.fullmatch(scene.get("color", "")):
                raise ValueError("Original color scenes require #RRGGBB")
            _validate_provenance(scene, original=True)
        else:
            _local_file(scene.get("path"), root)
            _validate_provenance(scene, original=False)
        if scene.get("concept") not in (True, False):
            raise ValueError("Concept scene status must be explicit")
    if total > MAX_DURATION_SECONDS:
        raise ValueError("Film exceeds five minute bounded render ceiling")
    for name in ("narration", "music"):
        item = storyboard.get(name)
        if item is not None:
            if not isinstance(item, dict):
                raise ValueError("Track must be a dictionary")
            _local_file(item.get("path"), root)
            _validate_audio_provenance(item, kind=name)
    return scenes


def _run(command: list[str], *, timeout: int = 120) -> None:
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError("FFmpeg failed: " + result.stderr[-1400:])


def _drawtext(textfile: Path, size: int, y: int, color: str = "white") -> str:
    # Text is read from an *authored local* file: avoid filter injection.
    return (f"drawtext=font='DejaVu Sans':textfile='{textfile.as_posix()}':"
            f"fontsize={size}:fontcolor={color}:x=(w-text_w)/2:y={y}:" )[:-1]


def _render_scene(scene: dict, idx: int, root: Path, scratch: Path) -> Path:
    video = scratch / f"scene-{idx:02d}.mp4"
    duration = scene["_frames"] / FPS
    frame = f"{SIZE[0]}x{SIZE[1]}"
    if scene["type"] == "color":
        color = "0x" + scene["color"][1:]
        command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                   f"color=c={color}:s={frame}:r={FPS}:d={duration:.6f}"]
        base = "format=yuv420p"
    else:
        source = _local_file(scene["path"], root)
        if scene["type"] == "image":
            command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-loop", "1", "-framerate", str(FPS), "-i", str(source)]
        else:
            command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-stream_loop", "-1", "-i", str(source)]
        base = f"scale={SIZE[0]}:{SIZE[1]}:force_original_aspect_ratio=increase,crop={SIZE[0]}:{SIZE[1]},setsar=1,fps={FPS},format=yuv420p"
    overlays = []
    title = scene.get("title", "")
    if title:
        p = scratch / f"title-{idx:02d}.txt"
        p.write_text(title, encoding="utf-8")
        overlays += [_drawtext(p, 47, 90)]
    caption = scene.get("caption", "")
    if caption:
        p = scratch / f"caption-{idx:02d}.txt"
        p.write_text(caption, encoding="utf-8")
        overlays += [_drawtext(p, 27, 580)]
    if scene["concept"]:
        p = scratch / f"status-{idx:02d}.txt"
        p.write_text("CONCEPT VISUALIZATION", encoding="utf-8")
        overlays += [_drawtext(p, 23, 660, "yellow")]
    filters = ",".join([base] + overlays)
    command += ["-vf", filters, "-t", f"{duration:.6f}", "-r", str(FPS),
                "-frames:v", str(scene["_frames"]), "-an", "-c:v", "libx264",
                "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p", str(video)]
    _run(command)
    return video


def _original_ambient(out: Path, seconds: float) -> None:
    """Original and very restrained instrumental underscore, no lifted loops."""
    hz, frame = 24000, 1024
    chords = (130.81, 164.81, 196.00)  # ordinary tonal pitches, not a melody
    with wave.open(str(out), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(hz)
        total = math.ceil(seconds * hz)
        for start in range(0, total, frame):
            end = min(start + frame, total)
            samples = bytearray()
            for i in range(start, end):
                t = i / hz
                fade = min(1.0, t / 0.7, max(0.0, (seconds - t) / 0.8))
                # slow evolving chord, not simulated narration or a claimed score from an artist
                value = sum(math.sin(2 * math.pi * freq * t) for freq in chords) / 3
                sample = max(-32768, min(32767, int(value * fade * 1800)))
                samples.extend(struct.pack("<h", sample))
            wav.writeframesraw(bytes(samples))



def _srt_timestamp(frame: int) -> str:
    """Frame-exact SubRip timestamps at the existing fixed 24 fps."""
    total_ms = round(frame * 1000 / FPS)
    total_seconds, ms = divmod(total_ms, 1000)
    hours, rem = divmod(total_seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"


def write_scene_caption_sidecar(scenes: list[dict], path: Path) -> int:
    """Export scene captions already shown in video: no synthetic word timings.

    This exports a useful accessible text alternative, not an independent
    transcript of narration and not proof the spoken word cue is synchronized.
    """
    position, cues = 0, []
    for scene in scenes:
        frames = scene["_frames"]
        caption = scene.get("caption", "").strip()
        if caption:
            cues.append(
                f"{len(cues)+1}\n{_srt_timestamp(position)} --> "
                f"{_srt_timestamp(position + frames)}\n{caption}\n"
            )
        position += frames
    if cues:
        path.write_text("\n".join(cues) + "\n", encoding="utf-8")
    return len(cues)


def render(storyboard_path: Path, output_dir: Path) -> dict:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("Requires free locally installed FFmpeg and FFprobe")
    root = storyboard_path.resolve().parent
    data = json.loads(storyboard_path.read_text(encoding="utf-8"))
    scenes = validate(data, root)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError("Output directory must be new or empty")
    output_dir.mkdir(parents=True, exist_ok=True)
    duration = sum(s["_frames"] / FPS for s in scenes)
    with tempfile.TemporaryDirectory(prefix="plenum-free-film-") as tmp:
        scratch = Path(tmp)
        videos = [_render_scene(scene, i, root, scratch) for i, scene in enumerate(scenes)]
        concat = scratch / "concat.txt"
        concat.write_text("".join("file '" + v.as_posix() + "'\n" for v in videos), encoding="utf-8")
        silent = scratch / "silent.mp4"
        _run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(silent)])
        music = data.get("music")
        if music is None:
            bed = scratch / "original-underscore.wav"
            _original_ambient(bed, duration)
            music_status = "original procedural underscore"
        else:
            bed = _local_file(music["path"], root)
            music_status = "owner-provided, claimed rights reviewed"
        final = output_dir / "film.mp4"
        command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(silent), "-i", str(bed)]
        narr = data.get("narration")
        if narr:
            command += ["-i", str(_local_file(narr["path"], root)),
                        "-filter_complex", "[1:a]volume=0.22[bed];[2:a]volume=1.0[voice];[bed][voice]amix=inputs=2:duration=first:dropout_transition=1[out]",
                        "-map", "0:v:0", "-map", "[out]"]
        else:
            command += ["-map", "0:v:0", "-map", "1:a:0"]
        command += ["-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-t", f"{duration:.6f}",
                    "-movflags", "+faststart", str(final)]
        _run(command, timeout=150)
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,codec_name",
                            "-of", "json", str(final)], capture_output=True, text=True, check=True)
    info = json.loads(probe.stdout)
    types = {stream.get("codec_type") for stream in info.get("streams", [])}
    if not {"video", "audio"} <= types or abs(float(info["format"]["duration"]) - duration) > 0.3:
        raise RuntimeError("Actual MP4 audio/video/duration failed independent probe")
    cue_count = write_scene_caption_sidecar(scenes, output_dir / "film.srt")
    report = {"schema": "plenum-free-film-render-v1", "status": "TECHNICAL_RENDER_COMPLETE",
              "film": str(final), "seconds": duration, "scenes": len(scenes),
              "image": f"{SIZE[0]}x{SIZE[1]}", "fps": FPS,
              "separate_subtitle_sidecar": str(output_dir / "film.srt") if cue_count else None,
              "subtitle_cues": cue_count,
              "caption_timing_scope": "scene_boundaries_only_not_narration_word_aligned",
              "audio": music_status, "voice_included": bool(data.get("narration")),
              "natural_voice_approved": False, "third_party_rights_independently_audited": False,
              "creative_quality_independently_accepted": False,
              "public_distribution_approved": False, "paid_services_used": False,
              "ffprobe_streams": info["streams"],
              "source_ledger": [{"scene": i + 1, "kind": s["type"], "license": s["license"],
                                 "source_url": s.get("source_url"), "rights_reviewed_claimed": s.get("rights_reviewed", False),
                                 "concept_visualization": s["concept"]} for i, s in enumerate(scenes)],
              "audio_source_ledger": {name: {
                  "license": item.get("license"),
                  "creator": item.get("creator"),
                  "origin": item.get("origin"),
                  "source_url": item.get("source_url"),
                  "rights_reviewed_claimed": item.get("rights_reviewed") is True,
                  "voice_usage_rights_reviewed_claimed": (
                      item.get("voice_usage_rights_reviewed") is True if name == "narration" else None
                  )
              } for name in ("music", "narration") if (item := data.get(name)) is not None}}
    (output_dir / "render_receipt.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Zero-vendor-fee local film renderer")
    parser.add_argument("--storyboard", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(render(args.storyboard, args.out_dir), indent=2))


if __name__ == "__main__":
    main()

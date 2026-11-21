#!/usr/bin/env python3
"""Fail-closed, stdlib-only structural gate for Terra's five-minute editorial cue source.

This is NOT an audio-sync, science, footage-rights, or MP4 acceptance test.
Usage: python scripts/validate_terra_editorial_release.py [path/to/editorial.json]
"""
import json
import math
import pathlib
import sys

DEFAULT = pathlib.Path(__file__).resolve().parents[1] / "docs/PLENUM_TERRA_5MIN_EDITORIAL_CAPTION_SOURCE_20261120.json"


def check(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    errors = []
    scenes = data.get("scenes", [])
    if data.get("status") != "UNSYNCED_EDITORIAL_SOURCE_NOT_RELEASE_CAPTIONS":
        errors.append("Source must remain explicitly UNSYNCED until separately accepted")
    if data.get("total_target_seconds") != 300 or len(scenes) != 10:
        errors.append("Expected ten scenes and exactly 300 target seconds")
    expected = 0
    for index, scene in enumerate(scenes, 1):
        prefix = f"scene {index}"
        if scene.get("scene") != index:
            errors.append(f"{prefix}: wrong ordinal")
        start, end = scene.get("picture_start_seconds"), scene.get("picture_end_seconds")
        if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (start, end)):
            errors.append(f"{prefix}: invalid picture bounds")
        elif start != expected or end != index * 30:
            errors.append(f"{prefix}: discontinuous or incorrect picture window")
        expected = index * 30
        if not isinstance(scene.get("narration_source_text"), str) or not scene["narration_source_text"].strip():
            errors.append(f"{prefix}: missing narration")
        if scene.get("audio_start_seconds") is not None or scene.get("audio_end_seconds") is not None:
            errors.append(f"{prefix}: audio timing entered without independent WAV acceptance")
        if scene.get("caption_cues") != []:
            errors.append(f"{prefix}: captions entered in unsynced source")
        if scene.get("voice_approved") is not False or scene.get("science_approved") is not False:
            errors.append(f"{prefix}: unverified approval flag")
        disclosure = scene.get("persistent_disclosure", "")
        if index in (4, 5) and disclosure != "PUBLISHED SUPPLEMENT RESEARCH — NOT PLENUM TERRA RESULTS":
            errors.append(f"{prefix}: missing supplement-versus-Terra distinction")
        if index in (6, 7, 8, 9) and disclosure != "CONCEPT VISUALIZATION — NOT FIELD RESULTS":
            errors.append(f"{prefix}: missing concept disclosure")
        if index in (4, 5) and not {"10.1371/journal.pone.0247820", "10.1093/jas/skae109"}.issubset(set(scene.get("source_dois", []))):
            errors.append(f"{prefix}: missing published-study DOI")
    return errors


def main():
    path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    try:
        errors = check(path)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"FAIL: cannot inspect editorial source: {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: ten contiguous 30s picture windows; explicit unsynced status; disclosures; DOI presence; no invented approvals.")
    print("NOT TESTED: WAV alignment, caption timing, rights, scientific full texts, narrator artistry, actual MP4 and independent acceptance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

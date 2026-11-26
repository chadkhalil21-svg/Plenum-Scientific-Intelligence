#!/usr/bin/env python3
"""Generate untimed caption phrase candidates from the public Terra editorial source.

No timestamps are invented: alignment requires actual approved narration WAVs.
Run: python scripts/terra_caption_phrase_plan.py INPUT.json OUTPUT.json
"""
import json
import re
import sys
from pathlib import Path

MAX_WORDS = 12

def phrases(text):
    # Split at natural sentence and clause boundaries, then into short word groups.
    chunks = re.split(r"(?<=[.!?;:])\s+|(?<=,)\s+", text.strip())
    result = []
    for chunk in chunks:
        words = chunk.split()
        while words:
            if len(words) <= MAX_WORDS:
                result.append(" ".join(words))
                break
            # Prefer a shorter segment near a syntactic boundary; never alter words.
            cut = min(MAX_WORDS, len(words))
            result.append(" ".join(words[:cut]))
            words = words[cut:]
    return result

def build(data):
    if data.get("total_target_seconds") != 300 or len(data.get("scenes", [])) != 10:
        raise ValueError("Expected ten scenes and a 300-second editorial target")
    output = {"status": "UNTIMED_PHRASE_CANDIDATES_NOT_SRT_OR_APPROVED_CAPTIONS",
              "source_schema": data.get("schema"), "scenes": []}
    for index, scene in enumerate(data["scenes"], 1):
        if scene["scene"] != index or scene["picture_start_seconds"] != (index-1)*30 or scene["picture_end_seconds"] != index*30:
            raise ValueError("Scene picture window mismatch")
        source = scene["narration_source_text"]
        cues = phrases(source)
        if " ".join(cues).split() != source.split():
            raise ValueError("Narration tokens were changed")
        output["scenes"].append({
            "scene": index, "picture_window_seconds": [scene["picture_start_seconds"], scene["picture_end_seconds"]],
            "disclosure": scene["persistent_disclosure"], "phrase_candidates": [
                {"text": phrase, "audio_start_seconds": None, "audio_end_seconds": None}
                for phrase in cues],
            "voice_approved": False, "science_approved": False})
    return output

def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: terra_caption_phrase_plan.py INPUT.json OUTPUT.json")
    source = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    output = build(source)
    Path(sys.argv[2]).write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()

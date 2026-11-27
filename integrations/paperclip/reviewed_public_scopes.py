"""Exact public source-bound mission admission; no arbitrary rich event scopes.

The original reviewed arithmetic and extractive engines remain unchanged.
The owner still creates the exact issue, which receives one native reservation.
All other rich scopes, including pipeline successors, remain denied.
"""
from pathlib import Path
from hashlib import sha256
import json

ROOT=Path(__file__).resolve().parents[2]
SOURCES={
    "timing":"docs/PLENUM_TERRA_5MIN_SCRIPT_TIMING_ACCEPTANCE_20261112.md",
    "scene":"docs/PLENUM_TERRA_SCENE04_PRIMARY_STUDY_SCOPE_20261119.md",
    "science":"docs/PLENUM_TERRA_5MIN_SCIENCE_CLAIM_RELEASE_GATE_20261118.md",
}
BLOBS={
    "timing":"d1efe1aac0ea4c6039a212b3f2d48c9566178117",
    "scene":"daaecf0b870e3d1a39498eaceb39ba68b8e5fd25",
    "science":"2b3610b8922cf43cac359d68001fee2fd629770d",
}
DOIS=["10.1371/journal.pone.0247820","10.1093/jas/skae109"]

def source(name):
    import hashlib
    path=ROOT/SOURCES[name]
    if path.is_symlink() or not path.is_file() or path.stat().st_size>32000:
        raise ValueError("Missing reviewed public source")
    data=path.read_bytes()
    blob=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
    if blob!=BLOBS[name]:raise ValueError("Reviewed public source changed")
    return data.decode("utf-8")

def q(n,d=1):return {"numerator":n,"denominator":d}

def scopes():
    from composition_contract import hash_value
    from synthesis_contract import digest,encoded
    # Actual 480-word revised candidate, original 590-word draft,
    # documented planning rate 118 wpm and 120 wpm comparison.
    # Not a measured WAV or release approval.
    timing,scene,science=(source(k) for k in ("timing","scene","science"))
    if not all(x in timing for x in ("590","118 words/minute","120 wpm")) or "480-word" not in scene:
        raise ValueError("Timing source no longer supports input values")
    arithmetic={"kind":"public_objective","objective":"For the five minute Terra film calculate narration duration in minutes at the specified reading rate and the remaining minutes for visual pauses.",
        "dois":DOIS,"inputs":{"composition":{
        "values":{"words":480,"words_per_minute":118,"film_minutes":5},
        "holdout":{"words":590,"words_per_minute":120,"film_minutes":5},
        "outputs":["narration_minutes","pause_minutes"],
        "dimensions":{"words":{"word":1},"words_per_minute":{"word":1,"time":-1},"film_minutes":{"time":1},"narration_minutes":{"time":1},"pause_minutes":{"time":1}},
        "integer_outputs":[]}},
        "result_commitment":hash_value({"results":{"narration_minutes":q(240,59),"pause_minutes":q(55,59)},
          "holdout":{"narration_minutes":q(59,12),"pause_minutes":q(1,12)}})}
    excerpts={
        "scene":["No Terra efficacy percentage may appear.",
            "An independent scientific reviewer must still check both complete original papers, methods, dosing definitions, statistical endpoints, residue/safety qualifications, conflicts, and any displayed graphics."],
        "science":["The current 480-word script is an editorial candidate.",
            "Founder retains separate authorization for any external publication."]}
    for key,lines in excerpts.items():
        original={"scene":scene,"science":science}[key]
        if any(line not in original for line in lines):raise ValueError("Source excerpt changed")
    wanted=[{"type":"extract","citations":[x]} for x in ("scene_1","scene_2","science_2")]
    synthesis={"kind":"public_objective","objective":"Extract the Terra efficacy claim restriction, the required independent primary paper review, and the separate founder publication authorization.",
       "dois":DOIS,"inputs":{"synthesis":{"documents":{k:" ".join(v) for k,v in excerpts.items()}}},
       "result_commitment":digest(sorted(wanted,key=encoded))}
    return {"terra-timing":arithmetic,"terra-release":synthesis}

def require(scope):
    from mission_scope import digest
    # No user-provided path, code, URL, access grant or answer substitution.
    # Scope equality and validated digest both bind the original reviewed data.
    for candidate in scopes().values():
        if scope==candidate and digest(scope)==digest(candidate):return
    raise PermissionError("Rich public scope requires exact protected review")

if __name__=="__main__":
    import sys
    from mission_scope import MAGIC,validate_scope
    if len(sys.argv)!=2:raise SystemExit("Select one reviewed public mission")
    print(MAGIC+"\n"+json.dumps(validate_scope(scopes()[sys.argv[1]]),separators=(",",":")))

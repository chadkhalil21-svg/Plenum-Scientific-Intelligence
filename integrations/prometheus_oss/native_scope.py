"""Exact independent native OSS scope; original adaptive commitments unchanged."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"paperclip"))
from adaptive_turns_smoke import scope as original
from mission_scope import validate_scope
def scope(case):
    if case not in ("oss-review","oss-defer"):raise ValueError("Unknown native OSS case")
    s=original("adaptive-"+case.split("-")[1])
    s["inputs"]["synthesis"]["followup"]["engine"]="deepagents"
    return validate_scope(s)
if __name__=="__main__":print(json.dumps(scope(sys.argv[1]),separators=(",",":")))

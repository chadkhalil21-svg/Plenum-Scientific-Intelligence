"""Fixed reviewed persistent process entrypoint; no configurable executable or stored env."""
import os
import runpy
import sys
from pathlib import Path

def main():
    if len(sys.argv)!=2 or sys.argv[1] not in ("minister","intelligence","research","engineering","commercial","verification"):
        raise SystemExit("Unknown persistent role")
    # Resolve mode from immutable prepared UUID-scoped mission, not adapter env.
    os.environ["PLENUM_PERSISTENT_BOARD"]="confirmed"
    os.environ.pop("PLENUM_PAPERCLIP_MODEL",None)
    # The pinned container and readonly checkout are the trust boundary.
    sys.path.insert(0,"/plenum/src")
    runpy.run_path(str(Path(__file__).with_name("sequential_mission.py")),run_name="__main__")

if __name__=="__main__":main()

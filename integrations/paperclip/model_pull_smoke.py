"""Offline transport fixtures: no registry or inference calls."""
import os
from pathlib import Path
import subprocess
import tempfile

SCRIPT=Path(__file__).with_name("pull_original_qwen.sh")
DOCKER="""#!/bin/sh
set -eu
test "$*" = 'exec plenum-paperclip-qwen ollama pull qwen3.5:4b' || exit 99
n=$(cat "$CALLS")
n=$((n+1))
printf '%s' "$n" > "$CALLS"
case "$CASE" in
    success) exit 0 ;;
    recover) if [ "$n" -eq 3 ]; then exit 0; fi ;;
    exhausted) ;;
    denied) echo 'Error: pull model manifest: 401: unauthorized' >&2; exit 1 ;;
    other) echo 'Error: pull model manifest: 404: not found' >&2; exit 1 ;;
    timeout) echo 'Error: pull model manifest: 503: timeout' >&2; exit 124 ;;
    misleading) echo 'Other error: pull model manifest: 503: unrelated' >&2; exit 1 ;;
    *) exit 99 ;;
esac
echo 'Error: pull model manifest: 503: upstream connection timeout' >&2
exit 1
"""
with tempfile.TemporaryDirectory() as root:
    d=Path(root)
    for name,body in {"docker":DOCKER,"sleep":'#!/bin/sh\nprintf "%s\\n" "$1" >> "$SLEEPS"\n'}.items():
        path=d/name;path.write_text(body);path.chmod(0o700)
    for case,rc,count,delays in [
        ("success",0,1,[]),("recover",0,3,["5","10"]),
        ("exhausted",1,3,["5","10"]),("denied",1,1,[]),
        ("other",1,1,[]),("timeout",124,1,[]),("misleading",1,1,[])]:
        calls=d/"calls";calls.write_text("0")
        sleeps=d/"sleeps";sleeps.write_text("")
        env=dict(os.environ,PATH=str(d)+":"+os.environ["PATH"],CASE=case,CALLS=str(calls),SLEEPS=str(sleeps))
        result=subprocess.run(["bash",str(SCRIPT)],env=env,capture_output=True,text=True,timeout=10)
        assert (result.returncode,int(calls.read_text()),sleeps.read_text().splitlines())==(rc,count,delays),case
print("PASS: bounded HTTP 503 recovery, exhaustion, non-503 and timeout fail-closed; original model only")

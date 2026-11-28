"""Independent read-only grader feedback; never expose hidden tests to agent."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile
from verify_original_openhands_candidate import sandbox_command, completed_task_acceptance

def sha(raw): return hashlib.sha256(raw).hexdigest()

def bind(archive, source, task, digest):
    expected="f5ecd52815d14a7d63a9f58754fd592c4ee7fdbdd203e4b650666aa0f73fdda3"
    if archive.is_symlink() or not archive.is_file() or archive.stat().st_size!=10067 or sha(archive.read_bytes())!=expected:
        raise ValueError("Unbound previous candidate")
    prefix="miniswe-1060-native-json/"
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None or len(z.namelist())!=11 or len(set(z.namelist()))!=11 or sum(i.file_size for i in z.infolist())>200000:
            raise ValueError("Invalid evidence archive")
        native=json.loads(z.read(prefix+"native-result.json"))
        verdict=json.loads(z.read(prefix+"independent-verdict.json"))
        report=json.loads(z.read(prefix+"candidate-report.json"))
        actions=[json.loads(x) for x in z.read(prefix+"staged-actions.jsonl").splitlines()]
        calls=[json.loads(x) for x in z.read(prefix+"model-reservations.jsonl").splitlines()]
        replies=[json.loads(x) for x in z.read(prefix+"model-responses.jsonl").splitlines()]
        patch=z.read("openhands-review/issue-1060.patch")
    keys={"3f00fa7104a443a94f4a154c8e87467951c13fba3892593a2ea7d27f1ecb60b2","6f6f74299eae625fe101b5f5e7e82027f3da390d98a29f701b25c6494667a62b"}
    if (native.get("exit_status")!="Submitted" or native.get("model_digest")!=digest or native.get("paid_inference") is not False
        or verdict.get("status")!="BLOCKED_TASK_ACCEPTANCE" or verdict.get("existing_focused_tests_passed") is not True
        or verdict.get("task_acceptance_passed") is not False or verdict.get("network_disabled_for_candidate") is not True
        or report.get("source_file")!=source or report.get("task")!=task or report.get("source_sha256")!=sha(Path(source).read_bytes())
        or sha(patch)!="ebb34bb9d2db59ca5c83a3b980c6a0ff9ff0d53a4b3ecaa3256bd8c1f25e949c"
        or report.get("candidate_artifact_sha256")!=sha(patch) or verdict.get("candidate_artifact_sha256")!=sha(patch)
        or len(calls)!=2 or len(replies)!=2 or {x["request_sha256"] for x in calls}!=keys or {x["request_sha256"] for x in replies}!=keys
        or [a["action"] for a in actions]!=["replace","submit"]):
        raise ValueError("Prior failure does not bind")
    with tempfile.TemporaryDirectory(prefix="plenum-resume-") as folder:
        root=Path(folder)
        p=root/source
        p.parent.mkdir(parents=True)
        p.write_bytes(Path(source).read_bytes())
        diff=root/"prior.patch"
        diff.write_bytes(patch)
        subprocess.run(["git","apply","--check",str(diff)],cwd=root,check=True,timeout=10)
        subprocess.run(["git","apply",str(diff)],cwd=root,check=True,timeout=10)
        candidate=p.read_bytes()
    if sha(candidate)!=report["candidate_sha256"]:
        raise ValueError("Prior candidate changed")
    return candidate, keys, expected

class IndependentFeedback:
    def __init__(self, source, acceptance, receipt):
        self.source,self.acceptance,self.receipt=source,acceptance,Path(receipt)
        self.seen={}
        self.last_candidate_sha256=None
        self.last_was_cached=False
    def __call__(self, env):
        candidate=subprocess.run(["docker","exec",env.container_id,"bash","-c",
            f'test -f /work/{self.source} && test ! -L /work/{self.source} && head -c 12001 /work/{self.source}'],
            capture_output=True,check=True,timeout=15).stdout
        if not 0<len(candidate)<=12000: raise ValueError("Unbounded candidate")
        key=sha(candidate)
        self.last_candidate_sha256=key
        self.last_was_cached=key in self.seen
        if self.last_was_cached: return self.seen[key]
        if len(self.seen)>=6: raise RuntimeError("Independent grading budget exhausted")
        with tempfile.TemporaryDirectory(prefix="plenum-hidden-grade-") as folder:
            root=Path(folder); root.chmod(0o755)
            for name in ("src/plenum_ai/__init__.py","tests/acceptance/"+self.acceptance):
                p=root/name; p.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(name,p); p.chmod(0o644)
            p=root/self.source; p.write_bytes(candidate); p.chmod(0o644)
            result=subprocess.run(sandbox_command(root,"python:3.12-slim","/work/tests/acceptance",self.acceptance),capture_output=True,text=True,timeout=150)
            passed=completed_task_acceptance(result,self.acceptance)
        self.seen[key]=passed
        with self.receipt.open("a",encoding="utf-8") as f:
            f.write(json.dumps({"candidate_sha256":key,"acceptance_passed":passed,"network_disabled":True,"ordinal":len(self.seen)})+"\n")
        return passed

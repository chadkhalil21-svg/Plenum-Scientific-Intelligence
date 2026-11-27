"""Resume original rejected mission with a distinct scoped correction.
No first-attempt replay, no candidate execution on host, no production write.
Uses original model adapter, function-scoped editor and networkless verifier.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

from verify_original_openhands_candidate import verify, TASK_ACCEPTANCE, sandbox_command
from plenum_ai.openhands_coding_agent import execute_local

SOURCE = "src/plenum_ai/mission_checkpoint.py"
ORIGINAL_TASK = ("Make checkpoint persistence reject invalid result envelopes and nonfinite JSON before changing disk. "
                 "Ensure loading also rejects nonfinite JSON. Preserve valid atomic writes and resume behavior.")
CORRECTIVE_TASK = ("Repair function save_checkpoint. Reject invalid result envelopes and nonfinite JSON before changing disk. "
                   "Then repair function load_checkpoint. Reject nonfinite JSON while preserving all existing checks and valid resume.")
ARCHIVE_SHA = "caee163990f81659c62af9891ce3f4f82db2d8e643b6a4b187349f920396c9ab"
PATCH_SHA = "6f547b252d207410c865eaf33d7491de830df039ac21555e5164a656d50dcb22"
OUT = Path("reports/mission-1036-correction")

def digest(b):
    return hashlib.sha256(b).hexdigest()

def public_functions(raw):
    return {n.name: ast.dump(n.args) for n in ast.parse(raw.decode()).body if isinstance(n, ast.FunctionDef)}

def main():
    if os.getenv("GITHUB_ACTIONS") != "true" or os.getenv("PLENUM_EPHEMERAL_RUNNER") != "confirmed" or os.getenv("PLENUM_CORRECTION_RESERVED") != "true":
        raise PermissionError("Original corrective reservation required")
    p = Path(sys.argv[1])
    if p.is_symlink() or not p.is_file() or not 0 < p.stat().st_size <= 2000000 or digest(p.read_bytes()) != ARCHIVE_SHA:
        raise ValueError("Original evidence mismatch")
    with zipfile.ZipFile(p) as z:
        if len(z.namelist()) != len(set(z.namelist())) or sum(i.file_size for i in z.infolist()) > 4000000 or z.testzip() is not None:
            raise ValueError("Unsafe original evidence")
        first = json.loads(z.read("openhands-agent-review.json"))
        verdict = json.loads(z.read("openhands-sandbox-verdict.json"))
        patch = z.read("openhands-review/issue-1036.patch")
    original = Path(SOURCE).read_bytes()
    if (first.get("task") != ORIGINAL_TASK or first.get("source_file") != SOURCE or
        first.get("source_sha256") != digest(original) or first.get("candidate_artifact_sha256") != PATCH_SHA or
        first.get("model_run_completed") is not True or first.get("repair_passes") != 0 or digest(patch) != PATCH_SHA or
        verdict.get("candidate_artifact_sha256") != PATCH_SHA or verdict.get("status") != "BLOCKED_EXISTING_FOCUSED_TESTS" or
        verdict.get("network_disabled_for_candidate") is not True):
        raise ValueError("Unbound original failed result")
    # Inspect the rejected patch as inert syntax, not executable code.
    lines = patch.decode().splitlines()
    if lines[:2] != ["--- a/"+SOURCE, "+++ b/"+SOURCE] or sum(x.startswith("--- ") for x in lines)!=1 or sum(x.startswith("+++ ") for x in lines)!=1:
        raise ValueError("Patch scope mismatch")
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root/SOURCE).parent.mkdir(parents=True)
        (root/SOURCE).write_bytes(original)
        subprocess.run(["git","apply","--whitespace=error","-"],cwd=root,input=patch,check=True,timeout=15)
        rejected = (root/SOURCE).read_bytes()
        if digest(rejected) != first["candidate_sha256"]:
            raise ValueError("Rejected candidate mismatch")
    before, after = public_functions(original), public_functions(rejected)
    removed = sorted(set(before)-set(after))
    if not removed:
        raise ValueError("Expected independent structural diagnosis missing")
    OUT.mkdir(parents=True,exist_ok=False)
    receipt = {"original_run":45990708690,"original_archive_sha256":ARCHIVE_SHA,
               "rejected_patch_sha256":PATCH_SHA,"removed_original_functions":removed,
               "strategy":"original scoped function editor, distinct corrective request",
               "authorized_function_edits":2,"original_inference_replayed":False,"paid_inference":False}
    (OUT/"diagnosis.json").write_text(json.dumps(receipt,indent=2))
    # Use the existing trusted suite against the unmodified source first.
    # No failed model output or raw sandbox text is passed into the model.
    import shutil
    with tempfile.TemporaryDirectory() as d:
        root=Path(d)
        shutil.copytree("src/plenum_ai",root/"src/plenum_ai")
        shutil.copytree("tests",root/"tests")
        if Path("integrations").is_dir():shutil.copytree("integrations",root/"integrations")
        root.chmod(0o755)
        baseline=subprocess.run(sandbox_command(root,"python:3.12-slim","/work/tests","test_mission_checkpoint.py"),
            capture_output=True,timeout=150,check=False)
        if baseline.returncode:
            raise ValueError("Original source baseline failed")
    (OUT/"baseline.json").write_text(json.dumps({"original_focused_baseline_passed":True}))
    # Distinct model-directed solution, preserving every byte outside the two
    # original functions. Never reconstruct or copy the rejected patch.
    report=execute_local(CORRECTIVE_TASK,source_file=SOURCE,candidate_out="reports/openhands-review/issue-1036.patch")
    if report.get("candidate_artifact_sha256")==PATCH_SHA:
        raise ValueError("Repeated rejected patch")
    report["original_mission_correction"]=receipt
    report["repair_passes"]=1
    report_path=OUT/"corrective-report.json"
    report_path.write_text(json.dumps(report,indent=2))
    TASK_ACCEPTANCE[(SOURCE,CORRECTIVE_TASK)]="checkpoint_mission_1036.py"
    result=verify(report_path,OUT/"corrective-verdict.json")
    print(json.dumps({"original_mission":1036,"diagnosis":receipt,"verdict":result},sort_keys=True))
    return 0 if result.get("existing_focused_tests_passed") is True and result.get("task_acceptance_passed") is True else 2

if __name__=="__main__":
    sys.exit(main())

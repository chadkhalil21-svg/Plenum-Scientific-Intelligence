"""One-time independent readback of the original mission 1036 candidate.
Use the existing verifier and independently frozen test; never call the model.
The caller must fetch the artifact from original authenticated run 45990708690
and supply its provider-verified SHA256. No candidate code runs on this host.
"""
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

from verify_original_openhands_candidate import verify, TASK_ACCEPTANCE

SOURCE = "src/plenum_ai/mission_checkpoint.py"
TASK = ("Make checkpoint persistence reject invalid result envelopes and nonfinite JSON before changing disk. "
        "Ensure loading also rejects nonfinite JSON. Preserve valid atomic writes and resume behavior.")
PATCH = "reports/openhands-review/issue-1036.patch"
REPORT = "reports/openhands-agent-review.json"
VERDICT = Path("reports/checkpoint-mission-1036-verdict.json")

def main():
    archive, expected = Path(sys.argv[1]), sys.argv[2]
    if len(sys.argv) != 3 or not re.fullmatch("[a-f0-9]{64}", expected):
        raise ValueError("Authenticated original archive digest required")
    if archive.is_symlink() or not archive.is_file() or not 0 < archive.stat().st_size <= 2_000_000:
        raise ValueError("Invalid archive")
    if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
        raise ValueError("Archive digest mismatch")
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or sum(x.file_size for x in z.infolist()) > 4_000_000 or z.testzip() is not None:
            raise ValueError("Unsafe archive")
        # Artifact uploader uses reports as the common root.
        raw_report = z.read(REPORT.removeprefix("reports/"))
        raw_patch = z.read(PATCH.removeprefix("reports/"))
        if not 0 < len(raw_report) <= 64_000 or not 0 < len(raw_patch) <= 80_000:
            raise ValueError("Unbounded evidence")
    row = json.loads(raw_report)
    if (row.get("task") != TASK or row.get("source_file") != SOURCE or
        row.get("candidate_artifact") != PATCH or row.get("engine") != "aider_local_ollama" or
        row.get("status") != "PROPOSAL_AWAITING_REVIEW" or row.get("model_run_completed") is not True or
        row.get("source_sha256") != hashlib.sha256(Path(SOURCE).read_bytes()).hexdigest() or
        row.get("candidate_artifact_sha256") != hashlib.sha256(raw_patch).hexdigest()):
        raise ValueError("Original candidate binding failed")
    for name, data in ((REPORT, raw_report), (PATCH, raw_patch)):
        target = Path(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(data)
    TASK_ACCEPTANCE[(SOURCE, TASK)] = "checkpoint_mission_1036.py"
    result = verify(Path(REPORT), VERDICT)
    print(json.dumps({"original_run":45990708690, "archive_sha256":expected,
                      "new_model_calls":0, "result":result}, sort_keys=True))
    return 0 if result.get("existing_focused_tests_passed") is True and result.get("task_acceptance_passed") is True else 2

if __name__ == "__main__":
    sys.exit(main())

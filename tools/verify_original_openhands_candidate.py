"""Independent, NO-NETWORK regression gate for an ORIGINAL OpenHands review-only patch.

This does not auto-merge, make a source change in the checkout, or count
passing existing tests as independent semantic approval. A model-generated
Python module is executed ONLY inside a secret-free, networkless, read-only
disposable Docker container; never in the host Actions process.
Reuse standard-library unittest and the already-present GitHub runner Docker.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

SOURCE = re.compile(r"src/plenum_ai/[a-z][a-z0-9_]{1,64}\.py\Z")
PATCH = re.compile(r"reports/openhands-review/issue-[1-9][0-9]{0,8}\.patch\Z")
SCHEMA = "plenum-original-openhands-candidate-regression-v1"


def verify(report_path: Path, verdict_path: Path, *, checkout: Path | None = None) -> dict:
    """Fail closed unless the original candidate passes EXISTING focused tests."""
    root = (checkout or Path.cwd()).resolve()
    verdict = {
        "schema": SCHEMA,
        "status": "BLOCKED_UNVERIFIED_CANDIDATE",
        "existing_focused_tests_passed": False,
        "independent_semantic_approval": False,
        "production_written": False,
        "external_accounts_changed": False,
        "network_disabled_for_candidate": True,
        "automatically_merged": False,
    }

    def persist(status: str, reason: str) -> dict:
        verdict.update(status=status, reason=reason)
        verdict_path.parent.mkdir(parents=True, exist_ok=True)
        with verdict_path.open("x", encoding="utf-8") as fh:
            json.dump(verdict, fh, indent=2, sort_keys=True)
            fh.write("\n")
        return verdict

    try:
        report = json.loads(report_path.read_text("utf-8"))
        source = report.get("source_file")
        candidate = report.get("candidate_artifact")
        if (report.get("status") != "PROPOSAL_AWAITING_REVIEW"
                or report.get("model_run_completed") is not True
                or report.get("candidate_persisted") is not True
                or report.get("candidate_syntax_valid") is not True
                or report.get("production_written") is not False
                or report.get("external_accounts_changed") is not False
                or not isinstance(source, str) or not SOURCE.fullmatch(source)
                or not isinstance(candidate, str) or not PATCH.fullmatch(candidate)):
            return persist("BLOCKED_UNVERIFIED_CANDIDATE", "original_model_report_not_accepted")
        source_path = root / source
        patch_path = root / candidate
        tests = root / "tests" / ("test_" + Path(source).stem + ".py")
        if (not source_path.is_file() or source_path.is_symlink()
                or not patch_path.is_file() or patch_path.is_symlink()):
            return persist("BLOCKED_UNVERIFIED_CANDIDATE", "original_source_or_patch_not_regular")
        original = source_path.read_bytes()
        patch_bytes = patch_path.read_bytes()
        if (not 0 < len(patch_bytes) <= 80_000
                or hashlib.sha256(original).hexdigest() != report.get("source_sha256")
                or hashlib.sha256(patch_bytes).hexdigest() != report.get("candidate_artifact_sha256")):
            return persist("BLOCKED_UNVERIFIED_CANDIDATE", "original_sha_or_patch_digest_mismatch")
        # The actual original adapter emits ONE unified source diff. Do not
        # accept rename, multiple files, absolute paths or a metadata patch.
        diff = patch_bytes.decode("utf-8")
        lines = diff.splitlines()
        if (len(lines) > 1500 or len(lines) < 3
                or lines[0] != "--- a/" + source
                or lines[1] != "+++ b/" + source
                or sum(x.startswith("--- ") for x in lines) != 1
                or sum(x.startswith("+++ ") for x in lines) != 1
                or not any(x.startswith("@@ ") for x in lines)
                or any(x.startswith(("diff --git", "rename from", "rename to", "Binary files"))
                       for x in lines)):
            return persist("BLOCKED_UNVERIFIED_CANDIDATE", "untrusted_patch_scope_or_format")
        if not tests.is_file() or tests.is_symlink():
            return persist("BLOCKED_NO_EXISTING_FOCUSED_TEST", "no_preexisting_source_test_to_reuse")
        verdict.update(source_file=source, test_file=tests.relative_to(root).as_posix(),
                       candidate_artifact_sha256=hashlib.sha256(patch_bytes).hexdigest())
        with tempfile.TemporaryDirectory(prefix="plenum-review-only-") as folder:
            isolated = Path(folder)
            shutil.copytree(root / "src" / "plenum_ai", isolated / "src" / "plenum_ai")
            shutil.copytree(root / "tests", isolated / "tests")
            if (root / "integrations").is_dir():
                shutil.copytree(root / "integrations", isolated / "integrations")
            os.chmod(isolated, 0o755)
            # git apply CHECK and apply operate on an isolated COPY, not main.
            # No generated Python is imported or executed on the host runner.
            for args in (["git", "apply", "--check", "--whitespace=error", str(patch_path)],
                         ["git", "apply", "--whitespace=error", str(patch_path)]):
                applied = subprocess.run(args, cwd=isolated, capture_output=True,
                                         text=True, timeout=15, check=False)
                if applied.returncode:
                    return persist("BLOCKED_PATCH_DOES_NOT_APPLY", "git_apply_rejected_candidate")
            source_copy = isolated / source
            if not source_copy.is_file() or source_copy.is_symlink():
                return persist("BLOCKED_PATCH_DOES_NOT_APPLY", "candidate_path_changed")
            actual = source_copy.read_bytes()
            if hashlib.sha256(actual).hexdigest() != report.get("candidate_sha256"):
                return persist("BLOCKED_PATCH_DOES_NOT_APPLY", "candidate_digest_mismatch")
            # No GitHub tokens, OIDC credentials, live network, code-write mount,
            # privilege escalation, persistent home or host project filesystem.
            command = [
                "docker", "run", "--rm", "--pull=missing", "--network=none",
                "--cap-drop=ALL", "--security-opt=no-new-privileges",
                "--pids-limit=64", "--memory=768m", "--cpus=1",
                "--read-only", "--user=65534:65534",
                "--tmpfs=/tmp:rw,nosuid,nodev,size=64m,mode=1777",
                "--mount", f"type=bind,src={isolated},dst=/work,readonly",
                "-e", "PYTHONPATH=/work/src", "-e", "PYTHONDONTWRITEBYTECODE=1",
                "-w", "/work", "python:3.12-slim",
                "python", "-B", "-m", "unittest", "discover",
                "-s", "/work/tests", "-p", tests.name, "-v",
            ]
            try:
                result = subprocess.run(command, capture_output=True, text=True,
                                        timeout=150, check=False, env={
                                            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                                            "HOME": "/tmp",
                                        })
            except subprocess.TimeoutExpired:
                return persist("BLOCKED_SANDBOX_TIMEOUT", "existing_tests_timed_out_without_network")
            except OSError:
                return persist("BLOCKED_SANDBOX_UNAVAILABLE", "no_disposable_networkless_container")
            if result.returncode:
                return persist("BLOCKED_EXISTING_FOCUSED_TESTS", "existing_source_regressions_failed")
            verdict["existing_focused_tests_passed"] = True
            return persist("FOCUSED_TESTS_PASS_REVIEW_STILL_REQUIRED",
                           "original_focused_contracts_only_not_semantic_approval")
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return persist("BLOCKED_UNVERIFIED_CANDIDATE", "untrusted_or_unreadable_candidate")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--verdict", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.report, args.verdict)
    print("Original networkless focused source gate:", result["status"])
    return 0 if result["existing_focused_tests_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

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
INTERRUPTED = "BLOCKED_INTERRUPTED_WITH_REVIEW_ARTIFACT"

# Exact founder task and source binding. The model may modify only its proposal,
# not this trusted test or the selection criteria.
# Preserve the original, already existing regression suite when its historical
# filename differs from the module name. No candidate can select its own tests.
FOCUSED_TESTS = {
    "src/plenum_ai/business_public_watch.py": "test_public_business_watch.py",
}

# NOAA's real numerical dependency is installed in a separate, source-free
# trusted build. The candidate container stays networkless and read-only.
NOAA_SOURCE = "src/plenum_ai/noaa_revision_agent.py"
NOAA_IMAGE = "plenum-noaa-review:np-2.2.6-cp312"
NOAA_NUMPY_SHA = "fd83c01228a688733f1ded5201c678f0c53ecc1006ffbc404db9f7a899ac6249"

def prepare_sandbox_image(source):
    if source != NOAA_SOURCE:
        return "python:3.12-slim"
    # Official PyPI CPython 3.12 Linux x86_64 wheel; no source build,
    # transitive resolution, credentials, checkout or candidate in build context.
    dockerfile = (
        "FROM python:3.12-slim\n"
        "RUN printf '%s\\n' 'numpy==2.2.6 --hash=sha256:" + NOAA_NUMPY_SHA +
        "' > /tmp/plenum-locked.txt && python -m pip --isolated install "
        "--index-url https://pypi.org/simple --no-deps --only-binary=:all: "
        "--require-hashes --no-cache-dir -r /tmp/plenum-locked.txt && "
        "rm /tmp/plenum-locked.txt\n"
    )
    with tempfile.TemporaryDirectory(prefix="plenum-trusted-image-") as empty:
        result = subprocess.run(
            ["docker", "build", "--platform=linux/amd64", "-t", NOAA_IMAGE, "-"],
            input=dockerfile, cwd=empty, text=True, capture_output=True,
            timeout=180, check=False,
            env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": empty})
    if result.returncode:
        raise RuntimeError("Trusted numerical dependency preparation failed")
    return NOAA_IMAGE


def sandbox_command(isolated, image, tests_dir, pattern):
    return [
        "docker", "run", "--rm", "--pull=missing", "--network=none",
        "--cap-drop=ALL", "--security-opt=no-new-privileges",
        "--pids-limit=64", "--memory=768m", "--cpus=1",
        "--read-only", "--user=65534:65534",
        "--tmpfs=/tmp:rw,nosuid,nodev,size=64m,mode=1777",
        "--mount", f"type=bind,src={isolated},dst=/work,readonly",
        "-e", "PYTHONPATH=/work/src", "-e", "PYTHONDONTWRITEBYTECODE=1",
        "-e", "OPENBLAS_NUM_THREADS=1", "-w", "/work", image,
        "python", "-B", "-m", "unittest", "discover",
        "-s", tests_dir, "-p", pattern, "-v",
    ]


from plenum_ai.openhands_coding_agent import TASK_ACCEPTANCE



def _bound_interrupted_origin(report: dict, root: Path) -> bool:
    """Only the original reserved issue job may examine its saved interrupted edit."""
    from plenum_ai.openhands_coding_agent import parse_owner_repair_event

    run = os.getenv("GITHUB_RUN_ID", "")
    attempt = os.getenv("GITHUB_RUN_ATTEMPT", "")
    if (os.getenv("PLENUM_REVIEW_INTERRUPTED") != "confirmed"
            or os.getenv("GITHUB_ACTIONS") != "true"
            or os.getenv("GITHUB_EVENT_NAME") != "issues"
            or os.getenv("GITHUB_REPOSITORY") != "chadkhalil21-svg/Plenum-Scientific-Intelligence"
            or not re.fullmatch(r"[1-9][0-9]{0,12}", run)
            or attempt not in ("1", "2")
            or root != Path.cwd().resolve()):
        return False
    event_path = Path(os.environ["GITHUB_EVENT_PATH"])
    if (not event_path.is_file() or event_path.is_symlink()
            or not 0 < event_path.stat().st_size <= 1_000_000):
        return False
    event = json.loads(event_path.read_text("utf-8"))
    if not isinstance(event, dict) or (event.get("sender") or {}).get("login") != "chadkhalil21-svg":
        return False
    owner = parse_owner_repair_event(event)
    issue = owner["issue_number"]
    return (not owner.get("engine")
            and report.get("schema") == "plenum-openhands-coding-agent-v1"
            and report.get("upstream") == "OpenHands/software-agent-sdk"
            and report.get("task") == owner["task"]
            and report.get("source_file") == owner["source_file"]
            and report.get("source_sha256") == owner["source_sha256"]
            and report.get("failure_category") in ("ORIGINAL_ENGINE_TRANSPORT", "LOCAL_DURABLE_OBJECT_DAILY_BUDGET")
            and type(report.get("origin_issue_number")) is int
            and report["origin_issue_number"] == issue
            and report.get("origin_run_id") == run and report.get("origin_run_attempt") == attempt
            and report.get("candidate_artifact") == f"reports/openhands-review/issue-{issue}.patch"
            and report.get("model_run_completed") is False
            and report.get("generated_code_executed") is False
            and report.get("verified_independent_quality") is False
            and report.get("human_review_required") is True
            and report.get("retry_same_day_authorized") is False
            and report.get("no_paid_fallback") is True)


def completed_unittest(result, *, failed):
    """Classify only bounded completed unittest outcomes, not runtime failures.

    Candidate text is never trusted as semantic approval or prompt content.
    A negative report can at most request the already authorized correction.
    """
    if result.returncode != (1 if failed else 0) or not isinstance(result.stderr, str):
        return False
    tail = result.stderr[-4096:]
    summary = re.search(r"(?m)^Ran ([1-9][0-9]*) tests? in [0-9.]+s$", tail)
    if not summary:
        return False
    if failed:
        return bool(re.search(r"(?m)^FAILED \((?:failures|errors)=[1-9][0-9]*(?:, (?:failures|errors|skipped|expected failures|unexpected successes)=[0-9]+)*\)\s*\Z", tail))
    return bool(re.search(r"(?m)^OK(?: \(skipped=[0-9]+\))?\s*\Z", tail))


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
        interrupted_only = os.getenv("PLENUM_REVIEW_INTERRUPTED") == "confirmed"
        if interrupted_only and (report_path.is_symlink() or not report_path.is_file()
                or report_path.parent.is_symlink()
                or report_path.resolve() != root / "reports/openhands-agent-review.json"
                or not 0 < report_path.stat().st_size <= 64_000):
            return persist("BLOCKED_UNVERIFIED_CANDIDATE", "interrupted_report_not_original_regular_file")
        report = json.loads(report_path.read_text("utf-8"))
        if not isinstance(report, dict):
            return persist("BLOCKED_UNVERIFIED_CANDIDATE", "original_model_report_not_object")
        source = report.get("source_file")
        candidate = report.get("candidate_artifact")
        interrupted = report.get("status") == INTERRUPTED
        authorized = (_bound_interrupted_origin(report, root) if interrupted and interrupted_only
                      else (not interrupted_only and report.get("status") == "PROPOSAL_AWAITING_REVIEW"
                            and report.get("model_run_completed") is True))
        if (not authorized
                or report.get("candidate_persisted") is not True
                or report.get("candidate_syntax_valid") is not True
                or report.get("production_written") is not False
                or report.get("external_accounts_changed") is not False
                or not isinstance(source, str) or not SOURCE.fullmatch(source)
                or not isinstance(candidate, str) or not PATCH.fullmatch(candidate)):
            return persist("BLOCKED_UNVERIFIED_CANDIDATE", "original_model_report_not_accepted")
        source_path = root / source
        patch_path = root / candidate
        tests = root / "tests" / FOCUSED_TESTS.get(source, "test_" + Path(source).stem + ".py")
        if (not source_path.is_file() or source_path.is_symlink()
                or not patch_path.is_file() or patch_path.is_symlink()
                or (interrupted and (source_path.parent.is_symlink() or patch_path.parent.is_symlink()
                    or patch_path.resolve() != patch_path or source_path.resolve() != source_path))):
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
        if interrupted:
            verdict.update(model_run_completed=False,
                           source_sha256=report["source_sha256"],
                           origin_issue_number=report["origin_issue_number"],
                           origin_run_id=report["origin_run_id"],
                           origin_run_attempt=report["origin_run_attempt"])
        try:
            image = prepare_sandbox_image(source)
        except (OSError, RuntimeError, subprocess.TimeoutExpired):
            return persist("BLOCKED_SANDBOX_UNAVAILABLE", "trusted_dependency_preparation_failed")
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
            command = sandbox_command(isolated, image, "/work/tests", tests.name)
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
                from plenum_ai.openhands_coding_agent import STRUCTURED_RECOVERY_TASKS
                acceptance = STRUCTURED_RECOVERY_TASKS.get((source, report.get("task")))
                if (not interrupted and acceptance and completed_unittest(result, failed=True)
                        and (isolated / "tests" / "acceptance" / acceptance).is_file()
                        and not (isolated / "tests" / "acceptance" / acceptance).is_symlink()):
                    # Establish that the unchanged source passes the very same
                    # trusted suite. No candidate bytes remain in this copy.
                    source_copy.write_bytes(original)
                    try:
                        baseline = subprocess.run(command, capture_output=True, text=True,
                            timeout=150, check=False, env={
                                "PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": "/tmp"})
                    except (OSError, subprocess.TimeoutExpired):
                        baseline = None
                    if baseline is not None and completed_unittest(baseline, failed=False):
                        verdict.update(regression_recovery_eligible=True,
                            original_focused_baseline_passed=True,
                            task_acceptance_test="tests/acceptance/" + acceptance,
                            task_acceptance_passed=False)
                return persist("BLOCKED_EXISTING_FOCUSED_TESTS", "existing_source_regressions_failed")
            verdict["existing_focused_tests_passed"] = True
            acceptance = TASK_ACCEPTANCE.get((source, report.get("task")))
            if acceptance:
                verdict["task_acceptance_passed"] = False
                test_path = isolated / "tests" / "acceptance" / acceptance
                if not test_path.is_file() or test_path.is_symlink():
                    return persist("BLOCKED_TASK_ACCEPTANCE_MISSING", "trusted_task_test_missing")
                task_command = sandbox_command(isolated, image, "/work/tests/acceptance", acceptance)
                verdict["task_acceptance_test"] = "tests/acceptance/" + acceptance
                try:
                    accepted = subprocess.run(task_command, capture_output=True, text=True,
                                              timeout=150, check=False, env={
                                                  "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                                                  "HOME": "/tmp",
                                              })
                except (OSError, subprocess.TimeoutExpired):
                    return persist("BLOCKED_TASK_ACCEPTANCE_UNAVAILABLE", "trusted_task_test_did_not_finish")
                if accepted.returncode or "Ran 2 tests" not in accepted.stderr:
                    return persist("BLOCKED_TASK_ACCEPTANCE", "trusted_task_behavior_not_verified")
                verdict["task_acceptance_passed"] = True
            return persist(("INTERRUPTED_FOCUSED_TESTS_PASS_REVIEW_STILL_REQUIRED" if interrupted
                            else "FOCUSED_TESTS_PASS_REVIEW_STILL_REQUIRED"),
                           "original_focused_contracts_only_not_semantic_approval")
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, AttributeError, json.JSONDecodeError):
        return persist("BLOCKED_UNVERIFIED_CANDIDATE", "untrusted_or_unreadable_candidate")


def recover_local_behavior(report_path: Path, verdict_path: Path, event_path: Path) -> dict:
    """One native correction from a trusted failed acceptance, never a replay.

    Original issue/source/patch/verdict must bind. Preserve all initial evidence
    before inference. Only fixed, pre-reviewed feedback is used; no model or
    sandbox text enters the prompt. The second candidate is review-only too.
    """
    from plenum_ai.openhands_coding_agent import (
        LOCAL_ENGINE, parse_owner_repair_event, execute_local, local_plan,
        STRUCTURED_RECOVERY_TASKS, StructuredEditFailure,
    )
    first = json.loads(report_path.read_text("utf-8"))
    verdict = json.loads(verdict_path.read_text("utf-8"))
    task_failure = (verdict.get("status") == "BLOCKED_TASK_ACCEPTANCE"
                    and verdict.get("existing_focused_tests_passed") is True)
    regression_failure = (verdict.get("status") == "BLOCKED_EXISTING_FOCUSED_TESTS"
                          and verdict.get("existing_focused_tests_passed") is False
                          and verdict.get("regression_recovery_eligible") is True
                          and verdict.get("original_focused_baseline_passed") is True)
    if (not (task_failure or regression_failure)
            or verdict.get("task_acceptance_passed") is not False
            or verdict.get("network_disabled_for_candidate") is not True):
        return verdict
    if (os.getenv("GITHUB_ACTIONS") != "true"
            or os.getenv("GITHUB_EVENT_NAME") != "issues"
            or os.getenv("GITHUB_REPOSITORY") != "chadkhalil21-svg/Plenum-Scientific-Intelligence"
            or os.getenv("GITHUB_RUN_ATTEMPT") != "1"
            or os.getenv("PLENUM_ORIGINAL_CODING_RESERVED") != "true"
            or os.getenv("PLENUM_EPHEMERAL_RUNNER") != "confirmed"
            or not re.fullmatch(r"[1-9][0-9]{0,12}", os.getenv("GITHUB_RUN_ID", ""))
            or event_path != Path(os.environ["GITHUB_EVENT_PATH"])
            or event_path.is_symlink() or not event_path.is_file()
            or not 0 < event_path.stat().st_size <= 1_000_000):
        return verdict
    owner = parse_owner_repair_event(json.loads(event_path.read_text("utf-8")))
    source, task = owner["source_file"], owner["task"]
    test = TASK_ACCEPTANCE.get((source, task))
    patch = Path("reports/openhands-review") / f"issue-{owner['issue_number']}.patch"
    if (owner.get("engine") != LOCAL_ENGINE or first.get("engine") != LOCAL_ENGINE
            or first.get("repair_passes") != 0 or test is None
            or (test != "health_body_limit.py" and STRUCTURED_RECOVERY_TASKS.get((source, task)) != test)
            or (regression_failure and (STRUCTURED_RECOVERY_TASKS.get((source, task)) != test
                or verdict.get("test_file") != "tests/" + FOCUSED_TESTS.get(source, "test_" + Path(source).stem + ".py")))
            or first.get("source_file") != source or first.get("task") != task
            or first.get("source_sha256") != owner["source_sha256"]
            or first.get("status") != "PROPOSAL_AWAITING_REVIEW"
            or first.get("candidate_artifact") != patch.as_posix()
            or verdict.get("source_file") != source
            or verdict.get("task_acceptance_test") != "tests/acceptance/" + test
            or report_path != Path("reports/openhands-agent-review.json")
            or verdict_path != Path("reports/openhands-sandbox-verdict.json")
            or any(p.is_symlink() or not p.is_file() or not 0 < p.stat().st_size <= 80_000
                   for p in (report_path, verdict_path, patch))
            or patch.parent.is_symlink()):
        return verdict
    digest = hashlib.sha256(patch.read_bytes()).hexdigest()
    if digest != first.get("candidate_artifact_sha256") or digest != verdict.get("candidate_artifact_sha256"):
        return verdict
    archive = patch.parent / "first-attempt"
    if archive.exists() or archive.is_symlink():
        return verdict
    archive.mkdir()
    # A reservation is written before another model call. A repeat invocation
    # can never consume another budget or overwrite the first evidence.
    reservation = {"schema": "plenum-local-behavior-recovery-v1",
                   "issue": owner["issue_number"], "run": os.environ["GITHUB_RUN_ID"],
                   "original_patch_sha256": digest, "source_sha256": owner["source_sha256"],
                   "trusted_test": test, "max_corrective_attempts": 1,
                   "diagnosis": "existing_regression" if regression_failure else "task_acceptance"}
    (archive / "reservation.json").write_text(json.dumps(reservation, indent=2) + "\n")
    for p in (report_path, verdict_path, patch):
        p.rename(archive / p.name)
    try:
        second = execute_local(task, source_file=source, candidate_out=patch.as_posix(),
                               behavioral_recovery=True, regression_recovery=regression_failure)
    except Exception as exc:
        second = {**local_plan(task, source_file=source),
                  "status": "BLOCKED_LOCAL_CODER_NO_REVIEWABLE_PATCH",
                  "failure_category": type(exc).__name__, "repair_passes": 1}
        if isinstance(exc, StructuredEditFailure):
            second["structured_failure_stage"] = exc.stage
            second["structured_failure_clause"] = exc.clause
    second["behavioral_recovery"] = reservation
    report_path.write_text(json.dumps(second, indent=2) + "\n", encoding="utf-8")
    return verify(report_path, verdict_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--verdict", type=Path, required=True)
    parser.add_argument("--recover-local-event", type=Path)
    args = parser.parse_args()
    result = verify(args.report, args.verdict)
    if args.recover_local_event and result["status"] in ("BLOCKED_TASK_ACCEPTANCE", "BLOCKED_EXISTING_FOCUSED_TESTS"):
        result = recover_local_behavior(args.report, args.verdict, args.recover_local_event)
    print("Original networkless focused source gate:", result["status"])
    return 0 if result["existing_focused_tests_passed"] and result.get("task_acceptance_passed") is not False and not result["status"].startswith("BLOCKED") else 2


if __name__ == "__main__":
    raise SystemExit(main())

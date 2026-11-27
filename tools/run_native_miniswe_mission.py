"""Native upstream mini-SWE-agent execution for original engineering mission 1040.

Only a public scratch copy, with no host mount or credentials. Upstream owns the
plan/action/observation/revision loop. Existing Plenum reviewer grades the result.
"""
import argparse
import ast
import difflib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import time

from minisweagent import __version__
from minisweagent.agents.default import DefaultAgent
from minisweagent.environments.docker import DockerEnvironment
from minisweagent.models.litellm_model import LitellmModel
from minisweagent.models.utils.actions_toolcall import BASH_TOOL
from openai import OpenAI
import httpx
from verify_original_openhands_candidate import verify, TASK_ACCEPTANCE, FOCUSED_TESTS
from plenum_ai.openhands_coding_agent import parse_owner_repair_event, MINISWE_ENGINE

SOURCE = "src/plenum_ai/mission_checkpoint.py"
TASK = ("Prevent checkpoint persistence and worker artifact verification from accepting a symlinked mission root "
        "or symlinked ancestor of that root. Preserve valid ordinary directories, creation of previously absent "
        "nested roots, existing checkpoint validation and valid resume.")
MODEL = "qwen3.5:9b-q4_K_M"
DIGEST = "56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90"
ISSUE = 1040
OUT = Path("reports/miniswe-1040")
PATCH = Path("reports/openhands-review/issue-1040.patch")
ACCEPTANCE = "mission_root_alias.py"
TEST = "test_mission_checkpoint.py"

def configure_event(event_path):
    """Reuse the original owner scope and reviewed public test closure."""
    global SOURCE, TASK, ISSUE, OUT, PATCH, ACCEPTANCE, TEST
    if (os.getenv("GITHUB_EVENT_NAME") != "issues"
            or Path(os.environ["GITHUB_EVENT_PATH"]) != event_path
            or event_path.is_symlink() or not 0 < event_path.stat().st_size <= 1_000_000):
        raise PermissionError("Original issue event required")
    event = json.loads(event_path.read_text("utf-8"))
    if (event.get("sender") or {}).get("login") != "chadkhalil21-svg":
        raise PermissionError("Original founder required")
    contract = parse_owner_repair_event(event)
    if contract.get("engine") != MINISWE_ENGINE:
        raise PermissionError("Exact native mini-SWE engine required")
    SOURCE, TASK, ISSUE = contract["source_file"], contract["task"], contract["issue_number"]
    TEST = FOCUSED_TESTS.get(SOURCE, "test_" + Path(SOURCE).stem + ".py")
    if not (Path("tests") / TEST).is_file():
        raise PermissionError("No existing focused public test suite")
    ACCEPTANCE = TASK_ACCEPTANCE.get((SOURCE, TASK))
    OUT = Path(f"reports/miniswe-{ISSUE}")
    PATCH = Path(f"reports/openhands-review/issue-{ISSUE}.patch")
    return contract

def sha(data):
    return hashlib.sha256(data).hexdigest()

class LocalOnlyModel(LitellmModel):
    """Reuse upstream toolcall parsing, feedback and serialization, no cloud fallback."""
    def __init__(self):
        super().__init__(model_name="openai/" + MODEL, cost_tracking="ignore_errors",
                         observation_template="Return code: {{output.returncode}}\n{{output.output[:6000]}}")
        self.client = OpenAI(base_url="http://127.0.0.1:11434/v1", api_key="local-only",
                             max_retries=0, timeout=115,
                             http_client=httpx.Client(trust_env=False, timeout=115))
        self.requests = set()

    def _query(self, messages, **kwargs):
        body = json.dumps(messages, sort_keys=True, separators=(",", ":")).encode()
        key = sha(body)
        if key in self.requests or len(self.requests) >= 12 or len(body) > 100_000:
            raise RuntimeError("Duplicate or unbounded native request")
        self.requests.add(key)
        with (OUT / "model-reservations.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"request_sha256": key, "ordinal": len(self.requests)}) + "\n")
        response = self.client.chat.completions.create(model=MODEL, messages=messages,
                   tools=[BASH_TOOL], temperature=0, max_tokens=1200,
                   extra_body={"think": False})
        with (OUT / "model-responses.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"request_sha256": key, "response_sha256": sha(response.model_dump_json().encode()),
                                "returned_model":response.model, "usage":response.usage.model_dump() if response.usage else None}) + "\n")
        return response

    def _calculate_cost(self, response):
        return {"cost":0.0}

def original_workspace():
    focused = Path("tests") / TEST
    files = [Path(SOURCE), Path("src/plenum_ai/__init__.py"), focused]
    # Copy only existing directly imported public acceptance modules.
    # Never copy a hidden objective-specific test, credentials, whole checkout,
    # git metadata or other workers' artifacts. Unsupported imports fail at
    # the unmodified baseline before inference rather than expanding scope.
    for node in ast.walk(ast.parse(focused.read_text("utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("acceptance."):
            name = node.module.removeprefix("acceptance.")
            if not name.isidentifier():
                raise PermissionError("Unexpected focused test dependency")
            p = Path("tests/acceptance") / (name + ".py")
            if p.name != ACCEPTANCE and p not in files:
                files.append(p)
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer,mode="w") as archive:
        for p in files:
            if not p.is_file() or p.is_symlink() or not 0 < p.stat().st_size < 100_000:
                raise ValueError("Original public source invalid")
            raw = p.read_bytes()
            entry = tarfile.TarInfo(p.as_posix())
            entry.size = len(raw)
            entry.mode = 0o644
            archive.addfile(entry, io.BytesIO(raw))
    return buffer.getvalue()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", type=Path)
    args = parser.parse_args()
    if (__version__ != "2.4.6" or os.getenv("PLENUM_MINISWE_RESERVED") != "true"
            or os.getenv("GITHUB_ACTIONS") != "true" or os.getenv("GITHUB_REPOSITORY") != "chadkhalil21-svg/Plenum-Scientific-Intelligence"):
        raise PermissionError("Original reserved public CI only")
    if args.event:
        configure_event(args.event)
    tags = httpx.get("http://127.0.0.1:11434/api/tags",trust_env=False,timeout=10).json()
    if not any(x.get("name")==MODEL and x.get("digest")==DIGEST for x in tags["models"]):
        raise ValueError("Local model digest mismatch")
    OUT.mkdir(parents=True,exist_ok=False)
    original = Path(SOURCE).read_bytes()
    env = DockerEnvironment(image="python:3.12-slim", cwd="/work", timeout=30,
        run_args=["--rm","--pull=never","--network=none","--cap-drop=ALL",
                  "--security-opt=no-new-privileges","--read-only","--user=65534:65534",
                  "--pids-limit=64","--memory=768m","--cpus=1",f"--label=plenum-miniswe-{ISSUE}",
                  "--tmpfs=/work:rw,nosuid,nodev,noexec,size=64m,mode=1777",
                  "--tmpfs=/tmp:rw,nosuid,nodev,noexec,size=32m,mode=1777"],
        env={"PYTHONPATH":"/work/src:/work/tests","PYTHONDONTWRITEBYTECODE":"1","HOME":"/tmp"},
        interpreter=["bash","-c",'set -o pipefail; bash -c "$1" 2>&1 | head -c 12000',"--"],
        container_timeout="25m")
    model = LocalOnlyModel()
    try:
        subprocess.run(["docker","exec","-i",env.container_id,"tar","-xf","-","-C","/work"],
                       input=original_workspace(),check=True,timeout=20)
        baseline = env.execute({"command":"python -B -m unittest discover -s tests -p " + TEST})
        if baseline["returncode"] != 0:
            raise RuntimeError("Unmodified public regression baseline failed")
        agent = DefaultAgent(model,env,step_limit=12,cost_limit=0,wall_time_limit_seconds=1050,
            max_consecutive_format_errors=2,
            system_template="You are the original Plenum engineering specialist. Solve the authorized public code issue in the isolated workspace. Use bash tools for actual inspection, edits and tests. No external services. Preserve existing interfaces. Each reply must call bash. Work from observed test output, diagnose failures and revise your solution.",
            instance_template="Objective: {{task}}\nThe editable module is " + SOURCE + ". Existing tests: python -B -m unittest discover -s tests -p " + TEST + ". Inspect relevant code, independently reproduce the problem with your own tests, implement a minimal fix, run tests and correct failures. Do not modify existing tests. When satisfied, execute exactly: echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT",
            output_path=OUT/"trajectory.json")
        started = time.monotonic()
        result = agent.run(TASK)
        summary = {"issue":ISSUE,"upstream":"SWE-agent/mini-swe-agent","version":__version__,
            "model":MODEL,"model_digest":DIGEST,"native_agent_calls":agent.n_calls,
            "reserved_model_calls":len(model.requests),"exit_status":result.get("exit_status"),
            "elapsed_seconds":time.monotonic()-started,"paid_inference":False,
            "original_source_sha256":sha(original),"baseline_passed":True,
            "production_written":False,"host_execution_of_candidate":False}
        (OUT/"native-result.json").write_text(json.dumps(summary,indent=2))
        if result.get("exit_status")!="Submitted" or not model.requests:
            raise RuntimeError("Native agent did not submit completed solution")
        # Read only one fixed candidate path, with a strict byte ceiling; no
        # archive extraction or execution of candidate-controlled data on host.
        candidate = subprocess.run(["docker","exec",env.container_id,"bash","-c",
             f'test -f /work/{SOURCE} && test ! -L /work/{SOURCE} && head -c 40001 /work/{SOURCE}'],
             capture_output=True,check=True,timeout=15).stdout
        if not 0<len(candidate)<=40000 or candidate==original:
            raise ValueError("No bounded changed candidate")
        ast.parse(candidate.decode("utf-8"))
        patch = "".join(difflib.unified_diff(original.decode().splitlines(keepends=True),
                 candidate.decode().splitlines(keepends=True),fromfile="a/"+SOURCE,tofile="b/"+SOURCE)).encode()
        PATCH.parent.mkdir(parents=True,exist_ok=True)
        with PATCH.open("xb") as f:f.write(patch)
        report = {"status":"PROPOSAL_AWAITING_REVIEW","model_run_completed":True,
                  "candidate_persisted":True,"candidate_syntax_valid":True,
                  "production_written":False,"external_accounts_changed":False,
                  "source_file":SOURCE,"task":TASK,"source_sha256":sha(original),
                  "candidate_artifact":PATCH.as_posix(),"candidate_artifact_sha256":sha(patch),
                  "candidate_sha256":sha(candidate),"engine":"mini_swe_agent_local",
                  "human_review_required":True}
        report_path=OUT/"candidate-report.json"
        report_path.write_text(json.dumps(report,indent=2))
    finally:
        model.client.close()
        subprocess.run(["docker","rm","-f",env.container_id],capture_output=True,timeout=30)
        env.container_id=None
    if ACCEPTANCE:
        TASK_ACCEPTANCE[(SOURCE,TASK)] = ACCEPTANCE
    verdict=verify(report_path,OUT/"independent-verdict.json")
    print(json.dumps({"native":summary,"independent":verdict},sort_keys=True))
    # An unfamiliar task without an independent behavioral grader remains
    # review-only even when all existing regressions pass.
    return 0 if verdict.get("existing_focused_tests_passed") is True and (not ACCEPTANCE or verdict.get("task_acceptance_passed") is True) else 2

if __name__=="__main__":
    raise SystemExit(main())

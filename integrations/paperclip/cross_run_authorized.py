"""Owner-authorized, signed public predecessor continuation; no arbitrary tools.

The existing cross-run workflow calls this only from an original owner issue
on main. A durable reservation precedes any new model work. Only attested
public pipeline memory is admitted, never model-selected URLs or private data.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile

from checkpoint_store import encoded
from cross_run_memory import validate_pin, validate_pinned_source, validate_pinned_memory
from mission_scope import validate_scope
from pipeline_contract import EXPORTS, digest
from plenum_ai.public_issue_wake import BASE, REPO, OWNER, checked_issue_number, gh_json, prior_execution_bodies

TITLE = "[Plenum Paperclip] authorized cross-run continuation"
MAGIC = "PLENUM_PUBLIC_CROSS_RUN_V2"
OBJECTIVES = {
    "engineering": "Determine effective capacity, required module count and daily energy requirement.",
    "commercial": "Calculate daily operating cost, daily margin and whole-day payback.",
}
PARAMETERS = {
    "engineering": {"target_mg_day", "nominal_mg_day", "energy_wh_module_day"},
    "commercial": {"tariff_cents_kwh", "labor_cents_module_day", "revenue_cents_day", "capital_cents_module"},
}


def unique_pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("Duplicate request field")
        result[key] = value
    return result


def parse_request(event):
    if (not isinstance(event, dict) or event.get("action") != "opened"
            or (event.get("repository") or {}).get("full_name") != REPO
            or (event.get("sender") or {}).get("login") != OWNER):
        raise PermissionError("Original owner issue event required")
    issue = event.get("issue") or {}
    number = checked_issue_number(issue.get("number"))
    body = issue.get("body")
    if (issue.get("title") != TITLE or (issue.get("user") or {}).get("login") != OWNER
            or "pull_request" in issue or issue.get("state") != "open"
            or not isinstance(body, str) or len(body) > 2400
            or not body.startswith(MAGIC + "\n")):
        raise PermissionError("Exact open owner continuation issue required")
    request = json.loads(body[len(MAGIC)+1:], object_pairs_hook=unique_pairs)
    if not isinstance(request, dict) or set(request) != {"source", "parameters", "dois"}:
        raise ValueError("Exact continuation request required")
    pin = validate_pin(request["source"])
    stage = "engineering" if pin["stage"] == "science" else "commercial"
    params = request["parameters"]
    if (not isinstance(params, dict) or set(params) != PARAMETERS[stage]
            or any(type(v) is not int or not 1 <= v <= 10**9 for v in params.values())):
        raise ValueError("Bounded successor parameters required")
    dois = request["dois"]
    if (not isinstance(dois, list) or not 1 <= len(dois) <= 2
            or any(not isinstance(x, str) or not re.fullmatch(r"10\.[0-9]{4,9}/[a-z0-9][a-z0-9.()/_+-]{0,100}", x) for x in dois)
            or len(set(dois)) != len(dois)):
        raise ValueError("Bounded public DOI identifiers required")
    return number, stage, request


def build_scope(request, prior, run, commit):
    pin = request["source"]
    validate_pinned_memory(prior, pin, run, commit)
    stage = "engineering" if pin["stage"] == "science" else "commercial"
    return validate_scope({"kind": "public_objective", "objective": OBJECTIVES[stage],
        "dois": request["dois"], "inputs": {"pipeline": {"stage": stage,
        "parameters": request["parameters"], "prior": prior}},
        "operation_commitment": digest(sorted(EXPORTS[stage]))})


def archive_memory(raw, pin):
    if not 0 < len(raw) <= 65536 or hashlib.sha256(raw).hexdigest() != pin["zip_sha256"]:
        raise ValueError("Predecessor archive digest or size mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        if (len(entries) != 1 or entries[0].filename != "memory.json"
                or not 0 < entries[0].file_size <= 32768 or archive.testzip() is not None):
            raise ValueError("Unexpected predecessor archive contents")
        memory = archive.read(entries[0])
    if hashlib.sha256(memory).hexdigest() != pin["memory_sha256"]:
        raise ValueError("Exact signed bytes required")
    return memory


def reserve(event, token, run, *, reader=gh_json):
    number, stage, request = parse_request(event)
    if not token or not re.fullmatch(r"[1-9][0-9]{0,12}", run):
        raise PermissionError("Missing authorized run")
    url = BASE + str(number)
    original = reader(url, token)
    issue = event["issue"]
    if (original.get("number") != number or original.get("state") != "open"
            or "pull_request" in original or (original.get("user") or {}).get("login") != OWNER
            or original.get("title") != TITLE or original.get("body") != issue["body"]):
        raise PermissionError("Changed or untrusted original issue")
    comments = reader(url + "/comments?per_page=100", token)
    if (not isinstance(comments, list) or original.get("comments") != len(comments)
            or prior_execution_bodies(number, comments)):
        raise PermissionError("Incomplete history or prior execution; never replay")
    ack = reader(url + "/comments", token, body={"body":
        f"<!-- plenum-public-workforce-run:{run}:execution-reserved -->\n"
        "Original signed continuation reserved once. Request SHA256: " + digest(request)})
    if (not isinstance(ack, dict) or not ack.get("html_url")
            or (ack.get("user") or {}).get("login") != "github-actions[bot]"):
        raise RuntimeError("No authenticated reservation acknowledgment")
    return stage, request


def gh(args):
    return subprocess.run(["gh", *args], check=True, stdout=subprocess.PIPE,
                          timeout=60).stdout


def prepare(event, directory, run, commit):
    stage, request = reserve(event, os.environ["GH_TOKEN"], run)
    pin = request["source"]
    prefix = "repos/" + REPO + "/actions/"
    run_raw = gh(["api", prefix + "runs/" + pin["run_id"]])
    artifact_raw = gh(["api", prefix + "artifacts/" + str(pin["artifact_id"])])
    artifact = json.loads(artifact_raw)
    validate_pinned_source(json.loads(run_raw), artifact, pin)
    if type(artifact.get("size_in_bytes")) is not int or not 0 < artifact["size_in_bytes"] <= 65536:
        raise ValueError("Unbounded artifact download refused")
    raw = gh(["api", prefix + "artifacts/" + str(pin["artifact_id"]) + "/zip"])
    memory = archive_memory(raw, pin)
    directory.mkdir(parents=True, exist_ok=False)
    path = directory / "memory.json"
    path.write_bytes(memory)
    attestation = gh(["attestation", "verify", str(path), "--repo", REPO,
        "--signer-workflow", REPO + "/.github/workflows/paperclip-native-integration.yml",
        "--source-digest", pin["commit"], "--source-ref", pin["ref"],
        "--deny-self-hosted-runners", "--format", "json"])
    (directory / "attestation.json").write_bytes(attestation)
    (directory / "run.json").write_bytes(run_raw)
    (directory / "artifact.json").write_bytes(artifact_raw)
    (directory / "request.json").write_bytes(encoded(request))
    prior = json.loads(memory, object_pairs_hook=unique_pairs)
    return stage, build_scope(request, prior, run, commit)


def check_scope(event, scope, run, commit):
    _, stage, request = parse_request(event)
    scope = validate_scope(scope)
    prior = scope["inputs"]["pipeline"]["prior"]
    if build_scope(request, prior, run, commit) != scope:
        raise ValueError("Authorized successor scope mismatch")
    return stage, scope


def main():
    if (os.environ.get("GITHUB_REPOSITORY") != REPO or os.environ.get("GITHUB_ACTIONS") != "true"
            or os.environ.get("GITHUB_EVENT_NAME") != "issues" or os.environ.get("GITHUB_REF") != "refs/heads/main"
            or os.environ.get("GITHUB_ACTOR") != OWNER or os.environ.get("GITHUB_RUN_ATTEMPT") != "1"):
        raise PermissionError("Unexpected continuation execution environment")
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    run = os.environ["GITHUB_RUN_ID"]
    commit = os.environ["GITHUB_SHA"]
    if sys.argv[1:] == ["prepare"]:
        stage, scope = prepare(event, Path("reports/authorized-cross-run"), run, commit)
    elif sys.argv[1:] == ["check-scope"]:
        stage, scope = check_scope(event, json.loads(os.environ["AUTHORIZED_SCOPE"]), run, commit)
        if stage != os.environ["STAGE"]:
            raise ValueError("Successor stage mismatch")
    else:
        raise ValueError("Unknown continuation command")
    with open(os.environ["GITHUB_OUTPUT"], "a") as out:
        out.write("stage=" + stage + "\n")
        out.write("scope=" + encoded(scope).decode() + "\n")


if __name__ == "__main__":
    main()

"""Single registered, independently accepted engineering promotion.

Only trusted main code runs with a job-local merge token. No candidate code,
new credentials, arbitrary paths, bypass, direct push, or inference.
"""
from plenum_ai.engineering_event_controller import request, authorized_pr, SHA

PR = 928
FILES = {
    ".github/workflows/prometheus-whisper-local.yml": "3f82c2ed3f180b52693be5464e3df822c46ccb16",
    ".github/workflows/prometheus-whisper-promotion.yml": "cf1a78c166a422dc75221f3a90bf96d3c17ba73d",
}
CHECKS = {
    "Prometheus | Accepted speech correction promotion",
    "Paperclip import and entrypoint gate",
    "Browser progress ledger guard",
}
ACCEPTANCE_RUN = 45773714957
ACCEPTANCE_HEAD = "0ade26ed7680d192502e281316535dad4465d30f"
ARTIFACT = 15095391384
DIGEST = "sha256:f49e4f032d49332d0d19ab351e876c9178cc2387ed1ea2916d0324456922c227"


def accepted(pr, main, comparison, runs, evidence, artifacts, jobs):
    if not authorized_pr(pr, PR) or pr.get("draft") is not False:
        return False
    head = pr["head"]["sha"]
    if not isinstance(main, str) or not SHA.fullmatch(main) or pr["base"].get("sha") != main:
        return False
    if comparison.get("merge_base_commit", {}).get("sha") != main:
        return False
    changed = comparison.get("files")
    if not isinstance(changed, list) or len(changed) != len(FILES):
        return False
    if {f.get("filename"): f.get("sha") for f in changed} != FILES:
        return False
    if any(f.get("status") != "added" for f in changed):
        return False
    if evidence.get("id") != ACCEPTANCE_RUN or evidence.get("head_sha") != ACCEPTANCE_HEAD or evidence.get("conclusion") != "success" or evidence.get("event") != "issues":
        return False
    if evidence.get("run_attempt") != 1 or evidence.get("repository", {}).get("full_name") != pr["base"]["repo"]["full_name"]:
        return False
    if not any(x.get("id") == ARTIFACT and x.get("digest") == DIGEST and x.get("expired") is False for x in artifacts):
        return False
    if not all(any(j.get("name") == name and j.get("run_id") == ACCEPTANCE_RUN and j.get("conclusion") == "success" for j in jobs)
               for name in ("observe-and-recover", "repair-whisper", "verify-whisper-repair")):
        return False
    for name in CHECKS:
        matches = [x for x in runs if x.get("name") == name and x.get("head_sha") == head and x.get("event") == "pull_request"]
        if not matches:
            return False
        latest = max(matches, key=lambda x: (x.get("id", 0), x.get("run_attempt", 0)))
        if latest.get("status") != "completed" or latest.get("conclusion") != "success":
            return False
        if latest.get("head_repository", {}).get("full_name") != pr["head"]["repo"]["full_name"]:
            return False
    return True


def snapshot():
    pr = request(f"/pulls/{PR}")
    if not authorized_pr(pr, PR) or pr.get("draft") is not False:
        return None
    head = pr["head"]["sha"]
    main = request("/branches/main")["commit"]["sha"]
    if pr["base"].get("sha") != main:
        return None
    comp = request(f"/compare/{main}...{head}")
    runs = request(f"/actions/runs?head_sha={head}&event=pull_request&per_page=100").get("workflow_runs", [])
    evidence = request(f"/actions/runs/{ACCEPTANCE_RUN}")
    artifacts = request(f"/actions/runs/{ACCEPTANCE_RUN}/artifacts?per_page=30").get("artifacts", [])
    jobs = request(f"/actions/runs/{ACCEPTANCE_RUN}/attempts/1/jobs?per_page=30").get("jobs", [])
    if accepted(pr, main, comp, runs, evidence, artifacts, jobs):
        return head, main
    return None


def promote():
    ready = snapshot()
    if ready is None:
        print("Not eligible: wait for exact accepted evidence and current base")
        return
    if snapshot() != ready:
        raise RuntimeError("Promotion authorization changed")
    head, main = ready
    # GitHub itself must enforce strict current-base checks, required status
    # checks, review rules and expected head. No bypass or direct branch write.
    outcome = request(f"/pulls/{PR}/merge", "PUT", {"sha": head, "merge_method": "merge"})
    if outcome.get("merged") is not True:
        raise RuntimeError("Protected merge not accepted")
    print("Registered independently accepted promotion merged:", outcome.get("sha"))


if __name__ == "__main__":
    promote()

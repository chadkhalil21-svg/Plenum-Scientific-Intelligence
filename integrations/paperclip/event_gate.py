"""Authorize one ORIGINAL owner-created, bounded public Paperclip qualification.

Only fixed public regression objective; not a production job host or generic agent.
Caller workflow owns per-issue concurrency. A durable GitHub bot reservation
precedes any inference. Ambiguous interruption is terminal, never auto-replayed.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from plenum_ai.public_issue_wake import BASE, REPO, checked_issue_number, gh_json, prior_execution_bodies

OWNER="chadkhalil21-svg"
TITLE="[Plenum Paperclip] public coastal qualification"
BODY="PLENUM_PAPERCLIP_PUBLIC_QUALIFICATION_V1\nobjective: Execute the reviewed five-division coastal monitoring qualification."


def authorize(issue, comments, number):
    if (not isinstance(issue,dict) or issue.get("number")!=number
        or issue.get("state")!="open" or "pull_request" in issue
        or (issue.get("user") or {}).get("login")!=OWNER
        or issue.get("title")!=TITLE or issue.get("body")!=BODY):
        return False
    if not isinstance(comments,list) or issue.get("comments")!=len(comments):
        raise ValueError("Incomplete or changed comment history")
    return not prior_execution_bodies(number,comments)


def reserve(number,token,run_id,attempt,*,reader=gh_json):
    number=checked_issue_number(number)
    if type(run_id) is not int or not 0<run_id<10**13 or attempt!=1:
        return False,None
    url=BASE+str(number)
    issue=reader(url,token)
    # Unrelated signed wakes do not consume the original task.
    if issue.get("title")!=TITLE:return False,None
    comments=reader(url+"/comments?per_page=100",token)
    if not authorize(issue,comments,number):return False,None
    created=datetime.fromisoformat(issue["created_at"].replace("Z","+00:00"))
    if created.tzinfo is None:raise ValueError("Missing source timestamp")
    ack=reader(url+"/comments",token,body={"body":
        f"<!-- plenum-public-workforce-run:{run_id}:execution-reserved -->\n"
        "Original bounded Paperclip qualification reserved; no automatic replay."})
    if not isinstance(ack,dict) or not ack.get("html_url"):
        raise RuntimeError("Reservation acknowledgment missing")
    return True,created.isoformat()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--issue",required=True)
    args=parser.parse_args()
    if os.environ.get("GITHUB_REPOSITORY")!=REPO:
        raise PermissionError("Unexpected repository")
    ok,created=reserve(args.issue,os.environ["GH_TOKEN"],int(os.environ["GITHUB_RUN_ID"]),
                       int(os.environ["GITHUB_RUN_ATTEMPT"]))
    with open(os.environ["GITHUB_OUTPUT"],"a") as out:
        out.write("authorized="+str(ok).lower()+"\n")
        if ok:out.write("created_at="+created+"\n")
    print(json.dumps({"authorized":ok,"issue":checked_issue_number(args.issue),"created_at":created}))


if __name__=="__main__":main()

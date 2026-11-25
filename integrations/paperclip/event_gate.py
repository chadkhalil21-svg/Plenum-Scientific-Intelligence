"""Authorize one ORIGINAL owner-created, bounded public Paperclip qualification.

Only fixed public regression objective; not a production job host or generic agent.
Caller workflow owns per-issue concurrency. A durable GitHub bot reservation
precedes any inference. Ambiguous interruption is terminal, never auto-replayed.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from plenum_ai.public_issue_wake import BASE, REPO, OWNER, PAPERCLIP_PUBLIC_TITLE, PAPERCLIP_EVIDENCE_TITLE, checked_issue_number, gh_json, prior_execution_bodies

from mission_scope import LEGACY, parse_body, digest
from checkpoint_store import encoded

TITLE=PAPERCLIP_PUBLIC_TITLE
BODY="PLENUM_PAPERCLIP_PUBLIC_QUALIFICATION_V1\nobjective: Execute the reviewed five-division coastal monitoring qualification."


def issue_scope(issue):
    if issue.get("title")==TITLE and issue.get("body")==BODY:return dict(LEGACY)
    if issue.get("title")==PAPERCLIP_EVIDENCE_TITLE:
        scope=parse_body(issue.get("body"))
        if any(k in scope.get("inputs",{}) for k in ("pipeline","composition","synthesis")):
            raise ValueError("Pipeline continuation requires independently attested memory workflow")
        return scope
    raise ValueError("Unapproved public mission envelope")


def authorize(issue, comments, number):
    if (not isinstance(issue,dict) or issue.get("number")!=number
        or issue.get("state")!="open" or "pull_request" in issue
        or (issue.get("user") or {}).get("login")!=OWNER
        or issue.get("title") not in (TITLE,PAPERCLIP_EVIDENCE_TITLE)):
        return False
    try:issue_scope(issue)
    except (ValueError,TypeError):
        return False
    if not isinstance(comments,list) or issue.get("comments")!=len(comments):
        raise ValueError("Incomplete or changed comment history")
    return not prior_execution_bodies(number,comments)


def reserve(number,token,run_id,attempt,*,reader=gh_json):
    number=checked_issue_number(number)
    if type(run_id) is not int or not 0<run_id<10**13 or attempt!=1:
        return False,None,None
    url=BASE+str(number)
    issue=reader(url,token)
    # Unrelated signed wakes do not consume the original task.
    if issue.get("title") not in (TITLE,PAPERCLIP_EVIDENCE_TITLE):return False,None,None
    comments=reader(url+"/comments?per_page=100",token)
    if not authorize(issue,comments,number):return False,None,None
    scope=issue_scope(issue)
    created=datetime.fromisoformat(issue["created_at"].replace("Z","+00:00"))
    if created.tzinfo is None or created>datetime.now(timezone.utc):
        raise ValueError("Invalid source timestamp")
    ack=reader(url+"/comments",token,body={"body":
        f"<!-- plenum-public-workforce-run:{run_id}:execution-reserved -->\n"
        "Original bounded Paperclip qualification reserved; no automatic replay. Scope SHA256: "+digest(scope)})
    if not isinstance(ack,dict) or not ack.get("html_url"):
        raise RuntimeError("Reservation acknowledgment missing")
    return True,created.isoformat(),scope


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--issue",required=True)
    args=parser.parse_args()
    if (os.environ.get("GITHUB_REPOSITORY")!=REPO or os.environ.get("GITHUB_ACTIONS")!="true"
            or os.environ.get("GITHUB_EVENT_NAME") not in ("issues","issue_comment","repository_dispatch","workflow_dispatch")):
        raise PermissionError("Unexpected repository or event")
    if not args.issue.isascii() or not args.issue.isdecimal():
        raise ValueError("Invalid public issue ID")
    number=checked_issue_number(int(args.issue))
    if str(number)!=args.issue:raise ValueError("Noncanonical issue ID")
    if not os.environ.get("GH_TOKEN"):raise PermissionError("Missing scoped issue token")
    ok,created,scope=reserve(number,os.environ["GH_TOKEN"],int(os.environ["GITHUB_RUN_ID"]),
                       int(os.environ["GITHUB_RUN_ATTEMPT"]))
    with open(os.environ["GITHUB_OUTPUT"],"a") as out:
        out.write("authorized="+str(ok).lower()+"\n")
        if ok:
            out.write("created_at="+created+"\n")
            out.write("scope="+encoded(scope).decode()+"\n")
    print(json.dumps({"authorized":ok,"issue":number,"created_at":created}))


if __name__=="__main__":main()

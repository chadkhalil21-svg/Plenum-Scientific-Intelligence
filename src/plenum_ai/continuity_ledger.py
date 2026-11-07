"""Validate and summarize a public-safe, source-linked AGI continuity ledger.

The strategic state lives on the separate research-memory branch. It contains
NO confidential research or personal data. No silent continuous awareness
is implied: future sessions must fetch the state before making status claims.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

SCHEMA="plenum-agi-program-continuity-v1"
ALLOWED_STATUS={"verified_foundation","measured_failure","scheduled","planned","not_achieved"}
TRUSTED="https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/"
MAX_BYTES=50000


def validate(value):
    if not isinstance(value,dict) or value.get("schema")!=SCHEMA:
        raise ValueError("Unknown public continuity ledger format")
    if (value.get("confidential_documents_copied") is not False
        or value.get("AGI_achieved") is not False
        or value.get("automatic_model_promotion") is not False):
        raise ValueError("Public ledger cannot claim AGI or include confidential content")
    mission=value.get("mission")
    if not isinstance(mission,str) or not 20<=len(mission)<=500:
        raise ValueError("Missing bounded public mission")
    date=value.get("last_reviewed_utc")
    try:
        timestamp=datetime.fromisoformat(date.replace("Z","+00:00"))
    except (TypeError,AttributeError,ValueError) as error:
        raise ValueError("Invalid UTC review timestamp") from error
    if timestamp.tzinfo is None or timestamp.utcoffset().total_seconds()!=0:
        raise ValueError("Review time must be UTC")
    items=value.get("evidence")
    if not isinstance(items,list) or not items or len(items)>30:
        raise ValueError("Missing bounded source-linked evidence")
    seen=set()
    for row in items:
        if not isinstance(row,dict) or row.get("status") not in ALLOWED_STATUS:
            raise ValueError("Invalid evidence status")
        identifier=row.get("id")
        link=row.get("url")
        if (not isinstance(identifier,str) or not identifier.isascii()
            or not 1<=len(identifier)<=64 or identifier in seen
            or not isinstance(link,str) or not link.startswith(TRUSTED)
            or len(link)>500):
            raise ValueError("Duplicate evidence or unreviewed source")
        seen.add(identifier)
        score=row.get("result")
        if score is not None:
            if (not isinstance(score,dict)
                or type(score.get("correct")) is not int
                or type(score.get("attempted")) is not int
                or not 0<=score["correct"]<=score["attempted"]<=100000):
                raise ValueError("Inconsistent independent benchmark score")
        if row.get("AGI_demonstrated") is not False:
            raise ValueError("Experiment cannot imply AGI")
    goals=value.get("next_actions")
    if not isinstance(goals,list) or not 1<=len(goals)<=12:
        raise ValueError("Missing ordered, bounded next actions")
    for i,row in enumerate(goals,1):
        if (not isinstance(row,dict)
            or row.get("priority")!=i
            or not isinstance(row.get("action"),str)
            or not 8<=len(row["action"])<=300):
            raise ValueError("Unprioritized or ambiguous next action")
    decisions=value.get("decisions")
    if not isinstance(decisions,list) or not decisions or len(decisions)>25:
        raise ValueError("Missing decisions and outcomes")
    for d in decisions:
        if not isinstance(d,dict) or not all(isinstance(d.get(k),str)
                                             and 4<=len(d[k])<=400
                                             for k in ("decision","reason")):
            raise ValueError("Invalid durable decision note")
    return value


def load(path):
    p=Path(path)
    if not p.is_file() or p.stat().st_size>MAX_BYTES:
        raise ValueError("Missing or oversized canonical public state")
    return validate(json.loads(p.read_text(encoding="utf-8")))


def brief(state):
    s=validate(state)
    lines=["Plenum Scientific Intelligence | durable public program state",
           "Reviewed UTC: "+s["last_reviewed_utc"],
           "Mission: "+s["mission"],
           "Verified AGI: NO",
           "Source-linked evidence:"]
    for item in s["evidence"]:
        measurement=item.get("result")
        ratio=" ("+str(measurement["correct"])+"/"+str(measurement["attempted"])+")" if measurement else ""
        lines.append("  - "+item["id"]+": "+item["status"]+ratio)
    lines.append("Next priorities:")
    for item in s["next_actions"]:
        lines.append("  "+str(item["priority"])+". "+item["action"])
    lines.append("This file is a checkpoint, not automatically consulted by new sessions.")
    return "\n".join(lines)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--state",required=True)
    p.add_argument("--print-brief",action="store_true")
    args=p.parse_args()
    state=load(args.state)
    print(brief(state) if args.print_brief else
          "Continuity ledger verified: "+str(len(state["evidence"]))+" evidence entries")


if __name__=="__main__":
    main()
